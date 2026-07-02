"""Диспетчер проверки: синхронно (dev/тесты) или через Celery (прод)."""
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.submission import Submission
from app.services.judge.executor import get_executor
from app.services.judge.runner import judge_submission


def run_judge_sync(submission_id: int) -> None:
    db = SessionLocal()
    try:
        submission = db.get(Submission, submission_id)
        if submission is not None:
            judge_submission(db, submission, get_executor())
    finally:
        db.close()


def dispatch_judge(submission_id: int) -> None:
    if settings.judge_inline:
        run_judge_sync(submission_id)
    else:
        from app.workers.tasks import run_judge_task

        run_judge_task.delay(submission_id)
