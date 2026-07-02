# Backend (FastAPI)

API платформы: авторизация (JWT access+refresh), профили, группы.

## Запуск через Docker Compose (из корня репозитория)

```bash
cp .env.example .env          # задать JWT_SECRET и пр.
docker compose up --build     # поднимет db, redis, api; миграции применятся автоматически
```

API: http://localhost:8000 · Swagger: http://localhost:8000/docs · Health: `/health`

## Локальная разработка

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# нужен запущенный PostgreSQL; строка подключения — в DATABASE_URL
export DATABASE_URL="postgresql+psycopg2://app:app@localhost:5432/online_programmer"
alembic upgrade head
uvicorn app.main:app --reload
```

## Тесты

Тесты используют изолированную SQLite-БД, внешние сервисы не нужны:

```bash
cd backend
. .venv/bin/activate
pytest
```

## Основные эндпоинты

| Метод | Путь | Доступ | Назначение |
|-------|------|--------|-----------|
| POST | `/api/auth/register` | — | Регистрация (роль student/teacher) |
| POST | `/api/auth/verify-email` | — | Подтверждение email по токену |
| POST | `/api/auth/login` | — | Вход → access + refresh |
| POST | `/api/auth/refresh` | — | Ротация токенов |
| POST | `/api/auth/logout` | — | Отзыв refresh-токена |
| POST | `/api/auth/forgot-password` | — | Запрос сброса пароля |
| POST | `/api/auth/reset-password` | — | Сброс пароля по токену |
| GET | `/api/users/me` | auth | Текущий пользователь + профиль |
| PATCH | `/api/users/me/student-profile` | student | Обновить профиль ученика |
| PATCH | `/api/users/me/teacher-profile` | teacher | Обновить профиль учителя |
| POST | `/api/groups` | teacher | Создать группу |
| GET | `/api/groups` | teacher | Свои группы |
| POST | `/api/groups/{id}/members` | teacher | Добавить ученика по email |
| GET | `/api/groups/{id}/members` | teacher | Участники группы |

> В dev-режиме письма (подтверждение email, сброс пароля) печатаются в лог
> контейнера `api` — ссылку с токеном видно там (`EMAIL_BACKEND=console`).
