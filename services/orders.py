"""Журнал заявок AgroParts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from config import BASE_DIR
from services.cart import Cart

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
        "ts": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "full_name": full_name,
        "username": username or "",
        "phone": phone,
        "note": note,
        "total_price": cart.total_price(),
        "total_qty": cart.total_qty(),
        "items": [
            {
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
    return ORDERS_FILE
