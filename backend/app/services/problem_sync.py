"""Синхронизация кэша задач Codeforces (problemset.problems)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.problem import Problem, ProblemSource, ProblemTag


def _cf_url(contest_id: int, index: str) -> str:
    return f"https://codeforces.com/problemset/problem/{contest_id}/{index}"


def sync_problemset(db: Session, client, limit: int | None = None) -> int:
    """Тянет problemset и upsert-ит задачи с тегами. Возвращает число задач."""
    result = client.problemset_problems()
    problems = result.get("problems", [])
    if limit is not None:
        problems = problems[:limit]

    count = 0
    for item in problems:
        contest_id = item.get("contestId")
        index = item.get("index")
        if contest_id is None or index is None:
            continue

        problem = db.scalar(
            select(Problem).where(
                Problem.cf_contest_id == contest_id, Problem.cf_index == index
            )
        )
        if problem is None:
            problem = Problem(
                source=ProblemSource.codeforces,
                cf_contest_id=contest_id,
                cf_index=index,
                title=item.get("name", ""),
            )
            db.add(problem)
            db.flush()

        problem.title = item.get("name", problem.title)
        problem.rating = item.get("rating")
        problem.url = _cf_url(contest_id, index)

        problem.tags.clear()
        db.flush()
        for tag in item.get("tags", []):
            problem.tags.append(ProblemTag(tag=tag))
        count += 1

    db.commit()
    return count
