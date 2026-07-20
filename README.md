# AgroParts

Мобильный каталог запчастей для сельхозтехники + обмен с **1С:Бухгалтерия**.

![Expo](https://img.shields.io/badge/Expo-React%20Native-000020)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![1C](https://img.shields.io/badge/1C-Бухгалтерия-e0a800)
![Agro](https://img.shields.io/badge/AgroParts-Catalog-2e7d32)

---

## Приложение на телефоне (Android Chrome)

```bash
cd mobile
node scripts/serve-web.js
# в другом терминале:
python api/server.py
```

Откройте http://localhost:8090 (или туннель) в Chrome на телефоне.

Сейчас в каталоге **80+ позиций**, 14 категорий, поля учёта 1С (код, НДС, штрихкод, склад, аналоги…).

Подробнее: [`mobile/README.md`](mobile/README.md)

---

## Интеграция с 1С

См. [`docs/1C.md`](docs/1C.md)

```bash
# импорт номенклатуры из выгрузки 1С
python scripts/sync_1c.py import-file data/1c/nomenclature.sample.json

# заявки из приложения → data/1c/orders_outbox/
# отправка в HTTP-сервис 1С:
python scripts/sync_1c.py push-orders https://YOUR-1C/hs/agroparts/orders --token SECRET
```

---

## Telegram-бот (опционально)

```bash
pip install -r requirements.txt
cp .env.example .env
python bot.py
pytest -q
```

---

## Структура

```text
ai-content-helper/
├── mobile/www/          ← веб-приложение для телефона
├── api/server.py        ← API каталога и заявок
├── services/onec_sync.py
├── scripts/sync_1c.py
├── data/parts.json
├── data/1c/             ← обмен с 1С
├── docs/1C.md
└── bot.py
```

---

## Автор

**Рустам** · [@Rust_prompt](https://t.me/Rust_prompt) · [GitHub](https://github.com/rustamilyasov73-cpu)
