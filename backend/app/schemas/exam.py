"""Схемы экзаменов."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.exam import AttemptEventType, AttemptStatus
from app.models.quiz import QuestionType


# --- Конструктор (учитель) ---
class ExamCreate(BaseModel):
    title: str
    target_level_id: int | None = None
    level_from_id: int | None = None
    duration_seconds: int = 7200
    pass_threshold: float = 0.7
    retake_delay_days: int = 3
    practical_weight: float = 0.5
    theory_weight: float = 0.5


class ExamUpdate(BaseModel):
    title: str | None = None
    is_published: bool | None = None
    duration_seconds: int | None = None
    pass_threshold: float | None = None
    retake_delay_days: int | None = None
    practical_weight: float | None = None
    theory_weight: float | None = None
    target_level_id: int | None = None


class ExamPracticalAdd(BaseModel):
    problem_id: int
    max_score: int = 100


class ExamTheoryAdd(BaseModel):
    module_id: int
    num_questions: int = 5


class ExamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    target_level_id: int | None = None
    level_from_id: int | None = None
    duration_seconds: int
    pass_threshold: float
    retake_delay_days: int
    practical_weight: float
    theory_weight: float
    is_published: bool


# --- Прохождение (ученик) ---
class AttemptQuestionView(BaseModel):
    id: int  # id записи attempt_questions
    question_id: int
    type: QuestionType
    prompt_md: str
    options: list[str] | None = None  # уже в порядке показа
    student_answer: Any = None
    order_index: int


class AttemptProblemView(BaseModel):
    id: int
    problem_id: int
    title: str
    order_index: int
    max_score: int
    best_score: int


class AttemptResult(BaseModel):
    total_score: int
    practical_score: int
    theory_score: int
    passed: bool
    next_retake_allowed_at: datetime | None = None


class AttemptDetail(BaseModel):
    id: int
    exam_id: int
    attempt_number: int
    status: AttemptStatus
    started_at: datetime
    ends_at: datetime
    remaining_seconds: int
    questions: list[AttemptQuestionView]
    problems: list[AttemptProblemView]
    result: AttemptResult | None = None


class SaveAnswersRequest(BaseModel):
    answers: list["SavedAnswer"]


class SavedAnswer(BaseModel):
    attempt_question_id: int
    answer: Any


class EventRequest(BaseModel):
    type: AttemptEventType


# --- Обзор результатов (учитель) ---
class AttemptSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    attempt_number: int
    status: AttemptStatus
    total_score: int
    practical_score: int
    theory_score: int
    passed: bool


SaveAnswersRequest.model_rebuild()
