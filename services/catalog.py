"""Каталог запчастей: загрузка, поиск, категории, бренды."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from config import PARTS_FILE

CATEGORY_LABELS: dict[str, str] = {
    "filters": "Фильтры",
    "belts": "Ремни",
    "bearings": "Подшипники",
    "cutting": "Режущие элементы",
    "hydraulics": "Гидравлика",
    "electrics": "Электрика",
    "chains": "Цепи",
    "chassis": "Ходовая",
    "cooling": "Охлаждение",
}


@dataclass(frozen=True)
class Part:
    id: str
    sku: str
    name: str
    category: str
    brand: str
    compatible: list[str]
    price: int
    stock: int
    unit: str
    description: str

    @property
    def category_label(self) -> str:
        return CATEGORY_LABELS.get(self.category, self.category)

    @property
    def in_stock(self) -> bool:
        return self.stock > 0

    def format_card(self) -> str:
        stock_line = (
            f"✅ В наличии: {self.stock} {self.unit}"
            if self.in_stock
            else "❌ Нет в наличии"
        )
        compatible = ", ".join(self.compatible)
        price = f"{self.price:,}".replace(",", " ")
        return (
            f"<b>{self.name}</b>\n"
            f"Артикул: <code>{self.sku}</code>\n"
            f"Бренд: {self.brand}\n"
            f"Категория: {self.category_label}\n"
            f"Совместимость: {compatible}\n"
            f"Цена: <b>{price} ₽</b> / {self.unit}\n"
            f"{stock_line}\n\n"
            f"{self.description}"
        )


def _normalize(text: str) -> str:
    text = text.strip().lower().replace("ё", "е")
    text = re.sub(r"[\s\-_/.,;:]+", " ", text)
    return text.strip()


def _compact(text: str) -> str:
    """Артикул без разделителей: RE-507.922 → re507922."""
    return re.sub(r"[^a-z0-9а-я]+", "", _normalize(text))


def load_parts(path: Path | None = None) -> list[Part]:
    file_path = path or PARTS_FILE
    with open(file_path, encoding="utf-8") as f:
        raw = json.load(f)
    parts: list[Part] = []
    for item in raw:
        parts.append(
            Part(
                id=item["id"],
                sku=item["sku"],
                name=item["name"],
                category=item["category"],
                brand=item["brand"],
                compatible=list(item.get("compatible", [])),
                price=int(item["price"]),
                stock=int(item["stock"]),
                unit=item.get("unit", "шт"),
                description=item.get("description", ""),
            )
        )
    return parts


class Catalog:
    def __init__(self, parts: Iterable[Part] | None = None) -> None:
        self._parts: list[Part] = []
        self._by_id: dict[str, Part] = {}
        self._by_sku: dict[str, Part] = {}
        self._by_sku_compact: dict[str, Part] = {}
        if parts is not None:
            self._set_parts(list(parts))
        else:
            self.reload()

    def _set_parts(self, parts: list[Part]) -> None:
        self._parts = parts
        self._by_id = {p.id: p for p in self._parts}
        self._by_sku = {_normalize(p.sku): p for p in self._parts}
        self._by_sku_compact = {_compact(p.sku): p for p in self._parts}

    def reload(self, path: Path | None = None) -> int:
        self._set_parts(load_parts(path))
        return len(self._parts)

    def all(self) -> list[Part]:
        return list(self._parts)

    def get(self, part_id: str) -> Part | None:
        return self._by_id.get(part_id)

    def categories(self) -> list[tuple[str, str, int]]:
        counts: dict[str, int] = {}
        for part in self._parts:
            counts[part.category] = counts.get(part.category, 0) + 1
        result = []
        for key, label in CATEGORY_LABELS.items():
            if key in counts:
                result.append((key, label, counts[key]))
        for key, count in counts.items():
            if key not in CATEGORY_LABELS:
                result.append((key, key, count))
        return result

    def brands(self) -> list[tuple[str, int]]:
        counts: dict[str, int] = {}
        for part in self._parts:
            counts[part.brand] = counts.get(part.brand, 0) + 1
        return sorted(counts.items(), key=lambda item: item[0].lower())

    def by_category(self, category: str) -> list[Part]:
        return [p for p in self._parts if p.category == category]

    def by_brand(self, brand: str) -> list[Part]:
        needle = _normalize(brand)
        return [p for p in self._parts if _normalize(p.brand) == needle]

    def search(self, query: str, limit: int = 10) -> list[Part]:
        q = _normalize(query)
        if not q:
            return []

        q_compact = _compact(query)
        exact = self._by_sku.get(q) or self._by_sku_compact.get(q_compact)
        if exact:
            return [exact]

        scored: list[tuple[int, Part]] = []
        for part in self._parts:
            sku_n = _normalize(part.sku)
            sku_c = _compact(part.sku)
            name_n = _normalize(part.name)
            brand_n = _normalize(part.brand)
            haystack = _normalize(
                " ".join(
                    [
                        part.sku,
                        part.name,
                        part.brand,
                        part.category_label,
                        " ".join(part.compatible),
                        part.description,
                    ]
                )
            )
            score = 0
            if q == sku_n or q_compact == sku_c:
                score += 120
            elif q in sku_n or (q_compact and q_compact in sku_c):
                score += 100
            elif sku_c and q_compact and (sku_c in q_compact or q_compact in sku_c):
                # OCR часто дописывает/обрезает символы
                if abs(len(sku_c) - len(q_compact)) <= 2:
                    score += 80
            if q in name_n:
                score += 50
            if q in brand_n:
                score += 30
            for token in q.split():
                if token and token in haystack:
                    score += 10
                token_c = _compact(token)
                if token_c and token_c in sku_c:
                    score += 40
            if score:
                scored.append((score, part))

        scored.sort(key=lambda item: (-item[0], item[1].name))
        return [part for _, part in scored[:limit]]
