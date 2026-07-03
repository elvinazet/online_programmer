"""Разбор результатов экзамена: карта тем, план подготовки, агрегаты."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.content import Lesson, Module
from app.models.exam import AttemptProblem, AttemptQuestion, AttemptStatus, ExamAttempt
from app.models.problem import Problem, ProblemTag
from app.models.quiz import Question
from app.models.submission import StudentSolvedProblem, Submission

WEAK_THRESHOLD = 70  # тема считается слабой при score < 70%


def topic_breakdown(db: Session, attempt: ExamAttempt) -> list[dict]:
    """Разбивка теории по темам (модулям) с уроками к повторению для слабых."""
    by_module: dict[int, list[int]] = {}
    for aq in db.scalars(
        select(AttemptQuestion).where(AttemptQuestion.attempt_id == attempt.id)
    ):
        question = db.get(Question, aq.question_id)
        bucket = by_module.setdefault(question.module_id, [0, 0])
        bucket[0] += int(aq.is_correct)
        bucket[1] += 1

    topics = []
    for module_id, (correct, total) in by_module.items():
        module = db.get(Module, module_id)
        score = round(correct / total * 100) if total else 0
        is_weak = score < WEAK_THRESHOLD
        lessons = []
        if is_weak:
            lessons = [
                {"id": lesson.id, "title": lesson.title}
                for lesson in db.scalars(
                    select(Lesson).where(Lesson.module_id == module_id).order_by(Lesson.order_index)
                )
            ]
        topics.append({
            "module_id": module_id,
            "module_title": module.title if module else "",
            "correct": correct,
            "total": total,
            "score": score,
            "is_weak": is_weak,
            "lessons": lessons,
        })
    topics.sort(key=lambda t: t["score"])
    return topics


def practice_recommendations(
    db: Session, attempt: ExamAttempt, student_id: int, limit: int = 5
) -> list[dict]:
    """Подбор тренировочных задач по слабым практическим темам (тегам/рейтингу)."""
    attempt_problems = list(
        db.scalars(select(AttemptProblem).where(AttemptProblem.attempt_id == attempt.id))
    )
    failed_tags: set[str] = set()
    ratings: list[int] = []
    for ap in attempt_problems:
        best = db.scalar(
            select(func.max(Submission.score)).where(
                Submission.exam_attempt_id == attempt.id,
                Submission.problem_id == ap.problem_id,
            )
        )
        if (best or 0) < 100:
            problem = db.get(Problem, ap.problem_id)
            if problem is not None:
                failed_tags.update(t.tag for t in problem.tags)
                if problem.rating:
                    ratings.append(problem.rating)

    if not failed_tags:
        return []

    solved_subq = select(StudentSolvedProblem.problem_id).where(
        StudentSolvedProblem.student_id == student_id
    )
    stmt = select(Problem).where(Problem.tags.any(ProblemTag.tag.in_(failed_tags)))
    if ratings:
        stmt = stmt.where(
            Problem.rating.isnot(None),
            Problem.rating >= min(ratings) - 200,
            Problem.rating <= max(ratings) + 200,
        )
    stmt = stmt.where(Problem.id.notin_(solved_subq))
    attempt_pids = [ap.problem_id for ap in attempt_problems]
    if attempt_pids:
        stmt = stmt.where(Problem.id.notin_(attempt_pids))

    problems = db.scalars(stmt.order_by(Problem.rating).limit(limit))
    return [
        {
            "problem_id": p.id,
            "title": p.title,
            "rating": p.rating,
            "url": p.url,
            "tags": [t.tag for t in p.tags],
        }
        for p in problems
    ]


def attempt_analysis(db: Session, attempt: ExamAttempt) -> dict:
    return {
        "attempt_id": attempt.id,
        "summary": {
            "total_score": attempt.total_score,
            "practical_score": attempt.practical_score,
            "theory_score": attempt.theory_score,
            "passed": attempt.passed,
        },
        "topics": topic_breakdown(db, attempt),
        "practice": practice_recommendations(db, attempt, attempt.student_id),
    }


def exam_topic_aggregate(db: Session, exam_id: int) -> list[dict]:
    """Агрегат по темам для учителя: средний балл по группе, какие темы западают."""
    attempt_ids = list(
        db.scalars(
            select(ExamAttempt.id).where(
                ExamAttempt.exam_id == exam_id,
                ExamAttempt.status != AttemptStatus.in_progress,
            )
        )
    )
    if not attempt_ids:
        return []

    by_module: dict[int, list[int]] = {}
    for aq in db.scalars(
        select(AttemptQuestion).where(AttemptQuestion.attempt_id.in_(attempt_ids))
    ):
        question = db.get(Question, aq.question_id)
        bucket = by_module.setdefault(question.module_id, [0, 0])
        bucket[0] += int(aq.is_correct)
        bucket[1] += 1

    aggregate = []
    for module_id, (correct, total) in by_module.items():
        module = db.get(Module, module_id)
        score = round(correct / total * 100) if total else 0
        aggregate.append({
            "module_id": module_id,
            "module_title": module.title if module else "",
            "score": score,
            "total_answers": total,
            "is_weak": score < WEAK_THRESHOLD,
        })
    aggregate.sort(key=lambda x: x["score"])
    return aggregate
