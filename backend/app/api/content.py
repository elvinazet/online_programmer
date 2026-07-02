"""Эндпоинты структуры учебника: курсы, уровни, модули, уроки."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.content import Course, Lesson, Level, Module
from app.models.quiz import LessonProgress
from app.models.user import User, UserRole
from app.schemas.content import (
    CourseCreate,
    CourseOut,
    CourseTreeOut,
    CourseUpdate,
    LessonCreate,
    LessonNode,
    LessonOut,
    LessonUpdate,
    LevelCreate,
    LevelNode,
    LevelOut,
    ModuleCreate,
    ModuleNode,
    ModuleOut,
)

router = APIRouter(tags=["textbooks"])


def _next_order(db: Session, order_column, filter_column, value: int) -> int:
    current_max = db.scalar(select(func.max(order_column)).where(filter_column == value))
    return (current_max or 0) + 1


def _get_or_404(db: Session, model, obj_id: int, name: str):
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{name} не найден(а)")
    return obj


# --- Курсы ---
@router.get("/courses", response_model=list[CourseOut])
def list_courses(
    _: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Course]:
    return list(db.scalars(select(Course).order_by(Course.id)))


@router.post("/courses", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreate,
    _: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> Course:
    course = Course(title=payload.title, language=payload.language, description=payload.description)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.patch("/courses/{course_id}", response_model=CourseOut)
def update_course(
    course_id: int,
    payload: CourseUpdate,
    _: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> Course:
    course = _get_or_404(db, Course, course_id, "Курс")
    if payload.title is not None:
        course.title = payload.title
    if payload.description is not None:
        course.description = payload.description
    db.commit()
    db.refresh(course)
    return course


@router.get("/courses/{course_id}", response_model=CourseTreeOut)
def get_course_tree(
    course_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CourseTreeOut:
    course = _get_or_404(db, Course, course_id, "Курс")

    status_by_lesson: dict[int, object] = {}
    if user.role == UserRole.student:
        rows = db.execute(
            select(LessonProgress.lesson_id, LessonProgress.status).where(
                LessonProgress.student_id == user.id
            )
        ).all()
        status_by_lesson = {lesson_id: st for lesson_id, st in rows}

    levels = [
        LevelNode(
            id=level.id,
            name=level.name,
            order_index=level.order_index,
            modules=[
                ModuleNode(
                    id=module.id,
                    title=module.title,
                    order_index=module.order_index,
                    lessons=[
                        LessonNode(
                            id=lesson.id,
                            title=lesson.title,
                            order_index=lesson.order_index,
                            status=status_by_lesson.get(lesson.id),
                        )
                        for lesson in module.lessons
                    ],
                )
                for module in level.modules
            ],
        )
        for level in course.levels
    ]
    return CourseTreeOut(
        id=course.id,
        title=course.title,
        language=course.language,
        description=course.description,
        levels=levels,
    )


# --- Уровни / модули / уроки (создание — только учитель) ---
@router.post(
    "/courses/{course_id}/levels", response_model=LevelOut, status_code=status.HTTP_201_CREATED
)
def create_level(
    course_id: int,
    payload: LevelCreate,
    _: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> Level:
    _get_or_404(db, Course, course_id, "Курс")
    order = (
        payload.order_index
        if payload.order_index is not None
        else _next_order(db, Level.order_index, Level.course_id, course_id)
    )
    level = Level(course_id=course_id, name=payload.name, order_index=order)
    db.add(level)
    db.commit()
    db.refresh(level)
    return level


@router.post(
    "/levels/{level_id}/modules", response_model=ModuleOut, status_code=status.HTTP_201_CREATED
)
def create_module(
    level_id: int,
    payload: ModuleCreate,
    _: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> Module:
    _get_or_404(db, Level, level_id, "Уровень")
    order = (
        payload.order_index
        if payload.order_index is not None
        else _next_order(db, Module.order_index, Module.level_id, level_id)
    )
    module = Module(level_id=level_id, title=payload.title, order_index=order)
    db.add(module)
    db.commit()
    db.refresh(module)
    return module


@router.post(
    "/modules/{module_id}/lessons", response_model=LessonOut, status_code=status.HTTP_201_CREATED
)
def create_lesson(
    module_id: int,
    payload: LessonCreate,
    teacher: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> Lesson:
    _get_or_404(db, Module, module_id, "Модуль")
    order = (
        payload.order_index
        if payload.order_index is not None
        else _next_order(db, Lesson.order_index, Lesson.module_id, module_id)
    )
    lesson = Lesson(
        module_id=module_id,
        title=payload.title,
        content_md=payload.content_md,
        order_index=order,
        created_by=teacher.id,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


@router.patch("/lessons/{lesson_id}", response_model=LessonOut)
def update_lesson(
    lesson_id: int,
    payload: LessonUpdate,
    _: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> Lesson:
    lesson = _get_or_404(db, Lesson, lesson_id, "Урок")
    if payload.title is not None:
        lesson.title = payload.title
    if payload.content_md is not None:
        lesson.content_md = payload.content_md
    if payload.order_index is not None:
        lesson.order_index = payload.order_index
    db.commit()
    db.refresh(lesson)
    return lesson
