"""Эндпоинты Codeforces: привязка хэндла, опрос статуса, синхронизация задач."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.problem import SyncResult
from app.schemas.auth import MessageResponse
from app.schemas.stats import CfLinkRequest, CfSyncResult
from app.services.cf_poll import sync_user_solved
from app.services.codeforces import CodeforcesClient
from app.services.problem_sync import sync_problemset
from app.services.rate_limit import get_default_limiter

router = APIRouter(prefix="/codeforces", tags=["codeforces"])


@router.post("/link", response_model=MessageResponse)
def link_handle(
    payload: CfLinkRequest,
    student: User = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
) -> MessageResponse:
    student.student_profile.codeforces_handle = payload.handle.strip()
    db.commit()
    return MessageResponse(message="Codeforces-хэндл привязан")


@router.post("/sync", response_model=CfSyncResult)
def sync_my_solved(
    student: User = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
) -> CfSyncResult:
    handle = student.student_profile.codeforces_handle
    if not handle:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Сначала привяжите Codeforces-хэндл")
    client = CodeforcesClient(limiter=get_default_limiter())
    newly = sync_user_solved(db, client, student.id, handle)
    return CfSyncResult(newly_solved=newly)


@router.post("/sync-problems", response_model=SyncResult)
def sync_problems(
    limit: int | None = None,
    _: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> SyncResult:
    client = CodeforcesClient(limiter=get_default_limiter())
    count = sync_problemset(db, client, limit=limit)
    return SyncResult(synced=count)
