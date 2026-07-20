"""Интеграция AgroParts с 1С:Бухгалтерия через HTTP-сервис.

Ожидаемый контракт HTTP-сервиса 1С (публикация hs/agroparts):

  GET  {base}/ping
  GET  {base}/nomenclature
  POST {base}/orders

См. docs/onec.md и onec/HTTPServiceModule.bsl
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from config import (
    ONEC_BASE_URL,
    ONEC_ENABLED,
    ONEC_PASSWORD,
    ONEC_TIMEOUT,
    ONEC_USER,
    PARTS_FILE,
)

logger = logging.getLogger(__name__)

CATEGORY_ALIASES: dict[str, str] = {
    "filters": "filters",
    "filter": "filters",
    "фильтры": "filters",
    "фильтр": "filters",
    "belts": "belts",
    "belt": "belts",
    "ремни": "belts",
    "ремень": "belts",
    "bearings": "bearings",
    "bearing": "bearings",
    "подшипники": "bearings",
    "подшипник": "bearings",
    "cutting": "cutting",
    "режущие": "cutting",
    "режущие элементы": "cutting",
    "нож": "cutting",
    "hydraulics": "hydraulics",
    "hydraulic": "hydraulics",
    "гидравлика": "hydraulics",
    "electrics": "electrics",
    "electric": "electrics",
    "электрика": "electrics",
    "chains": "chains",
    "chain": "chains",
    "цепи": "chains",
    "цепь": "chains",
    "chassis": "chassis",
    "ходовая": "chassis",
    "cooling": "cooling",
    "охлаждение": "cooling",
}


@dataclass(frozen=True)
class OneCOrderResult:
    ok: bool
    number: str = ""
    ref: str = ""
    message: str = ""
    skipped: bool = False
    raw: dict[str, Any] | None = None


@dataclass(frozen=True)
class SyncResult:
    ok: bool
    count: int = 0
    path: str = ""
    message: str = ""
    skipped: bool = False


def is_configured() -> bool:
    return bool(ONEC_ENABLED and ONEC_BASE_URL.strip())


def _auth() -> httpx.BasicAuth | None:
    if ONEC_USER:
        return httpx.BasicAuth(ONEC_USER, ONEC_PASSWORD)
    return None


def _url(path: str) -> str:
    base = ONEC_BASE_URL.rstrip("/")
    suffix = path if path.startswith("/") else f"/{path}"
    return f"{base}{suffix}"


def _client() -> httpx.Client:
    return httpx.Client(
        timeout=ONEC_TIMEOUT,
        auth=_auth(),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )


def ping() -> dict[str, Any]:
    """Проверка доступности HTTP-сервиса 1С."""
    if not is_configured():
        return {"ok": False, "enabled": False, "message": "1С не настроена (ONEC_ENABLED/ONEC_BASE_URL)"}
    with _client() as client:
        response = client.get(_url("/ping"))
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            data.setdefault("ok", True)
            return data
        return {"ok": True, "raw": data}


def fetch_nomenclature() -> list[dict[str, Any]]:
    """Загрузить номенклатуру из 1С."""
    if not is_configured():
        raise RuntimeError("1С не настроена: укажите ONEC_ENABLED=true и ONEC_BASE_URL")
    with _client() as client:
        response = client.get(_url("/nomenclature"))
        response.raise_for_status()
        data = response.json()
    if isinstance(data, dict):
        items = data.get("items") or data.get("nomenclature") or data.get("value") or []
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError("Неожиданный ответ /nomenclature от 1С")
    if not isinstance(items, list):
        raise ValueError("Поле items в ответе 1С должно быть массивом")
    return [normalize_part(item, index=i + 1) for i, item in enumerate(items) if _has_sku(item)]


def _has_sku(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    sku = _first(item, "sku", "SKU", "Артикул", "артикул", "Code", "code", "АртикулНоменклатуры")
    return bool(str(sku or "").strip())


def _first(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in item and item[key] not in (None, ""):
            return item[key]
    lower_map = {str(k).lower(): v for k, v in item.items()}
    for key in keys:
        if key.lower() in lower_map and lower_map[key.lower()] not in (None, ""):
            return lower_map[key.lower()]
    return None


def _as_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().replace(" ", "").replace(",", ".")
    try:
        return int(float(text))
    except ValueError:
        return default


def _as_str_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in re.split(r"[,;|/]+", text) if part.strip()]


def normalize_category(value: Any) -> str:
    raw = str(value or "filters").strip().lower().replace("ё", "е")
    return CATEGORY_ALIASES.get(raw, re.sub(r"[^a-z0-9_]+", "_", raw) or "filters")


def normalize_part(item: dict[str, Any], *, index: int) -> dict[str, Any]:
    sku = str(
        _first(item, "sku", "SKU", "Артикул", "артикул", "Code", "code", "АртикулНоменклатуры")
    ).strip()
    name = str(
        _first(item, "name", "Name", "Наименование", "наименование", "Description", "description")
        or sku
    ).strip()
    part_id = str(_first(item, "id", "ID", "Ref", "ref", "УникальныйИдентификатор") or "").strip()
    if not part_id:
        compact = re.sub(r"[^a-zA-Z0-9]+", "", sku).lower() or f"{index:04d}"
        part_id = f"1c-{compact}"[:64]

    brand = str(_first(item, "brand", "Brand", "Бренд", "бренд", "Производитель") or "1С").strip()
    category = normalize_category(_first(item, "category", "Category", "Категория", "ВидНоменклатуры"))
    compatible = _as_str_list(
        _first(item, "compatible", "Compatible", "Совместимость", "Модели", "models")
    )
    if not compatible:
        compatible = ["универсальный"]

    price = _as_int(_first(item, "price", "Price", "Цена", "цена", "ЦенаПродажи"), 0)
    stock = _as_int(_first(item, "stock", "Stock", "Остаток", "остаток", "Количество", "Balance"), 0)
    unit = str(_first(item, "unit", "Unit", "Единица", "ЕдиницаИзмерения") or "шт").strip() or "шт"
    description = str(
        _first(item, "description", "Description", "Описание", "Комментарий") or f"{name} ({sku})"
    ).strip()

    return {
        "id": part_id,
        "sku": sku,
        "name": name,
        "category": category,
        "brand": brand,
        "compatible": compatible,
        "price": max(price, 0),
        "stock": max(stock, 0),
        "unit": unit,
        "description": description,
    }


def write_parts(parts: list[dict[str, Any]], path: Path | None = None) -> Path:
    target = path or PARTS_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(parts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def sync_catalog(
    *,
    path: Path | None = None,
    mirror_paths: list[Path] | None = None,
) -> SyncResult:
    """Выгрузить номенклатуру из 1С в parts.json (и зеркала mobile)."""
    if not is_configured():
        return SyncResult(
            ok=False,
            skipped=True,
            message="1С отключена или не задан ONEC_BASE_URL",
        )
    parts = fetch_nomenclature()
    if not parts:
        return SyncResult(ok=False, count=0, message="1С вернула пустую номенклатуру")
    target = write_parts(parts, path=path)
    for mirror in mirror_paths or []:
        write_parts(parts, path=mirror)
    return SyncResult(
        ok=True,
        count=len(parts),
        path=str(target),
        message=f"Синхронизировано позиций: {len(parts)}",
    )


def build_order_payload(
    *,
    phone: str,
    comment: str = "",
    customer_name: str = "",
    source: str = "agroparts",
    external_id: str = "",
    items: list[dict[str, Any]],
    total_price: int | None = None,
) -> dict[str, Any]:
    normalized_items = []
    computed_total = 0
    for item in items:
        sku = str(item.get("sku") or "").strip()
        if not sku:
            continue
        qty = max(_as_int(item.get("qty"), 1), 1)
        price = max(_as_int(item.get("price"), 0), 0)
        computed_total += price * qty
        normalized_items.append(
            {
                "sku": sku,
                "name": str(item.get("name") or sku),
                "qty": qty,
                "price": price,
                "amount": price * qty,
            }
        )
    return {
        "external_id": external_id or f"ap-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "source": source,
        "ts": datetime.now(timezone.utc).isoformat(),
        "phone": phone.strip(),
        "comment": comment.strip(),
        "customer_name": customer_name.strip(),
        "total": total_price if total_price is not None else computed_total,
        "items": normalized_items,
    }


def push_order(payload: dict[str, Any]) -> OneCOrderResult:
    """Отправить заявку в 1С как документ заказа / заявку покупателя."""
    if not is_configured():
        return OneCOrderResult(
            ok=True,
            skipped=True,
            message="1С отключена — заявка сохранена только локально",
        )
    if not payload.get("items"):
        return OneCOrderResult(ok=False, message="Пустой состав заявки")
    if not str(payload.get("phone") or "").strip():
        return OneCOrderResult(
            ok=True,
            skipped=True,
            message="1С пропущена — нет телефона клиента",
        )

    with _client() as client:
        response = client.post(_url("/orders"), content=json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        if response.status_code >= 400:
            return OneCOrderResult(
                ok=False,
                message=f"1С HTTP {response.status_code}: {response.text[:300]}",
                raw={"status_code": response.status_code, "text": response.text[:1000]},
            )
        try:
            data = response.json()
        except ValueError:
            data = {"raw": response.text}

    if not isinstance(data, dict):
        return OneCOrderResult(ok=True, message="Заявка принята 1С", raw={"raw": data})

    ok = bool(data.get("ok", True))
    return OneCOrderResult(
        ok=ok,
        number=str(data.get("number") or data.get("Number") or data.get("Номер") or ""),
        ref=str(data.get("ref") or data.get("Ref") or data.get("Ссылка") or ""),
        message=str(data.get("message") or data.get("Message") or ("Принято" if ok else "Ошибка 1С")),
        raw=data,
    )


async def push_order_async(payload: dict[str, Any]) -> OneCOrderResult:
    """Асинхронная обёртка для бота/API."""
    if not is_configured():
        return OneCOrderResult(
            ok=True,
            skipped=True,
            message="1С отключена — заявка сохранена только локально",
        )
    if not payload.get("items"):
        return OneCOrderResult(ok=False, message="Пустой состав заявки")
    if not str(payload.get("phone") or "").strip():
        return OneCOrderResult(
            ok=True,
            skipped=True,
            message="1С пропущена — нет телефона клиента",
        )

    async with httpx.AsyncClient(
        timeout=ONEC_TIMEOUT,
        auth=_auth(),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    ) as client:
        response = await client.post(
            _url("/orders"),
            content=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        )
        if response.status_code >= 400:
            return OneCOrderResult(
                ok=False,
                message=f"1С HTTP {response.status_code}: {response.text[:300]}",
                raw={"status_code": response.status_code, "text": response.text[:1000]},
            )
        try:
            data = response.json()
        except ValueError:
            data = {"raw": response.text}

    if not isinstance(data, dict):
        return OneCOrderResult(ok=True, message="Заявка принята 1С", raw={"raw": data})

    ok = bool(data.get("ok", True))
    return OneCOrderResult(
        ok=ok,
        number=str(data.get("number") or data.get("Number") or data.get("Номер") or ""),
        ref=str(data.get("ref") or data.get("Ref") or data.get("Ссылка") or ""),
        message=str(data.get("message") or data.get("Message") or ("Принято" if ok else "Ошибка 1С")),
        raw=data,
    )
