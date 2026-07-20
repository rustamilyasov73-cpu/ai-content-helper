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
        if part.stock <= 0:
            return self.items[part.id].qty if part.id in self.items else 0
        current = self.items[part.id].qty if part.id in self.items else 0
        new_qty = min(current + qty, part.stock)
        self.items[part.id] = CartItem(part=part, qty=new_qty)
        return new_qty

    def change(self, part_id: str, delta: int) -> int:
        item = self.items.get(part_id)
        if not item:
            return 0
        return self.set_qty(part_id, item.qty + delta)

    def set_qty(self, part_id: str, qty: int) -> int:
        item = self.items.get(part_id)
        if not item:
            return 0
        if qty <= 0 or item.part.stock <= 0:
            del self.items[part_id]
            return 0
        item.qty = min(qty, item.part.stock)
        return item.qty

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

    def validate_stock(self) -> list[str]:
        """Вернуть список проблем по остаткам и поправить корзину."""
        problems: list[str] = []
        for item in list(self.items.values()):
            if item.part.stock <= 0:
                problems.append(f"{item.part.sku}: нет в наличии")
                self.remove(item.part.id)
            elif item.qty > item.part.stock:
                item.qty = item.part.stock
                problems.append(
                    f"{item.part.sku}: уменьшили до {item.part.stock} {item.part.unit}"
                )
        return problems

    def format(self) -> str:
        if self.is_empty():
            return "Корзина пуста. Найдите деталь через /search или каталог."
        lines = ["<b>Ваша корзина</b>\n"]
        for item in self.items.values():
            line_sum = item.part.price * item.qty
            lines.append(
                f"• {item.part.name} (<code>{item.part.sku}</code>)\n"
                f"  {item.qty} × {item.part.price} ₽ = <b>{line_sum} ₽</b>"
            )
        lines.append(
            f"\nИтого: <b>{self.total_price()} ₽</b> "
            f"({len(self.items)} поз., {self.total_qty()} шт.)"
        )
        return "\n".join(lines)

    def order_summary(self, user_note: str = "", phone: str = "") -> str:
        body = self.format()
        if phone:
            body += f"\n\nТелефон: {phone}"
        if user_note:
            body += f"\nКомментарий: {user_note}"
        return body


class CartStore:
    def __init__(self) -> None:
        self._carts: dict[int, Cart] = defaultdict(Cart)

    def get(self, user_id: int) -> Cart:
        return self._carts[user_id]
