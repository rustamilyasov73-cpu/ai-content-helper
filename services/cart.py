"""Корзина пользователя в памяти процесса."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from services.catalog import Part


@dataclass
class CartItem:
    part: Part
    qty: int = 1


@dataclass
class Cart:
    items: dict[str, CartItem] = field(default_factory=dict)

    def add(self, part: Part, qty: int = 1) -> int:
        if qty < 1:
            qty = 1
        if part.id in self.items:
            self.items[part.id].qty += qty
        else:
            self.items[part.id] = CartItem(part=part, qty=qty)
        return self.items[part.id].qty

    def set_qty(self, part_id: str, qty: int) -> None:
        if part_id not in self.items:
            return
        if qty <= 0:
            del self.items[part_id]
        else:
            self.items[part_id].qty = qty

    def remove(self, part_id: str) -> None:
        self.items.pop(part_id, None)

    def clear(self) -> None:
        self.items.clear()

    def is_empty(self) -> bool:
        return not self.items

    def total_qty(self) -> int:
        return sum(item.qty for item in self.items.values())

    def total_price(self) -> int:
        return sum(item.part.price * item.qty for item in self.items.values())

    def format(self) -> str:
        if self.is_empty():
            return "Корзина пуста. Найдите деталь через /search или каталог."
        lines = ["<b>Ваша корзина</b>\n"]
        for item in self.items.values():
            lines.append(
                f"• {item.part.name} (<code>{item.part.sku}</code>)\n"
                f"  {item.qty} × {item.part.price} ₽ = "
                f"<b>{item.part.price * item.qty} ₽</b>"
            )
        lines.append(f"\nИтого: <b>{self.total_price()} ₽</b> ({self.total_qty()} поз.)")
        return "\n".join(lines)

    def order_summary(self, user_note: str = "") -> str:
        body = self.format()
        if user_note:
            body += f"\n\nКомментарий: {user_note}"
        return body


class CartStore:
    def __init__(self) -> None:
        self._carts: dict[int, Cart] = defaultdict(Cart)

    def get(self, user_id: int) -> Cart:
        return self._carts[user_id]
