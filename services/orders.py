"""Журнал заявок AgroParts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from config import BASE_DIR
from services.cart import Cart
from services.onec_sync import enqueue_order_for_1c

ORDERS_DIR = BASE_DIR / "logs"
ORDERS_FILE = ORDERS_DIR / "orders.jsonl"


def save_order(
    *,
    user_id: int,
    full_name: str,
    username: str | None,
    cart: Cart,
    note: str = "",
    phone: str = "",
) -> Path:
    ORDERS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "id": f"ord-{int(datetime.now(timezone.utc).timestamp())}-{user_id}",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "ts": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "full_name": full_name,
        "username": username or "",
        "phone": phone,
        "comment": note,
        "note": note,
        "total": cart.total_price(),
        "total_price": cart.total_price(),
        "total_qty": cart.total_qty(),
        "items": [
            {
                "partId": item.part.id,
                "id": item.part.id,
                "sku": item.part.sku,
                "name": item.part.name,
                "price": item.part.price,
                "qty": item.qty,
            }
            for item in cart.items.values()
        ],
    }
    with open(ORDERS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    enqueue_order_for_1c(payload)
    return ORDERS_FILE
