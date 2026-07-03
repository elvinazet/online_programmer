"""Импорт всех моделей — чтобы Base.metadata был полным (для Alembic и тестов)."""
from app.models.content import Course, CourseLanguage, Lesson, Level, LevelName, Module
from app.models.exam import (
    AttemptEvent,
    AttemptEventType,
    AttemptProblem,
    AttemptQuestion,
    AttemptStatus,
    Exam,
    ExamAttempt,
    ExamPracticalProblem,
    ExamTheoryConfig,
    StudentLevelAccess,
)
from app.models.group import Group, GroupMember
from app.models.problem import Problem, ProblemSource, ProblemTag, ProblemTest
from app.models.quiz import (
    LessonProgress,
    LessonQuestion,
    ProgressStatus,
    Question,
    QuestionType,
)
from app.models.submission import (
    CfSyncState,
    SolvedSource,
    StudentSolvedProblem,
    Submission,
    SubmissionLanguage,
    SubmissionStatus,
)
from app.models.token import (
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
)
from app.models.user import StudentProfile, TeacherProfile, User, UserRole

__all__ = [
    "User",
    "UserRole",
    "StudentProfile",
    "TeacherProfile",
    "RefreshToken",
    "EmailVerificationToken",
    "PasswordResetToken",
    "Group",
    "GroupMember",
    "Course",
    "CourseLanguage",
    "Level",
    "LevelName",
    "Module",
    "Lesson",
    "Question",
    "QuestionType",
    "LessonQuestion",
    "LessonProgress",
    "ProgressStatus",
    "Problem",
    "ProblemSource",
    "ProblemTag",
    "ProblemTest",
    "Submission",
    "SubmissionLanguage",
    "SubmissionStatus",
    "StudentSolvedProblem",
    "SolvedSource",
    "CfSyncState",
    "Exam",
    "ExamPracticalProblem",
    "ExamTheoryConfig",
    "ExamAttempt",
    "AttemptStatus",
    "AttemptProblem",
    "AttemptQuestion",
    "AttemptEvent",
    "AttemptEventType",
    "StudentLevelAccess",
]
