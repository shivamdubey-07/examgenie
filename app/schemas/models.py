from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.common.enums import AttemptStatus, DifficultyLevel, ExamStatus, UserRole

class UserCreate(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    username: str
    password: str
    role: UserRole = UserRole.student


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: Optional[str] = None
    email: str
    username: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ExamCreate(BaseModel):
    title: str
    subject: str
    topic: str
    difficulty: DifficultyLevel
    created_by: UUID
    status: ExamStatus = ExamStatus.draft


class ExamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    subject: str
    topic: str
    difficulty: DifficultyLevel
    created_by: UUID
    status: ExamStatus
    created_at: Optional[datetime] = None


class QuestionOptionCreate(BaseModel):
    option_text: str
    is_correct: bool = False


class QuestionOptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    option_text: str
    is_correct: bool


class QuestionExplanationCreate(BaseModel):
    explanation_text: str


class QuestionExplanationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    explanation_text: str


class QuestionCreate(BaseModel):
    question_text: str
    difficulty: DifficultyLevel
    subject: str
    topic: str
    created_by: Optional[UUID] = None
    ai_generated: bool = False
    options: List[QuestionOptionCreate] = []
    explanations: List[QuestionExplanationCreate] = []


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question_text: str
    difficulty: DifficultyLevel
    subject: str
    topic: str
    created_by: Optional[UUID] = None
    ai_generated: bool
    created_at: Optional[datetime] = None
    options: List[QuestionOptionRead] = []
    explanations: List[QuestionExplanationRead] = []


class ExamQuestionCreate(BaseModel):
    exam_id: UUID
    question_id: UUID
    question_order: int
    marks: int = 1


class ExamQuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    exam_id: UUID
    question_id: UUID
    question_order: int
    marks: int


class AIGenerationLogCreate(BaseModel):
    exam_id: UUID
    model_used: str
    prompt: str
    tokens_used: Optional[int] = None
    generation_time: Optional[float] = None


class AIGenerationLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    exam_id: UUID
    model_used: str
    prompt: str
    tokens_used: Optional[int] = None
    generation_time: Optional[float] = None
    created_at: Optional[datetime] = None


class ExamAttemptCreate(BaseModel):
    exam_id: UUID
    user_id: UUID


class ExamAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    exam_id: UUID
    user_id: UUID
    start_time: Optional[datetime] = None
    submit_time: Optional[datetime] = None
    score: int
    status: AttemptStatus


class AttemptAnswerCreate(BaseModel):
    attempt_id: UUID
    question_id: UUID
    selected_option_id: Optional[UUID] = None


class AttemptAnswerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    attempt_id: UUID
    question_id: UUID
    selected_option_id: Optional[UUID] = None
    answered_at: Optional[datetime] = None


class ExamSessionCreate(BaseModel):
    exam_id: UUID
    user_id: UUID
    session_token: str
    expires_at: datetime


class ExamSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    exam_id: UUID
    user_id: UUID
    session_token: str
    expires_at: datetime
    created_at: Optional[datetime] = None


class ExamExportCreate(BaseModel):
    exam_id: UUID
    file_url: str


class ExamExportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    exam_id: UUID
    file_url: str
    generated_at: Optional[datetime] = None


class QuestionStatisticCreate(BaseModel):
    question_id: UUID
    times_attempted: int = 0
    times_correct: int = 0
    times_wrong: int = 0


class QuestionStatisticRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question_id: UUID
    times_attempted: int
    times_correct: int
    times_wrong: int


class UserActivityLogCreate(BaseModel):
    user_id: UUID
    action: str
    log_metadata: Optional[Dict[str, Any]] = None


class UserActivityLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    action: str
    log_metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
