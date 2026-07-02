"""Эндпоинты задач: список/фильтр, деталь, авторские задачи и тесты."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.problem import Problem, ProblemSource, ProblemTag, ProblemTest
from app.models.submission import StudentSolvedProblem
from app.models.user import User, UserRole
from app.schemas.auth import MessageResponse
from app.schemas.problem import (
    AuthoredProblemCreate,
    ProblemDetail,
    ProblemOut,
    ProblemTestCreate,
    SampleTest,
)

router = APIRouter(tags=["problems"])


def _solved_ids(db: Session, student_id: int, problem_ids: list[int]) -> set[int]:
    if not problem_ids:
        return set()
    return set(
        db.scalars(
            select(StudentSolvedProblem.problem_id).where(
                StudentSolvedProblem.student_id == student_id,
                StudentSolvedProblem.problem_id.in_(problem_ids),
            )
        )
    )


def _to_out(problem: Problem, solved: bool) -> ProblemOut:
    return ProblemOut(
        id=problem.id,
        source=problem.source,
        title=problem.title,
        rating=problem.rating,
        url=problem.url,
        cf_contest_id=problem.cf_contest_id,
        cf_index=problem.cf_index,
        tags=[t.tag for t in problem.tags],
        solved=solved,
    )


@router.get("/problems", response_model=list[ProblemOut])
def list_problems(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    tags: str | None = Query(None, description="теги через запятую (AND)"),
    min_rating: int | None = None,
    max_rating: int | None = None,
    solved: bool | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
) -> list[ProblemOut]:
    stmt = select(Problem)
    if min_rating is not None:
        stmt = stmt.where(Problem.rating >= min_rating)
    if max_rating is not None:
        stmt = stmt.where(Problem.rating <= max_rating)
    if tags:
        for tag in [t.strip() for t in tags.split(",") if t.strip()]:
            stmt = stmt.where(Problem.tags.any(ProblemTag.tag == tag))

    if solved is not None and user.role == UserRole.student:
        subq = select(StudentSolvedProblem.problem_id).where(
            StudentSolvedProblem.student_id == user.id
        )
        stmt = stmt.where(Problem.id.in_(subq) if solved else Problem.id.notin_(subq))

    stmt = stmt.order_by(Problem.rating.is_(None), Problem.rating, Problem.id).limit(limit).offset(offset)
    problems = list(db.scalars(stmt))

    solved_set = (
        _solved_ids(db, user.id, [p.id for p in problems])
        if user.role == UserRole.student
        else set()
    )
    return [_to_out(p, p.id in solved_set) for p in problems]


@router.get("/problems/{problem_id}", response_model=ProblemDetail)
def get_problem(
    problem_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProblemDetail:
    problem = db.get(Problem, problem_id)
    if problem is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Задача не найдена")
    solved = bool(_solved_ids(db, user.id, [problem.id])) if user.role == UserRole.student else False
    samples = [
        SampleTest(input=t.input, expected_output=t.expected_output)
        for t in problem.tests
        if t.is_sample
    ]
    base = _to_out(problem, solved)
    return ProblemDetail(
        **base.model_dump(),
        statement_md=problem.statement_md,
        time_limit_ms=problem.time_limit_ms,
        memory_limit_mb=problem.memory_limit_mb,
        samples=samples,
    )


@router.post("/problems", response_model=ProblemOut, status_code=status.HTTP_201_CREATED)
def create_authored_problem(
    payload: AuthoredProblemCreate,
    teacher: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> ProblemOut:
    problem = Problem(
        source=ProblemSource.authored,
        title=payload.title,
        statement_md=payload.statement_md,
        rating=payload.rating,
        time_limit_ms=payload.time_limit_ms,
        memory_limit_mb=payload.memory_limit_mb,
        created_by=teacher.id,
    )
    for tag in payload.tags:
        problem.tags.append(ProblemTag(tag=tag))
    db.add(problem)
    db.commit()
    db.refresh(problem)
    return _to_out(problem, False)


@router.post("/problems/{problem_id}/tests", response_model=MessageResponse)
def add_problem_test(
    problem_id: int,
    payload: ProblemTestCreate,
    _: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> MessageResponse:
    problem = db.get(Problem, problem_id)
    if problem is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Задача не найдена")
    order = db.scalar(
        select(func.max(ProblemTest.order_index)).where(ProblemTest.problem_id == problem_id)
    )
    db.add(
        ProblemTest(
            problem_id=problem_id,
            input=payload.input,
            expected_output=payload.expected_output,
            is_sample=payload.is_sample,
            order_index=(order or 0) + 1,
        )
    )
    db.commit()
    return MessageResponse(message="Тест добавлен")
