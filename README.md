# AgroParts

Telegram-бот каталога запчастей для сельхозтехники: поиск по артикулу, категории, корзина и заявка менеджеру.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![aiogram](https://img.shields.io/badge/aiogram-3.x-blueviolet)
![Agro](https://img.shields.io/badge/AgroParts-Catalog-2e7d32)

---

## Задача

Ускорить подбор и заказ запчастей для тракторов и комбайнов:
- поиск по артикулу, названию и бренду;
- просмотр категорий и карточек позиций;
- корзина и оформление заявки;
- опциональный AI-помощник по подбору.

---

## Стек

- **Python 3.11+**
- **aiogram 3** — Telegram Bot API
- **JSON-каталог** — `data/parts.json`
- **OpenAI API** (опционально) — команда `/ask`
- **python-dotenv** — конфигурация

---

## Функции

1. **Каталог** — категории фильтров, ремней, гидравлики и др.
2. **Поиск** — `/search` по артикулу, названию, бренду, модели
3. **Карточка детали** — цена, остаток, совместимость
4. **Корзина** — добавление, очистка, итоговая сумма
5. **Заявка** — `/order` + уведомление оператору (`OPERATOR_CHAT_ID`)
6. **AI-помощник** — `/ask` (работает и без ключа: отдаёт результаты поиска)

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

Заполните в `.env` минимум `BOT_TOKEN`.  
`OPENAI_API_KEY` и `OPERATOR_CHAT_ID` — по желанию.

```bash
python bot.py
```

Примеры:
- `/search RE507922`
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
│   └── llm.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## Каталог

Демо-данные в `data/parts.json` (John Deere, CLAAS, New Holland, Case IH, Krone, МТЗ и др.).  
Для боевого использования замените файл на свой прайс с полями: `id`, `sku`, `name`, `category`, `brand`, `compatible`, `price`, `stock`, `unit`, `description`.

---

## Автор

**Рустам** · [@Rust_prompt](https://t.me/Rust_prompt) · [GitHub](https://github.com/rustamilyasov73-cpu)
