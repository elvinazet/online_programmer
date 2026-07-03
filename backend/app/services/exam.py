"""Логика экзаменов: старт попытки (материализация варианта), проверка,
завершение с серверным таймером, открытие уровня."""
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.exam import (
    AttemptProblem,
    AttemptQuestion,
    AttemptStatus,
    Exam,
    ExamAttempt,
    StudentLevelAccess,
)
from app.models.quiz import Question, QuestionType
from app.models.submission import Submission
from app.services.quiz import grade_answer


class ExamError(Exception):
    """Нарушение правил экзамена (API маппит в 400)."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def grade_attempt_question(question: Question, options_order, student_answer) -> bool:
    """Проверка теор-вопроса с учётом перестановки вариантов (options_order)."""
    if student_answer is None:
        return False
    if question.type == QuestionType.single_choice:
        if not isinstance(student_answer, int):
            return False
        if options_order:
            if not 0 <= student_answer < len(options_order):
                return False
            original = options_order[student_answer]
        else:
            original = student_answer
        return original == (question.correct_answer or {}).get("correct")
    if question.type == QuestionType.multiple_choice:
        if not isinstance(student_answer, list):
            return False
        try:
            originals = sorted(options_order[d] if options_order else d for d in student_answer)
        except (IndexError, TypeError):
            return False
        return originals == sorted((question.correct_answer or {}).get("correct", []))
    # short_answer / code_output — по тексту
    return grade_answer(question, student_answer)


def start_attempt(db: Session, exam: Exam, student_id: int) -> ExamAttempt:
    if not exam.is_published:
        raise ExamError("Экзамен не опубликован")

    # активная попытка: если время вышло — завершаем, иначе возобновляем
    active = db.scalar(
        select(ExamAttempt).where(
            ExamAttempt.exam_id == exam.id,
            ExamAttempt.student_id == student_id,
            ExamAttempt.status == AttemptStatus.in_progress,
        )
    )
    if active is not None:
        if _as_aware(active.ends_at) <= _utcnow():
            finalize_attempt(db, active, timed_out=True)
        else:
            return active

    last = db.scalar(
        select(ExamAttempt)
        .where(ExamAttempt.exam_id == exam.id, ExamAttempt.student_id == student_id)
        .order_by(ExamAttempt.attempt_number.desc())
    )
    if last is not None and last.next_retake_allowed_at is not None:
        if _as_aware(last.next_retake_allowed_at) > _utcnow():
            raise ExamError("Пересдача пока недоступна")

    now = _utcnow()
    attempt = ExamAttempt(
        exam_id=exam.id,
        student_id=student_id,
        attempt_number=(last.attempt_number if last else 0) + 1,
        started_at=now,
        ends_at=now + timedelta(seconds=exam.duration_seconds),
        status=AttemptStatus.in_progress,
    )
    db.add(attempt)
    db.flush()

    # практика: тот же набор, но порядок перемешан (антивариативность)
    practical = list(exam.practical_problems)
    random.shuffle(practical)
    for i, epp in enumerate(practical):
        db.add(
            AttemptProblem(
                attempt_id=attempt.id,
                problem_id=epp.problem_id,
                order_index=i,
                max_score=epp.max_score,
            )
        )

    # теория: случайная выборка из банков модулей + перемешивание
    picked: list[Question] = []
    for cfg in exam.theory_configs:
        bank = list(db.scalars(select(Question).where(Question.module_id == cfg.module_id)))
        random.shuffle(bank)
        picked.extend(bank[: cfg.num_questions])
    random.shuffle(picked)
    for i, question in enumerate(picked):
        options_order = None
        if question.type in (QuestionType.single_choice, QuestionType.multiple_choice) and question.options:
            options_order = list(range(len(question.options)))
            random.shuffle(options_order)
        db.add(
            AttemptQuestion(
                attempt_id=attempt.id,
                question_id=question.id,
                order_index=i,
                options_order=options_order,
            )
        )

    db.commit()
    db.refresh(attempt)
    return attempt


def unlock_level(db: Session, student_id: int, level_id: int) -> None:
    access = db.scalar(
        select(StudentLevelAccess).where(
            StudentLevelAccess.student_id == student_id,
            StudentLevelAccess.level_id == level_id,
        )
    )
    if access is None:
        db.add(
            StudentLevelAccess(
                student_id=student_id, level_id=level_id, unlocked=True, exam_passed=True
            )
        )
    else:
        access.unlocked = True
        access.exam_passed = True


def finalize_attempt(db: Session, attempt: ExamAttempt, timed_out: bool = False) -> ExamAttempt:
    if attempt.status != AttemptStatus.in_progress:
        return attempt
    exam = db.get(Exam, attempt.exam_id)

    # теория
    attempt_questions = list(
        db.scalars(select(AttemptQuestion).where(AttemptQuestion.attempt_id == attempt.id))
    )
    correct = 0
    for aq in attempt_questions:
        question = db.get(Question, aq.question_id)
        ok = grade_attempt_question(question, aq.options_order, aq.student_answer)
        aq.is_correct = ok
        aq.score = 100 if ok else 0
        correct += int(ok)
    theory_score = round(correct / len(attempt_questions) * 100) if attempt_questions else 0

    # практика: лучший балл сабмита по каждой задаче, взвешенно по max_score
    attempt_problems = list(
        db.scalars(select(AttemptProblem).where(AttemptProblem.attempt_id == attempt.id))
    )
    if attempt_problems:
        total_weight = sum(ap.max_score for ap in attempt_problems) or 1
        accumulated = 0
        for ap in attempt_problems:
            best = db.scalar(
                select(func.max(Submission.score)).where(
                    Submission.exam_attempt_id == attempt.id,
                    Submission.problem_id == ap.problem_id,
                )
            )
            accumulated += (best or 0) * ap.max_score
        practical_score = round(accumulated / total_weight)
    else:
        practical_score = 0

    weight_sum = (exam.practical_weight + exam.theory_weight) or 1
    total = round(
        (practical_score * exam.practical_weight + theory_score * exam.theory_weight) / weight_sum
    )
    passed = total >= exam.pass_threshold * 100

    attempt.theory_score = theory_score
    attempt.practical_score = practical_score
    attempt.total_score = total
    attempt.passed = passed
    attempt.status = AttemptStatus.timed_out if timed_out else AttemptStatus.submitted
    attempt.submitted_at = _utcnow()

    if passed and exam.target_level_id:
        unlock_level(db, attempt.student_id, exam.target_level_id)
        attempt.next_retake_allowed_at = None
    else:
        attempt.next_retake_allowed_at = _utcnow() + timedelta(days=exam.retake_delay_days)

    db.commit()
    db.refresh(attempt)
    return attempt


def ensure_finalized_if_expired(db: Session, attempt: ExamAttempt) -> ExamAttempt:
    """Серверная проверка таймера: если время вышло — авто-завершение."""
    if attempt.status == AttemptStatus.in_progress and _as_aware(attempt.ends_at) <= _utcnow():
        finalize_attempt(db, attempt, timed_out=True)
    return attempt


def remaining_seconds(attempt: ExamAttempt) -> int:
    return max(0, int((_as_aware(attempt.ends_at) - _utcnow()).total_seconds()))
