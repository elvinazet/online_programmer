"""Модели учебного контента: курс → уровень → модуль → урок."""
import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BigInt, Base, TimestampMixin


class CourseLanguage(str, enum.Enum):
    cpp = "cpp"
    python = "python"


class LevelName(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class Course(Base, TimestampMixin):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[CourseLanguage] = mapped_column(
        Enum(CourseLanguage, name="course_language"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text)

    levels: Mapped[list["Level"]] = relationship(
        back_populates="course",
        order_by="Level.order_index",
        cascade="all, delete-orphan",
    )


class Level(Base, TimestampMixin):
    __tablename__ = "levels"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[LevelName] = mapped_column(Enum(LevelName, name="level_name"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    course: Mapped["Course"] = relationship(back_populates="levels")
    modules: Mapped[list["Module"]] = relationship(
        back_populates="level",
        order_by="Module.order_index",
        cascade="all, delete-orphan",
    )


class Module(Base, TimestampMixin):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    level_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("levels.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    level: Mapped["Level"] = relationship(back_populates="modules")
    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="module",
        order_by="Lesson.order_index",
        cascade="all, delete-orphan",
    )


class Lesson(Base, TimestampMixin):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    module_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("modules.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_md: Mapped[str] = mapped_column(Text, default="", nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by: Mapped[int | None] = mapped_column(
        BigInt, ForeignKey("users.id", ondelete="SET NULL")
    )

    module: Mapped["Module"] = relationship(back_populates="lessons")
