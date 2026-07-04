"""Наполнение демо-данными. Запуск: python -m app.seed

Идемпотентно: если демо-учитель уже есть, ничего не делает.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.content import Course, CourseLanguage, Lesson, Level, LevelName, Module
from app.models.exam import Exam, ExamPracticalProblem, ExamTheoryConfig
from app.models.problem import Problem, ProblemSource, ProblemTag, ProblemTest
from app.models.quiz import LessonQuestion, Question, QuestionType
from app.models.user import StudentProfile, TeacherProfile, User, UserRole

# .local — зарезервированный домен, его отклоняет email-валидатор, поэтому example.com
TEACHER_EMAIL = "teacher@example.com"
STUDENT_EMAIL = "student@example.com"
DEMO_PASSWORD = "password123"


def seed(db: Session) -> bool:
    """Возвращает True, если данные созданы; False — если уже были."""
    if db.scalar(select(User).where(User.email == TEACHER_EMAIL)) is not None:
        return False

    teacher = User(
        email=TEACHER_EMAIL, password_hash=hash_password(DEMO_PASSWORD),
        role=UserRole.teacher, email_verified=True,
    )
    student = User(
        email=STUDENT_EMAIL, password_hash=hash_password(DEMO_PASSWORD),
        role=UserRole.student, email_verified=True,
    )
    db.add_all([teacher, student])
    db.flush()
    db.add(TeacherProfile(user_id=teacher.id, display_name="Демо-учитель"))
    db.add(StudentProfile(user_id=student.id, codeforces_handle="tourist"))

    # Курс Python → Beginner → Основы → урок + квиз
    course = Course(title="Python с нуля", language=CourseLanguage.python,
                    description="Демо-курс")
    db.add(course)
    db.flush()
    level = Level(course_id=course.id, name=LevelName.beginner, order_index=1)
    db.add(level)
    db.flush()
    module = Module(level_id=level.id, title="Основы", order_index=1)
    db.add(module)
    db.flush()
    lesson = Lesson(
        module_id=module.id, title="Переменные и ввод",
        content_md="# Переменные\n\n```python\na, b = map(int, input().split())\nprint(a + b)\n```",
        order_index=1, created_by=teacher.id,
    )
    db.add(lesson)
    db.flush()

    questions = [
        Question(module_id=module.id, type=QuestionType.single_choice,
                 prompt_md="Что выведет `print(2 + 2)`?", options=["2", "4", "22"],
                 correct_answer={"correct": 1}, explanation_md="Это сложение чисел."),
        Question(module_id=module.id, type=QuestionType.short_answer,
                 prompt_md="Какой тип у `input()`?", correct_answer={"accepted": ["str", "строка"]}),
    ]
    db.add_all(questions)
    db.flush()
    for i, q in enumerate(questions):
        db.add(LessonQuestion(lesson_id=lesson.id, question_id=q.id, order_index=i))

    # Задача A+B + тесты
    problem = Problem(source=ProblemSource.authored, title="A + B",
                      statement_md="Даны два числа. Выведите их сумму.",
                      rating=800, created_by=teacher.id)
    problem.tags.append(ProblemTag(tag="math"))
    problem.tags.append(ProblemTag(tag="implementation"))
    db.add(problem)
    db.flush()
    for inp, out in [("2 3\n", "5\n"), ("10 20\n", "30\n"), ("-1 1\n", "0\n")]:
        db.add(ProblemTest(problem_id=problem.id, input=inp, expected_output=out, is_sample=True))

    # Экзамен (опубликован)
    exam = Exam(title="Экзамен: Основы Python", created_by=teacher.id,
                duration_seconds=3600, pass_threshold=0.7, is_published=True)
    db.add(exam)
    db.flush()
    db.add(ExamPracticalProblem(exam_id=exam.id, problem_id=problem.id, order_index=1, max_score=100))
    db.add(ExamTheoryConfig(exam_id=exam.id, module_id=module.id, num_questions=2))

    db.commit()
    return True


def main() -> None:
    db = SessionLocal()
    try:
        created = seed(db)
        print("Демо-данные созданы." if created else "Демо-данные уже существуют.")
        if created:
            print(f"Учитель: {TEACHER_EMAIL} / {DEMO_PASSWORD}")
            print(f"Ученик:  {STUDENT_EMAIL} / {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
