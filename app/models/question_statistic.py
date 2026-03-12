import uuid

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.db import Base


class QuestionStatistic(Base):
    __tablename__ = "question_statistics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), unique=True, nullable=False)
    times_attempted = Column(Integer, default=0, nullable=False)
    times_correct = Column(Integer, default=0, nullable=False)
    times_wrong = Column(Integer, default=0, nullable=False)

    question = relationship("Question", back_populates="statistics")
