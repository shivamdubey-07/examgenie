from enum import Enum


class UserRole(str, Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"


class ExamStatus(str, Enum):
    draft = "draft"
    generating = "generating"
    ready = "ready"
    published = "published"
    failed = "failed"


class AttemptStatus(str, Enum):
    in_progress = "in_progress"
    submitted = "submitted"
    abandoned = "abandoned"
    expired = "expired"


class DifficultyLevel(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"