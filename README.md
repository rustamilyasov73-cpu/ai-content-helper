# AgroParts

Telegram-бот каталога запчастей для сельхозтехники: поиск по артикулу, категории и бренды, корзина с количеством и заявка менеджеру.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![aiogram](https://img.shields.io/badge/aiogram-3.x-blueviolet)
![Agro](https://img.shields.io/badge/AgroParts-Catalog-2e7d32)

---

## Задача

Ускорить подбор и заказ запчастей для тракторов и комбайнов:
- поиск по артикулу, названию и бренду;
- **распознавание бирок/узлов/артикулов по фото**;
- просмотр категорий и брендов;
- корзина с изменением количества;
- заявка с телефоном и комментарием;
- опциональный AI-помощник по подбору.

---

## Стек

- **Python 3.11+**
- **aiogram 3** — Telegram Bot API + FSM
- **JSON-каталог** — `data/parts.json`
- **OpenAI API** — `/ask` и **Vision OCR** для фото бирок (`gpt-4o-mini`)
- **python-dotenv** — конфигурация

---

## Функции

1. **Каталог** — категории и бренды
2. **Поиск** — `/search` по артикулу, названию, бренду, модели
3. **Фото** — отправьте снимок бирки/шильдика/упаковки (`/photo` или кнопка 📷)
4. **Карточка детали** — цена, остаток, совместимость
5. **Корзина** — ➕/➖, удаление позиции, проверка остатков
6. **Заявка** — телефон, комментарий, журнал `logs/orders.jsonl`
7. **Уведомление оператору** — `OPERATOR_CHAT_ID`
8. **AI-помощник** — `/ask`
9. **Обновление каталога** — `/reload`

---

## Запуск

```bash
git clone https://github.com/rustamilyasov73-cpu/ai-content-helper.git
cd ai-content-helper
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Windows: copy .env.example .env
```

В `.env` укажите `BOT_TOKEN`.  
Для распознавания фото обязателен `OPENAI_API_KEY` (модель с vision, по умолчанию `gpt-4o-mini`).  
`OPERATOR_CHAT_ID` — по желанию.

```bash
python bot.py
```

Тесты:

```bash
pip install pytest
pytest -q
```

Примеры:
- `/search RE507922`
- просто пришлите **фото бирки** с артикулом
- `/search фильтр John Deere`
- `/ask какой масляный фильтр на трактор 6R?`

---

## Структура

```text
ai-content-helper/
├── bot.py
├── config.py
├── data/
│   └── parts.json
├── keyboards/
│   └── menu.py
├── services/
│   ├── catalog.py
│   ├── cart.py
│   ├── orders.py
│   ├── vision.py
│   └── llm.py
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

---

## Каталог

Демо-данные в `data/parts.json` (John Deere, CLAAS, New Holland, Case IH, Krone, МТЗ и др.).  
Для боевого использования замените файл на свой прайс с полями: `id`, `sku`, `name`, `category`, `brand`, `compatible`, `price`, `stock`, `unit`, `description`. Затем `/reload`.

---

## Автор

**Рустам** · [@Rust_prompt](https://t.me/Rust_prompt) · [GitHub](https://github.com/rustamilyasov73-cpu)
