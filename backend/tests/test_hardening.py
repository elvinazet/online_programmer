"""Тесты харденинга: seed-данные, безопасность judge (TLE), rate-limit."""
from sqlalchemy import func, select

from app.models.problem import Problem
from app.models.submission import SubmissionLanguage
from app.models.user import User
from app.seed import STUDENT_EMAIL, TEACHER_EMAIL, seed


def test_seed_is_idempotent(db):
    assert seed(db) is True
    assert db.scalar(select(User).where(User.email == TEACHER_EMAIL)) is not None
    assert db.scalar(select(User).where(User.email == STUDENT_EMAIL)) is not None
    assert db.scalar(select(func.count()).select_from(Problem)) >= 1
    # повторный запуск не дублирует
    assert seed(db) is False


def test_local_executor_enforces_time_limit():
    from app.services.judge.executor import LocalExecutor

    session = LocalExecutor().session(SubmissionLanguage.python, "while True:\n    pass\n")
    try:
        assert session.compile().ok
        result = session.run("", 500, 128)
        assert result.timed_out is True
    finally:
        session.close()


def test_local_executor_runtime_error():
    from app.services.judge.executor import LocalExecutor

    session = LocalExecutor().session(SubmissionLanguage.python, "raise ValueError('boom')\n")
    try:
        assert session.compile().ok
        result = session.run("", 1000, 128)
        assert result.timed_out is False
        assert result.exit_code != 0
    finally:
        session.close()


def test_local_executor_caps_output():
    from app.services.judge.executor import MAX_OUTPUT_BYTES, LocalExecutor

    session = LocalExecutor().session(SubmissionLanguage.python, "print('x' * 2_000_000)\n")
    try:
        assert session.compile().ok
        result = session.run("", 2000, 128)
        assert result.timed_out is False
        assert len(result.stdout) <= MAX_OUTPUT_BYTES
    finally:
        session.close()


def test_auth_rate_limiter_fixed_window():
    import fakeredis

    from app.services.rate_limit import allow_request

    client = fakeredis.FakeStrictRedis()
    allowed = [allow_request(client, "k", 3, 60) for _ in range(5)]
    assert allowed == [True, True, True, False, False]
