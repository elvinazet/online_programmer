"""Эндпоинты сабмитов: отправка кода на проверку и просмотр вердикта."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.problem import Problem
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User, UserRole
from app.schemas.submission import SubmissionCreate, SubmissionOut
from app.services.judge.dispatch import dispatch_judge

router = APIRouter(tags=["submissions"])


@router.post(
    "/problems/{problem_id}/submissions",
    response_model=SubmissionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_submission(
    problem_id: int,
    payload: SubmissionCreate,
    student: User = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
) -> Submission:
    problem = db.get(Problem, problem_id)
    if problem is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Задача не найдена")

    submission = Submission(
        student_id=student.id,
        problem_id=problem_id,
        language=payload.language,
        source_code=payload.source_code,
        status=SubmissionStatus.queued,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    dispatch_judge(submission.id)  # inline (dev) сразу проставит вердикт; celery — асинхронно
    db.refresh(submission)
    return submission


@router.get("/submissions/{submission_id}", response_model=SubmissionOut)
def get_submission(
    submission_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Submission:
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Сабмит не найден")
    if user.role == UserRole.student and submission.student_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет доступа")
    return submission


@router.get("/me/submissions", response_model=list[SubmissionOut])
def my_submissions(
    student: User = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
) -> list[Submission]:
    return list(
        db.scalars(
            select(Submission)
            .where(Submission.student_id == student.id)
            .order_by(Submission.id.desc())
            .limit(50)
        )
    )
