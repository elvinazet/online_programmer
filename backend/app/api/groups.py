"""Эндпоинты групп (только для учителей)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.core.utils import normalize_email
from app.db.session import get_db
from app.models.group import Group, GroupMember
from app.models.user import User, UserRole
from app.schemas.auth import MessageResponse
from app.schemas.group import AddMemberRequest, GroupCreate, GroupMemberOut, GroupOut

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("", response_model=GroupOut, status_code=status.HTTP_201_CREATED)
def create_group(
    payload: GroupCreate,
    teacher: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> Group:
    group = Group(teacher_id=teacher.id, name=payload.name)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@router.get("", response_model=list[GroupOut])
def list_groups(
    teacher: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> list[Group]:
    return list(db.scalars(select(Group).where(Group.teacher_id == teacher.id)))


def _owned_group_or_404(db: Session, group_id: int, teacher: User) -> Group:
    group = db.get(Group, group_id)
    if group is None or group.teacher_id != teacher.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Группа не найдена")
    return group


@router.post("/{group_id}/members", response_model=MessageResponse)
def add_member(
    group_id: int,
    payload: AddMemberRequest,
    teacher: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> MessageResponse:
    _owned_group_or_404(db, group_id, teacher)

    student = db.scalar(
        select(User).where(User.email == normalize_email(payload.student_email))
    )
    if student is None or student.role != UserRole.student:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ученик не найден")

    exists = db.scalar(
        select(GroupMember).where(
            GroupMember.group_id == group_id, GroupMember.student_id == student.id
        )
    )
    if exists is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ученик уже в группе")

    db.add(GroupMember(group_id=group_id, student_id=student.id))
    db.commit()
    return MessageResponse(message="Ученик добавлен в группу")


@router.get("/{group_id}/members", response_model=list[GroupMemberOut])
def list_members(
    group_id: int,
    teacher: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> list[GroupMemberOut]:
    _owned_group_or_404(db, group_id, teacher)
    rows = db.execute(
        select(GroupMember.student_id, User.email)
        .join(User, User.id == GroupMember.student_id)
        .where(GroupMember.group_id == group_id)
    ).all()
    return [GroupMemberOut(student_id=sid, email=email) for sid, email in rows]
