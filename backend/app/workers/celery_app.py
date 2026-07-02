"""Celery-приложение: брокер и расписание фоновых задач."""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "online_programmer",
    broker=settings.broker_url,
    backend=settings.broker_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    beat_schedule={
        "poll-codeforces": {
            "task": "app.workers.tasks.poll_all_codeforces",
            "schedule": 300.0,  # каждые 5 минут
        },
    },
)

# регистрируем задачи
import app.workers.tasks  # noqa: E402,F401
