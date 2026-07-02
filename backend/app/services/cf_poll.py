"""Опрос user.status и автопометка решённых на CF задач как решённых у нас."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.problem import Problem
from app.models.submission import CfSyncState, SolvedSource, StudentSolvedProblem


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def sync_user_solved(db: Session, client, student_id: int, handle: str) -> int:
    """Помечает задачи, сданные на CF (verdict OK), как решённые. Возвращает,
    сколько новых задач засчитано."""
    submissions = client.user_status(handle)
    solved_keys: set[tuple[int, str]] = set()
    for sub in submissions:
        if sub.get("verdict") != "OK":
            continue
        problem = sub.get("problem", {})
        contest_id, index = problem.get("contestId"), problem.get("index")
        if contest_id is not None and index is not None:
            solved_keys.add((contest_id, index))

    newly = 0
    for contest_id, index in solved_keys:
        problem = db.scalar(
            select(Problem).where(
                Problem.cf_contest_id == contest_id, Problem.cf_index == index
            )
        )
        if problem is None:
            continue  # задачи нет в нашем кэше — пропускаем
        exists = db.scalar(
            select(StudentSolvedProblem).where(
                StudentSolvedProblem.student_id == student_id,
                StudentSolvedProblem.problem_id == problem.id,
            )
        )
        if exists is None:
            db.add(
                StudentSolvedProblem(
                    student_id=student_id,
                    problem_id=problem.id,
                    source=SolvedSource.cf_poll,
                    solved_at=_utcnow(),
                )
            )
            newly += 1

    state = db.get(CfSyncState, student_id)
    if state is None:
        state = CfSyncState(student_id=student_id)
        db.add(state)
    state.last_synced_at = _utcnow()

    db.commit()
    return newly
