"""Журнал заявок AgroParts + выгрузка в 1С."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import BASE_DIR
from services.cart import Cart
from services.onec import OneCOrderResult, build_order_payload, push_order

logger = logging.getLogger(__name__)

ORDERS_DIR = BASE_DIR / "logs"
ORDERS_FILE = ORDERS_DIR / "orders.jsonl"


def order_items_from_cart(cart: Cart) -> list[dict[str, Any]]:
    return [
        {
            "id": item.part.id,
            "sku": item.part.sku,
            "name": item.part.name,
            "price": item.part.price,
            "qty": item.qty,
        }
        for item in cart.items.values()
    ]


def build_order_record(
    *,
    user_id: int | str,
    full_name: str,
    username: str | None,
    items: list[dict[str, Any]],
    note: str = "",
    phone: str = "",
    source: str = "telegram",
    external_id: str = "",
    total_price: int | None = None,
) -> dict[str, Any]:
    computed_total = sum(int(i.get("price", 0)) * int(i.get("qty", 0)) for i in items)
    total_qty = sum(int(i.get("qty", 0)) for i in items)
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "full_name": full_name,
        "username": username or "",
        "phone": phone,
        "note": note,
        "source": source,
        "external_id": external_id,
        "total_price": total_price if total_price is not None else computed_total,
        "total_qty": total_qty,
        "items": items,
    }


def append_order(record: dict[str, Any]) -> Path:
    ORDERS_DIR.mkdir(parents=True, exist_ok=True)
    with open(ORDERS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return ORDERS_FILE


def find_order_by_external_id(external_id: str) -> dict[str, Any] | None:
    if not external_id or not ORDERS_FILE.exists():
        return None
    found: dict[str, Any] | None = None
    with open(ORDERS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("type") == "onec_status":
                continue
            if str(row.get("external_id") or "") == external_id:
                found = row
    return found


def _attach_onec(
    record: dict[str, Any],
    *,
    phone: str,
    comment: str,
    customer_name: str,
    source: str,
    external_id: str,
    items: list[dict[str, Any]],
) -> OneCOrderResult:
    payload = build_order_payload(
        phone=phone,
        comment=comment,
        customer_name=customer_name,
        source=source,
        external_id=external_id,
        items=items,
        total_price=record["total_price"],
    )
    onec_result = push_order(payload)
    record["onec"] = {
        "ok": onec_result.ok,
        "skipped": onec_result.skipped,
        "number": onec_result.number,
        "ref": onec_result.ref,
        "message": onec_result.message,
    }
    if not onec_result.skipped:
        append_order(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "type": "onec_status",
                "external_id": external_id,
                "phone": phone,
                "onec": record["onec"],
            }
        )
    if not onec_result.ok and not onec_result.skipped:
        logger.error("1С отклонила заявку: %s", onec_result.message)
    elif onec_result.skipped:
        logger.info("1С пропущена: %s", onec_result.message)
    else:
        logger.info("Заявка в 1С: %s %s", onec_result.number or "", onec_result.message)
    return onec_result


def save_order(
    *,
    user_id: int,
    full_name: str,
    username: str | None,
    cart: Cart,
    note: str = "",
    phone: str = "",
    source: str = "telegram",
    push_to_onec: bool = True,
) -> tuple[Path, dict[str, Any], OneCOrderResult | None]:
    items = order_items_from_cart(cart)
    external_id = f"tg-{user_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    record = build_order_record(
        user_id=user_id,
        full_name=full_name,
        username=username,
        items=items,
        note=note,
        phone=phone,
        source=source,
        external_id=external_id,
        total_price=cart.total_price(),
    )
    path = append_order(record)

    onec_result: OneCOrderResult | None = None
    if push_to_onec:
        onec_result = _attach_onec(
            record,
            phone=phone,
            comment=note,
            customer_name=full_name,
            source=source,
            external_id=external_id,
            items=items,
        )
    return path, record, onec_result


def save_order_from_items(
    *,
    user_id: int | str,
    full_name: str,
    username: str | None,
    items: list[dict[str, Any]],
    note: str = "",
    phone: str = "",
    source: str = "api",
    total_price: int | None = None,
    external_id: str = "",
    push_to_onec: bool = True,
) -> tuple[Path, dict[str, Any], OneCOrderResult | None, bool]:
    """Сохранить заявку из API. Возвращает duplicate=True при повторном external_id."""
    if external_id:
        existing = find_order_by_external_id(external_id)
        if existing:
            onec = existing.get("onec") or {}
            return (
                ORDERS_FILE,
                existing,
                OneCOrderResult(
                    ok=bool(onec.get("ok", True)),
                    skipped=bool(onec.get("skipped", False)),
                    number=str(onec.get("number") or ""),
                    ref=str(onec.get("ref") or ""),
                    message=str(onec.get("message") or "Уже принята ранее"),
                ),
                True,
            )

    eid = external_id or f"{source}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    record = build_order_record(
        user_id=user_id,
        full_name=full_name,
        username=username,
        items=items,
        note=note,
        phone=phone,
        source=source,
        external_id=eid,
        total_price=total_price,
    )
    path = append_order(record)
    onec_result: OneCOrderResult | None = None
    if push_to_onec:
        onec_result = _attach_onec(
            record,
            phone=phone,
            comment=note,
            customer_name=full_name,
            source=source,
            external_id=eid,
            items=items,
        )
    return path, record, onec_result, False
