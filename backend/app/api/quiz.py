"""Эндпоинты банка вопросов, мини-квиза урока и его прохождения."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.content import Lesson, Module
from app.models.quiz import LessonQuestion, ProgressStatus, Question, QuestionType
from app.models.user import User, UserRole
from app.schemas.auth import MessageResponse
from app.schemas.quiz import (
    AttachQuestionRequest,
    LessonDetailOut,
    ProgressOut,
    QuestionCreate,
    QuestionOut,
    QuestionPublicOut,
    QuizResultItem,
    QuizResultOut,
    QuizSubmitRequest,
)
from app.services import quiz as quiz_service

router = APIRouter(tags=["quiz"])


def _validate_correct_answer(payload: QuestionCreate) -> None:
    """Базовая валидация формата эталонного ответа под тип вопроса."""
    ca = payload.correct_answer
    if payload.type in (QuestionType.single_choice, QuestionType.multiple_choice):
        options = payload.options or []
        if not options:
            raise HTTPException(422, "Нужны варианты ответа (options)")
        if payload.type == QuestionType.single_choice:
            idx = ca.get("correct")
            if not isinstance(idx, int) or not 0 <= idx < len(options):
                raise HTTPException(422, "correct_answer.correct должен быть индексом варианта")
        else:
            indices = ca.get("correct")
            if not isinstance(indices, list) or not indices or any(
                not isinstance(i, int) or not 0 <= i < len(options) for i in indices
            ):
                raise HTTPException(422, "correct_answer.correct — список индексов вариантов")
    else:  # short_answer / code_output
        accepted = ca.get("accepted")
        if not isinstance(accepted, list) or not accepted:
            raise HTTPException(422, "correct_answer.accepted — непустой список допустимых ответов")


def _get_or_404(db: Session, model, obj_id: int, name: str):
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{name} не найден(а)")
    return obj


# --- Банк вопросов модуля (учитель) ---
@router.post(
    "/modules/{module_id}/questions", response_model=QuestionOut, status_code=status.HTTP_201_CREATED
)
def create_question(
    module_id: int,
    payload: QuestionCreate,
    _: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> Question:
    _get_or_404(db, Module, module_id, "Модуль")
    _validate_correct_answer(payload)
    question = Question(
        module_id=module_id,
        type=payload.type,
        prompt_md=payload.prompt_md,
        options=payload.options,
        correct_answer=payload.correct_answer,
        explanation_md=payload.explanation_md,
        difficulty=payload.difficulty,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.get("/modules/{module_id}/questions", response_model=list[QuestionOut])
def list_module_questions(
    module_id: int,
    _: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> list[Question]:
    _get_or_404(db, Module, module_id, "Модуль")
    return list(
        db.scalars(select(Question).where(Question.module_id == module_id).order_by(Question.id))
    )


# --- Состав мини-квиза урока (учитель) ---
@router.post("/lessons/{lesson_id}/questions", response_model=MessageResponse)
def attach_question(
    lesson_id: int,
    payload: AttachQuestionRequest,
    _: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> MessageResponse:
    lesson = _get_or_404(db, Lesson, lesson_id, "Урок")
    question = _get_or_404(db, Question, payload.question_id, "Вопрос")
    if question.module_id != lesson.module_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Вопрос должен принадлежать модулю урока"
        )
    exists = db.scalar(
        select(LessonQuestion).where(
            LessonQuestion.lesson_id == lesson_id,
            LessonQuestion.question_id == payload.question_id,
        )
    )
    if exists is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Вопрос уже в квизе урока")

    if payload.order_index is not None:
        order = payload.order_index
    else:
        current_max = db.scalar(
            select(func.max(LessonQuestion.order_index)).where(
                LessonQuestion.lesson_id == lesson_id
            )
        )
        order = (current_max or 0) + 1
    db.add(
        LessonQuestion(lesson_id=lesson_id, question_id=payload.question_id, order_index=order)
    )
    db.commit()
    return MessageResponse(message="Вопрос добавлен в квиз урока")


@router.get("/lessons/{lesson_id}/questions", response_model=list[QuestionOut])
def list_lesson_questions(
    lesson_id: int,
    _: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> list[Question]:
    _get_or_404(db, Lesson, lesson_id, "Урок")
    lesson_questions = db.scalars(
        select(LessonQuestion)
        .where(LessonQuestion.lesson_id == lesson_id)
        .order_by(LessonQuestion.order_index)
    ).all()
    return [lq.question for lq in lesson_questions]


# --- Просмотр урока и прохождение квиза (любой авторизованный / ученик) ---
@router.get("/lessons/{lesson_id}", response_model=LessonDetailOut)
def get_lesson(
    lesson_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LessonDetailOut:
    lesson = _get_or_404(db, Lesson, lesson_id, "Урок")
    lesson_questions = db.scalars(
        select(LessonQuestion)
        .where(LessonQuestion.lesson_id == lesson_id)
        .order_by(LessonQuestion.order_index)
    ).all()
    questions = [
        QuestionPublicOut(
            id=lq.question.id,
            type=lq.question.type,
            prompt_md=lq.question.prompt_md,
            options=lq.question.options,
        )
        for lq in lesson_questions
    ]

    progress = None
    if user.role == UserRole.student:
        prog = quiz_service.get_or_create_progress(db, user.id, lesson_id)
        if prog.status == ProgressStatus.not_started:
            prog.status = ProgressStatus.in_progress
        db.commit()
        progress = ProgressOut(status=prog.status, quiz_score=prog.quiz_score)

    return LessonDetailOut(
        id=lesson.id,
        module_id=lesson.module_id,
        title=lesson.title,
        content_md=lesson.content_md,
        questions=questions,
        progress=progress,
    )


@router.post("/lessons/{lesson_id}/quiz", response_model=QuizResultOut)
def submit_quiz(
    lesson_id: int,
    payload: QuizSubmitRequest,
    student: User = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
) -> QuizResultOut:
    _get_or_404(db, Lesson, lesson_id, "Урок")
    answers = {item.question_id: item.answer for item in payload.answers}
    score, passed, prog_status, graded = quiz_service.grade_quiz(
        db, student.id, lesson_id, answers
    )
    db.commit()
    results = [
        QuizResultItem(
            question_id=question.id,
            is_correct=is_correct,
            correct_answer=question.correct_answer,
            explanation_md=question.explanation_md,
        )
        for question, is_correct in graded
    ]
    return QuizResultOut(score=score, passed=passed, status=prog_status, results=results)
