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

# --- 1С:Бухгалтерия (HTTP-сервис hs/agroparts) ---
ONEC_ENABLED = os.getenv("ONEC_ENABLED", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
ONEC_BASE_URL = os.getenv("ONEC_BASE_URL", "").strip()
ONEC_USER = os.getenv("ONEC_USER", "").strip()
ONEC_PASSWORD = os.getenv("ONEC_PASSWORD", "")
ONEC_TIMEOUT = float(os.getenv("ONEC_TIMEOUT", "30"))
# Telegram user id через запятую — кто может /sync1c
ONEC_ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ONEC_ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}
# API-шлюз для мобильного приложения → заявки в 1С
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8080"))
API_TOKEN = os.getenv("API_TOKEN", "").strip()


def require_bot_token() -> str:
    if not BOT_TOKEN:
        raise RuntimeError("Заполните BOT_TOKEN в .env")
    return BOT_TOKEN
