import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_user
from app.services.attempts.attempts_service import AttemptsService

router = APIRouter()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class SubmitAttemptRequest(BaseModel):
    exam_id: UUID
    answers: dict[str, str]  # {question_id: option_id}

    @field_validator("answers")
    @classmethod
    def answers_not_empty(cls, v: dict) -> dict:
        if not v:
            raise ValueError("answers must not be empty")
        return v


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/submit", status_code=status.HTTP_200_OK)
def submit_attempt(
    payload: SubmitAttemptRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit answers for an exam.

    - Validates every answer references a real question in the exam.
    - Validates every selected option belongs to that question.
    - Scores the attempt and persists everything in one transaction.
    - Updates per-question statistics.

    Returns the attempt ID so the frontend can redirect to /results/:id.
    """
    user_id = UUID(current_user["sub"])

    service = AttemptsService(db)
    try:
        attempt = service.submit_attempt(
            exam_id=payload.exam_id,
            user_id=user_id,
            answers=payload.answers,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error submitting attempt: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit attempt. Please try again.",
        )

    return {"id": str(attempt.id)}


@router.get("/{attempt_id}", status_code=status.HTTP_200_OK)
def get_attempt_results(
    attempt_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve full results for a submitted attempt.

    Returns score, per-question breakdown, correct answers, and explanations.
    """
    user_id = UUID(current_user["sub"])

    service = AttemptsService(db)
    try:
        results = service.get_attempt_results(
            attempt_id=attempt_id,
            user_id=user_id,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error fetching results: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch results.",
        )

    return results