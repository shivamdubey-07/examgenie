import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_user
from app.schemas.models import (
    ExamGenerateRequest,
    ExamGenerateResponse,
    ExamStatusResponse,
    ExamDetailResponse,
)
from app.services.exam.exam_service import ExamService
from app.services.exam.exam_session_service import ExamSessionService
from app.common.enums import ExamStatus
from app.models.exam import Exam
from app.worker.tasks import generate_exam_task

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/generate", response_model=ExamGenerateResponse, status_code=status.HTTP_202_ACCEPTED)
def generate_exam(
    payload: ExamGenerateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new exam and queue it for AI generation.
    
    Returns exam_id with status 'generating'. 
    Frontend should poll GET /status to check when generation completes.
    """
    try:
        # Validate input
        if payload.num_questions < 1 or payload.num_questions > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Number of questions must be between 1 and 50",
            )

        user_id = UUID(current_user["sub"])

        # Create exam record with draft status
        exam_service = ExamService(db)
        exam = exam_service.create_exam(
            title=payload.title,
            subject=payload.subject,
            topic=payload.topic,
            difficulty=payload.difficulty,
            created_by=user_id,
        )

        # Update status to generating
        exam_service.update_exam_status(exam.id, ExamStatus.generating)

        # Queue background task for AI generation
        logger.info(f"Queuing exam generation task for exam {exam.id}")
        generate_exam_task.delay(
            exam_id=str(exam.id),
            subject=payload.subject,
            topic=payload.topic,
            difficulty=payload.difficulty.value,
            num_questions=payload.num_questions,
        )

        return ExamGenerateResponse(
            exam_id=exam.id,
            status=ExamStatus.generating,
            message="Exam generation queued. Check status endpoint for updates.",
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error creating exam: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create exam. Please try again.",
        )


@router.get("/my-exams")
def get_my_exams(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = UUID(current_user["sub"])
    exams = db.query(Exam).filter(Exam.created_by == user_id).order_by(Exam.created_at.desc()).all()
    result = []
    for exam in exams:
        result.append({
            "id": exam.id,
            "name": exam.title,
            "subject": exam.subject,
            "topic": exam.topic,
            "difficulty": exam.difficulty.value.capitalize(),
            "status": exam.status.value,
            "created_at": exam.created_at,
            "attempted": len(exam.attempts) > 0,
            "score": exam.attempts[-1].score if exam.attempts else None,
            "questions": [{"id": str(eq.id)} for eq in exam.exam_questions],
        })
    return result


@router.get("/{exam_id}/status", response_model=ExamStatusResponse)
def get_exam_status(
    exam_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the current status of an exam.
    
    Returns status (draft, generating, ready, published, failed) and question count if ready.
    """
    try:
        exam = db.query(Exam).filter(Exam.id == exam_id).first()

        if not exam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Exam {exam_id} not found",
            )

        # Verify user owns the exam or is admin
        user_id = UUID(current_user["sub"])
        if exam.created_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this exam",
            )

        # Count questions
        question_count = len(exam.exam_questions) if exam.exam_questions else 0

        return ExamStatusResponse(
            exam_id=exam.id,
            status=exam.status,
            title=exam.title,
            question_count=question_count,
            failure_reason=exam.failure_reason,
            created_at=exam.created_at,
            updated_at=exam.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching exam status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch exam status",
        )


@router.get("/{exam_id}", response_model=ExamDetailResponse)
def get_exam_details(
    exam_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get full exam details including all questions and options.
    
    Only returns if exam status is 'ready' or 'published'.
    """
    try:
        exam = db.query(Exam).filter(Exam.id == exam_id).first()

        if not exam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Exam {exam_id} not found",
            )

        # Verify user owns the exam or is admin
        user_id = UUID(current_user["sub"])
        if exam.created_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this exam",
            )

        # Check if exam is ready
        if exam.status not in [ExamStatus.ready, ExamStatus.published]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Exam is still {exam.status.value}. Please wait for generation to complete.",
            )

        # Build response with questions
        questions_list = []
        for exam_question in exam.exam_questions:
            q = exam_question.question
            question_dict = {
                "id": q.id,
                "text": q.question_text,
                "options": [
                    {
                        "id": opt.id,
                        "text": opt.option_text,
                        "is_correct": opt.is_correct,
                    }
                    for opt in q.options
                ],
            }
            questions_list.append(question_dict)

        return ExamDetailResponse(
            id=exam.id,
            title=exam.title,
            subject=exam.subject,
            topic=exam.topic,
            difficulty=exam.difficulty,
            status=exam.status,
            created_by=exam.created_by,
            created_at=exam.created_at,
            updated_at=exam.updated_at,
            questions=questions_list,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching exam details: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch exam details",
        )


@router.post("/{exam_id}/start", status_code=status.HTTP_200_OK)
def start_exam(
    exam_id: UUID,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Start or resume an exam session.
    Returns session_token, time_remaining_seconds, and saved_answers if resuming.
    """
    user_id = UUID(current_user["sub"])
    service = ExamSessionService(db)
    try:
        return service.start_or_resume(
            exam_id=exam_id,
            user_id=user_id,
            request=request,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Start exam error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to start exam session."
        )