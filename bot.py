"""AgroParts — Telegram-бот каталога запчастей для сельхозтехники."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config import OPERATOR_CHAT_ID, require_bot_token
from keyboards.menu import (
    cart_keyboard,
    categories_keyboard,
    main_menu,
    part_actions_keyboard,
    parts_keyboard,
)
from services.cart import CartStore
from services.catalog import Catalog
from services.llm import advise

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()
catalog = Catalog()
carts = CartStore()
bot: Bot | None = None


class Form(StatesGroup):
    waiting_search = State()
    waiting_ask = State()
    waiting_order_note = State()


HELP_TEXT = (
    "<b>AgroParts</b> — запчасти для сельхозтехники\n\n"
    "Команды:\n"
    "/start — главное меню\n"
    "/catalog — категории\n"
    "/search &lt;запрос&gt; — поиск по артикулу, названию, бренду\n"
    "/cart — корзина\n"
    "/order — оформить заявку\n"
    "/ask &lt;вопрос&gt; — AI-помощник по подбору\n"
    "/help — эта справка\n\n"
    "Примеры:\n"
    "<code>/search RE507922</code>\n"
    "<code>/search фильтр John Deere</code>\n"
    "<code>/ask какой масляный фильтр на 6R?</code>"
)


async def show_catalog(message: Message) -> None:
    await message.answer(
        "Выберите категорию:",
        reply_markup=categories_keyboard(catalog.categories()),
    )


async def show_cart(target: Message | CallbackQuery) -> None:
    user_id = target.from_user.id if target.from_user else 0
    cart = carts.get(user_id)
    text = cart.format()
    markup = cart_keyboard(cart.is_empty())
    if isinstance(target, CallbackQuery):
        await target.message.answer(text, reply_markup=markup, parse_mode="HTML")
        await target.answer()
    else:
        await target.answer(text, reply_markup=markup, parse_mode="HTML")


async def show_part(message: Message, part_id: str) -> None:
    part = catalog.get(part_id)
    if not part:
        await message.answer("Позиция не найдена.")
        return
    await message.answer(
        part.format_card(),
        reply_markup=part_actions_keyboard(part.id),
        parse_mode="HTML",
    )


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Добро пожаловать в <b>AgroParts</b>!\n"
        "Оригинальные и аналоговые запчасти для тракторов и комбайнов.\n\n"
        "Откройте каталог или найдите деталь по артикулу.",
        reply_markup=main_menu(),
        parse_mode="HTML",
    )


@dp.message(Command("help"))
@dp.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(HELP_TEXT, parse_mode="HTML", reply_markup=main_menu())


@dp.message(Command("catalog"))
@dp.message(F.text == "📦 Каталог")
async def cmd_catalog(message: Message, state: FSMContext) -> None:
    await state.clear()
    await show_catalog(message)


@dp.message(Command("cart"))
@dp.message(F.text == "🛒 Корзина")
async def cmd_cart(message: Message, state: FSMContext) -> None:
    await state.clear()
    await show_cart(message)


@dp.message(Command("search"))
async def cmd_search(message: Message, state: FSMContext) -> None:
    query = (message.text or "").removeprefix("/search").strip()
    if not query:
        await state.set_state(Form.waiting_search)
        await message.answer("Введите артикул, название или бренд:")
        return
    await state.clear()
    await reply_search(message, query)


@dp.message(F.text == "🔍 Поиск")
async def btn_search(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.waiting_search)
    await message.answer("Введите артикул, название или бренд:")


@dp.message(Command("ask"))
async def cmd_ask(message: Message, state: FSMContext) -> None:
    query = (message.text or "").removeprefix("/ask").strip()
    if not query:
        await state.set_state(Form.waiting_ask)
        await message.answer("Опишите технику и какую деталь ищете:")
        return
    await state.clear()
    await message.answer("Подбираю варианты…")
    await message.answer(await advise(query, catalog), parse_mode="HTML")


@dp.message(F.text == "🤖 Помощник")
async def btn_ask(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.waiting_ask)
    await message.answer("Опишите технику и какую деталь ищете:")


@dp.message(Command("order"))
async def cmd_order(message: Message, state: FSMContext) -> None:
    cart = carts.get(message.from_user.id)
    if cart.is_empty():
        await message.answer("Корзина пуста. Добавьте позиции из каталога.")
        return
    await state.set_state(Form.waiting_order_note)
    await message.answer(
        "Оставьте комментарий к заявке (телефон, модель техники) "
        "или отправьте «-» без комментария:"
    )


async def reply_search(message: Message, query: str) -> None:
    results = catalog.search(query)
    if not results:
        await message.answer(
            "Ничего не найдено. Попробуйте другой артикул или откройте /catalog."
        )
        return
    if len(results) == 1:
        await show_part(message, results[0].id)
        return
    await message.answer(
        f"Найдено: {len(results)}. Выберите позицию:",
        reply_markup=parts_keyboard(results),
    )


@dp.message(Form.waiting_search)
async def on_search_query(message: Message, state: FSMContext) -> None:
    if not message.text:
        return
    await state.clear()
    await reply_search(message, message.text)


@dp.message(Form.waiting_ask)
async def on_ask_query(message: Message, state: FSMContext) -> None:
    if not message.text:
        return
    await state.clear()
    await message.answer("Подбираю варианты…")
    await message.answer(await advise(message.text, catalog), parse_mode="HTML")


@dp.message(Form.waiting_order_note)
async def on_order_note(message: Message, state: FSMContext) -> None:
    await state.clear()
    note = (message.text or "").strip()
    if note == "-":
        note = ""
    await place_order(message, note)


async def place_order(message: Message, note: str = "") -> None:
    user = message.from_user
    if not user:
        return
    cart = carts.get(user.id)
    if cart.is_empty():
        await message.answer("Корзина пуста.")
        return

    summary = cart.order_summary(note)
    username = f"@{user.username}" if user.username else "без username"
    operator_text = (
        f"<b>Новая заявка AgroParts</b>\n"
        f"Клиент: {user.full_name} ({username}), id={user.id}\n\n"
        f"{summary}"
    )

    if OPERATOR_CHAT_ID and bot is not None:
        try:
            await bot.send_message(
                OPERATOR_CHAT_ID,
                operator_text,
                parse_mode="HTML",
            )
        except Exception:
            logger.exception("Не удалось отправить заявку оператору")

    await message.answer(
        "Заявка принята! Менеджер свяжется с вами.\n\n" + summary,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )
    cart.clear()


@dp.callback_query(F.data == "catalog")
async def cb_catalog(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(
        "Выберите категорию:",
        reply_markup=categories_keyboard(catalog.categories()),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("cat:"))
async def cb_category(callback: CallbackQuery) -> None:
    category = (callback.data or "").split(":", 1)[1]
    parts = catalog.by_category(category)
    if not parts:
        await callback.answer("В категории пусто", show_alert=True)
        return
    await callback.message.answer(
        "Позиции категории:",
        reply_markup=parts_keyboard(parts),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("part:"))
async def cb_part(callback: CallbackQuery) -> None:
    part_id = (callback.data or "").split(":", 1)[1]
    part = catalog.get(part_id)
    if not part:
        await callback.answer("Не найдено", show_alert=True)
        return
    await callback.message.answer(
        part.format_card(),
        reply_markup=part_actions_keyboard(part.id),
        parse_mode="HTML",
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("add:"))
async def cb_add(callback: CallbackQuery) -> None:
    part_id = (callback.data or "").split(":", 1)[1]
    part = catalog.get(part_id)
    if not part:
        await callback.answer("Не найдено", show_alert=True)
        return
    if not part.in_stock:
        await callback.answer("Нет в наличии", show_alert=True)
        return
    user_id = callback.from_user.id if callback.from_user else 0
    qty = carts.get(user_id).add(part)
    await callback.answer(f"Добавлено. В корзине: {qty} шт.")


@dp.callback_query(F.data == "cart")
async def cb_cart(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show_cart(callback)


@dp.callback_query(F.data == "clear_cart")
async def cb_clear_cart(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id if callback.from_user else 0
    carts.get(user_id).clear()
    await callback.message.answer("Корзина очищена.", reply_markup=main_menu())
    await callback.answer()


@dp.callback_query(F.data == "order")
async def cb_order(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id if callback.from_user else 0
    if carts.get(user_id).is_empty():
        await callback.answer("Корзина пуста", show_alert=True)
        return
    await state.set_state(Form.waiting_order_note)
    await callback.message.answer(
        "Оставьте комментарий к заявке (телефон, модель техники) "
        "или отправьте «-» без комментария:"
    )
    await callback.answer()


@dp.message()
async def fallback(message: Message, state: FSMContext) -> None:
    """Свободный текст — пробуем поиск."""
    if not message.text:
        return
    current = await state.get_state()
    if current:
        return
    await reply_search(message, message.text)


async def main() -> None:
    global bot
    bot = Bot(token=require_bot_token())
    logger.info("AgroParts bot starting, parts=%s", len(catalog.all()))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
