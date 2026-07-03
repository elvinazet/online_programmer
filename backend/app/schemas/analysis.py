"""Схемы разбора результатов экзамена и планов подготовки."""
from datetime import datetime

from pydantic import BaseModel

from app.models.exam import AttemptStatus


class LessonRef(BaseModel):
    id: int
    title: str


class TopicResult(BaseModel):
    module_id: int
    module_title: str
    correct: int
    total: int
    score: int
    is_weak: bool
    lessons: list[LessonRef] = []  # уроки к повторению (для слабых тем)


class PracticeRec(BaseModel):
    problem_id: int
    title: str
    rating: int | None = None
    url: str | None = None
    tags: list[str] = []


class AnalysisSummary(BaseModel):
    total_score: int
    practical_score: int
    theory_score: int
    passed: bool


class AttemptAnalysis(BaseModel):
    attempt_id: int
    summary: AnalysisSummary
    topics: list[TopicResult]
    practice: list[PracticeRec]


class ExamHistoryItem(BaseModel):
    attempt_id: int
    exam_id: int
    exam_title: str
    attempt_number: int
    status: AttemptStatus
    total_score: int
    practical_score: int
    theory_score: int
    passed: bool
    submitted_at: datetime | None = None


class ExamTopicAggregate(BaseModel):
    module_id: int
    module_title: str
    score: int
    total_answers: int
    is_weak: bool
