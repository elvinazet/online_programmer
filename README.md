# onproger — платформа онлайн-школы программирования

Веб-платформа для обучения **C++** и **Python** с нуля до продвинутого уровня:
учебники, практика на задачах **Codeforces** с локальной проверкой кода в
изолированном sandbox, и экзамены для перехода между уровнями с детальным
разбором результатов по темам.

## Стек

| Слой | Технологии |
|------|-----------|
| Frontend | Next.js (React, TypeScript), Tailwind CSS, Monaco Editor |
| Backend | FastAPI (Python), SQLAlchemy, Alembic |
| БД / кэш | PostgreSQL, Redis |
| Фоновые задачи | Celery (worker + beat) |
| Sandbox | Docker с ограничениями CPU/памяти/сети (изоляция запуска кода) |
| Авторизация | JWT (access + refresh) |
| Деплой | Docker Compose |

## Документация (Этап 1 — проектирование)

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — архитектура: компоненты,
  потоки данных, интеграция с Codeforces, устройство sandbox, деплой.
- [`docs/DATABASE.md`](docs/DATABASE.md) — схема базы данных: ER-диаграммы и
  описание всех таблиц.
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — план разработки по этапам
  (MVP → полная версия), с критериями готовности и что тестировать.

## Статус

🟢 **Все этапы (1–7) реализованы.** Авторизация, учебники, задачи Codeforces
с локальной проверкой, экзамены, разбор результатов и харденинг — готовы.
Backend покрыт тестами (pytest), frontend собирается (`next build`), есть CI.

> Judge через Docker собран, но его изоляцию нужно проверить в среде с Docker —
> в CI/разработке judge гоняется на `LocalExecutor` (Python). См. ROADMAP.

## Запуск

```bash
cp .env.example .env                  # задать JWT_SECRET и пр.
bash backend/sandbox/build.sh         # собрать sandbox-образы для judge (нужен Docker)
docker compose up --build             # db, redis, api, worker, beat, frontend, nginx
docker compose exec api python -m app.seed   # демо-данные (по желанию)
```

Приложение: **http://localhost** (через nginx). Swagger API: http://localhost/api… ,
напрямую — http://localhost:8000/docs.

**Демо-доступы после seed:** учитель `teacher@example.com`, ученик
`student@example.com`, пароль `password123`.

## Тесты и локальная разработка

```bash
# backend
cd backend && python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt && pytest

# frontend (нужен запущенный backend на :8000)
cd frontend && npm install && npm run dev
```

Подробности — в [`backend/README.md`](backend/README.md) и
[`frontend/README.md`](frontend/README.md).
