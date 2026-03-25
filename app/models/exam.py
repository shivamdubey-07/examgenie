import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.db import Base
from app.common.enums import ExamStatus, DifficultyLevel


class Exam(Base):
    __tablename__ = "exams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    difficulty = Column(Enum(DifficultyLevel, name="difficulty_level"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(Enum(ExamStatus, name="exam_status"), default=ExamStatus.draft, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    failure_reason = Column(Text, nullable=True)

    creator = relationship("User", backref="exams")
    exam_questions = relationship("ExamQuestion", back_populates="exam", cascade="all, delete-orphan")
    attempts = relationship("ExamAttempt", back_populates="exam", cascade="all, delete-orphan")
    sessions = relationship("ExamSession", back_populates="exam", cascade="all, delete-orphan")
    exports = relationship("ExamExport", back_populates="exam", cascade="all, delete-orphan")
    ai_logs = relationship("AIGenerationLog", back_populates="exam", cascade="all, delete-orphan")
