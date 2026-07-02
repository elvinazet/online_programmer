"""E2E: кэш CF (моки), фильтр задач, judge (LocalExecutor, Python), статистика."""
import time

import pytest
from sqlalchemy import select

from app.models.problem import Problem
from app.models.user import User
from app.services.cf_poll import sync_user_solved
from app.services.problem_sync import sync_problemset


class FakeCF:
    def __init__(self, problems=None, statuses=None):
        self._problems = problems or []
        self._statuses = statuses or []

    def problemset_problems(self, tags=None):
        return {"problems": self._problems}

    def user_status(self, handle, count=10000, frm=1):
        return self._statuses


def _h(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


# --------------------------- CF services ---------------------------
def test_sync_problemset(db):
    fake = FakeCF(problems=[
        {"contestId": 1, "index": "A", "name": "Watermelon", "rating": 800, "tags": ["math", "brute force"]},
        {"contestId": 4, "index": "A", "name": "Theatre", "rating": 1000, "tags": ["math"]},
    ])
    assert sync_problemset(db, fake) == 2
    problem = db.scalar(select(Problem).where(Problem.cf_contest_id == 1, Problem.cf_index == "A"))
    assert problem.rating == 800
    assert {t.tag for t in problem.tags} == {"math", "brute force"}
    # повторная синхронизация обновляет, не дублирует
    assert sync_problemset(db, fake) == 2
    assert db.scalar(select(Problem).where(Problem.cf_contest_id == 1)).rating == 800


def test_cf_poll_marks_solved(db, register_verify_login):
    register_verify_login("cf@e.com", role="student", codeforces_handle="tourist")
    student = db.scalar(select(User).where(User.email == "cf@e.com"))
    sync_problemset(db, FakeCF(problems=[
        {"contestId": 1, "index": "A", "name": "W", "rating": 800, "tags": ["math"]},
    ]))
    fake = FakeCF(statuses=[
        {"verdict": "OK", "problem": {"contestId": 1, "index": "A"}},
        {"verdict": "WRONG_ANSWER", "problem": {"contestId": 99, "index": "Z"}},
    ])
    assert sync_user_solved(db, fake, student.id, "tourist") == 1
    assert sync_user_solved(db, fake, student.id, "tourist") == 0  # уже засчитано


# --------------------------- Problems API ---------------------------
def test_problems_filter(client, register_verify_login):
    teacher = register_verify_login("t2@e.com", role="teacher")
    student = register_verify_login("s2@e.com", role="student")
    th, sh = _h(teacher), _h(student)
    client.post("/api/problems", json={"title": "Easy", "rating": 800, "tags": ["math"]}, headers=th)
    client.post("/api/problems", json={"title": "Hard", "rating": 2000, "tags": ["dp"]}, headers=th)

    by_rating = client.get("/api/problems?min_rating=1000", headers=sh).json()
    assert by_rating and all(p["rating"] >= 1000 for p in by_rating)

    by_tag = client.get("/api/problems?tags=math", headers=sh).json()
    assert by_tag and all("math" in p["tags"] for p in by_tag)


def test_student_cannot_create_problem(client, register_verify_login):
    student = register_verify_login("s3@e.com", role="student")
    r = client.post("/api/problems", json={"title": "X"}, headers=_h(student))
    assert r.status_code == 403


# --------------------------- Judge (inline + LocalExecutor) ---------------------------
@pytest.fixture
def sum_problem(client, register_verify_login):
    teacher = register_verify_login("jt@e.com", role="teacher")
    student = register_verify_login("js@e.com", role="student")
    th, sh = _h(teacher), _h(student)
    pid = client.post(
        "/api/problems",
        json={"title": "A+B", "statement_md": "сумма", "tags": ["math"], "rating": 800},
        headers=th,
    ).json()["id"]
    for inp, out in [("2 3\n", "5\n"), ("10 20\n", "30\n")]:
        assert client.post(
            f"/api/problems/{pid}/tests",
            json={"input": inp, "expected_output": out, "is_sample": True},
            headers=th,
        ).status_code == 200
    return {"pid": pid, "sh": sh, "th": th}


def _submit(client, prob, code):
    return client.post(
        f"/api/problems/{prob['pid']}/submissions",
        json={"language": "python", "source_code": code},
        headers=prob["sh"],
    )


def test_submission_accepted(client, sum_problem):
    r = _submit(client, sum_problem, "a,b=map(int,input().split())\nprint(a+b)\n")
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "accepted"
    assert body["score"] == 100 and body["passed_tests"] == 2

    stats = client.get("/api/me/stats", headers=sum_problem["sh"]).json()
    assert stats["solved_total"] == 1
    assert stats["by_tag"].get("math") == 1


def test_submission_wrong_answer(client, sum_problem):
    body = _submit(client, sum_problem, "a,b=map(int,input().split())\nprint(a-b)\n").json()
    assert body["status"] == "wrong_answer"
    assert body["passed_tests"] == 0


def test_submission_runtime_error(client, sum_problem):
    body = _submit(client, sum_problem, "import sys\nsys.exit(1)\n").json()
    assert body["status"] == "runtime_error"


def test_submission_compile_error(client, sum_problem):
    body = _submit(client, sum_problem, "def f(:\n    pass\n").json()
    assert body["status"] == "compile_error"
    assert body["compile_output"]


# --------------------------- Rate limiter ---------------------------
def test_rate_limiter():
    import fakeredis

    from app.services.rate_limit import RedisRateLimiter

    limiter = RedisRateLimiter(fakeredis.FakeStrictRedis(), key="t", window_ms=200)
    assert limiter.acquire(block=False) is True
    assert limiter.acquire(block=False) is False
    time.sleep(0.25)
    assert limiter.acquire(block=False) is True
