"""Фоновые задачи Celery: проверка сабмитов и опрос Codeforces."""
import logging

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.user import StudentProfile
from app.services.cf_poll import sync_user_solved
from app.services.codeforces import CodeforcesClient
from app.services.judge.dispatch import run_judge_sync
from app.services.rate_limit import get_default_limiter
from app.workers.celery_app import celery_app

logger = logging.getLogger("app.workers")


@celery_app.task(name="app.workers.tasks.run_judge_task")
def run_judge_task(submission_id: int) -> None:
    run_judge_sync(submission_id)


@celery_app.task(name="app.workers.tasks.poll_all_codeforces")
def poll_all_codeforces() -> None:
    """Опрос user.status по всем привязанным хэндлам (с общим rate-limit)."""
    db = SessionLocal()
    try:
        client = CodeforcesClient(limiter=get_default_limiter())
        profiles = db.scalars(
            select(StudentProfile).where(StudentProfile.codeforces_handle.isnot(None))
        ).all()
        for profile in profiles:
            try:
                sync_user_solved(db, client, profile.user_id, profile.codeforces_handle)
            except Exception as exc:  # noqa: BLE001 — один сбой не должен ронять весь опрос
                logger.warning("CF poll failed for %s: %s", profile.codeforces_handle, exc)
    finally:
        db.close()
