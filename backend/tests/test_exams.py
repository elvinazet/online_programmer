"""E2E экзаменов: старт с материализацией, серверный таймер, оценивание
(теория с перестановкой вариантов + практика через judge), пересдача, античит."""
from datetime import datetime, timedelta, timezone

import pytest

from app.models.exam import ExamAttempt


def _h(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def exam_env(client, register_verify_login):
    teacher = register_verify_login("et@e.com", role="teacher")
    student = register_verify_login("es@e.com", role="student")
    th, sh = _h(teacher), _h(student)

    # структура для теор-банка
    course = client.post("/api/courses", json={"title": "C", "language": "python"}, headers=th).json()
    level = client.post(f"/api/courses/{course['id']}/levels", json={"name": "beginner"}, headers=th).json()
    target = client.post(f"/api/courses/{course['id']}/levels", json={"name": "intermediate"}, headers=th).json()
    module = client.post(f"/api/levels/{level['id']}/modules", json={"title": "M"}, headers=th).json()

    # два single_choice вопроса с известными правильными ответами (по тексту)
    correct_text = {}
    for prompt, options, correct in [("2+2?", ["3", "4", "5"], 1), ("Небо?", ["зелёное", "синее"], 1)]:
        q = client.post(
            f"/api/modules/{module['id']}/questions",
            json={"type": "single_choice", "prompt_md": prompt, "options": options,
                  "correct_answer": {"correct": correct}},
            headers=th,
        ).json()
        correct_text[q["id"]] = options[correct]

    # практическая задача A+B с тестами
    pid = client.post("/api/problems", json={"title": "A+B", "tags": ["math"]}, headers=th).json()["id"]
    for inp, out in [("2 3\n", "5\n"), ("7 8\n", "15\n")]:
        client.post(f"/api/problems/{pid}/tests",
                    json={"input": inp, "expected_output": out, "is_sample": True}, headers=th)

    # экзамен
    exam = client.post("/api/exams", json={
        "title": "Beginner → Intermediate", "target_level_id": target["id"],
        "duration_seconds": 7200, "pass_threshold": 0.7,
    }, headers=th).json()
    eid = exam["id"]
    client.post(f"/api/exams/{eid}/problems", json={"problem_id": pid, "max_score": 100}, headers=th)
    client.post(f"/api/exams/{eid}/theory", json={"module_id": module["id"], "num_questions": 2}, headers=th)
    client.patch(f"/api/exams/{eid}", json={"is_published": True}, headers=th)

    return {"th": th, "sh": sh, "eid": eid, "pid": pid, "target_level": target["id"], "correct_text": correct_text}


def _answer_theory_correctly(client, sh, detail, correct_text):
    answers = []
    for q in detail["questions"]:
        idx = q["options"].index(correct_text[q["question_id"]])
        answers.append({"attempt_question_id": q["id"], "answer": idx})
    return client.patch(
        f"/api/attempts/{detail['id']}/answers", json={"answers": answers}, headers=sh
    )


def test_student_cannot_create_exam(client, register_verify_login):
    student = register_verify_login("x@e.com", role="student")
    assert client.post("/api/exams", json={"title": "X"}, headers=_h(student)).status_code == 403


def test_exam_full_flow_pass_and_unlock(client, exam_env):
    sh = exam_env["sh"]
    detail = client.post(f"/api/exams/{exam_env['eid']}/attempts", headers=sh).json()
    assert detail["status"] == "in_progress"
    assert len(detail["questions"]) == 2
    assert len(detail["problems"]) == 1
    assert detail["remaining_seconds"] > 0

    # теория — правильно (с учётом перестановки вариантов)
    assert _answer_theory_correctly(client, sh, detail, exam_env["correct_text"]).status_code == 200

    # практика — верное решение
    sub = client.post(
        f"/api/attempts/{detail['id']}/problems/{exam_env['pid']}/submissions",
        json={"language": "python", "source_code": "a,b=map(int,input().split())\nprint(a+b)\n"},
        headers=sh,
    ).json()
    assert sub["status"] == "accepted"

    final = client.post(f"/api/attempts/{detail['id']}/submit", headers=sh).json()
    assert final["status"] == "submitted"
    assert final["result"]["theory_score"] == 100
    assert final["result"]["practical_score"] == 100
    assert final["result"]["total_score"] == 100
    assert final["result"]["passed"] is True

    # уровень открыт
    access = client.get("/api/me/level-access", headers=sh).json()
    assert any(a["level_id"] == exam_env["target_level"] and a["unlocked"] for a in access)


def test_server_timer_autofinalize(client, db, exam_env):
    sh = exam_env["sh"]
    detail = client.post(f"/api/exams/{exam_env['eid']}/attempts", headers=sh).json()
    # сдвигаем дедлайн в прошлое напрямую в БД
    attempt = db.get(ExamAttempt, detail["id"])
    attempt.ends_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()

    # любое обращение сервер завершает по таймеру
    refreshed = client.get(f"/api/attempts/{detail['id']}", headers=sh).json()
    assert refreshed["status"] == "timed_out"
    assert refreshed["result"] is not None
    # приём ответов после завершения запрещён
    late = client.patch(
        f"/api/attempts/{detail['id']}/answers", json={"answers": []}, headers=sh
    )
    assert late.status_code == 400


def test_fail_blocks_retake(client, exam_env):
    sh = exam_env["sh"]
    detail = client.post(f"/api/exams/{exam_env['eid']}/attempts", headers=sh).json()
    # сдаём без ответов → провал
    final = client.post(f"/api/attempts/{detail['id']}/submit", headers=sh).json()
    assert final["result"]["passed"] is False
    assert final["result"]["next_retake_allowed_at"] is not None
    # повторный старт заблокирован
    retry = client.post(f"/api/exams/{exam_env['eid']}/attempts", headers=sh)
    assert retry.status_code == 400


def test_anticheat_event_and_teacher_results(client, exam_env):
    sh, th = exam_env["sh"], exam_env["th"]
    detail = client.post(f"/api/exams/{exam_env['eid']}/attempts", headers=sh).json()
    assert client.post(
        f"/api/attempts/{detail['id']}/events", json={"type": "focus_lost"}, headers=sh
    ).status_code == 200
    client.post(f"/api/attempts/{detail['id']}/submit", headers=sh)

    # учитель видит попытки по экзамену
    results = client.get(f"/api/exams/{exam_env['eid']}/attempts", headers=th).json()
    assert len(results) == 1
    assert results[0]["student_id"]


def test_resume_active_attempt(client, exam_env):
    sh = exam_env["sh"]
    first = client.post(f"/api/exams/{exam_env['eid']}/attempts", headers=sh).json()
    # повторный старт при активной попытке возвращает ту же
    again = client.post(f"/api/exams/{exam_env['eid']}/attempts", headers=sh).json()
    assert again["id"] == first["id"]
