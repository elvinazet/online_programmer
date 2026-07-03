"""Эндпоинты экзаменов: конструктор (учитель), список, обзор результатов."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.exam import (
    Exam,
    ExamAttempt,
    ExamPracticalProblem,
    ExamTheoryConfig,
)
from app.models.content import Module
from app.models.problem import Problem
from app.models.user import User, UserRole
from app.schemas.auth import MessageResponse
from app.schemas.exam import (
    AttemptSummary,
    ExamCreate,
    ExamOut,
    ExamPracticalAdd,
    ExamTheoryAdd,
    ExamUpdate,
)

router = APIRouter(tags=["exams"])


def _owned_exam_or_404(db: Session, exam_id: int, teacher: User) -> Exam:
    exam = db.get(Exam, exam_id)
    if exam is None or exam.created_by != teacher.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Экзамен не найден")
    return exam


@router.post("/exams", response_model=ExamOut, status_code=status.HTTP_201_CREATED)
def create_exam(
    payload: ExamCreate,
    teacher: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> Exam:
    exam = Exam(created_by=teacher.id, **payload.model_dump())
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam


@router.patch("/exams/{exam_id}", response_model=ExamOut)
def update_exam(
    exam_id: int,
    payload: ExamUpdate,
    teacher: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> Exam:
    exam = _owned_exam_or_404(db, exam_id, teacher)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(exam, field, value)
    db.commit()
    db.refresh(exam)
    return exam


@router.post("/exams/{exam_id}/problems", response_model=MessageResponse)
def add_practical_problem(
    exam_id: int,
    payload: ExamPracticalAdd,
    teacher: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> MessageResponse:
    _owned_exam_or_404(db, exam_id, teacher)
    if db.get(Problem, payload.problem_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Задача не найдена")
    order = db.scalar(
        select(func.max(ExamPracticalProblem.order_index)).where(
            ExamPracticalProblem.exam_id == exam_id
        )
    )
    db.add(
        ExamPracticalProblem(
            exam_id=exam_id,
            problem_id=payload.problem_id,
            max_score=payload.max_score,
            order_index=(order or 0) + 1,
        )
    )
    db.commit()
    return MessageResponse(message="Задача добавлена в экзамен")


@router.post("/exams/{exam_id}/theory", response_model=MessageResponse)
def add_theory_config(
    exam_id: int,
    payload: ExamTheoryAdd,
    teacher: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> MessageResponse:
    _owned_exam_or_404(db, exam_id, teacher)
    if db.get(Module, payload.module_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Модуль не найден")
    db.add(
        ExamTheoryConfig(
            exam_id=exam_id, module_id=payload.module_id, num_questions=payload.num_questions
        )
    )
    db.commit()
    return MessageResponse(message="Тема добавлена в теоретическую часть")


@router.get("/exams", response_model=list[ExamOut])
def list_exams(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Exam]:
    if user.role == UserRole.teacher:
        stmt = select(Exam).where(Exam.created_by == user.id)
    else:
        stmt = select(Exam).where(Exam.is_published.is_(True))
    return list(db.scalars(stmt.order_by(Exam.id.desc())))


@router.get("/exams/{exam_id}", response_model=ExamOut)
def get_exam(
    exam_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Exam:
    exam = db.get(Exam, exam_id)
    if exam is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Экзамен не найден")
    if user.role == UserRole.student and not exam.is_published:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Экзамен не найден")
    return exam


@router.get("/exams/{exam_id}/attempts", response_model=list[AttemptSummary])
def exam_attempts(
    exam_id: int,
    teacher: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> list[ExamAttempt]:
    _owned_exam_or_404(db, exam_id, teacher)
    return list(
        db.scalars(
            select(ExamAttempt)
            .where(ExamAttempt.exam_id == exam_id)
            .order_by(ExamAttempt.id.desc())
        )
    )
