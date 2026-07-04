"""Дашборд прогресса ученика: решено, streak, график по времени, темы, уровни."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.models.content import Course, Level
from app.models.exam import StudentLevelAccess
from app.models.problem import Problem, ProblemTag
from app.models.submission import StudentSolvedProblem
from app.models.user import User, UserRole
from app.schemas.stats import StatsOut, TimelinePoint

router = APIRouter(tags=["stats"])


class LevelAccessOut(BaseModel):
    level_id: int
    level_name: str
    course_title: str
    unlocked: bool
    exam_passed: bool


@router.get("/me/stats", response_model=StatsOut)
def my_stats(
    student: User = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
) -> StatsOut:
    solved_total = db.scalar(
        select(func.count())
        .select_from(StudentSolvedProblem)
        .where(StudentSolvedProblem.student_id == student.id)
    )

    rating_rows = db.execute(
        select(Problem.rating, func.count())
        .join(StudentSolvedProblem, StudentSolvedProblem.problem_id == Problem.id)
        .where(StudentSolvedProblem.student_id == student.id)
        .group_by(Problem.rating)
    ).all()
    by_rating = {str(rating if rating is not None else "unrated"): count for rating, count in rating_rows}

    tag_rows = db.execute(
        select(ProblemTag.tag, func.count())
        .join(StudentSolvedProblem, StudentSolvedProblem.problem_id == ProblemTag.problem_id)
        .where(StudentSolvedProblem.student_id == student.id)
        .group_by(ProblemTag.tag)
    ).all()
    by_tag = {tag: count for tag, count in tag_rows}

    streak = student.student_profile.streak_count if student.student_profile else 0

    return StatsOut(solved_total=solved_total or 0, streak=streak, by_rating=by_rating, by_tag=by_tag)


@router.get("/me/solved-timeline", response_model=list[TimelinePoint])
def solved_timeline(
    student: User = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
) -> list[TimelinePoint]:
    day = func.date(StudentSolvedProblem.solved_at)
    rows = db.execute(
        select(day, func.count())
        .where(StudentSolvedProblem.student_id == student.id)
        .group_by(day)
        .order_by(day)
    ).all()
    return [TimelinePoint(date=str(d), count=c) for d, c in rows]


@router.get("/me/level-access", response_model=list[LevelAccessOut])
def my_level_access(
    student: User = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
) -> list[LevelAccessOut]:
    rows = db.execute(
        select(
            StudentLevelAccess.level_id,
            StudentLevelAccess.unlocked,
            StudentLevelAccess.exam_passed,
            Level.name,
            Course.title,
        )
        .join(Level, Level.id == StudentLevelAccess.level_id)
        .join(Course, Course.id == Level.course_id)
        .where(StudentLevelAccess.student_id == student.id)
    ).all()
    return [
        LevelAccessOut(
            level_id=level_id, unlocked=unlocked, exam_passed=exam_passed,
            level_name=name.value if hasattr(name, "value") else str(name),
            course_title=course_title,
        )
        for level_id, unlocked, exam_passed, name, course_title in rows
    ]
