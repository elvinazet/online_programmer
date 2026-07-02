"""Схемы задач."""
from pydantic import BaseModel

from app.models.problem import ProblemSource


class ProblemOut(BaseModel):
    id: int
    source: ProblemSource
    title: str
    rating: int | None = None
    url: str | None = None
    cf_contest_id: int | None = None
    cf_index: str | None = None
    tags: list[str] = []
    solved: bool = False


class SampleTest(BaseModel):
    input: str
    expected_output: str


class ProblemDetail(ProblemOut):
    statement_md: str | None = None
    time_limit_ms: int
    memory_limit_mb: int
    samples: list[SampleTest] = []


class AuthoredProblemCreate(BaseModel):
    title: str
    statement_md: str | None = None
    rating: int | None = None
    time_limit_ms: int = 2000
    memory_limit_mb: int = 256
    tags: list[str] = []


class ProblemTestCreate(BaseModel):
    input: str
    expected_output: str
    is_sample: bool = False


class SyncResult(BaseModel):
    synced: int
