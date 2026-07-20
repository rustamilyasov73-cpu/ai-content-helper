"""Конфигурация AgroParts."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PARTS_FILE = DATA_DIR / "parts.json"

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
OPERATOR_CHAT_ID = os.getenv("OPERATOR_CHAT_ID", "")

# Мягкая проверка: падаем только при реальном запуске бота
def require_bot_token() -> str:
    if not BOT_TOKEN:
        raise RuntimeError("Заполните BOT_TOKEN в .env")
    return BOT_TOKEN
