# Интеграция AgroParts ↔ 1С:Бухгалтерия

Обмен идёт через **HTTP-сервис** конфигурации 1С (рекомендуется публикация `hs/agroparts`).

## Что синхронизируется

| Направление | Данные |
|-------------|--------|
| 1С → AgroParts | Номенклатура, цены, остатки → `data/parts.json` |
| AgroParts → 1С | Заявки с телефона / из Telegram → документ заказа покупателя |

## Переменные `.env`

```env
ONEC_ENABLED=true
ONEC_BASE_URL=http://1c-server/buh/hs/agroparts
ONEC_USER=AgroParts
ONEC_PASSWORD=secret
ONEC_TIMEOUT=30
ONEC_ADMIN_IDS=123456789

API_HOST=0.0.0.0
API_PORT=8080
API_TOKEN=optional-shared-secret
```

## Контракт HTTP-сервиса 1С

Базовый URL: `ONEC_BASE_URL` (без завершающего `/`).

### `GET /ping`

```json
{ "ok": true, "version": "1.0" }
```

### `GET /nomenclature`

```json
{
  "items": [
    {
      "sku": "RE507922",
      "name": "Фильтр масляный двигателя",
      "category": "filters",
      "brand": "John Deere",
      "compatible": ["6R", "7R"],
      "price": 2890,
      "stock": 24,
      "unit": "шт",
      "description": "…"
    }
  ]
}
```

Допускаются русские поля: `Артикул`, `Наименование`, `Категория`, `Цена`, `Остаток`.

### `POST /orders`

Запрос:

```json
{
  "external_id": "ord-1710000000",
  "source": "mobile",
  "phone": "+79001234567",
  "customer_name": "Иван",
  "comment": "трактор 6R",
  "total": 5780,
  "items": [
    { "sku": "RE507922", "name": "Фильтр масляный", "qty": 2, "price": 2890, "amount": 5780 }
  ]
}
```

Ответ:

```json
{ "ok": true, "number": "00000012", "ref": "…", "message": "Заказ создан" }
```

## Команды AgroParts

```bash
# проверка связи
python sync_onec.py --ping

# выгрузить номенклатуру из 1С в parts.json (+ mobile зеркала)
python sync_onec.py

# API для телефона
python api_server.py
```

В Telegram (если id в `ONEC_ADMIN_IDS`): `/sync1c`

Мобильное приложение:
1. В **Настройках** укажите URL API, например `http://192.168.1.10:8080`
2. Нажмите **Обновить каталог с сервера** (`GET /api/parts`)
3. Оформляйте заявки — они уйдут в журнал и в 1С

При ошибке сети корзина **не очищается**, можно повторить отправку.

## Пример модуля 1С

См. `onec/HTTPServiceModule.bsl` — каркас обработчиков `ping`, `nomenclature`, `orders` для вставки в HTTP-сервис.
