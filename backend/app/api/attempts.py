"""Эндпоинты прохождения экзамена (ученик)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.exam import (
    AttemptEvent,
    AttemptProblem,
    AttemptQuestion,
    AttemptStatus,
    Exam,
    ExamAttempt,
)
from app.models.problem import Problem
from app.models.quiz import Question
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User, UserRole
from app.schemas.auth import MessageResponse
from app.schemas.exam import (
    AttemptDetail,
    AttemptProblemView,
    AttemptQuestionView,
    AttemptResult,
    EventRequest,
    SaveAnswersRequest,
)
from app.schemas.submission import SubmissionCreate, SubmissionOut
from app.services import exam as exam_service
from app.services.judge.dispatch import dispatch_judge

router = APIRouter(tags=["attempts"])


def _student_attempt(db: Session, attempt_id: int, student: User) -> ExamAttempt:
    attempt = db.get(ExamAttempt, attempt_id)
    if attempt is None or attempt.student_id != student.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Попытка не найдена")
    return attempt


def _build_detail(db: Session, attempt: ExamAttempt) -> AttemptDetail:
    question_views = []
    for aq in db.scalars(
        select(AttemptQuestion)
        .where(AttemptQuestion.attempt_id == attempt.id)
        .order_by(AttemptQuestion.order_index)
    ):
        question = db.get(Question, aq.question_id)
        options = None
        if question.options:
            options = (
                [question.options[i] for i in aq.options_order]
                if aq.options_order
                else question.options
            )
        question_views.append(
            AttemptQuestionView(
                id=aq.id,
                question_id=question.id,
                type=question.type,
                prompt_md=question.prompt_md,
                options=options,
                student_answer=aq.student_answer,
                order_index=aq.order_index,
            )
        )

    problem_views = []
    for ap in db.scalars(
        select(AttemptProblem)
        .where(AttemptProblem.attempt_id == attempt.id)
        .order_by(AttemptProblem.order_index)
    ):
        problem = db.get(Problem, ap.problem_id)
        best = db.scalar(
            select(func.max(Submission.score)).where(
                Submission.exam_attempt_id == attempt.id,
                Submission.problem_id == ap.problem_id,
            )
        )
        problem_views.append(
            AttemptProblemView(
                id=ap.id,
                problem_id=ap.problem_id,
                title=problem.title if problem else "",
                order_index=ap.order_index,
                max_score=ap.max_score,
                best_score=best or 0,
            )
        )

    result = None
    if attempt.status != AttemptStatus.in_progress:
        result = AttemptResult(
            total_score=attempt.total_score,
            practical_score=attempt.practical_score,
            theory_score=attempt.theory_score,
            passed=attempt.passed,
            next_retake_allowed_at=attempt.next_retake_allowed_at,
        )

    return AttemptDetail(
        id=attempt.id,
        exam_id=attempt.exam_id,
        attempt_number=attempt.attempt_number,
        status=attempt.status,
        started_at=attempt.started_at,
        ends_at=attempt.ends_at,
        remaining_seconds=exam_service.remaining_seconds(attempt),
        questions=question_views,
        problems=problem_views,
        result=result,
    )


@router.post(
    "/exams/{exam_id}/attempts", response_model=AttemptDetail, status_code=status.HTTP_201_CREATED
)
def start_attempt(
    exam_id: int,
    student: User = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
) -> AttemptDetail:
    exam = db.get(Exam, exam_id)
    if exam is None or not exam.is_published:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Экзамен не найден")
    try:
        attempt = exam_service.start_attempt(db, exam, student.id)
    except exam_service.ExamError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return _build_detail(db, attempt)


@router.get("/attempts/{attempt_id}", response_model=AttemptDetail)
def get_attempt(
    attempt_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AttemptDetail:
    attempt = db.get(ExamAttempt, attempt_id)
    if attempt is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Попытка не найдена")
    if user.role == UserRole.student:
        if attempt.student_id != user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет доступа")
        exam_service.ensure_finalized_if_expired(db, attempt)
    return _build_detail(db, attempt)


@router.patch("/attempts/{attempt_id}/answers", response_model=AttemptDetail)
def save_answers(
    attempt_id: int,
    payload: SaveAnswersRequest,
    student: User = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
) -> AttemptDetail:
    attempt = _student_attempt(db, attempt_id, student)
    exam_service.ensure_finalized_if_expired(db, attempt)
    if attempt.status != AttemptStatus.in_progress:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Время вышло, попытка завершена")

    by_id = {
        aq.id: aq
        for aq in db.scalars(
            select(AttemptQuestion).where(AttemptQuestion.attempt_id == attempt.id)
        )
    }
    for answer in payload.answers:
        target = by_id.get(answer.attempt_question_id)
        if target is not None:
            target.student_answer = answer.answer
    db.commit()
    return _build_detail(db, attempt)


@router.post(
    "/attempts/{attempt_id}/problems/{problem_id}/submissions",
    response_model=SubmissionOut,
    status_code=status.HTTP_201_CREATED,
)
def attempt_submission(
    attempt_id: int,
    problem_id: int,
    payload: SubmissionCreate,
    student: User = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
) -> Submission:
    attempt = _student_attempt(db, attempt_id, student)
    exam_service.ensure_finalized_if_expired(db, attempt)
    if attempt.status != AttemptStatus.in_progress:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Время вышло, попытка завершена")

    in_attempt = db.scalar(
        select(AttemptProblem).where(
            AttemptProblem.attempt_id == attempt.id, AttemptProblem.problem_id == problem_id
        )
    )
    if in_attempt is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Задача не входит в эту попытку")

    submission = Submission(
        student_id=student.id,
        problem_id=problem_id,
        exam_attempt_id=attempt.id,
        language=payload.language,
        source_code=payload.source_code,
        status=SubmissionStatus.queued,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    dispatch_judge(submission.id)
    db.refresh(submission)
    return submission


@router.post("/attempts/{attempt_id}/submit", response_model=AttemptDetail)
def submit_attempt(
    attempt_id: int,
    student: User = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
) -> AttemptDetail:
    attempt = _student_attempt(db, attempt_id, student)
    if attempt.status == AttemptStatus.in_progress:
        exam_service.finalize_attempt(db, attempt, timed_out=False)
    return _build_detail(db, attempt)


@router.post("/attempts/{attempt_id}/events", response_model=MessageResponse)
def record_event(
    attempt_id: int,
    payload: EventRequest,
    student: User = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
) -> MessageResponse:
    attempt = _student_attempt(db, attempt_id, student)
    db.add(AttemptEvent(attempt_id=attempt.id, type=payload.type))
    db.commit()
    return MessageResponse(message="Событие записано")
