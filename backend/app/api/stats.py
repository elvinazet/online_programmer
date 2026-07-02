"""Дашборд прогресса ученика: решено всего, по рейтингу и тегам."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.models.problem import Problem, ProblemTag
from app.models.submission import StudentSolvedProblem
from app.models.user import User, UserRole
from app.schemas.stats import StatsOut

router = APIRouter(tags=["stats"])


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

    return StatsOut(solved_total=solved_total or 0, by_rating=by_rating, by_tag=by_tag)
