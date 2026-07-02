"""End-to-end проверка авторизации: регистрация → verify → login → refresh →
reset, а также RBAC и группы."""
from sqlalchemy import select

from app.models.token import EmailVerificationToken, PasswordResetToken
from app.models.user import User


def _register(client, email, password, role="student", **extra):
    return client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "role": role, **extra},
    )


def _verify_token(db, email):
    user = db.scalar(select(User).where(User.email == email))
    return db.scalar(
        select(EmailVerificationToken).where(EmailVerificationToken.user_id == user.id)
    ).token


def _register_verify_login(client, db, email, password, role="student", **extra):
    assert _register(client, email, password, role, **extra).status_code == 201
    token = _verify_token(db, email)
    assert client.post("/api/auth/verify-email", json={"token": token}).status_code == 200
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_login_blocked_until_verified(client, db):
    assert _register(client, "a@example.com", "password123").status_code == 201
    resp = client.post(
        "/api/auth/login", json={"email": "a@example.com", "password": "password123"}
    )
    assert resp.status_code == 403


def test_duplicate_email_rejected(client, db):
    assert _register(client, "dup@example.com", "password123").status_code == 201
    assert _register(client, "dup@example.com", "password123").status_code == 409


def test_full_flow_and_refresh_rotation(client, db):
    tokens = _register_verify_login(
        client, db, "stud@example.com", "password123",
        role="student", codeforces_handle="tourist",
    )
    access, refresh = tokens["access_token"], tokens["refresh_token"]

    me = client.get("/api/users/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "stud@example.com"
    assert body["role"] == "student"
    assert body["student_profile"]["codeforces_handle"] == "tourist"

    # ротация refresh: старый отзывается, новый работает
    rotated = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert rotated.status_code == 200
    new_refresh = rotated.json()["refresh_token"]
    assert new_refresh != refresh
    assert client.post("/api/auth/refresh", json={"refresh_token": refresh}).status_code == 401
    assert client.post("/api/auth/refresh", json={"refresh_token": new_refresh}).status_code == 200


def test_password_reset(client, db):
    _register_verify_login(client, db, "reset@example.com", "oldpassword1")
    assert client.post(
        "/api/auth/forgot-password", json={"email": "reset@example.com"}
    ).status_code == 200

    user = db.scalar(select(User).where(User.email == "reset@example.com"))
    reset_token = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
    ).token
    assert client.post(
        "/api/auth/reset-password",
        json={"token": reset_token, "new_password": "newpassword2"},
    ).status_code == 200

    # старый пароль больше не работает, новый — работает
    assert client.post(
        "/api/auth/login", json={"email": "reset@example.com", "password": "oldpassword1"}
    ).status_code == 401
    assert client.post(
        "/api/auth/login", json={"email": "reset@example.com", "password": "newpassword2"}
    ).status_code == 200


def test_rbac_and_groups(client, db):
    student = _register_verify_login(client, db, "s2@example.com", "password123", role="student")
    teacher = _register_verify_login(
        client, db, "t1@example.com", "password123", role="teacher", display_name="Иван"
    )
    s_headers = {"Authorization": f"Bearer {student['access_token']}"}
    t_headers = {"Authorization": f"Bearer {teacher['access_token']}"}

    # ученик не может создавать группы, учитель может
    assert client.post("/api/groups", json={"name": "G1"}, headers=s_headers).status_code == 403
    created = client.post("/api/groups", json={"name": "G1"}, headers=t_headers)
    assert created.status_code == 201
    group_id = created.json()["id"]

    added = client.post(
        f"/api/groups/{group_id}/members",
        json={"student_email": "s2@example.com"},
        headers=t_headers,
    )
    assert added.status_code == 200

    members = client.get(f"/api/groups/{group_id}/members", headers=t_headers)
    assert members.status_code == 200
    assert members.json()[0]["email"] == "s2@example.com"


def test_unauthenticated_rejected(client, db):
    assert client.get("/api/users/me").status_code == 401


def test_health(client, db):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
