"""Общие фикстуры тестов. Используем изолированную SQLite-БД."""
import os
import pathlib
import tempfile

# Настраиваем окружение ДО импорта приложения (settings читается при импорте).
_DB_PATH = pathlib.Path(tempfile.gettempdir()) / "op_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH}"
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("EMAIL_BACKEND", "console")
# Судим синхронно локальным исполнителем — без Docker/Celery/Redis.
os.environ.setdefault("JUDGE_INLINE", "true")
os.environ.setdefault("JUDGE_BACKEND", "local")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.models  # noqa: E402,F401 — наполняет Base.metadata
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def register_verify_login(client, db):
    """Хелпер: регистрирует, подтверждает email и логинит пользователя.

    Возвращает тело ответа /login (access_token, refresh_token).
    """
    from sqlalchemy import select

    from app.models.token import EmailVerificationToken
    from app.models.user import User

    def _make(email, password="password123", role="student", **extra):
        resp = client.post(
            "/api/auth/register",
            json={"email": email, "password": password, "role": role, **extra},
        )
        assert resp.status_code == 201, resp.text
        user = db.scalar(select(User).where(User.email == email))
        token = db.scalar(
            select(EmailVerificationToken).where(EmailVerificationToken.user_id == user.id)
        ).token
        assert client.post("/api/auth/verify-email", json={"token": token}).status_code == 200
        login = client.post("/api/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200, login.text
        return login.json()

    return _make
