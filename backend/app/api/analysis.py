"""Эндпоинты разбора экзамена: анализ попытки, история, агрегат для учителя."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.exam import AttemptStatus, Exam, ExamAttempt
from app.models.user import User, UserRole
from app.schemas.analysis import (
    AttemptAnalysis,
    ExamHistoryItem,
    ExamTopicAggregate,
)
from app.services import analysis as analysis_service

router = APIRouter(tags=["analysis"])


@router.get("/attempts/{attempt_id}/analysis", response_model=AttemptAnalysis)
def attempt_analysis(
    attempt_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    attempt = db.get(ExamAttempt, attempt_id)
    if attempt is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Попытка не найдена")
    if user.role == UserRole.student and attempt.student_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет доступа")
    if attempt.status == AttemptStatus.in_progress:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Экзамен ещё не завершён")
    return analysis_service.attempt_analysis(db, attempt)


@router.get("/me/exam-history", response_model=list[ExamHistoryItem])
def exam_history(
    student: User = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
) -> list[ExamHistoryItem]:
    rows = db.execute(
        select(ExamAttempt, Exam.title)
        .join(Exam, Exam.id == ExamAttempt.exam_id)
        .where(
            ExamAttempt.student_id == student.id,
            ExamAttempt.status != AttemptStatus.in_progress,
        )
        .order_by(ExamAttempt.id.desc())
    ).all()
    return [
        ExamHistoryItem(
            attempt_id=attempt.id,
            exam_id=attempt.exam_id,
            exam_title=title,
            attempt_number=attempt.attempt_number,
            status=attempt.status,
            total_score=attempt.total_score,
            practical_score=attempt.practical_score,
            theory_score=attempt.theory_score,
            passed=attempt.passed,
            submitted_at=attempt.submitted_at,
        )
        for attempt, title in rows
    ]


@router.get("/exams/{exam_id}/analysis", response_model=list[ExamTopicAggregate])
def exam_analysis(
    exam_id: int,
    teacher: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> list[dict]:
    exam = db.get(Exam, exam_id)
    if exam is None or exam.created_by != teacher.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Экзамен не найден")
    return analysis_service.exam_topic_aggregate(db, exam_id)
