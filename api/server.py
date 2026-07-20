"""Лёгкий API: каталог, заявки и синхронизация с 1С."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.onec_sync import (  # noqa: E402
    enqueue_order_for_1c,
    import_from_file,
    import_nomenclature_payload,
)
from config import PARTS_FILE  # noqa: E402

ONEC_SAMPLE = ROOT / "data" / "1c" / "nomenclature.sample.json"
HOST = "0.0.0.0"
PORT = 8100


def load_parts() -> list:
    return json.loads(PARTS_FILE.read_text(encoding="utf-8"))


class Handler(BaseHTTPRequestHandler):
    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _json(self, code: int, payload: dict | list) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/", "/health"):
            self._json(200, {"ok": True, "service": "agroparts-api", "parts": len(load_parts())})
            return
        if path == "/parts":
            self._json(200, load_parts())
            return
        if path == "/1c/sample":
            self._json(200, json.loads(ONEC_SAMPLE.read_text(encoding="utf-8")))
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid json"})
            return

        if path == "/orders":
            # заявка из приложения → outbox 1С
            path_out = enqueue_order_for_1c(payload)
            # также локальный журнал
            logs = ROOT / "logs"
            logs.mkdir(exist_ok=True)
            with (logs / "orders.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
            self._json(201, {"ok": True, "onec_outbox": str(path_out), "id": payload.get("id")})
            return

        if path == "/1c/import":
            # 1С или шлюз присылает номенклатуру
            result = import_nomenclature_payload(payload)
            if result.error:
                self._json(400, {"ok": False, "error": result.error})
                return
            self._json(200, {"ok": True, "imported": result.imported})
            return

        if path == "/1c/import-file":
            file_path = Path(str(payload.get("path", ONEC_SAMPLE)))
            result = import_from_file(file_path)
            if result.error:
                self._json(400, {"ok": False, "error": result.error})
                return
            self._json(200, {"ok": True, "imported": result.imported, "source": result.source})
            return

        self._json(404, {"error": "not found"})

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("api: " + (fmt % args) + "\n")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"AgroParts API http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
