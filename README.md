# AgroParts

Каталог запчастей для сельхозтехники.

**Главное — мобильное приложение на телефоне** (`mobile/`).  
Telegram-бот в корне репозитория — дополнительный канал, не обязателен.

![Expo](https://img.shields.io/badge/Expo-React%20Native-000020)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Agro](https://img.shields.io/badge/AgroParts-Catalog-2e7d32)

---

## Приложение на телефоне

Папка `mobile/` — Expo / React Native:

- каталог, категории и бренды
- поиск по артикулу
- распознавание бирок по фото
- корзина и заявка с телефоном

### Как открыть

1. Установите [Expo Go](https://expo.dev/go) на телефон.
2. На компьютере:

```bash
cd mobile
npm install
npx expo start
```

3. Отсканируйте QR-код в Expo Go (Android) или камерой (iPhone).

Подробнее: [`mobile/README.md`](mobile/README.md).

Для фото-распознавания укажите OpenAI API ключ во вкладке **Настройки** приложения.

---

## Telegram-бот (опционально)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # BOT_TOKEN, OPENAI_API_KEY
python bot.py
```

Тесты: `pytest -q`

---

## 1С:Бухгалтерия

Обмен через HTTP-сервис 1С:

- **1С → AgroParts** — номенклатура, цены, остатки (`python sync_onec.py`)
- **AgroParts → 1С** — заявки с телефона и из Telegram

```bash
# .env
ONEC_ENABLED=true
ONEC_BASE_URL=http://1c-server/buh/hs/agroparts
ONEC_USER=AgroParts
ONEC_PASSWORD=secret

python sync_onec.py --ping
python sync_onec.py
python api_server.py   # шлюз для телефона :8080
```

В приложении: **Настройки → URL API** (`http://IP:8080`).  
Подробности и пример модуля 1С: [`docs/onec.md`](docs/onec.md), [`onec/HTTPServiceModule.bsl`](onec/HTTPServiceModule.bsl).

---

## Структура

```text
ai-content-helper/
├── mobile/           ← приложение для телефона
├── bot.py            ← Telegram-бот (опционально)
├── api_server.py     ← API → заявки в 1С
├── sync_onec.py      ← выгрузка номенклатуры из 1С
├── data/parts.json
├── services/onec.py
├── docs/onec.md
└── onec/HTTPServiceModule.bsl
```

---

## Автор

**Рустам** · [@Rust_prompt](https://t.me/Rust_prompt) · [GitHub](https://github.com/rustamilyasov73-cpu)
