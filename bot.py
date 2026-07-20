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
    brands_keyboard,
    cart_keyboard,
    catalog_root_keyboard,
    categories_keyboard,
    contact_keyboard,
    main_menu,
    part_actions_keyboard,
    parts_keyboard,
)
from services.cart import CartStore
from services.catalog import Catalog
from services.llm import advise
from services.orders import save_order

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()
catalog = Catalog()
carts = CartStore()
bot: Bot | None = None


class Form(StatesGroup):
    waiting_search = State()
    waiting_ask = State()
    waiting_phone = State()
    waiting_order_note = State()


HELP_TEXT = (
    "<b>AgroParts</b> — запчасти для сельхозтехники\n\n"
    "Команды:\n"
    "/start — главное меню\n"
    "/catalog — категории и бренды\n"
    "/brands — список брендов\n"
    "/search &lt;запрос&gt; — поиск по артикулу, названию, бренду\n"
    "/cart — корзина (количество можно менять кнопками)\n"
    "/order — оформить заявку\n"
    "/ask &lt;вопрос&gt; — AI-помощник по подбору\n"
    "/reload — обновить каталог из файла\n"
    "/help — эта справка\n\n"
    "Примеры:\n"
    "<code>/search RE507922</code>\n"
    "<code>/search фильтр John Deere</code>\n"
    "<code>/ask какой масляный фильтр на 6R?</code>"
)


def _msg(callback: CallbackQuery) -> Message:
    if callback.message is None or not isinstance(callback.message, Message):
        raise RuntimeError("Нет сообщения для ответа")
    return callback.message


async def show_catalog_root(message: Message) -> None:
    await message.answer(
        "Каталог AgroParts — выберите способ просмотра:",
        reply_markup=catalog_root_keyboard(),
    )


async def show_categories(message: Message) -> None:
    await message.answer(
        "Категории:",
        reply_markup=categories_keyboard(catalog.categories()),
    )


async def show_brands(message: Message) -> None:
    brands = catalog.brands()
    if not brands:
        await message.answer("Бренды не найдены.")
        return
    await message.answer(
        "Бренды:",
        reply_markup=brands_keyboard(brands),
    )


async def show_cart(target: Message | CallbackQuery) -> None:
    user_id = target.from_user.id if target.from_user else 0
    cart = carts.get(user_id)
    problems = cart.validate_stock()
    text = cart.format()
    if problems:
        text = "⚠ Обновили корзину по остаткам:\n• " + "\n• ".join(problems) + "\n\n" + text
    markup = cart_keyboard(cart)
    if isinstance(target, CallbackQuery):
        message = _msg(target)
        try:
            await message.edit_text(text, reply_markup=markup, parse_mode="HTML")
        except Exception:
            await message.answer(text, reply_markup=markup, parse_mode="HTML")
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


async def begin_order(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user:
        return
    cart = carts.get(user.id)
    problems = cart.validate_stock()
    if problems:
        await message.answer(
            "⚠ " + "; ".join(problems),
            parse_mode="HTML",
        )
    if cart.is_empty():
        await message.answer("Корзина пуста. Добавьте позиции из каталога.")
        return
    await state.set_state(Form.waiting_phone)
    await message.answer(
        "Для заявки удобно оставить телефон — или нажмите «Пропустить».",
        reply_markup=contact_keyboard(),
    )


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Добро пожаловать в <b>AgroParts</b>!\n"
        "Оригинальные и аналоговые запчасти для тракторов и комбайнов.\n\n"
        "Откройте каталог, бренды или найдите деталь по артикулу.",
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
    await show_catalog_root(message)


@dp.message(Command("brands"))
@dp.message(F.text == "🏷 Бренды")
async def cmd_brands(message: Message, state: FSMContext) -> None:
    await state.clear()
    await show_brands(message)


@dp.message(Command("cart"))
@dp.message(F.text == "🛒 Корзина")
async def cmd_cart(message: Message, state: FSMContext) -> None:
    await state.clear()
    await show_cart(message)


@dp.message(Command("reload"))
async def cmd_reload(message: Message, state: FSMContext) -> None:
    await state.clear()
    count = catalog.reload()
    await message.answer(f"Каталог обновлён. Позиций: {count}")


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
    await begin_order(message, state)


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
        reply_markup=parts_keyboard(results, back_callback="catalog"),
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


@dp.message(Form.waiting_phone, F.contact)
async def on_phone_contact(message: Message, state: FSMContext) -> None:
    phone = message.contact.phone_number if message.contact else ""
    await state.update_data(phone=phone)
    await state.set_state(Form.waiting_order_note)
    await message.answer(
        "Телефон принят. Добавьте комментарий (модель техники) или отправьте «-».",
        reply_markup=main_menu(),
    )


@dp.message(Form.waiting_phone, F.text.casefold() == "пропустить")
async def on_phone_skip(message: Message, state: FSMContext) -> None:
    await state.update_data(phone="")
    await state.set_state(Form.waiting_order_note)
    await message.answer(
        "Оставьте комментарий к заявке (модель техники) или отправьте «-».",
        reply_markup=main_menu(),
    )


@dp.message(Form.waiting_phone)
async def on_phone_text(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    await state.update_data(phone=text)
    await state.set_state(Form.waiting_order_note)
    await message.answer(
        "Контакт сохранён. Добавьте комментарий или отправьте «-».",
        reply_markup=main_menu(),
    )


@dp.message(Form.waiting_order_note)
async def on_order_note(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    note = (message.text or "").strip()
    if note == "-":
        note = ""
    await place_order(message, note=note, phone=str(data.get("phone", "")))


async def place_order(message: Message, note: str = "", phone: str = "") -> None:
    user = message.from_user
    if not user:
        return
    cart = carts.get(user.id)
    problems = cart.validate_stock()
    if problems:
        await message.answer("⚠ " + "; ".join(problems))
    if cart.is_empty():
        await message.answer("Корзина пуста.", reply_markup=main_menu())
        return

    summary = cart.order_summary(user_note=note, phone=phone)
    username = f"@{user.username}" if user.username else "без username"
    operator_text = (
        f"<b>Новая заявка AgroParts</b>\n"
        f"Клиент: {user.full_name} ({username}), id={user.id}\n\n"
        f"{summary}"
    )

    try:
        save_order(
            user_id=user.id,
            full_name=user.full_name,
            username=user.username,
            cart=cart,
            note=note,
            phone=phone,
        )
    except Exception:
        logger.exception("Не удалось записать заявку в журнал")

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
    await _msg(callback).answer(
        "Каталог AgroParts — выберите способ просмотра:",
        reply_markup=catalog_root_keyboard(),
    )
    await callback.answer()


@dp.callback_query(F.data == "cats")
async def cb_cats(callback: CallbackQuery) -> None:
    await _msg(callback).answer(
        "Категории:",
        reply_markup=categories_keyboard(catalog.categories()),
    )
    await callback.answer()


@dp.callback_query(F.data == "brands")
async def cb_brands(callback: CallbackQuery) -> None:
    await _msg(callback).answer(
        "Бренды:",
        reply_markup=brands_keyboard(catalog.brands()),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("cat:"))
async def cb_category(callback: CallbackQuery) -> None:
    category = (callback.data or "").split(":", 1)[1]
    parts = catalog.by_category(category)
    if not parts:
        await callback.answer("В категории пусто", show_alert=True)
        return
    await _msg(callback).answer(
        "Позиции категории:",
        reply_markup=parts_keyboard(parts, back_callback="cats"),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("brand:"))
async def cb_brand(callback: CallbackQuery) -> None:
    try:
        idx = int((callback.data or "").split(":", 1)[1])
        brand = catalog.brands()[idx][0]
    except (ValueError, IndexError):
        await callback.answer("Бренд не найден", show_alert=True)
        return
    parts = catalog.by_brand(brand)
    if not parts:
        await callback.answer("Позиций нет", show_alert=True)
        return
    await _msg(callback).answer(
        f"Бренд {brand}:",
        reply_markup=parts_keyboard(parts, back_callback="brands"),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("part:"))
async def cb_part(callback: CallbackQuery) -> None:
    part_id = (callback.data or "").split(":", 1)[1]
    part = catalog.get(part_id)
    if not part:
        await callback.answer("Не найдено", show_alert=True)
        return
    await _msg(callback).answer(
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
    await callback.answer(f"В корзине: {qty} шт.")


@dp.callback_query(F.data.startswith("qty:"))
async def cb_qty(callback: CallbackQuery) -> None:
    try:
        _, part_id, delta_s = (callback.data or "").split(":", 2)
        delta = int(delta_s)
    except ValueError:
        await callback.answer("Ошибка", show_alert=True)
        return
    user_id = callback.from_user.id if callback.from_user else 0
    cart = carts.get(user_id)
    # подтянуть актуальные данные детали из каталога
    part = catalog.get(part_id)
    if part and part_id in cart.items:
        cart.items[part_id].part = part
    cart.change(part_id, delta)
    await show_cart(callback)


@dp.callback_query(F.data.startswith("del:"))
async def cb_del(callback: CallbackQuery) -> None:
    part_id = (callback.data or "").split(":", 1)[1]
    user_id = callback.from_user.id if callback.from_user else 0
    carts.get(user_id).remove(part_id)
    await show_cart(callback)


@dp.callback_query(F.data == "cart")
async def cb_cart(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show_cart(callback)


@dp.callback_query(F.data == "clear_cart")
async def cb_clear_cart(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id if callback.from_user else 0
    carts.get(user_id).clear()
    await show_cart(callback)


@dp.callback_query(F.data == "order")
async def cb_order(callback: CallbackQuery, state: FSMContext) -> None:
    await begin_order(_msg(callback), state)
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
