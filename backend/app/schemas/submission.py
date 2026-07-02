"""Схемы сабмитов."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.submission import SubmissionLanguage, SubmissionStatus


class SubmissionCreate(BaseModel):
    language: SubmissionLanguage
    source_code: str


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    problem_id: int
    language: SubmissionLanguage
    status: SubmissionStatus
    passed_tests: int
    total_tests: int
    score: int
    time_ms: int | None = None
    compile_output: str | None = None
    created_at: datetime
