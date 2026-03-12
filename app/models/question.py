import uuid

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.db import Base
from app.common.enums import DifficultyLevel


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_text = Column(String, nullable=False)
    difficulty = Column(Enum(DifficultyLevel, name="difficulty_level"), nullable=False)
    subject = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    ai_generated = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    creator = relationship("User", backref="questions")
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")
    explanations = relationship("QuestionExplanation", back_populates="question", cascade="all, delete-orphan")
    exam_links = relationship("ExamQuestion", back_populates="question", cascade="all, delete-orphan")
    statistics = relationship("QuestionStatistic", back_populates="question", uselist=False, cascade="all, delete-orphan")
