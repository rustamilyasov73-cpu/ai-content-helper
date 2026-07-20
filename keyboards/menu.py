"""Главное меню и inline-кнопки каталога."""

from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from services.catalog import Part


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Каталог"), KeyboardButton(text="🔍 Поиск")],
            [KeyboardButton(text="🛒 Корзина"), KeyboardButton(text="🤖 Помощник")],
            [KeyboardButton(text="ℹ️ Помощь")],
        ],
        resize_keyboard=True,
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
    return InlineKeyboardMarkup(inline_keyboard=rows)


def parts_keyboard(parts: list[Part], prefix: str = "part") -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{part.sku} · {part.price} ₽",
                callback_data=f"{prefix}:{part.id}",
            )
        ]
        for part in parts
    ]
    rows.append(
        [InlineKeyboardButton(text="« К категориям", callback_data="catalog")]
    )
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
                InlineKeyboardButton(text="« Назад", callback_data="catalog"),
            ],
        ]
    )


def cart_keyboard(is_empty: bool) -> InlineKeyboardMarkup:
    if is_empty:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📦 В каталог", callback_data="catalog")]
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Оформить заказ", callback_data="order"),
                InlineKeyboardButton(text="🗑 Очистить", callback_data="clear_cart"),
            ],
            [InlineKeyboardButton(text="📦 В каталог", callback_data="catalog")],
        ]
    )
