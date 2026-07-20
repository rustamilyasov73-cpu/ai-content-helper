"""HTTP API-шлюз AgroParts: заявки с телефона → журнал + 1С."""

from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from config import (
    API_HOST,
    API_PORT,
    API_TOKEN,
    BASE_DIR,
    PARTS_FILE,
)
from services.catalog import Catalog
from services.onec import is_configured, ping, sync_catalog
from services.orders import save_order_from_items

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agroparts.api")

catalog = Catalog()
MIRROR_PARTS = [
    BASE_DIR / "mobile" / "data" / "parts.json",
    BASE_DIR / "mobile" / "www" / "parts.json",
]


def _cors_headers(handler: BaseHTTPRequestHandler) -> None:
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-API-Token")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    _cors_headers(handler)
    handler.end_headers()
    handler.wfile.write(body)


def _empty_response(handler: BaseHTTPRequestHandler, status: int) -> None:
    handler.send_response(status)
    handler.send_header("Content-Length", "0")
    _cors_headers(handler)
    handler.end_headers()


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length") or "0")
    raw = handler.rfile.read(length) if length else b"{}"
    if not raw:
        return {}
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Ожидался JSON-объект")
    return data


def _authorized(handler: BaseHTTPRequestHandler) -> bool:
    if not API_TOKEN:
        return True
    auth = handler.headers.get("Authorization", "")
    token_header = handler.headers.get("X-API-Token", "")
    if token_header and token_header == API_TOKEN:
        return True
    if auth.startswith("Bearer ") and auth.removeprefix("Bearer ").strip() == API_TOKEN:
        return True
    return False


class Handler(BaseHTTPRequestHandler):
    server_version = "AgroPartsAPI/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        logger.info("%s - %s", self.address_string(), fmt % args)

    def do_OPTIONS(self) -> None:  # noqa: N802
        _empty_response(self, 204)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path in {"/health", "/api/health"}:
            _json_response(
                self,
                200,
                {
                    "ok": True,
                    "service": "agroparts-api",
                    "onec_configured": is_configured(),
                    "parts": len(catalog.all()),
                },
            )
            return
        if path == "/api/parts":
            # публичный каталог для телефона
            parts = json.loads(Path(PARTS_FILE).read_text(encoding="utf-8"))
            _json_response(self, 200, {"ok": True, "count": len(parts), "items": parts})
            return
        if path == "/api/onec/ping":
            if not _authorized(self):
                _json_response(self, 401, {"ok": False, "message": "Unauthorized"})
                return
            try:
                _json_response(self, 200, ping())
            except Exception as exc:
                _json_response(self, 502, {"ok": False, "message": str(exc)})
            return
        _json_response(self, 404, {"ok": False, "message": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path.rstrip("/") or "/"
        if not _authorized(self):
            _json_response(self, 401, {"ok": False, "message": "Unauthorized"})
            return

        try:
            data = _read_json(self)
        except Exception as exc:
            _json_response(self, 400, {"ok": False, "message": f"Некорректный JSON: {exc}"})
            return

        if path == "/api/orders":
            self._handle_order(data)
            return
        if path == "/api/sync/catalog":
            self._handle_sync()
            return
        _json_response(self, 404, {"ok": False, "message": "Not found"})

    def _handle_order(self, data: dict[str, Any]) -> None:
        phone = str(data.get("phone") or "").strip()
        items = data.get("items") or []
        if not phone:
            _json_response(self, 400, {"ok": False, "message": "Укажите phone"})
            return
        if not isinstance(items, list) or not items:
            _json_response(self, 400, {"ok": False, "message": "Пустой items"})
            return

        normalized = []
        for item in items:
            if not isinstance(item, dict):
                continue
            sku = str(item.get("sku") or "").strip()
            if not sku:
                continue
            normalized.append(
                {
                    "id": str(item.get("partId") or item.get("id") or ""),
                    "sku": sku,
                    "name": str(item.get("name") or sku),
                    "price": int(item.get("price") or 0),
                    "qty": max(int(item.get("qty") or 1), 1),
                }
            )
        if not normalized:
            _json_response(self, 400, {"ok": False, "message": "Нет валидных позиций"})
            return

        path, record, onec_result, duplicate = save_order_from_items(
            user_id=str(data.get("user_id") or data.get("device_id") or "mobile"),
            full_name=str(data.get("customer_name") or data.get("full_name") or "Мобильный клиент"),
            username=str(data.get("username") or ""),
            items=normalized,
            note=str(data.get("comment") or data.get("note") or ""),
            phone=phone,
            source=str(data.get("source") or "mobile"),
            external_id=str(data.get("id") or data.get("external_id") or ""),
            total_price=int(data["total"]) if data.get("total") is not None else None,
        )
        payload = {
            "ok": True,
            "duplicate": duplicate,
            "order_id": record.get("external_id") or record.get("ts"),
            "saved": str(path),
            "total": record.get("total_price"),
            "onec": None
            if onec_result is None
            else {
                "ok": onec_result.ok,
                "skipped": onec_result.skipped,
                "number": onec_result.number,
                "ref": onec_result.ref,
                "message": onec_result.message,
            },
        }
        if duplicate:
            payload["message"] = "Заявка уже была принята ранее"
        status = 200 if (onec_result is None or onec_result.ok or onec_result.skipped) else 502
        if status == 502:
            payload["ok"] = False
            payload["message"] = onec_result.message if onec_result else "Ошибка 1С"
        _json_response(self, status, payload)

    def _handle_sync(self) -> None:
        result = sync_catalog(mirror_paths=[p for p in MIRROR_PARTS if p.parent.exists()])
        if result.ok:
            catalog.reload()
        status = 200 if result.ok else (503 if result.skipped else 502)
        _json_response(
            self,
            status,
            {
                "ok": result.ok,
                "skipped": result.skipped,
                "count": result.count,
                "path": result.path,
                "message": result.message,
            },
        )


def main() -> None:
    server = ThreadingHTTPServer((API_HOST, API_PORT), Handler)
    logger.info(
        "AgroParts API on http://%s:%s (1C configured=%s)",
        API_HOST,
        API_PORT,
        is_configured(),
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
