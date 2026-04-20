# Payment API

Асинхронное веб-приложение в парадигме REST API с использованием:
- База данных: PostgreSQL
- ORM: SQLAlchemy
- Веб-фреймворк: Sanic
- Контейнеризация: Docker Compose

## Сущности
- Пользователь
- Администратор
- Счет (привязан к пользователю, имеет баланс)
- Платеж (пополнение баланса)

## Функциональность

### Пользователь
- Авторизация по email/password
- Получение данных о себе (id, email, full_name)
- Получение списка своих счетов и балансов
- Получение списка своих платежей

### Администратор
- Авторизация по email/password
- Получение данных о себе (id, email, full_name)
- Создание/Обновление/Удаление пользователя
- Получение списка пользователей и их счетов с балансами

### Платежи
- Роут для обработки вебхука от сторонней платежной системы
- Проверка подписи (SHA256 от concatenated sorted keys + secret_key)
- Создание счета, если не существует
- Сохранение транзакции (уникальная по transaction_id)
- Начисление суммы на счет

## Тестовые данные
В миграциях созданы:
- Тестового пользователя: email=`testuser@example.com`, password=`password`
- Счет тестового пользователя
- Тестового администратора: email=`testadmin@example.com`, password=`password`

## Инструкция по запуску

### 1. С использованием Docker Compose
```bash
docker-compose up --build
```
Приложение будет доступно по адресу: http://localhost:8000

### 2. Без Docker (локально)
Требуется установленный PostgreSQL и Python 3.12+

#### Шаги:
1. Склонировать репозиторий и перейти в директорию проекта.
2. Установить зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Создать базу данных PostgreSQL (например, `payment_db`) и обновить строку подключения в `.env` или в `src/core/database.py` по умолчанию.
4. Применить миграции:
   ```bash
   alembic upgrade head
   ```
5. Запустить приложение:
   ```bash
   python src/main.py
   ```
Приложение будет доступно по адресу: http://localhost:8000

## Default Credentials
Для входа в систему используйте следующие учетные данные:

### Тестовый пользователь
- Email: `testuser@example.com`
- Password: `password`

### Тестовый администратор
- Email: `testadmin@example.com`
- Password: `password`

## API Endpoints

### ⚡ API Documentation & Help
Для просмотра всей документации API используйте:

1. **Интерактивная документация (Swagger)**:
   - URL: `http://localhost:8000/docs`
   - Интерактивный интерфейс для тестирования всех endpoints

2. **JSON документация API** (список всех endpoints):
   - URL: `http://localhost:8000/api-docs`
   - Показывает все endpoints с описанием в JSON формате

3. **Информация о API**:
   - URL: `http://localhost:8000/`
   - Показывает приветственное сообщение и ссылки на документацию

### Auth
- POST `/auth/login` - Вход в систему (для пользователя и администратора)
  - Тело запроса: `{ "email": "string", "password": "string" }`
  - Ответ: `{ "access_token": "string", "token_type": "bearer" }`

### User
- GET `/user/profile` - Получить профиль текущего пользователя (требуется токен)
  - Header: `Authorization: Bearer <token>`
- GET `/user/accounts` - Получить список счетов и балансов текущего пользователя (требуется токен)
  - Header: `Authorization: Bearer <token>`
- GET `/user/payments` - Получить список платежей текущего пользователя (требуется токен)
  - Header: `Authorization: Bearer <token>`

### Admin
- POST `/admin/login` - Вход в систему для администратора (аналогично `/auth/login`)
- GET `/admin/profile` - Получить профиль текущего администратора (требуется токен)
  - Header: `Authorization: Bearer <admin_token>`
- GET `/admin/users` - Получить список пользователей и их счетов с балансами (требуется токен администратора)
  - Header: `Authorization: Bearer <admin_token>`
- POST `/admin/users` - Создать нового пользователя (требуется токен администратора)
  - Header: `Authorization: Bearer <admin_token>`
  - Тело запроса: `{ "email": "string", "password": "string", "full_name": "string", "is_admin": "boolean (optional)" }`
- PUT `/admin/users/{user_id}` - Обновить существующего пользователя (требуется токен администратора)
  - Header: `Authorization: Bearer <admin_token>`
- DELETE `/admin/users/{user_id}` - Удалить пользователя (требуется токен администратора)
  - Header: `Authorization: Bearer <admin_token>`

### Webhook
- POST `/webhook/payment` - Обработка вебхука от платежной системы
  - Заголовки: `X-Signature: <signature>`
  - Тело запроса: `{ "user_id": "integer", "transaction_id": "string", "amount": "number" }`
  - Ответ: `{ "status": "success", "account_id": "integer", "new_balance": "number" }` или `{ "status": "already processed" }`

## Примеры запросов

### Получение токена (Login)
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "testuser@example.com", "password": "password"}'
```

### Получение профиля пользователя (с токеном)
```bash
curl -X GET http://localhost:8000/user/profile \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Создание пользователя (только админ)
```bash
curl -X POST http://localhost:8000/admin/users \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "newuser@example.com", "password": "password123", "full_name": "New User"}'
```

### Тестирование вебхука
```bash
curl -X POST http://localhost:8000/webhook/payment \
  -H "X-Signature: your_signature" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "transaction_id": "txn_12345", "amount": 100.50}'
```

## Примечания
- Для работы вебхука необходимо настроить секретный ключ в переменной окружения `SECRET_KEY` (по умолчанию `your-secret-key-here`).
- Подпись вебхука вычисляется как SHA256 от concatenated sorted keys + secret_key, где keys - это ключи JSON-полезной нагрузки, отсортированные в алфавитном порядке, а значения преобразуются в строки и конкатенируются в этом порядке, затем добавляется secret_key.
- Приложение поддерживает автоматическую генерацию документации через Sanic-EXT. Для работы в режиме разработки с интерактивной документацией используйте `debug=True`.