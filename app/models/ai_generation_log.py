import uuid

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.db import Base


class AIGenerationLog(Base):
    __tablename__ = "ai_generation_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    model_used = Column(String, nullable=False)
    prompt = Column(String, nullable=False)
    tokens_used = Column(Integer, nullable=True)
    generation_time = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    exam = relationship("Exam", back_populates="ai_logs")
