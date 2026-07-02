"""E2E проверка учебников: структура курса, банк вопросов, мини-квиз, прогресс."""
import pytest


def _h(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def scaffold(client, register_verify_login):
    """Учитель создаёт курс → уровень → модуль → урок + 3 вопроса в квизе."""
    teacher = register_verify_login("teacher@e.com", role="teacher", display_name="T")
    student = register_verify_login("student@e.com", role="student")
    th, sh = _h(teacher), _h(student)

    course = client.post(
        "/api/courses", json={"title": "Python", "language": "python"}, headers=th
    ).json()
    level = client.post(
        f"/api/courses/{course['id']}/levels", json={"name": "beginner"}, headers=th
    ).json()
    module = client.post(
        f"/api/levels/{level['id']}/modules", json={"title": "Основы"}, headers=th
    ).json()
    lesson = client.post(
        f"/api/modules/{module['id']}/lessons",
        json={"title": "Переменные", "content_md": "# Переменные\nТекст урока"},
        headers=th,
    ).json()

    questions = []
    specs = [
        {"type": "single_choice", "prompt_md": "2+2?", "options": ["3", "4", "5"],
         "correct_answer": {"correct": 1}, "explanation_md": "Это 4"},
        {"type": "short_answer", "prompt_md": "Ответ на всё?",
         "correct_answer": {"accepted": ["42", "сорок два"]}},
        {"type": "code_output", "prompt_md": "print('Hello')?",
         "correct_answer": {"accepted": ["Hello"]}},
    ]
    for spec in specs:
        q = client.post(
            f"/api/modules/{module['id']}/questions", json=spec, headers=th
        )
        assert q.status_code == 201, q.text
        qid = q.json()["id"]
        questions.append(qid)
        attached = client.post(
            f"/api/lessons/{lesson['id']}/questions", json={"question_id": qid}, headers=th
        )
        assert attached.status_code == 200, attached.text

    return {
        "th": th, "sh": sh,
        "course_id": course["id"], "level_id": level["id"],
        "module_id": module["id"], "lesson_id": lesson["id"], "questions": questions,
    }


def test_student_cannot_create_course(client, register_verify_login):
    student = register_verify_login("s2@e.com", role="student")
    resp = client.post(
        "/api/courses", json={"title": "X", "language": "cpp"}, headers=_h(student)
    )
    assert resp.status_code == 403


def test_course_tree(client, scaffold):
    resp = client.get(f"/api/courses/{scaffold['course_id']}", headers=scaffold["sh"])
    assert resp.status_code == 200
    tree = resp.json()
    assert tree["language"] == "python"
    lesson = tree["levels"][0]["modules"][0]["lessons"][0]
    assert lesson["id"] == scaffold["lesson_id"]
    assert lesson["status"] is None  # ученик ещё не открывал урок


def test_student_sees_no_answers(client, scaffold):
    resp = client.get(f"/api/lessons/{scaffold['lesson_id']}", headers=scaffold["sh"])
    assert resp.status_code == 200
    body = resp.json()
    assert body["progress"]["status"] == "in_progress"  # открытие урока → in_progress
    assert len(body["questions"]) == 3
    for q in body["questions"]:
        assert "correct_answer" not in q
        assert "explanation_md" not in q


def test_teacher_sees_full_questions(client, scaffold):
    resp = client.get(f"/api/lessons/{scaffold['lesson_id']}/questions", headers=scaffold["th"])
    assert resp.status_code == 200
    questions = resp.json()
    assert len(questions) == 3
    assert questions[0]["correct_answer"] == {"correct": 1}


def test_quiz_pass_marks_completed(client, scaffold):
    q1, q2, q3 = scaffold["questions"]
    resp = client.post(
        f"/api/lessons/{scaffold['lesson_id']}/quiz",
        json={"answers": [
            {"question_id": q1, "answer": 1},
            {"question_id": q2, "answer": "42"},
            {"question_id": q3, "answer": "Hello"},
        ]},
        headers=scaffold["sh"],
    )
    assert resp.status_code == 200, resp.text
    result = resp.json()
    assert result["score"] == 100
    assert result["passed"] is True
    assert result["status"] == "completed"
    # разбор содержит правильные ответы и пояснение
    assert all(item["is_correct"] for item in result["results"])
    assert result["results"][0]["explanation_md"] == "Это 4"

    # дерево теперь показывает урок как пройденный
    tree = client.get(f"/api/courses/{scaffold['course_id']}", headers=scaffold["sh"]).json()
    assert tree["levels"][0]["modules"][0]["lessons"][0]["status"] == "completed"


def test_quiz_partial_fail_keeps_in_progress(client, scaffold):
    q1, q2, q3 = scaffold["questions"]
    resp = client.post(
        f"/api/lessons/{scaffold['lesson_id']}/quiz",
        json={"answers": [
            {"question_id": q1, "answer": 0},   # неверно
            {"question_id": q2, "answer": "нет"},  # неверно
            {"question_id": q3, "answer": "Hello"},  # верно
        ]},
        headers=scaffold["sh"],
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["score"] == 33  # 1 из 3
    assert result["passed"] is False
    assert result["status"] == "in_progress"


def test_short_answer_is_case_insensitive(client, scaffold):
    _, q2, _ = scaffold["questions"]
    # проверяем нормализацию: "  СОРОК ДВА " принимается
    resp = client.post(
        f"/api/lessons/{scaffold['lesson_id']}/quiz",
        json={"answers": [{"question_id": q2, "answer": "  СОРОК ДВА "}]},
        headers=scaffold["sh"],
    )
    assert resp.status_code == 200
    item = next(r for r in resp.json()["results"] if r["question_id"] == q2)
    assert item["is_correct"] is True


def test_invalid_question_payload_rejected(client, scaffold):
    # single_choice без вариантов → 422
    resp = client.post(
        f"/api/modules/{scaffold['module_id']}/questions",
        json={"type": "single_choice", "prompt_md": "?", "correct_answer": {"correct": 0}},
        headers=scaffold["th"],
    )
    assert resp.status_code == 422
