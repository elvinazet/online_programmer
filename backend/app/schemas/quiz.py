"""Схемы вопросов, мини-квиза и прогресса."""
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.quiz import ProgressStatus, QuestionType


class QuestionCreate(BaseModel):
    type: QuestionType
    prompt_md: str
    options: list[str] | None = None
    # эталон: {"correct": 1} | {"correct": [0,2]} | {"accepted": ["42"]}
    correct_answer: dict
    explanation_md: str | None = None
    difficulty: int | None = None


class QuestionOut(BaseModel):
    """Полный вид вопроса (для учителя) — с ответами."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    module_id: int
    type: QuestionType
    prompt_md: str
    options: list[str] | None = None
    correct_answer: dict
    explanation_md: str | None = None
    difficulty: int | None = None


class QuestionPublicOut(BaseModel):
    """Вид вопроса для ученика — без правильного ответа."""

    id: int
    type: QuestionType
    prompt_md: str
    options: list[str] | None = None


class AttachQuestionRequest(BaseModel):
    question_id: int
    order_index: int | None = None


class ProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: ProgressStatus
    quiz_score: int | None = None


class LessonDetailOut(BaseModel):
    id: int
    module_id: int
    title: str
    content_md: str
    questions: list[QuestionPublicOut]
    progress: ProgressOut | None = None


class QuizAnswer(BaseModel):
    question_id: int
    answer: Any


class QuizSubmitRequest(BaseModel):
    answers: list[QuizAnswer]


class QuizResultItem(BaseModel):
    question_id: int
    is_correct: bool
    correct_answer: dict
    explanation_md: str | None = None


class QuizResultOut(BaseModel):
    score: int
    passed: bool
    status: ProgressStatus
    results: list[QuizResultItem]
