import json
import time
import uuid
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.exam import Exam
from app.models.question import Question
from app.models.question_option import QuestionOption
from app.models.exam_question import ExamQuestion
from app.models.ai_generation_log import AIGenerationLog
from app.common.enums import ExamStatus, DifficultyLevel
from app.services.cache.redis_client import get_redis_client


class ExamService:
    def __init__(self, db: Session):
        self.db = db
        self.redis = get_redis_client()

    def create_exam(
        self,
        title: str,
        subject: str,
        topic: str,
        difficulty: DifficultyLevel,
        created_by: UUID,
    ) -> Exam:
        """Create a new exam with draft status."""
        exam = Exam(
            id=uuid.uuid4(),
            title=title,
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            created_by=created_by,
            status=ExamStatus.draft,
        )
        self.db.add(exam)
        self.db.commit()
        self.db.refresh(exam)
        return exam

    def update_exam_status(
        self,
        exam_id: UUID,
        status: ExamStatus,
        failure_reason: Optional[str] = None,
    ) -> Exam:
        """Update exam status and optionally set failure reason."""
        exam = self.db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            raise ValueError(f"Exam {exam_id} not found")

        exam.status = status
        if failure_reason:
            exam.failure_reason = failure_reason

        self.db.commit()
        self.db.refresh(exam)

        # Update Redis cache
        self._set_exam_status_cache(exam_id, status)

        return exam

    def get_exam_with_questions(self, exam_id: UUID) -> Optional[Dict[str, Any]]:
        """Get exam details with all questions and options."""
        exam = self.db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            return None

        return {
            "id": exam.id,
            "title": exam.title,
            "subject": exam.subject,
            "topic": exam.topic,
            "difficulty": exam.difficulty,
            "status": exam.status,
            "created_at": exam.created_at,
            "updated_at": exam.updated_at,
            "questions": [
                {
                    "id": eq.question.id,
                    "order": eq.question_order,
                    "text": eq.question.question_text,
                    "options": [
                        {
                            "id": opt.id,
                            "text": opt.option_text,
                            "is_correct": opt.is_correct,
                        }
                        for opt in eq.question.options
                    ],
                }
                for eq in exam.exam_questions
            ],
        }

    def persist_generated_questions(
        self,
        exam_id: UUID,
        questions_data: Dict[str, Any],
        model_used: str = "gpt-4o-mini",
        prompt_text: str = "",
        tokens_used: Optional[int] = None,
        generation_time: Optional[float] = None,
    ) -> int:
        """
        Persist AI-generated questions to database.
        
        :param exam_id: ID of the exam
        :param questions_data: Dict with 'questions' list
        :param model_used: AI model used
        :param prompt_text: Original prompt sent to AI
        :param tokens_used: Token count from API response
        :param generation_time: Time taken for generation in seconds
        :return: Number of questions created
        """
        if "questions" not in questions_data:
            raise ValueError("Invalid questions data format: missing 'questions' key")

        questions_list = questions_data["questions"]
        if not questions_list:
            raise ValueError("No questions in generated data")

        created_count = 0

        try:
            for idx, q_data in enumerate(questions_list):
                # Create Question record
                question = Question(
                    id=uuid.uuid4(),
                    question_text=q_data.get("question", ""),
                    difficulty=DifficultyLevel.medium,  # Set by the prompt, but could be extracted
                    subject=self.db.query(Exam).filter(Exam.id == exam_id).first().subject,
                    topic=self.db.query(Exam).filter(Exam.id == exam_id).first().topic,
                    ai_generated=True,
                )
                self.db.add(question)
                self.db.flush()  # Get the ID

                # Create QuestionOption records
                options = q_data.get("options", {})
                correct_answer = q_data.get("correct_answer", "A")

                for option_key, option_text in options.items():
                    is_correct = option_key == correct_answer
                    option = QuestionOption(
                        id=uuid.uuid4(),
                        question_id=question.id,
                        option_text=option_text,
                        is_correct=is_correct,
                    )
                    self.db.add(option)

                # Create ExamQuestion junction
                exam_question = ExamQuestion(
                    id=uuid.uuid4(),
                    exam_id=exam_id,
                    question_id=question.id,
                    question_order=idx + 1,
                    marks=1,
                )
                self.db.add(exam_question)

                created_count += 1

            # Log the generation
            ai_log = AIGenerationLog(
                id=uuid.uuid4(),
                exam_id=exam_id,
                model_used=model_used,
                prompt=prompt_text,
                tokens_used=tokens_used,
                generation_time=generation_time,
            )
            self.db.add(ai_log)

            # Commit all changes
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            raise

        return created_count

    def _set_exam_status_cache(self, exam_id: UUID, status: ExamStatus) -> None:
        """Cache exam status in Redis for fast lookups."""
        try:
            key = f"exam:{str(exam_id)}:status"
            self.redis.setex(
                key,
                24 * 3600,  # 24 hour TTL
                status.value,
            )
        except Exception:
            # Redis failure shouldn't block the operation
            pass

    def get_exam_status_from_cache(self, exam_id: UUID) -> Optional[str]:
        """Get cached exam status, returns None if not cached."""
        try:
            key = f"exam:{str(exam_id)}:status"
            status = self.redis.get(key)
            return status.decode() if status else None
        except Exception:
            return None
