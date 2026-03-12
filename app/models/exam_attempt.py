import uuid

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.db import Base
from app.common.enums import AttemptStatus


class ExamAttempt(Base):
    __tablename__ = "exam_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    submit_time = Column(DateTime(timezone=True), nullable=True)
    score = Column(Integer, default=0, nullable=False)
    status = Column(Enum(AttemptStatus, name="attempt_status"), default=AttemptStatus.in_progress, nullable=False)

    exam = relationship("Exam", back_populates="attempts")
    user = relationship("User", backref="attempts")
    answers = relationship("AttemptAnswer", back_populates="attempt", cascade="all, delete-orphan")
