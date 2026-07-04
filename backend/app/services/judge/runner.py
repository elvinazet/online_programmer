"""Конвейер проверки сабмита: компиляция → прогон по тестам → вердикт."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.problem import Problem, ProblemTest
from app.models.submission import (
    SolvedSource,
    StudentSolvedProblem,
    Submission,
    SubmissionStatus,
)
from app.services.streak import bump_streak


def _normalize(text: str) -> str:
    """Сравнение вывода без учёта хвостовых пробелов и переводов строк."""
    lines = text.replace("\r\n", "\n").rstrip("\n").split("\n")
    return "\n".join(line.rstrip() for line in lines)


def _mark_solved(db: Session, student_id: int, problem_id: int) -> None:
    exists = db.scalar(
        select(StudentSolvedProblem).where(
            StudentSolvedProblem.student_id == student_id,
            StudentSolvedProblem.problem_id == problem_id,
        )
    )
    if exists is None:
        db.add(
            StudentSolvedProblem(
                student_id=student_id,
                problem_id=problem_id,
                source=SolvedSource.local,
                solved_at=datetime.now(timezone.utc),
            )
        )
        bump_streak(db, student_id)
        db.commit()


def judge_submission(db: Session, submission: Submission, executor) -> Submission:
    problem = db.get(Problem, submission.problem_id)
    tests = list(
        db.scalars(
            select(ProblemTest)
            .where(ProblemTest.problem_id == problem.id)
            .order_by(ProblemTest.order_index)
        )
    )

    submission.status = SubmissionStatus.running
    submission.total_tests = len(tests)
    db.commit()

    session = executor.session(submission.language, submission.source_code)
    try:
        compiled = session.compile()
        if not compiled.ok:
            submission.status = SubmissionStatus.compile_error
            submission.compile_output = compiled.message
            submission.score = 0
            db.commit()
            return submission

        time_limit = problem.time_limit_ms or settings.judge_default_time_limit_ms
        memory_limit = problem.memory_limit_mb or settings.judge_default_memory_mb

        passed = 0
        max_time = 0
        verdict = SubmissionStatus.accepted
        for test in tests:
            result = session.run(test.input, time_limit, memory_limit)
            max_time = max(max_time, result.time_ms)
            if result.timed_out:
                verdict = SubmissionStatus.tle
                break
            if result.oom:
                verdict = SubmissionStatus.mle
                break
            if result.exit_code != 0:
                verdict = SubmissionStatus.runtime_error
                break
            if _normalize(result.stdout) != _normalize(test.expected_output):
                verdict = SubmissionStatus.wrong_answer
                break
            passed += 1

        submission.passed_tests = passed
        submission.total_tests = len(tests)
        submission.time_ms = max_time
        submission.score = 100 if not tests else round(passed / len(tests) * 100)
        submission.status = verdict
        db.commit()

        if verdict == SubmissionStatus.accepted:
            _mark_solved(db, submission.student_id, problem.id)
        return submission
    finally:
        session.close()
