"""Эндпоинты заданий: учитель назначает задачи/главы, ученик видит свои."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.assignment import Assignment, AssignmentType
from app.models.content import Lesson
from app.models.group import Group, GroupMember
from app.models.problem import Problem
from app.models.quiz import LessonProgress, ProgressStatus
from app.models.submission import StudentSolvedProblem
from app.models.user import User, UserRole
from app.schemas.assignment import AssignmentCreate, AssignmentOut
from app.schemas.auth import MessageResponse

router = APIRouter(tags=["assignments"])


def _teacher_can_target(db: Session, teacher_id: int, student_id: int) -> bool:
    """Ученик доступен учителю, если состоит в его группе."""
    row = db.scalar(
        select(GroupMember.id)
        .join(Group, Group.id == GroupMember.group_id)
        .where(Group.teacher_id == teacher_id, GroupMember.student_id == student_id)
    )
    return row is not None


@router.post("/assignments", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(
    payload: AssignmentCreate,
    teacher: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> MessageResponse:
    # проверка ссылки на объект
    if payload.type == AssignmentType.problem and db.get(Problem, payload.problem_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Задача не найдена")
    if payload.type == AssignmentType.lesson and db.get(Lesson, payload.lesson_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Урок не найден")

    # список получателей
    if payload.group_id is not None:
        group = db.get(Group, payload.group_id)
        if group is None or group.teacher_id != teacher.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Группа не найдена")
        student_ids = list(
            db.scalars(select(GroupMember.student_id).where(GroupMember.group_id == group.id))
        )
    else:
        if not _teacher_can_target(db, teacher.id, payload.student_id):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Ученик не в вашей группе")
        student_ids = [payload.student_id]

    for sid in student_ids:
        db.add(
            Assignment(
                teacher_id=teacher.id,
                student_id=sid,
                type=payload.type,
                problem_id=payload.problem_id,
                lesson_id=payload.lesson_id,
                note=payload.note,
                due_date=payload.due_date,
            )
        )
    db.commit()
    return MessageResponse(message=f"Назначено ученикам: {len(student_ids)}")


@router.get("/me/assignments", response_model=list[AssignmentOut])
def my_assignments(
    student: User = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
) -> list[AssignmentOut]:
    assignments = db.scalars(
        select(Assignment).where(Assignment.student_id == student.id).order_by(Assignment.id.desc())
    ).all()

    result = []
    for a in assignments:
        if a.type == AssignmentType.problem:
            problem = db.get(Problem, a.problem_id)
            title = problem.title if problem else "(задача удалена)"
            done = db.scalar(
                select(StudentSolvedProblem.id).where(
                    StudentSolvedProblem.student_id == student.id,
                    StudentSolvedProblem.problem_id == a.problem_id,
                )
            ) is not None
        else:
            lesson = db.get(Lesson, a.lesson_id)
            title = lesson.title if lesson else "(урок удалён)"
            done = db.scalar(
                select(LessonProgress.id).where(
                    LessonProgress.student_id == student.id,
                    LessonProgress.lesson_id == a.lesson_id,
                    LessonProgress.status == ProgressStatus.completed,
                )
            ) is not None
        result.append(
            AssignmentOut(
                id=a.id, type=a.type, title=title, problem_id=a.problem_id,
                lesson_id=a.lesson_id, note=a.note, due_date=a.due_date, done=done,
            )
        )
    return result


@router.delete("/assignments/{assignment_id}", response_model=MessageResponse)
def delete_assignment(
    assignment_id: int,
    teacher: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> MessageResponse:
    assignment = db.get(Assignment, assignment_id)
    if assignment is None or assignment.teacher_id != teacher.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Задание не найдено")
    db.delete(assignment)
    db.commit()
    return MessageResponse(message="Задание удалено")
