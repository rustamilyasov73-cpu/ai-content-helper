"""Распознавание артикулов/бирок на фото (Vision OCR)."""

from __future__ import annotations

import base64
import json
import logging
import re
from dataclasses import dataclass, field

from openai import AsyncOpenAI

from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, VISION_MODEL
from services.catalog import Catalog, Part

logger = logging.getLogger(__name__)

# Типичные артикулы сельхозтехники: RE507922, 0.012.4890.0, AL156625, KK06696880
SKU_PATTERN = re.compile(
    r"(?i)(?<![A-Z0-9])("
    r"[A-Z]{1,4}[-_ ]?\d{4,10}"  # RE507922, AL-156625
    r"|\d+(?:\.\d+){1,4}"  # 0.012.4890.0
    r"|[A-Z]{2,}\d{3,}[A-Z0-9]*"  # KK06696880, VXE71076
    r"|\d{6,12}"  # длинные числовые
    r")(?![A-Z0-9])"
)

VISION_PROMPT = """\
Ты OCR-помощник магазина запчастей AgroParts.
На фото бирка, шильдик, узел, упаковка или этикетка сельхозтехники.
Извлеки ВСЕ читаемые артикулы/part number/OEM/номера деталей, бренд и полезный текст.

Верни ТОЛЬКО JSON без markdown:
{
  "raw_text": "весь распознанный текст кратко",
  "candidates": ["артикул1", "артикул2"],
  "brand": "бренд или пусто",
  "model": "модель техники или пусто",
  "notes": "что видно на фото одним предложением"
}

Правила:
- candidates — только коды деталей (не даты, не серийники машины целиком, если есть явный Part No)
- сохраняй буквы/цифры как на бирке, можно без лишних пробелов
- если ничего не читается — candidates: []
"""


@dataclass
class PhotoRecognition:
    raw_text: str = ""
    candidates: list[str] = field(default_factory=list)
    brand: str = ""
    model: str = ""
    notes: str = ""
    error: str = ""

    @property
    def ok(self) -> bool:
        return not self.error and bool(self.candidates or self.raw_text)


def _client() -> AsyncOpenAI | None:
    if not OPENAI_API_KEY:
        return None
    kwargs: dict = {"api_key": OPENAI_API_KEY}
    if OPENAI_BASE_URL:
        kwargs["base_url"] = OPENAI_BASE_URL
    return AsyncOpenAI(**kwargs)


def extract_sku_candidates(text: str) -> list[str]:
    """Достать похожие на артикулы токены из сырого текста."""
    found: list[str] = []
    seen: set[str] = set()
    for match in SKU_PATTERN.finditer(text or ""):
        token = re.sub(r"\s+", "", match.group(1)).upper()
        key = re.sub(r"[^A-Z0-9]", "", token)
        if len(key) < 5 or key in seen:
            continue
        seen.add(key)
        found.append(token)
    return found


def _parse_vision_json(content: str) -> PhotoRecognition:
    text = (content or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # модель вернула не JSON — вытащим артикулы регуляркой
        return PhotoRecognition(
            raw_text=text[:1000],
            candidates=extract_sku_candidates(text),
            notes="Распознан текст без строгого JSON",
        )

    candidates = [str(c).strip() for c in data.get("candidates", []) if str(c).strip()]
    raw_text = str(data.get("raw_text", "") or "")
    # дополним кандидатов из raw_text
    for extra in extract_sku_candidates(raw_text + " " + " ".join(candidates)):
        if extra not in candidates:
            candidates.append(extra)

    return PhotoRecognition(
        raw_text=raw_text,
        candidates=candidates,
        brand=str(data.get("brand", "") or ""),
        model=str(data.get("model", "") or ""),
        notes=str(data.get("notes", "") or ""),
    )


async def recognize_part_photo(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
) -> PhotoRecognition:
    client = _client()
    if client is None:
        return PhotoRecognition(
            error=(
                "Распознавание фото требует OPENAI_API_KEY в .env "
                "(модель с vision, например gpt-4o-mini)."
            )
        )
    if not image_bytes:
        return PhotoRecognition(error="Пустое изображение.")

    # ограничим размер ~4 МБ base64 payload
    if len(image_bytes) > 4_500_000:
        return PhotoRecognition(
            error="Фото слишком большое. Пришлите снимок бирки поближе (до ~4 МБ)."
        )

    b64 = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:{mime_type};base64,{b64}"
    model = VISION_MODEL or OPENAI_MODEL

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url, "detail": "high"},
                        },
                    ],
                }
            ],
            temperature=0.1,
            max_tokens=800,
        )
        content = response.choices[0].message.content or ""
        result = _parse_vision_json(content)
        if not result.candidates and result.raw_text:
            result.candidates = extract_sku_candidates(result.raw_text)
        return result
    except Exception as exc:  # noqa: BLE001
        logger.exception("Vision OCR failed")
        return PhotoRecognition(error=f"Не удалось распознать фото: {type(exc).__name__}")


def match_recognition(
    recognition: PhotoRecognition,
    catalog: Catalog,
    limit: int = 8,
) -> list[Part]:
    """Сопоставить кандидатов OCR с каталогом."""
    ordered: list[Part] = []
    seen: set[str] = set()

    queries: list[str] = []
    queries.extend(recognition.candidates)
    if recognition.brand:
        queries.append(recognition.brand)
    if recognition.model:
        queries.append(recognition.model)
    # отдельные токены из raw_text
    queries.extend(extract_sku_candidates(recognition.raw_text))

    for query in queries:
        for part in catalog.search(query, limit=5):
            if part.id not in seen:
                seen.add(part.id)
                ordered.append(part)
                if len(ordered) >= limit:
                    return ordered

    # запасной поиск по всему raw_text целиком
    if recognition.raw_text and len(ordered) < limit:
        for part in catalog.search(recognition.raw_text, limit=limit):
            if part.id not in seen:
                seen.add(part.id)
                ordered.append(part)
    return ordered[:limit]


def format_recognition(recognition: PhotoRecognition, matches: list[Part]) -> str:
    lines = ["<b>Распознавание фото</b>"]
    if recognition.notes:
        lines.append(recognition.notes)
    if recognition.brand or recognition.model:
        lines.append(
            "Техника: "
            + ", ".join(x for x in (recognition.brand, recognition.model) if x)
        )
    if recognition.candidates:
        codes = ", ".join(f"<code>{c}</code>" for c in recognition.candidates[:8])
        lines.append(f"Найденные коды: {codes}")
    elif recognition.raw_text:
        lines.append(f"Текст с фото: <i>{recognition.raw_text[:300]}</i>")

    if matches:
        lines.append(f"\nСовпадения в каталоге: {len(matches)}")
    else:
        lines.append(
            "\nВ каталоге точных совпадений нет. "
            "Можно уточнить артикул текстом через /search "
            "или добавить позицию в data/parts.json."
        )
    return "\n".join(lines)
