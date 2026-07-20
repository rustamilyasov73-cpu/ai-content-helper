"""Журнал заявок AgroParts + выгрузка в 1С."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import BASE_DIR
from services.cart import Cart
from services.onec import OneCOrderResult, build_order_payload, push_order, push_order_async

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
    record = build_order_record(
        user_id=user_id,
        full_name=full_name,
        username=username,
        items=items,
        note=note,
        phone=phone,
        source=source,
        total_price=cart.total_price(),
    )
    path = append_order(record)

    onec_result: OneCOrderResult | None = None
    if push_to_onec:
        payload = build_order_payload(
            phone=phone,
            comment=note,
            customer_name=full_name,
            source=source,
            external_id=str(record.get("external_id") or f"tg-{user_id}-{record['ts']}"),
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
        # допишем статус 1С отдельной строкой-обновлением не нужно —
        # фиксируем рядом в той же записи через rewrite last line слишком сложно;
        # пишем отдельный audit-хвост
        if not onec_result.skipped:
            append_order(
                {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "type": "onec_status",
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

    return path, record, onec_result


async def save_order_async(
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
) -> tuple[Path, dict[str, Any], OneCOrderResult | None]:
    record = build_order_record(
        user_id=user_id,
        full_name=full_name,
        username=username,
        items=items,
        note=note,
        phone=phone,
        source=source,
        external_id=external_id,
        total_price=total_price,
    )
    path = append_order(record)
    onec_result: OneCOrderResult | None = None
    if push_to_onec:
        payload = build_order_payload(
            phone=phone,
            comment=note,
            customer_name=full_name,
            source=source,
            external_id=external_id or f"{source}-{record['ts']}",
            items=items,
            total_price=record["total_price"],
        )
        onec_result = await push_order_async(payload)
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
                    "phone": phone,
                    "onec": record["onec"],
                }
            )
    return path, record, onec_result
