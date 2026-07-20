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
# Модель с vision для фото бирок/артикулов (по умолчанию та же)
VISION_MODEL = os.getenv("VISION_MODEL", OPENAI_MODEL)
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
OPERATOR_CHAT_ID = os.getenv("OPERATOR_CHAT_ID", "")


def require_bot_token() -> str:
    if not BOT_TOKEN:
        raise RuntimeError("Заполните BOT_TOKEN в .env")
    return BOT_TOKEN
