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
from app.services.cache.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class AttemptsService:
    def __init__(self, db: Session):
        self.db = db
        self.redis = get_redis_client()

    def submit_attempt(
        self,
        exam_id: UUID,
        user_id: UUID,
        answers: dict[str, str],  # {question_id (str): option_id (str)}
    ) -> ExamAttempt:
        """
        Submit an exam attempt.

        Validates the exam is available, every answer references a real
        question in that exam, and every selected option belongs to that
        question. Scores the attempt, persists everything in one transaction,
        and updates per-question statistics.

        :param exam_id: UUID of the exam being attempted
        :param user_id: UUID of the submitting user
        :param answers: mapping of question_id -> selected_option_id (both as str)
        :return: Completed ExamAttempt ORM object
        :raises ValueError: on invalid exam state or bad answer data
        :raises PermissionError: if the user doesn't own this resource
        """
        # --- 1. Validate exam exists and is takeable ---
        exam = (
            self.db.query(Exam)
            .options(joinedload(Exam.exam_questions))
            .filter(Exam.id == exam_id)
            .first()
        )
        if not exam:
            raise ValueError(f"Exam {exam_id} not found")

        if exam.status not in (ExamStatus.ready, ExamStatus.published):
            raise ValueError(
                f"Exam is not available for attempt (status: {exam.status.value})"
            )

        valid_question_ids: set[UUID] = {
            eq.question_id for eq in exam.exam_questions
        }
        if not valid_question_ids:
            raise ValueError("Exam has no questions")

        # --- 2. Parse and validate submitted question IDs ---
        try:
            parsed_answers: dict[UUID, UUID] = {
                UUID(q_id): UUID(opt_id)
                for q_id, opt_id in answers.items()
            }
        except ValueError as e:
            raise ValueError(f"Invalid UUID in answers: {e}") from e

        unknown = set(parsed_answers) - valid_question_ids
        if unknown:
            raise ValueError(
                f"Questions not in this exam: {[str(q) for q in unknown]}"
            )

        # --- 3. Load questions + options in one query ---
        questions: list[Question] = (
            self.db.query(Question)
            .options(
                joinedload(Question.options),
                joinedload(Question.explanations),
            )
            .filter(Question.id.in_(parsed_answers.keys()))
            .all()
        )
        question_map: dict[UUID, Question] = {q.id: q for q in questions}

        # Build fast-lookup structures
        correct_option_map: dict[UUID, Optional[UUID]] = {}
        valid_options_map: dict[UUID, set[UUID]] = {}
        for q in questions:
            correct_opt = next((o for o in q.options if o.is_correct), None)
            correct_option_map[q.id] = correct_opt.id if correct_opt else None
            valid_options_map[q.id] = {o.id for o in q.options}

        # --- 4. Validate each selected option belongs to its question ---
        for q_uuid, opt_uuid in parsed_answers.items():
            if opt_uuid not in valid_options_map.get(q_uuid, set()):
                raise ValueError(
                    f"Option {opt_uuid} does not belong to question {q_uuid}"
                )

        # --- 5. Create ExamAttempt ---
        now = datetime.now(timezone.utc)
        attempt = ExamAttempt(
            id=uuid.uuid4(),
            exam_id=exam_id,
            user_id=user_id,
            score=0,
            status=AttemptStatus.in_progress,
        )
        self.db.add(attempt)
        self.db.flush()  # get attempt.id without committing

        # --- 6. Record answers and tally score ---
        correct_count = 0
        answer_records: list[AttemptAnswer] = []

        for q_uuid, opt_uuid in parsed_answers.items():
            is_correct = opt_uuid == correct_option_map.get(q_uuid)
            if is_correct:
                correct_count += 1

            answer_records.append(
                AttemptAnswer(
                    id=uuid.uuid4(),
                    attempt_id=attempt.id,
                    question_id=q_uuid,
                    selected_option_id=opt_uuid,
                )
            )

        self.db.bulk_save_objects(answer_records)

        # --- 7. Finalise attempt ---
        attempt.score = correct_count
        attempt.status = AttemptStatus.submitted
        attempt.submit_time = now

        # --- 8. Update per-question statistics (upsert) ---
        self._update_question_statistics(
            q_ids=list(parsed_answers.keys()),
            answers=parsed_answers,
            correct_option_map=correct_option_map,
        )

        self.db.commit()
        self.db.refresh(attempt)

        logger.info(
            "Attempt %s submitted: %d/%d correct (exam=%s, user=%s)",
            attempt.id, correct_count, len(valid_question_ids), exam_id, user_id,
        )
        return attempt

    def get_attempt_results(self, attempt_id: UUID, user_id: UUID) -> dict:
        """
        Return full results for a completed attempt.

        Includes per-question breakdown with correct answer, user's answer,
        and explanation text.

        :param attempt_id: UUID of the attempt
        :param user_id: UUID of the requesting user (ownership check)
        :raises ValueError: if attempt not found or not yet submitted
        :raises PermissionError: if the attempt belongs to a different user
        """
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
            # Stable ordering: sort options by their text so A/B/C/D is
            # deterministic and matches what the exam page rendered.
            sorted_opts: list[QuestionOption] = sorted(
                q.options, key=lambda o: o.option_text
            )
            options_dict = {
                chr(65 + i): opt.option_text
                for i, opt in enumerate(sorted_opts)
            }
            label_by_id = {opt.id: chr(65 + i) for i, opt in enumerate(sorted_opts)}

            correct_opt = next((o for o in q.options if o.is_correct), None)
            explanation = (
                q.explanations[0].explanation_text if q.explanations else None
            )

            questions_result.append({
                "id": str(q.id),
                "question": q.question_text,
                "options": options_dict,
                "correct_answer": label_by_id.get(correct_opt.id) if correct_opt else None,
                "user_answer": label_by_id.get(ans.selected_option_id),
                "explanation": explanation,
            })

        return {
            "id": str(attempt.id),
            "exam_name": attempt.exam.title,
            "total": total,
            "correct": correct,
            "score_percent": round((correct / total) * 100, 1) if total else 0,
            "submitted_at": attempt.submit_time.isoformat() if attempt.submit_time else None,
            "questions": questions_result,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _update_question_statistics(
        self,
        q_ids: list[UUID],
        answers: dict[UUID, UUID],
        correct_option_map: dict[UUID, Optional[UUID]],
    ) -> None:
        """
        Upsert QuestionStatistic rows for every answered question.

        Uses a single bulk SELECT then targeted updates / inserts to avoid
        N+1 queries even for large answer sets.
        """
        existing: dict[UUID, QuestionStatistic] = {
            s.question_id: s
            for s in self.db.query(QuestionStatistic)
            .filter(QuestionStatistic.question_id.in_(q_ids))
            .all()
        }

        new_stats: list[QuestionStatistic] = []

        for q_uuid, opt_uuid in answers.items():
            is_correct = opt_uuid == correct_option_map.get(q_uuid)
            stat = existing.get(q_uuid)
            if stat:
                stat.times_attempted += 1
                stat.times_correct += int(is_correct)
                stat.times_wrong += int(not is_correct)
            else:
                new_stat = QuestionStatistic(
                    id=uuid.uuid4(),
                    question_id=q_uuid,
                    times_attempted=1,
                    times_correct=int(is_correct),
                    times_wrong=int(not is_correct),
                )
                new_stats.append(new_stat)
                existing[q_uuid] = new_stat  # guard against dup q_ids

        if new_stats:
            self.db.bulk_save_objects(new_stats)