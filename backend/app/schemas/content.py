"""Схемы учебного контента и дерева курса."""
from pydantic import BaseModel, ConfigDict

from app.models.content import CourseLanguage, LevelName
from app.models.quiz import ProgressStatus


# --- Создание / обновление ---
class CourseCreate(BaseModel):
    title: str
    language: CourseLanguage
    description: str | None = None


class CourseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class LevelCreate(BaseModel):
    name: LevelName
    order_index: int | None = None


class ModuleCreate(BaseModel):
    title: str
    order_index: int | None = None


class LessonCreate(BaseModel):
    title: str
    content_md: str = ""
    order_index: int | None = None


class LessonUpdate(BaseModel):
    title: str | None = None
    content_md: str | None = None
    order_index: int | None = None


# --- Ответы ---
class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    language: CourseLanguage
    description: str | None = None


class LevelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    name: LevelName
    order_index: int


class ModuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    level_id: int
    title: str
    order_index: int


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    module_id: int
    title: str
    content_md: str
    order_index: int


# --- Дерево курса (с прогрессом ученика) ---
class LessonNode(BaseModel):
    id: int
    title: str
    order_index: int
    status: ProgressStatus | None = None


class ModuleNode(BaseModel):
    id: int
    title: str
    order_index: int
    lessons: list[LessonNode]


class LevelNode(BaseModel):
    id: int
    name: LevelName
    order_index: int
    modules: list[ModuleNode]


class CourseTreeOut(BaseModel):
    id: int
    title: str
    language: CourseLanguage
    description: str | None = None
    levels: list[LevelNode]
