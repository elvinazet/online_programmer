"""Учёт streak ученика: серия дней подряд с решёнными задачами."""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.user import StudentProfile


def bump_streak(db: Session, student_id: int, today: date | None = None) -> None:
    today = today or date.today()
    profile = db.get(StudentProfile, student_id)
    if profile is None:
        return
    last = profile.last_active_date
    if last == today:
        return  # уже отмечен сегодня
    if last == today - timedelta(days=1):
        profile.streak_count += 1
    else:
        profile.streak_count = 1
    profile.last_active_date = today
