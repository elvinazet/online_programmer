"""Точка входа FastAPI-приложения."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.analysis import router as analysis_router
from app.api.attempts import router as attempts_router
from app.api.auth import router as auth_router
from app.api.codeforces import router as codeforces_router
from app.api.content import router as content_router
from app.api.exams import router as exams_router
from app.api.groups import router as groups_router
from app.api.problems import router as problems_router
from app.api.quiz import router as quiz_router
from app.api.stats import router as stats_router
from app.api.submissions import router as submissions_router
from app.api.users import router as users_router
from app.core.config import settings
from app.db.session import engine

logging.basicConfig(level=logging.INFO)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(groups_router, prefix="/api")
app.include_router(content_router, prefix="/api")
app.include_router(quiz_router, prefix="/api")
app.include_router(problems_router, prefix="/api")
app.include_router(submissions_router, prefix="/api")
app.include_router(codeforces_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
app.include_router(exams_router, prefix="/api")
app.include_router(attempts_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")


@app.get("/health", tags=["health"])
def health() -> dict:
    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 — health-check не должен падать
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "database": db_ok}
