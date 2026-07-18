# AI Content Helper

Помощник для генерации контента: посты для Telegram, идеи, промпты и короткие тексты под ваш тон.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Content](https://img.shields.io/badge/AI-Content-ff69b4)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4)

---

## 🎯 Задача

Ускорить создание контента для канала и клиентов:
- генерация постов по теме;
- несколько вариантов текста на выбор;
- готовые шаблоны промптов;
- единый стиль «коротко и по делу».

---

## 🧰 Стек технологий

- **Python 3.11+**
- **aiogram 3**
- **OpenAI API**
- **Шаблоны промптов** в `prompts/`
- **python-dotenv**

---

## 🧩 Функциональные блоки

1. **Команда /post** — пост для Telegram по теме
2. **Команда /ideas** — 5 идей для контента
3. **Команда /prompt** — улучшить пользовательский промпт
4. **Шаблоны** — системные инструкции под задачи
5. **Тон голоса** — деловой / дружелюбный / экспертный

---

## 🖼️ Скриншоты

![Генерация поста](docs/screenshot-post.png)

![Идеи для контента](docs/screenshot-ideas.png)

---

## 🚀 Инструкция по запуску

```bash
git clone https://github.com/rustamilyasov73-cpu/ai-content-helper.git
cd ai-content-helper
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python bot.py
```

Примеры:
- `/post Как AI помогает малому бизнесу`
- `/ideas канал про автоматизацию`
- `/prompt напиши пост про ботов`

---

## 📁 Структура

```text
ai-content-helper/
├── bot.py
├── config.py
├── prompts/
│   └── templates.py
├── services/
│   └── llm.py
├── docs/
├── requirements.txt
├── .env.example
└── README.md
```

---

## 👤 Автор

**Рустам** · [@Rust_prompt](https://t.me/Rust_prompt) · [GitHub](https://github.com/rustamilyasov73-cpu)
