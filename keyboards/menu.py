"""Главное меню и inline-кнопки каталога."""

from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from services.cart import Cart
from services.catalog import Part


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Каталог"), KeyboardButton(text="🏷 Бренды")],
            [KeyboardButton(text="🔍 Поиск"), KeyboardButton(text="📷 Фото")],
            [KeyboardButton(text="🛒 Корзина"), KeyboardButton(text="🤖 Помощник")],
            [KeyboardButton(text="ℹ️ Помощь")],
        ],
        resize_keyboard=True,
    )


def contact_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить телефон", request_contact=True)],
            [KeyboardButton(text="Пропустить")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def catalog_root_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📂 Категории", callback_data="cats"),
                InlineKeyboardButton(text="🏷 Бренды", callback_data="brands"),
            ]
        ]
    )


def categories_keyboard(categories: list[tuple[str, str, int]]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for key, label, count in categories:
        row.append(
            InlineKeyboardButton(
                text=f"{label} ({count})",
                callback_data=f"cat:{key}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="« Каталог", callback_data="catalog")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def brands_keyboard(brands: list[tuple[str, int]]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for idx, (brand, count) in enumerate(brands):
        row.append(
            InlineKeyboardButton(
                text=f"{brand} ({count})",
                callback_data=f"brand:{idx}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="« Каталог", callback_data="catalog")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def parts_keyboard(
    parts: list[Part],
    *,
    back_callback: str = "cats",
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{part.sku} · {part.price} ₽",
                callback_data=f"part:{part.id}",
            )
        ]
        for part in parts
    ]
    rows.append([InlineKeyboardButton(text="« Назад", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def part_actions_keyboard(part_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ В корзину",
                    callback_data=f"add:{part_id}",
                )
            ],
            [
                InlineKeyboardButton(text="🛒 Корзина", callback_data="cart"),
                InlineKeyboardButton(text="« Каталог", callback_data="catalog"),
            ],
        ]
    )


def cart_keyboard(cart: Cart) -> InlineKeyboardMarkup:
    if cart.is_empty():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📦 В каталог", callback_data="catalog")]
            ]
        )

    rows: list[list[InlineKeyboardButton]] = []
    for item in cart.items.values():
        pid = item.part.id
        rows.append(
            [
                InlineKeyboardButton(text="➖", callback_data=f"qty:{pid}:-1"),
                InlineKeyboardButton(
                    text=f"{item.part.sku} ×{item.qty}",
                    callback_data=f"part:{pid}",
                ),
                InlineKeyboardButton(text="➕", callback_data=f"qty:{pid}:1"),
                InlineKeyboardButton(text="✕", callback_data=f"del:{pid}"),
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(text="✅ Оформить", callback_data="order"),
            InlineKeyboardButton(text="🗑 Очистить", callback_data="clear_cart"),
        ]
    )
    rows.append([InlineKeyboardButton(text="📦 В каталог", callback_data="catalog")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
