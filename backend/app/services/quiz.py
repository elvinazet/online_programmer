"""Проверка мини-квиза и учёт прогресса по уроку."""
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.quiz import (
    LessonProgress,
    LessonQuestion,
    ProgressStatus,
    Question,
    QuestionType,
)

# Порог прохождения мини-квиза урока, %
LESSON_QUIZ_PASS = 60


def _norm_text(value: Any) -> str:
    return " ".join(str(value).strip().split()).lower()


def grade_answer(question: Question, answer: Any) -> bool:
    correct = question.correct_answer or {}
    if question.type == QuestionType.single_choice:
        return answer == correct.get("correct")
    if question.type == QuestionType.multiple_choice:
        if not isinstance(answer, list):
            return False
        return sorted(answer) == sorted(correct.get("correct", []))
    if question.type == QuestionType.short_answer:
        accepted = {_norm_text(a) for a in correct.get("accepted", [])}
        return _norm_text(answer) in accepted
    if question.type == QuestionType.code_output:
        # для вывода кода регистр важен, лишь обрезаем крайние пробелы/переводы строк
        accepted = {str(a).strip() for a in correct.get("accepted", [])}
        return str(answer).strip() in accepted
    return False


def get_or_create_progress(db: Session, student_id: int, lesson_id: int) -> LessonProgress:
    progress = db.scalar(
        select(LessonProgress).where(
            LessonProgress.student_id == student_id,
            LessonProgress.lesson_id == lesson_id,
        )
    )
    if progress is None:
        progress = LessonProgress(
            student_id=student_id, lesson_id=lesson_id, status=ProgressStatus.not_started
        )
        db.add(progress)
    return progress


def grade_quiz(
    db: Session, student_id: int, lesson_id: int, answers: dict[int, Any]
) -> tuple[int, bool, ProgressStatus, list[tuple[Question, bool]]]:
    lesson_questions = db.scalars(
        select(LessonQuestion)
        .where(LessonQuestion.lesson_id == lesson_id)
        .order_by(LessonQuestion.order_index)
    ).all()

    graded: list[tuple[Question, bool]] = []
    correct_count = 0
    for lq in lesson_questions:
        is_correct = grade_answer(lq.question, answers.get(lq.question.id))
        correct_count += int(is_correct)
        graded.append((lq.question, is_correct))

    total = len(lesson_questions)
    score = 100 if total == 0 else round(correct_count / total * 100)
    passed = score >= LESSON_QUIZ_PASS

    progress = get_or_create_progress(db, student_id, lesson_id)
    # храним лучший балл; уже пройденный урок не «раззавершаем» при пересдаче
    best = score if progress.quiz_score is None else max(progress.quiz_score, score)
    if progress.status == ProgressStatus.completed:
        progress.quiz_score = best
    elif passed:
        progress.status = ProgressStatus.completed
        progress.completed_at = datetime.now(timezone.utc)
        progress.quiz_score = best
    else:
        progress.status = ProgressStatus.in_progress
        progress.quiz_score = score

    return score, passed, progress.status, graded
