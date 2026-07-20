"""Опциональный AI-помощник по подбору запчастей."""

from __future__ import annotations

from openai import AsyncOpenAI

from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from services.catalog import Catalog

SYSTEM_PROMPT = (
    "Ты консультант магазина AgroParts по запчастям для сельхозтехники. "
    "Отвечай кратко на русском. Если данных из каталога недостаточно — "
    "честно скажи об этом и предложи уточнить артикул, бренд или модель техники. "
    "Не выдумывай наличие и цены вне переданного каталога."
)


def _client() -> AsyncOpenAI | None:
    if not OPENAI_API_KEY:
        return None
    kwargs: dict = {"api_key": OPENAI_API_KEY}
    if OPENAI_BASE_URL:
        kwargs["base_url"] = OPENAI_BASE_URL
    return AsyncOpenAI(**kwargs)


def _catalog_context(catalog: Catalog, query: str, limit: int = 5) -> str:
    matches = catalog.search(query, limit=limit)
    if not matches:
        # даём обзор категорий, если точного поиска нет
        cats = ", ".join(label for _, label, _ in catalog.categories())
        return f"По запросу совпадений нет. Доступные категории: {cats}."
    lines = []
    for part in matches:
        lines.append(
            f"- {part.sku}: {part.name}, бренд {part.brand}, "
            f"цена {part.price} ₽, остаток {part.stock} {part.unit}, "
            f"совместимость: {', '.join(part.compatible)}"
        )
    return "Найденные позиции:\n" + "\n".join(lines)


async def advise(query: str, catalog: Catalog) -> str:
    client = _client()
    context = _catalog_context(catalog, query)
    if client is None:
        # Работаем без API-ключа: отдаём результаты поиска
        matches = catalog.search(query, limit=5)
        if not matches:
            return (
                "AI-помощник отключён (нет OPENAI_API_KEY).\n"
                "Попробуйте /search артикул или название, либо откройте /catalog."
            )
        lines = ["Без AI — вот что нашлось в каталоге:\n"]
        for part in matches:
            lines.append(f"• <code>{part.sku}</code> — {part.name} ({part.price} ₽)")
        lines.append("\nОткройте карточку через поиск или каталог.")
        return "\n".join(lines)

    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Вопрос клиента: {query}\n\nКаталог:\n{context}",
                },
            ],
            temperature=0.3,
            max_tokens=500,
        )
        text = (response.choices[0].message.content or "").strip()
        return text or "Не удалось сформировать ответ. Уточните артикул."
    except Exception as exc:  # noqa: BLE001 — показать пользователю понятную ошибку
        return (
            "Сейчас AI-помощник недоступен. Используйте /search или /catalog.\n"
            f"Техническая деталь: {type(exc).__name__}"
        )
