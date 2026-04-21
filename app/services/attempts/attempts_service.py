import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.exam import Exam
from app.models.exam_attempt import ExamAttempt
from app.models.attempt_answer import AttemptAnswer
from app.models.question import Question
from app.models.question_option import QuestionOption
from app.models.question_statistic import QuestionStatistic
from app.common.enums import AttemptStatus, ExamStatus

logger = logging.getLogger(__name__)


class AttemptsService:
    def __init__(self, db: Session):
        self.db = db

    def submit_existing_attempt(
        self,
        attempt_id: UUID,
        user_id: UUID,
    ) -> ExamAttempt:
        """
        Score and finalize an attempt that was created at exam start.
        Answers are already saved incrementally — this just scores them.
        """
        attempt = (
            self.db.query(ExamAttempt)
            .options(
                joinedload(ExamAttempt.answers)
                .joinedload(AttemptAnswer.question)
                .joinedload(Question.options),
            )
            .filter(ExamAttempt.id == attempt_id)
            .first()
        )

        if not attempt:
            raise ValueError(f"Attempt {attempt_id} not found")

        if attempt.user_id != user_id:
            raise PermissionError("You do not own this attempt")

        if attempt.status != AttemptStatus.in_progress:
            raise ValueError(
                f"Attempt is already {attempt.status.value} and cannot be submitted"
            )

        # Score the saved answers
        correct_count = 0
        q_ids_answered = []

        for answer in attempt.answers:
            q = answer.question
            if not q:
                continue

            correct_opt = next((o for o in q.options if o.is_correct), None)
            if correct_opt and answer.selected_option_id == correct_opt.id:
                correct_count += 1

            q_ids_answered.append(answer.question_id)

        attempt.score = correct_count
        attempt.status = AttemptStatus.submitted
        attempt.submit_time = datetime.now(timezone.utc)

        # Update statistics
        self._update_question_statistics(attempt.answers)

        self.db.commit()
        self.db.refresh(attempt)

        logger.info(
            "Attempt %s submitted: %d/%d correct",
            attempt_id, correct_count, len(attempt.answers)
        )
        return attempt

    def get_attempt_results(self, attempt_id: UUID, user_id: UUID) -> dict:
        attempt = (
            self.db.query(ExamAttempt)
            .options(
                joinedload(ExamAttempt.exam),
                joinedload(ExamAttempt.answers)
                    .joinedload(AttemptAnswer.question)
                    .joinedload(Question.options),
                joinedload(ExamAttempt.answers)
                    .joinedload(AttemptAnswer.question)
                    .joinedload(Question.explanations),
            )
            .filter(ExamAttempt.id == attempt_id)
            .first()
        )

        if not attempt:
            raise ValueError(f"Attempt {attempt_id} not found")

        if attempt.user_id != user_id:
            raise PermissionError("You do not have access to this attempt")

        if attempt.status != AttemptStatus.submitted:
            raise ValueError("Attempt has not been submitted yet")

        total = len(attempt.answers)
        correct = attempt.score

        questions_result = []
        for ans in attempt.answers:
            q = ans.question
            sorted_opts = sorted(q.options, key=lambda o: o.option_text)
            options_dict = {
                chr(65 + i): opt.option_text
                for i, opt in enumerate(sorted_opts)
            }
            label_by_id = {
                opt.id: chr(65 + i)
                for i, opt in enumerate(sorted_opts)
            }

            correct_opt = next((o for o in q.options if o.is_correct), None)
            explanation = (
                q.explanations[0].explanation_text if q.explanations else None
            )

            questions_result.append({
                "id": str(q.id),
                "question": q.question_text,
                "options": options_dict,
                "correct_answer": (
                    label_by_id.get(correct_opt.id) if correct_opt else None
                ),
                "user_answer": label_by_id.get(ans.selected_option_id),
                "explanation": explanation,
            })

        return {
            "id": str(attempt.id),
            "exam_name": attempt.exam.title,
            "total": total,
            "correct": correct,
            "score_percent": round((correct / total) * 100, 1) if total else 0,
            "submitted_at": (
                attempt.submit_time.isoformat()
                if attempt.submit_time else None
            ),
            "questions": questions_result,
        }

    def _update_question_statistics(
        self, answers: list[AttemptAnswer]
    ) -> None:
        q_ids = [a.question_id for a in answers]

        existing: dict[UUID, QuestionStatistic] = {
            s.question_id: s
            for s in self.db.query(QuestionStatistic)
            .filter(QuestionStatistic.question_id.in_(q_ids))
            .all()
        }

        new_stats = []
        for answer in answers:
            q = answer.question
            correct_opt = next((o for o in q.options if o.is_correct), None)
            is_correct = (
                correct_opt is not None
                and answer.selected_option_id == correct_opt.id
            )

            stat = existing.get(answer.question_id)
            if stat:
                stat.times_attempted += 1
                stat.times_correct += int(is_correct)
                stat.times_wrong += int(not is_correct)
            else:
                new_stat = QuestionStatistic(
                    id=uuid.uuid4(),
                    question_id=answer.question_id,
                    times_attempted=1,
                    times_correct=int(is_correct),
                    times_wrong=int(not is_correct),
                )
                new_stats.append(new_stat)
                existing[answer.question_id] = new_stat

        if new_stats:
            self.db.bulk_save_objects(new_stats)