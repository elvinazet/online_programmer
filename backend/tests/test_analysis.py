"""E2E разбора экзамена: карта тем, уроки к повторению, рекомендации задач,
история попыток, агрегат по группе для учителя."""
import pytest


def _h(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def failed_attempt(client, register_verify_login):
    teacher = register_verify_login("at@e.com", role="teacher")
    student = register_verify_login("as@e.com", role="student")
    th, sh = _h(teacher), _h(student)

    course = client.post("/api/courses", json={"title": "C", "language": "python"}, headers=th).json()
    level = client.post(f"/api/courses/{course['id']}/levels", json={"name": "beginner"}, headers=th).json()
    module = client.post(f"/api/levels/{level['id']}/modules", json={"title": "Динамика"}, headers=th).json()
    lesson = client.post(
        f"/api/modules/{module['id']}/lessons", json={"title": "Введение в ДП"}, headers=th
    ).json()
    for prompt in ("Q1", "Q2"):
        client.post(
            f"/api/modules/{module['id']}/questions",
            json={"type": "single_choice", "prompt_md": prompt, "options": ["a", "b"],
                  "correct_answer": {"correct": 0}},
            headers=th,
        )

    # практическая задача (tag dp) + пул рекомендаций с тем же тегом
    pid = client.post(
        "/api/problems", json={"title": "DP task", "tags": ["dp"], "rating": 1200}, headers=th
    ).json()["id"]
    client.post(f"/api/problems/{pid}/tests", json={"input": "1\n", "expected_output": "1\n"}, headers=th)
    for i in range(2):
        client.post(
            "/api/problems",
            json={"title": f"DP rec {i}", "tags": ["dp"], "rating": 1200}, headers=th,
        )

    exam = client.post("/api/exams", json={
        "title": "E", "target_level_id": level["id"], "duration_seconds": 3600,
    }, headers=th).json()
    client.post(f"/api/exams/{exam['id']}/problems", json={"problem_id": pid}, headers=th)
    client.post(f"/api/exams/{exam['id']}/theory", json={"module_id": module["id"], "num_questions": 2}, headers=th)
    client.patch(f"/api/exams/{exam['id']}", json={"is_published": True}, headers=th)

    # ученик стартует и сдаёт без ответов/решений → провал
    attempt = client.post(f"/api/exams/{exam['id']}/attempts", headers=sh).json()
    client.post(f"/api/attempts/{attempt['id']}/submit", headers=sh)

    return {"th": th, "sh": sh, "exam_id": exam["id"], "attempt_id": attempt["id"],
            "module_id": module["id"], "lesson_id": lesson["id"]}


def test_attempt_analysis_weak_topic_and_practice(client, failed_attempt):
    resp = client.get(f"/api/attempts/{failed_attempt['attempt_id']}/analysis", headers=failed_attempt["sh"])
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["summary"]["passed"] is False
    # слабая тема с прямыми ссылками на уроки
    weak = [t for t in data["topics"] if t["is_weak"]]
    assert weak, "ожидалась хотя бы одна слабая тема"
    topic = next(t for t in data["topics"] if t["module_id"] == failed_attempt["module_id"])
    assert topic["score"] == 0
    assert any(l["id"] == failed_attempt["lesson_id"] for l in topic["lessons"])

    # рекомендации тренировочных задач по слабому тегу
    assert data["practice"], "ожидались рекомендации задач"
    assert all("dp" in rec["tags"] for rec in data["practice"])


def test_analysis_forbidden_while_in_progress(client, register_verify_login):
    teacher = register_verify_login("at2@e.com", role="teacher")
    student = register_verify_login("as2@e.com", role="student")
    th, sh = _h(teacher), _h(student)
    course = client.post("/api/courses", json={"title": "C", "language": "python"}, headers=th).json()
    level = client.post(f"/api/courses/{course['id']}/levels", json={"name": "beginner"}, headers=th).json()
    module = client.post(f"/api/levels/{level['id']}/modules", json={"title": "M"}, headers=th).json()
    client.post(f"/api/modules/{module['id']}/questions",
                json={"type": "single_choice", "prompt_md": "Q", "options": ["a", "b"],
                      "correct_answer": {"correct": 0}}, headers=th)
    exam = client.post("/api/exams", json={"title": "E"}, headers=th).json()
    client.post(f"/api/exams/{exam['id']}/theory", json={"module_id": module["id"], "num_questions": 1}, headers=th)
    client.patch(f"/api/exams/{exam['id']}", json={"is_published": True}, headers=th)
    attempt = client.post(f"/api/exams/{exam['id']}/attempts", headers=sh).json()

    resp = client.get(f"/api/attempts/{attempt['id']}/analysis", headers=sh)
    assert resp.status_code == 400


def test_exam_history(client, failed_attempt):
    history = client.get("/api/me/exam-history", headers=failed_attempt["sh"]).json()
    assert len(history) == 1
    assert history[0]["exam_id"] == failed_attempt["exam_id"]
    assert history[0]["passed"] is False


def test_teacher_exam_aggregate(client, failed_attempt):
    agg = client.get(f"/api/exams/{failed_attempt['exam_id']}/analysis", headers=failed_attempt["th"]).json()
    assert agg, "ожидался агрегат по темам"
    module = next(a for a in agg if a["module_id"] == failed_attempt["module_id"])
    assert module["is_weak"] is True
    assert module["score"] == 0
