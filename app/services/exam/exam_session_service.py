import uuid
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.models.exam_session import ExamSession
from app.models.exam_attempt import ExamAttempt
from app.models.attempt_answer import AttemptAnswer
from app.models.exam import Exam
from app.common.enums import ExamStatus, AttemptStatus

EXAM_SESSION_DURATION_MINUTES = 90


def _make_device_fingerprint(request: Request) -> str:
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    raw = f"{ip}:{ua}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class ExamSessionService:
    def __init__(self, db: Session):
        self.db = db

    def start_or_resume(
        self,
        exam_id: UUID,
        user_id: UUID,
        request: Request,
    ) -> dict:
        now = datetime.now(timezone.utc)
        device_fp = _make_device_fingerprint(request)

        existing_session: Optional[ExamSession] = (
            self.db.query(ExamSession)
            .filter(
                ExamSession.exam_id == exam_id,
                ExamSession.user_id == user_id,
                ExamSession.is_active == True,
                ExamSession.expires_at > now,
            )
            .first()
        )

        if existing_session:
            if (
                existing_session.device_fingerprint
                and existing_session.device_fingerprint != device_fp
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "This exam is already open on another device or browser. "
                        "Please close it there before continuing here."
                    ),
                )

            existing_session.last_heartbeat = now
            self.db.commit()

            saved_answers = self._get_saved_answers(existing_session.attempt_id)
            return {
                "session_token": existing_session.session_token,
                "attempt_id": str(existing_session.attempt_id),
                "exam_id": str(exam_id),
                "expires_at": existing_session.expires_at.isoformat(),
                "is_resume": True,
                "saved_answers": saved_answers,
                "time_remaining_seconds": int(
                    (existing_session.expires_at - now).total_seconds()
                ),
            }

        exam = self.db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")

        if exam.status not in (ExamStatus.ready, ExamStatus.published):
            raise HTTPException(
                status_code=400,
                detail=f"Exam is not available (status: {exam.status.value})"
            )

        attempt = ExamAttempt(
            id=uuid.uuid4(),
            exam_id=exam_id,
            user_id=user_id,
            score=0,
            status=AttemptStatus.in_progress,
        )
        self.db.add(attempt)
        self.db.flush()

        session_token = secrets.token_urlsafe(32)
        expires_at = now + timedelta(minutes=EXAM_SESSION_DURATION_MINUTES)

        session = ExamSession(
            id=uuid.uuid4(),
            exam_id=exam_id,
            user_id=user_id,
            attempt_id=attempt.id,
            session_token=session_token,
            device_fingerprint=device_fp,
            expires_at=expires_at,
            is_active=True,
        )
        self.db.add(session)
        self.db.commit()

        return {
            "session_token": session_token,
            "attempt_id": str(attempt.id),
            "exam_id": str(exam_id),
            "expires_at": expires_at.isoformat(),
            "is_resume": False,
            "saved_answers": {},
            "time_remaining_seconds": EXAM_SESSION_DURATION_MINUTES * 60,
        }

    def save_answer(
        self,
        session_token: str,
        user_id: UUID,
        question_id: UUID,
        option_id: UUID,
    ) -> dict:
        session = self._get_valid_session(session_token, user_id)

        existing: Optional[AttemptAnswer] = (
            self.db.query(AttemptAnswer)
            .filter(
                AttemptAnswer.attempt_id == session.attempt_id,
                AttemptAnswer.question_id == question_id,
            )
            .first()
        )

        if existing:
            existing.selected_option_id = option_id
        else:
            self.db.add(AttemptAnswer(
                id=uuid.uuid4(),
                attempt_id=session.attempt_id,
                question_id=question_id,
                selected_option_id=option_id,
            ))

        session.last_heartbeat = datetime.now(timezone.utc)
        self.db.commit()

        return {"saved": True, "question_id": str(question_id)}

    def heartbeat(self, session_token: str, user_id: UUID) -> dict:
        session = self._get_valid_session(session_token, user_id)
        now = datetime.now(timezone.utc)
        session.last_heartbeat = now
        self.db.commit()

        return {
            "time_remaining_seconds": int(
                (session.expires_at - now).total_seconds()
            )
        }

    def abandon_attempt(self, session_token: str, user_id: UUID) -> dict:
        session = self._get_valid_session(session_token, user_id)

        attempt = (
            self.db.query(ExamAttempt)
            .filter(ExamAttempt.id == session.attempt_id)
            .first()
        )
        if attempt:
            attempt.status = AttemptStatus.abandoned
            attempt.submit_time = datetime.now(timezone.utc)

        session.is_active = False
        self.db.commit()

        return {"abandoned": True, "attempt_id": str(session.attempt_id)}

    def validate_and_get_session(
        self, session_token: str, user_id: UUID
    ) -> ExamSession:
        return self._get_valid_session(session_token, user_id)

    def finalize_session(self, session_token: str) -> None:
        session = (
            self.db.query(ExamSession)
            .filter(ExamSession.session_token == session_token)
            .first()
        )
        if session:
            session.is_active = False
            self.db.commit()

    def _get_valid_session(
        self, session_token: str, user_id: UUID
    ) -> ExamSession:
        now = datetime.now(timezone.utc)
        session = (
            self.db.query(ExamSession)
            .filter(
                ExamSession.session_token == session_token,
                ExamSession.user_id == user_id,
                ExamSession.is_active == True,
                ExamSession.expires_at > now,
            )
            .first()
        )
        if not session:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired exam session. The exam may have timed out.",
            )
        return session

    def _get_saved_answers(self, attempt_id: Optional[UUID]) -> dict:
        if not attempt_id:
            return {}
        answers = (
            self.db.query(AttemptAnswer)
            .filter(AttemptAnswer.attempt_id == attempt_id)
            .all()
        )
        return {
            str(a.question_id): str(a.selected_option_id)
            for a in answers
            if a.selected_option_id
        }
