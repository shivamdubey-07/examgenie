import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.db import Base


class ExamExport(Base):
    __tablename__ = "exam_exports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    file_url = Column(String, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    exam = relationship("Exam", back_populates="exports")
