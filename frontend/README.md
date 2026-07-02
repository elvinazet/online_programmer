# Frontend (Next.js)

UI платформы: авторизация, читалка учебников с подсветкой кода и запуском
примеров в браузере (Monaco + Pyodide), прохождение мини-квизов, админка учителя.

## Стек

Next.js 14 (App Router, TypeScript) · Tailwind CSS · Monaco Editor ·
react-markdown + highlight.js · Pyodide (запуск Python в браузере).

## Разработка

```bash
cd frontend
cp .env.local.example .env.local      # NEXT_PUBLIC_API_URL (по умолчанию http://localhost:8000)
npm install
npm run dev                            # http://localhost:3000
```

Бэкенд должен быть запущен (см. `../backend/README.md` или `docker compose up`).

## Сборка

```bash
npm run build && npm run start
```

## Структура

```
app/                    # маршруты (App Router)
  login, register, verify-email, forgot-password, reset-password
  page.tsx              # список курсов
  courses/[id]          # дерево курса с прогрессом
  lessons/[id]          # урок: Markdown + песочница + мини-квиз
  teach/                # админка учителя (создание, Markdown-редактор)
components/             # Markdown, CodeRunner (Monaco+Pyodide), Quiz, Nav, MarkdownEditor
lib/                    # api-клиент (авто-refresh JWT), auth-контекст, типы
```

> Запуск Python-примеров использует Pyodide, который подгружается из CDN в
> браузере при первом запуске кода (нужен интернет). C++ в браузере не
> исполняется — это появится в разделе задач с серверным sandbox (этап 4).
