"""Обмен с 1С:Бухгалтерия — импорт номенклатуры и выгрузка заявок.

Поддерживаются два режима:
1) Файловый обмен JSON (выгрузка из 1С в data/1c/)
2) HTTP JSON API (публикация HTTP-сервиса в 1С или промежуточный шлюз)

Формат номенклатуры совместим с типовыми реквизитами:
Артикул, Код, Описание, Цена, Остаток, СтавкаНДС, ЕдиницаИзмерения, Штрихкод.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from config import BASE_DIR, PARTS_FILE

logger = logging.getLogger(__name__)

ONEC_DIR = BASE_DIR / "data" / "1c"
ORDERS_OUTBOX = ONEC_DIR / "orders_outbox"
ORDERS_SENT = ONEC_DIR / "orders_sent"


CATEGORY_FROM_1C = {
    "фильтры": "filters",
    "ремни": "belts",
    "подшипники": "bearings",
    "режущие элементы": "cutting",
    "гидравлика": "hydraulics",
    "электрика": "electrics",
    "цепи": "chains",
    "ходовая": "chassis",
    "охлаждение": "cooling",
    "двигатель": "engine",
    "трансмиссия": "transmission",
    "уплотнения": "seals",
    "освещение": "lighting",
    "кабина": "cabin",
}


@dataclass
class SyncResult:
    imported: int = 0
    updated: int = 0
    source: str = ""
    error: str = ""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_list(payload: Any) -> list[dict]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("Номенклатура", "nomenclature", "value", "items", "Goods"):
            if isinstance(payload.get(key), list):
                return [x for x in payload[key] if isinstance(x, dict)]
        # одиночный объект
        return [payload]
    return []


def _get(item: dict, *keys: str, default: Any = "") -> Any:
    for key in keys:
        if key in item and item[key] not in (None, ""):
            return item[key]
    lower = {str(k).lower(): v for k, v in item.items()}
    for key in keys:
        if key.lower() in lower and lower[key.lower()] not in (None, ""):
            return lower[key.lower()]
    return default


def map_1c_item(item: dict, index: int) -> dict:
    sku = str(_get(item, "Артикул", "sku", "OEM", "Article", default=f"SKU-{index}"))
    code_1c = str(_get(item, "Code", "Код", "Ref_Key", "code_1c", default=f"1C-{index:06d}"))
    name = str(_get(item, "Description", "Наименование", "name", "full_name", default=sku))
    category_raw = str(_get(item, "Группа", "category_1c", "category", default="filters"))
    category = CATEGORY_FROM_1C.get(category_raw.lower(), category_raw if category_raw.isascii() else "filters")
    brand = str(_get(item, "Бренд", "brand", "Производитель", default=""))
    manufacturer = str(_get(item, "Производитель", "manufacturer", default=brand))
    compatible_raw = str(_get(item, "Совместимость", "compatible", default=""))
    compatible = [x.strip() for x in compatible_raw.replace(";", ",").split(",") if x.strip()]
    analogues_raw = str(_get(item, "Аналоги", "analogues", default=""))
    analogues = [x.strip() for x in analogues_raw.replace(";", ",").split(",") if x.strip()]
    specs = _get(item, "Характеристики", "specs", default={}) or {}
    if isinstance(specs, str):
        specs = {"note": specs}
    vat = _get(item, "СтавкаНДС", "vat_rate", default=20)
    if isinstance(vat, str):
        digits = "".join(ch for ch in vat if ch.isdigit())
        vat = int(digits or 20)
    unit = str(_get(item, "ЕдиницаИзмерения", "unit", default="шт"))
    return {
        "id": f"1c-{code_1c}".replace(" ", ""),
        "sku": sku,
        "oem": str(_get(item, "OEM", "oem", default=sku)),
        "code_1c": code_1c,
        "name": name,
        "full_name": str(_get(item, "ПолноеНаименование", "full_name", default=f"{name} {brand} {sku}")),
        "category": category,
        "category_1c": category_raw or category,
        "brand": brand,
        "manufacturer": manufacturer,
        "compatible": compatible,
        "price": int(float(_get(item, "Цена", "price", default=0) or 0)),
        "price_purchase": int(float(_get(item, "ЦенаЗакупки", "price_purchase", default=0) or 0)),
        "vat_rate": int(vat),
        "currency": "RUB",
        "stock": int(float(_get(item, "Остаток", "stock", default=0) or 0)),
        "warehouse": str(_get(item, "Склад", "warehouse", default="Основной склад")),
        "unit": unit,
        "unit_okei": str(_get(item, "КодОКЕИ", "unit_okei", default="796")),
        "weight_kg": float(_get(item, "Вес", "weight_kg", default=0) or 0),
        "barcode": str(_get(item, "Штрихкод", "barcode", default="")),
        "country": str(_get(item, "Страна", "country", default="")),
        "analogues": analogues,
        "description": str(_get(item, "Комментарий", "description", default="")),
        "specs": specs if isinstance(specs, dict) else {},
        "active": not bool(_get(item, "DeletionMark", "deletion_mark", default=False)),
        "updated_at": _now(),
    }


def import_nomenclature_payload(payload: Any, parts_file: Path | None = None) -> SyncResult:
    items = _as_list(payload)
    if not items:
        return SyncResult(error="В файле нет номенклатуры")

    mapped = [map_1c_item(item, i + 1) for i, item in enumerate(items)]
    mapped = [p for p in mapped if p.get("active", True)]
    target = parts_file or PARTS_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(mapped, ensure_ascii=False, indent=2), encoding="utf-8")
    # зеркала для мобильного приложения
    mirrors = [
        BASE_DIR / "mobile" / "www" / "parts.json",
        BASE_DIR / "mobile" / "data" / "parts.json",
    ]
    raw = target.read_text(encoding="utf-8")
    for mirror in mirrors:
        if mirror.parent.exists():
            mirror.write_text(raw, encoding="utf-8")
    return SyncResult(imported=len(mapped), updated=len(mapped), source=str(target))


def import_from_file(path: Path, parts_file: Path | None = None) -> SyncResult:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return SyncResult(error=f"Не удалось прочитать {path}: {exc}")
    result = import_nomenclature_payload(payload, parts_file=parts_file)
    if not result.error:
        result.source = str(path)
    return result


def import_from_http(url: str, token: str = "", parts_file: Path | None = None) -> SyncResult:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, headers=headers, method="GET")
    try:
        with urlopen(req, timeout=60) as resp:  # noqa: S310
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        return SyncResult(error=f"Ошибка HTTP 1С: {exc}")
    result = import_nomenclature_payload(payload, parts_file=parts_file)
    if not result.error:
        result.source = url
    return result


def enqueue_order_for_1c(order: dict) -> Path:
    """Кладёт заявку в outbox для загрузки в 1С как заказ покупателя / реализация."""
    ORDERS_OUTBOX.mkdir(parents=True, exist_ok=True)
    order_1c = {
        "Date": order.get("createdAt") or _now(),
        "Number": order.get("id"),
        "CounterpartyPhone": order.get("phone", ""),
        "Comment": order.get("comment", ""),
        "Currency": "RUB",
        "VATIncluded": True,
        "Items": [
            {
                "Артикул": item.get("sku"),
                "Description": item.get("name"),
                "Quantity": item.get("qty"),
                "Price": item.get("price"),
                "Amount": int(item.get("qty", 0)) * int(item.get("price", 0)),
                "code_1c": item.get("code_1c", ""),
                "partId": item.get("partId", ""),
            }
            for item in order.get("items", [])
        ],
        "Total": order.get("total", 0),
        "Source": "AgroParts",
    }
    path = ORDERS_OUTBOX / f"{order.get('id', 'order')}.json"
    path.write_text(json.dumps(order_1c, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def export_pending_orders() -> list[Path]:
    if not ORDERS_OUTBOX.exists():
        return []
    return sorted(ORDERS_OUTBOX.glob("*.json"))


def mark_order_sent(path: Path) -> Path:
    ORDERS_SENT.mkdir(parents=True, exist_ok=True)
    target = ORDERS_SENT / path.name
    target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.unlink(missing_ok=True)
    return target


def push_order_http(order_path: Path, url: str, token: str = "") -> bool:
    raw = order_path.read_bytes()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, data=raw, headers=headers, method="POST")
    with urlopen(req, timeout=60) as resp:  # noqa: S310
        ok = 200 <= getattr(resp, "status", 200) < 300
    if ok:
        mark_order_sent(order_path)
    return ok
