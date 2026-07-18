"""AI Content Helper — генерация постов и промптов."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from config import BOT_TOKEN
from prompts.templates import IDEAS_SYSTEM, POST_SYSTEM, PROMPT_SYSTEM
from services.llm import generate

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "AI Content Helper\n\n"
        "/post тема — пост для Telegram\n"
        "/ideas тема — 5 идей\n"
        "/prompt текст — улучшить промпт"
    )


@dp.message(Command("post"))
async def cmd_post(message: Message) -> None:
    topic = (message.text or "").removeprefix("/post").strip()
    if not topic:
        await message.answer("Пример: /post Как AI помогает бизнесу")
        return
    await message.answer(await generate(POST_SYSTEM, topic))


@dp.message(Command("ideas"))
async def cmd_ideas(message: Message) -> None:
    topic = (message.text or "").removeprefix("/ideas").strip()
    if not topic:
        await message.answer("Пример: /ideas канал про автоматизацию")
        return
    await message.answer(await generate(IDEAS_SYSTEM, topic))


@dp.message(Command("prompt"))
async def cmd_prompt(message: Message) -> None:
    text = (message.text or "").removeprefix("/prompt").strip()
    if not text:
        await message.answer("Пример: /prompt напиши пост про ботов")
        return
    await message.answer(await generate(PROMPT_SYSTEM, text))


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
