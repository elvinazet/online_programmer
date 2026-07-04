"""E2E: задания (назначение задач/уроков), прогресс группы, streak, таймлайн."""
import pytest


def _h(t):
    return {"Authorization": f"Bearer {t['access_token']}"}


@pytest.fixture
def env(client, register_verify_login):
    teacher = register_verify_login("tt@e.com", role="teacher")
    student = register_verify_login("ss@e.com", role="student")
    outsider = register_verify_login("out@e.com", role="student")
    th, sh, oh = _h(teacher), _h(student), _h(outsider)

    # группа + участник
    gid = client.post("/api/groups", json={"name": "G"}, headers=th).json()["id"]
    client.post(f"/api/groups/{gid}/members", json={"student_email": "ss@e.com"}, headers=th)

    # задача A+B с тестами
    pid = client.post("/api/problems", json={"title": "A+B", "tags": ["math"]}, headers=th).json()["id"]
    for inp, out in [("2 3\n", "5\n"), ("4 5\n", "9\n")]:
        client.post(f"/api/problems/{pid}/tests", json={"input": inp, "expected_output": out}, headers=th)

    # ученику нужен id — достанем через group members
    members = client.get(f"/api/groups/{gid}/members", headers=th).json()
    student_id = members[0]["student_id"]

    return {"th": th, "sh": sh, "oh": oh, "gid": gid, "pid": pid, "student_id": student_id}


def test_assign_problem_and_done_status(client, env):
    r = client.post("/api/assignments", json={
        "type": "problem", "student_id": env["student_id"], "problem_id": env["pid"],
        "note": "решите к пятнице",
    }, headers=env["th"])
    assert r.status_code == 201, r.text

    mine = client.get("/api/me/assignments", headers=env["sh"]).json()
    assert len(mine) == 1
    assert mine[0]["title"] == "A+B"
    assert mine[0]["done"] is False
    assert mine[0]["note"] == "решите к пятнице"

    # ученик решает задачу → done становится True
    sub = client.post(
        f"/api/problems/{env['pid']}/submissions",
        json={"language": "python", "source_code": "a,b=map(int,input().split())\nprint(a+b)\n"},
        headers=env["sh"],
    ).json()
    assert sub["status"] == "accepted"
    mine = client.get("/api/me/assignments", headers=env["sh"]).json()
    assert mine[0]["done"] is True


def test_assign_to_outsider_forbidden(client, env):
    # outsider не в группе учителя
    outsider_me = client.get("/api/users/me", headers=env["oh"]).json()
    r = client.post("/api/assignments", json={
        "type": "problem", "student_id": outsider_me["id"], "problem_id": env["pid"],
    }, headers=env["th"])
    assert r.status_code == 403


def test_assign_to_group_expands(client, env, register_verify_login):
    # добавим второго ученика в группу
    second = register_verify_login("ss2@e.com", role="student")
    client.post(f"/api/groups/{env['gid']}/members", json={"student_email": "ss2@e.com"}, headers=env["th"])

    r = client.post("/api/assignments", json={
        "type": "problem", "group_id": env["gid"], "problem_id": env["pid"],
    }, headers=env["th"])
    assert r.status_code == 201
    assert "2" in r.json()["message"]  # назначено двоим

    assert len(client.get("/api/me/assignments", headers=env["sh"]).json()) == 1
    assert len(client.get("/api/me/assignments", headers=_h(second)).json()) == 1


def test_streak_and_timeline_on_solve(client, env):
    client.post(
        f"/api/problems/{env['pid']}/submissions",
        json={"language": "python", "source_code": "a,b=map(int,input().split())\nprint(a+b)\n"},
        headers=env["sh"],
    )
    stats = client.get("/api/me/stats", headers=env["sh"]).json()
    assert stats["solved_total"] == 1
    assert stats["streak"] == 1

    timeline = client.get("/api/me/solved-timeline", headers=env["sh"]).json()
    assert len(timeline) == 1
    assert timeline[0]["count"] == 1


def test_group_progress(client, env):
    client.post(
        f"/api/problems/{env['pid']}/submissions",
        json={"language": "python", "source_code": "a,b=map(int,input().split())\nprint(a+b)\n"},
        headers=env["sh"],
    )
    progress = client.get(f"/api/groups/{env['gid']}/progress", headers=env["th"]).json()
    assert len(progress) == 1
    assert progress[0]["solved_total"] == 1
    assert progress[0]["email"] == "ss@e.com"


def test_assign_lesson(client, env, register_verify_login):
    # создать урок для назначения
    th = env["th"]
    course = client.post("/api/courses", json={"title": "C", "language": "python"}, headers=th).json()
    level = client.post(f"/api/courses/{course['id']}/levels", json={"name": "beginner"}, headers=th).json()
    module = client.post(f"/api/levels/{level['id']}/modules", json={"title": "M"}, headers=th).json()
    lesson = client.post(f"/api/modules/{module['id']}/lessons", json={"title": "Урок 1"}, headers=th).json()

    r = client.post("/api/assignments", json={
        "type": "lesson", "student_id": env["student_id"], "lesson_id": lesson["id"],
    }, headers=th)
    assert r.status_code == 201
    mine = client.get("/api/me/assignments", headers=env["sh"]).json()
    assert any(a["type"] == "lesson" and a["title"] == "Урок 1" for a in mine)
