import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_user
from app.services.attempts.attempts_service import AttemptsService
from app.services.exam.exam_session_service import ExamSessionService

router = APIRouter()
logger = logging.getLogger(__name__)


class SubmitAttemptRequest(BaseModel):
    exam_session_token: str


class SaveAnswerRequest(BaseModel):
    session_token: str
    question_id: UUID
    option_id: UUID


class HeartbeatRequest(BaseModel):
    session_token: str


class AbandonRequest(BaseModel):
    session_token: str


@router.post("/submit", status_code=status.HTTP_200_OK)
def submit_attempt(
    payload: SubmitAttemptRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = UUID(current_user["sub"])

    session_service = ExamSessionService(db)
    session = session_service.validate_and_get_session(
        session_token=payload.exam_session_token,
        user_id=user_id,
    )

    attempts_service = AttemptsService(db)
    try:
        attempt = attempts_service.submit_existing_attempt(
            attempt_id=session.attempt_id,
            user_id=user_id,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Submit error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit attempt.")

    session_service.finalize_session(payload.exam_session_token)

    return {"id": str(attempt.id)}


@router.post("/answer", status_code=status.HTTP_200_OK)
def save_answer(
    payload: SaveAnswerRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = UUID(current_user["sub"])
    service = ExamSessionService(db)
    try:
        return service.save_answer(
            session_token=payload.session_token,
            user_id=user_id,
            question_id=payload.question_id,
            option_id=payload.option_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Save answer error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save answer.")


@router.post("/heartbeat", status_code=status.HTTP_200_OK)
def heartbeat(
    payload: HeartbeatRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = UUID(current_user["sub"])
    service = ExamSessionService(db)
    try:
        return service.heartbeat(
            session_token=payload.session_token,
            user_id=user_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Heartbeat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Heartbeat failed.")


@router.post("/abandon", status_code=status.HTTP_200_OK)
def abandon_attempt(
    payload: AbandonRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = UUID(current_user["sub"])
    service = ExamSessionService(db)
    try:
        return service.abandon_attempt(
            session_token=payload.session_token,
            user_id=user_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Abandon error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to abandon attempt.")


@router.get("/{attempt_id}", status_code=status.HTTP_200_OK)
def get_attempt_results(
    attempt_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = UUID(current_user["sub"])
    service = AttemptsService(db)
    try:
        return service.get_attempt_results(
            attempt_id=attempt_id,
            user_id=user_id,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Results error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch results.")
