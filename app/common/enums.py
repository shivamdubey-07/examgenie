from enum import Enum


class UserRole(str, Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"


class ExamStatus(str, Enum):
    draft = "draft"
    published = "published"


class AttemptStatus(str, Enum):
    in_progress = "in_progress"
    submitted = "submitted"
    expired = "expired"


class DifficultyLevel(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"
