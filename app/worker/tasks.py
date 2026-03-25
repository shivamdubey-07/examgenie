import logging
import time
from uuid import UUID
from typing import Optional

from sqlalchemy.orm import Session

from app.worker.celery_app import celery_app
from app.database.db import SessionLocal
from app.common.enums import ExamStatus
from app.models.exam import Exam
from app.services.exam.exam_service import ExamService
from app.services.ai.generator import generate_questions
from app.services.ai.prompts import build_question_prompt

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    time_limit=60,  # Hard timeout at 60 seconds
)
def generate_exam_task(
    self,
    exam_id: str,
    subject: str,
    topic: str,
    difficulty: str,
    num_questions: int,
) -> dict:
    """
    Background task to generate exam questions using AI.
    
    :param exam_id: UUID of the exam to generate
    :param subject: Exam subject
    :param topic: Exam topic
    :param difficulty: Difficulty level
    :param num_questions: Number of questions to generate
    :return: Dict with status and result
    """
    db: Optional[Session] = None
    start_time = time.time()

    try:
        db = SessionLocal()
        exam_service = ExamService(db)

        # Convert exam_id string to UUID
        exam_uuid = UUID(exam_id)

        # Check if exam exists
        exam = db.query(Exam).filter(Exam.id == exam_uuid).first()
        if not exam:
            logger.error(f"Exam {exam_id} not found")
            return {
                "exam_id": exam_id,
                "status": "failed",
                "error": "Exam not found",
            }

        logger.info(f"Starting generation for exam {exam_id}")

        # Update status to generating
        exam_service.update_exam_status(exam_uuid, ExamStatus.generating)

        # Build prompt for AI
        prompt_text = build_question_prompt(subject, topic, difficulty, num_questions)

        # Call AI to generate questions
        logger.info(f"Calling AI to generate {num_questions} questions")
        questions_data = generate_questions(subject, topic, difficulty, num_questions)

        # Persist questions to database
        logger.info(f"Persisting {len(questions_data.get('questions', []))} questions to database")
        created_count = exam_service.persist_generated_questions(
            exam_id=exam_uuid,
            questions_data=questions_data,
            model_used="gpt-4o-mini",
            prompt_text=prompt_text,
            generation_time=time.time() - start_time,
        )

        # Update exam status to ready
        exam_service.update_exam_status(exam_uuid, ExamStatus.ready)

        logger.info(
            f"Successfully generated exam {exam_id} with {created_count} questions "
            f"in {time.time() - start_time:.2f}s"
        )

        return {
            "exam_id": exam_id,
            "status": "success",
            "question_count": created_count,
            "generation_time": time.time() - start_time,
        }

    except Exception as e:
        logger.error(f"Error generating exam {exam_id}: {str(e)}", exc_info=True)

        # Update exam status to failed
        if db:
            try:
                exam_service = ExamService(db)
                exam_service.update_exam_status(
                    UUID(exam_id),
                    ExamStatus.failed,
                    failure_reason=str(e),
                )
            except Exception as update_error:
                logger.error(f"Failed to update exam status: {update_error}")

        # Retry logic
        if self.request.retries < self.max_retries:
            logger.warning(
                f"Retrying exam generation {exam_id} "
                f"(attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=e, countdown=5)
        else:
            logger.error(f"Max retries exceeded for exam {exam_id}")
            return {
                "exam_id": exam_id,
                "status": "failed",
                "error": str(e),
                "retries_exhausted": True,
            }

    finally:
        if db:
            db.close()


@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=10,
    time_limit=120,
)
def generate_pdf_task(
    self,
    exam_id: str,
) -> dict:
    """
    Background task to generate and upload PDF for an exam.
    
    :param exam_id: UUID of the exam
    :return: Dict with status and result
    """
    # TODO: Implement PDF generation + upload to storage
    return {"exam_id": exam_id, "status": "queued"}
