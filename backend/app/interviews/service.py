"""
Interviews service — PostgreSQL version.

Replaces every Motor call with SQLAlchemy AsyncSession queries.
Public function signatures are unchanged so the router needs no edits.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.interview_agent.service import (
    _load_resume_context,
    evaluate_answer_only,
    generate_adaptive_followup,
    generate_devils_advocate_challenge_question,
    generate_question_bank,
    get_max_questions,
)
from app.interview_agent.tts import synthesize_question_audio_data_uri
from app.interviews.contradiction import detect_contradiction
from app.interviews.question_pipeline import (
    compose_hybrid_bank,
    dynamic_followup_budget,
    select_curated_questions,
)
from app.interviews.schemas import StartInterviewRequest, SubmitAnswerRequest
from app.models.interview import Interview, InterviewResponse
from app.results.scoring_engine import scoring_engine

logger = logging.getLogger(__name__)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_uuid(raw: str, field_name: str) -> uuid.UUID:
    try:
        return uuid.UUID(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}",
        ) from exc


def _normalize_difficulty(difficulty: str | None) -> str:
    normalized = (difficulty or "").strip().lower()
    aliases = {
        "beginner": "easy", "junior": "easy",
        "mid": "medium", "mid-level": "medium", "intermediate": "medium",
        "senior": "hard", "advanced": "hard", "expert": "hard",
    }
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in {"easy", "medium", "hard"} else "medium"


def _normalize_persona(persona: str | None) -> str:
    return (persona or "").strip().lower().replace("-", "_").replace(" ", "_").replace("'", "")


def _is_devils_advocate(persona: str | None) -> bool:
    return _normalize_persona(persona) in {"devils_advocate", "devil_advocate"}


def _sanitize_contradiction(raw: Any) -> dict | None:
    if not isinstance(raw, dict):
        return None
    required = {"contradiction", "confidence", "topic", "previous_claim", "current_claim", "explanation", "severity"}
    if not required.issubset(raw.keys()):
        return None
    try:
        confidence = float(raw.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    return {
        "contradiction": bool(raw.get("contradiction", False)),
        "confidence": max(0.0, min(1.0, confidence)),
        "topic": str(raw.get("topic") or "").strip(),
        "previous_claim": str(raw.get("previous_claim") or "").strip(),
        "current_claim": str(raw.get("current_claim") or "").strip(),
        "explanation": str(raw.get("explanation") or "").strip(),
        "severity": str(raw.get("severity") or "low").strip().lower() or "low",
    }


def _detect_uncertainty_reasons(*, answer: str, evaluation: dict, contradiction_result: dict | None) -> list[str]:
    reasons: list[str] = []
    lowered = answer.lower()
    if any(m in lowered for m in ["i think", "maybe", "not sure", "i guess", "probably", "kind of", "sort of", "might be", "i don't know"]):
        reasons.append("verbal uncertainty markers")
    if _coerce_int(evaluation.get("score"), 5) <= 5:
        reasons.append("low answer score")
    feedback_text = str(evaluation.get("feedback") or "").lower()
    if any(m in feedback_text for m in ["unclear", "vague", "not enough detail", "insufficient", "uncertain", "contradict", "inconsistent"]):
        reasons.append("evaluation flagged weak clarity")
    if contradiction_result and contradiction_result.get("contradiction") and float(contradiction_result.get("confidence") or 0.0) >= 0.55:
        reasons.append("high-confidence contradiction")
    return list(dict.fromkeys(reasons))


def _interview_deadline(interview: Interview) -> datetime | None:
    deadline = interview.deadline_at
    if not isinstance(deadline, datetime):
        return None
    return deadline if deadline.tzinfo else deadline.replace(tzinfo=timezone.utc)


# ── Serializers ───────────────────────────────────────────────────────────────

def _serialize_interview(row: Interview) -> dict[str, Any]:
    bank = row.questions_bank or []
    return {
        "id": str(row.id),
        "user_id": row.user_id,
        "role": row.role,
        "difficulty": row.difficulty,
        "persona": row.persona,
        "status": row.status,
        "created_at": row.created_at,
        "questions_bank": bank,
        "total_questions": len(bank),
        "session_analysis": row.session_analysis,
        "duration_minutes": row.duration_minutes,
        "deadline_at": row.deadline_at,
        "questions_meta": row.questions_meta,
    }


def _serialize_response(row: InterviewResponse) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "interview_id": str(row.interview_id),
        "user_id": row.user_id,
        "question": row.question,
        "answer": row.answer,
        "score": row.score,
        "feedback": row.feedback,
        "strengths": row.strengths,
        "weaknesses": row.weaknesses,
        "contradiction_analysis": row.contradiction_analysis,
        "created_at": row.created_at,
    }


# ── Service functions ─────────────────────────────────────────────────────────

async def ensure_interview_indexes(db: AsyncSession) -> None:
    """No-op — indexes are managed by Alembic."""
    pass


async def start_interview(
    db: AsyncSession,
    payload: StartInterviewRequest,
    user_id: str,
) -> dict[str, Any]:
    difficulty = _normalize_difficulty(payload.difficulty)
    max_questions = payload.max_questions or get_max_questions()
    duration_minutes = payload.duration_minutes

    logger.info("Starting interview", extra={"user_id": user_id, "role": payload.role})

    resume = await _load_resume_context(db, user_id)
    resume_skills = resume.get("skills") or []

    curated_count = round(max(0, max_questions - 1) * 0.4)
    curated_items = select_curated_questions(
        role=payload.role,
        difficulty=difficulty,
        resume_skills=resume_skills,
        count=curated_count,
        seed=f"{user_id}:{datetime.now(timezone.utc).isoformat()}",
    )

    llm_count = max(1, max_questions - len(curated_items))
    llm_bank = await generate_question_bank(
        db=db,
        user_id=user_id,
        role=payload.role,
        difficulty=difficulty,
        persona=payload.persona,
        max_questions=llm_count,
    )

    questions_bank, questions_meta = compose_hybrid_bank(
        intro_question=llm_bank[0],
        llm_questions=llm_bank[1:],
        curated_items=curated_items,
        max_questions=max_questions,
    )
    first_question = questions_bank[0]

    deadline_at = (
        datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
        if duration_minutes
        else None
    )

    interview = Interview(
        user_id=user_id,
        role=payload.role,
        difficulty=difficulty,
        persona=payload.persona,
        current_question=first_question,
        current_question_index=0,
        max_questions=len(questions_bank),
        questions_bank=questions_bank,
        questions_meta=questions_meta,
        dynamic_budget=dynamic_followup_budget(len(questions_bank)),
        dynamic_used=0,
        duration_minutes=duration_minutes,
        deadline_at=deadline_at,
        status="ongoing",
    )
    db.add(interview)
    await db.flush()

    first_question_audio = await asyncio.to_thread(synthesize_question_audio_data_uri, first_question)

    logger.info("Interview created", extra={"interview_id": str(interview.id)})
    return {
        "interview_id": str(interview.id),
        "first_question": first_question,
        "first_question_audio_data_uri": first_question_audio,
        "questions_bank": questions_bank,
        "total_questions": len(questions_bank),
        "status": "ongoing",
        "duration_minutes": duration_minutes,
        "deadline_at": deadline_at,
    }


async def submit_answer(
    db: AsyncSession,
    payload: SubmitAnswerRequest,
    user_id: str,
) -> dict[str, Any]:
    interview_uuid = _parse_uuid(payload.interview_id, "interview_id")

    result = await db.execute(select(Interview).where(Interview.id == interview_uuid))
    interview = result.scalar_one_or_none()

    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    if interview.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to access this interview")
    if interview.status == "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Interview is already completed")

    deadline_at = _interview_deadline(interview)
    time_expired = deadline_at is not None and datetime.now(timezone.utc) >= deadline_at

    # Load all past responses (ordered by creation time)
    resp_result = await db.execute(
        select(InterviewResponse)
        .where(InterviewResponse.interview_id == interview_uuid)
        .order_by(InterviewResponse.created_at)
    )
    past_responses = resp_result.scalars().all()
    answered_count = len(past_responses)

    questions_bank = interview.questions_bank or []
    if not questions_bank:
        # Legacy: generate on the fly
        questions_bank = await generate_question_bank(
            db=db,
            user_id=user_id,
            role=interview.role,
            difficulty=interview.difficulty,
            persona=interview.persona,
            max_questions=interview.max_questions or get_max_questions(),
        )
        interview.questions_bank = questions_bank
        await db.flush()

    max_questions = len(questions_bank)
    if max_questions <= 0:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Questions bank is empty")

    current_question_index = _coerce_int(interview.current_question_index, answered_count)
    current_question_index = max(0, min(current_question_index, max_questions - 1))

    if answered_count >= max_questions:
        interview.status = "completed"
        await db.flush()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Interview has no remaining questions")

    current_question = (interview.current_question or "").strip()
    if not current_question:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Interview current question is missing")

    questions_meta = interview.questions_meta or []
    current_meta: dict = (
        questions_meta[current_question_index]
        if current_question_index < len(questions_meta) and isinstance(questions_meta[current_question_index], dict)
        else {}
    )

    # Evaluate answer
    try:
        agent_result = await evaluate_answer_only(
            db=db,
            interview_id=interview_uuid,
            user_id=user_id,
            role=interview.role,
            difficulty=interview.difficulty,
            persona=interview.persona,
            question=current_question,
            answer=payload.answer,
            expected_keywords=current_meta.get("expected_keywords") or None,
            evaluation_criteria=current_meta.get("evaluation_criteria") or None,
        )
        evaluation = agent_result["evaluation"]
    except Exception:
        logger.exception("Answer evaluation failed; using fallback")
        evaluation = {"score": 5, "feedback": "Evaluation temporarily unavailable.", "strengths": [], "weaknesses": []}

    # Contradiction detection
    memory_parts = [f"Q: {r.question}\nA: {r.answer}" for r in past_responses]
    memory = "\n\n".join(memory_parts)
    try:
        contradiction_result = _sanitize_contradiction(await detect_contradiction(memory, payload.answer))
    except Exception:
        logger.exception("Contradiction detection failed")
        contradiction_result = None

    # Save response row
    response_row = InterviewResponse(
        interview_id=interview_uuid,
        user_id=user_id,
        question=current_question,
        answer=payload.answer,
        score=evaluation.get("score"),
        feedback=evaluation.get("feedback"),
        strengths=evaluation.get("strengths", []),
        weaknesses=evaluation.get("weaknesses", []),
        contradiction_analysis=contradiction_result,
    )
    db.add(response_row)
    await db.flush()

    next_question_index = current_question_index + 1

    if time_expired or next_question_index >= max_questions:
        interview.status = "completed"
        interview.current_question = None
        interview.current_question_index = min(next_question_index, max_questions)
        interview.last_score = evaluation["score"]
        await db.flush()
        return {
            "interview_id": str(interview.id),
            "evaluation": evaluation,
            "next_question": None,
            "next_question_audio_data_uri": None,
            "status": "completed",
            "contradiction_analysis": contradiction_result,
            "time_expired": time_expired,
        }

    # Determine next question
    next_question = questions_bank[next_question_index] if next_question_index < len(questions_bank) else None
    adaptive_meta: dict | None = None

    # Dynamic follow-up budget (20% adaptive slice)
    dynamic_budget = _coerce_int(interview.dynamic_budget, 0)
    dynamic_used = _coerce_int(interview.dynamic_used, 0)

    if next_question and not _is_devils_advocate(interview.persona) and dynamic_used < dynamic_budget:
        score = _coerce_int(evaluation.get("score"), 5)
        adaptive_question: str | None = None
        adaptive_mode: str | None = None

        high_conf_contradiction = bool(
            contradiction_result
            and contradiction_result.get("contradiction")
            and float(contradiction_result.get("confidence") or 0.0) >= 0.55
        )
        if high_conf_contradiction:
            adaptive_mode = "challenge"
            adaptive_question = await generate_adaptive_followup(
                mode="challenge",
                role=interview.role,
                difficulty=interview.difficulty,
                last_question=current_question,
                last_answer=payload.answer,
                context_note=str(contradiction_result.get("explanation") or ""),
            )
        elif score <= 4:
            curated_followups = [str(f).strip() for f in (current_meta.get("follow_ups") or []) if str(f).strip()]
            if curated_followups:
                adaptive_mode = "curated_followup"
                adaptive_question = curated_followups[dynamic_used % len(curated_followups)]
            else:
                adaptive_mode = "clarify"
                adaptive_question = await generate_adaptive_followup(
                    mode="clarify",
                    role=interview.role,
                    difficulty=interview.difficulty,
                    last_question=current_question,
                    last_answer=payload.answer,
                )
        elif score >= 8:
            adaptive_mode = "escalate"
            adaptive_question = await generate_adaptive_followup(
                mode="escalate",
                role=interview.role,
                difficulty=interview.difficulty,
                last_question=current_question,
                last_answer=payload.answer,
            )

        if adaptive_question:
            next_question = adaptive_question
            adaptive_meta = {
                "source": "followup",
                "mode": adaptive_mode,
                "parent_index": current_question_index,
                "parent_subject": current_meta.get("subject"),
            }

    if _is_devils_advocate(interview.persona):
        uncertainty_reasons = _detect_uncertainty_reasons(
            answer=payload.answer,
            evaluation=evaluation,
            contradiction_result=contradiction_result,
        )
        if uncertainty_reasons:
            history_for_challenge = [
                {"question": r.question, "answer": r.answer, "score": r.score or 5, "feedback": r.feedback or ""}
                for r in past_responses
            ]
            history_for_challenge.append({
                "question": current_question,
                "answer": payload.answer,
                "score": _coerce_int(evaluation.get("score"), 5),
                "feedback": str(evaluation.get("feedback") or ""),
            })
            next_question = await generate_devils_advocate_challenge_question(
                role=interview.role,
                difficulty=interview.difficulty,
                last_question=current_question,
                last_answer=payload.answer,
                history=history_for_challenge,
                trigger_reasons=uncertainty_reasons,
            )

    if not next_question:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Questions bank exhausted unexpectedly")

    # Update interview state
    # JSONB mutation requires reassignment for SQLAlchemy to detect the change
    updated_bank = list(questions_bank)
    updated_meta = list(questions_meta)

    if adaptive_meta is not None:
        if next_question_index < len(updated_bank):
            updated_bank[next_question_index] = next_question
        if next_question_index < len(updated_meta):
            updated_meta[next_question_index] = adaptive_meta
        interview.dynamic_used = dynamic_used + 1

    interview.questions_bank = updated_bank
    interview.questions_meta = updated_meta
    interview.current_question = next_question
    interview.current_question_index = next_question_index
    interview.last_score = evaluation["score"]
    await db.flush()

    next_audio = await asyncio.to_thread(synthesize_question_audio_data_uri, next_question)

    return {
        "interview_id": str(interview.id),
        "evaluation": evaluation,
        "next_question": next_question,
        "next_question_audio_data_uri": next_audio,
        "status": "ongoing",
        "contradiction_analysis": contradiction_result,
        "time_expired": False,
    }


async def get_interview_details(db: AsyncSession, interview_id_raw: str, user_id: str) -> dict[str, Any]:
    interview_uuid = _parse_uuid(interview_id_raw, "id")

    result = await db.execute(select(Interview).where(Interview.id == interview_uuid))
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    if interview.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to access this interview")

    resp_result = await db.execute(
        select(InterviewResponse)
        .where(InterviewResponse.interview_id == interview_uuid)
        .order_by(InterviewResponse.created_at)
    )
    responses = resp_result.scalars().all()
    return {"interview": _serialize_interview(interview), "responses": [_serialize_response(r) for r in responses]}


async def create_share_token(db: AsyncSession, interview_id_raw: str, user_id: str) -> dict[str, Any]:
    from uuid import uuid4
    interview_uuid = _parse_uuid(interview_id_raw, "interview_id")
    result = await db.execute(select(Interview).where(Interview.id == interview_uuid))
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    if interview.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to access this interview")

    if not interview.share_token:
        interview.share_token = uuid4().hex
        await db.flush()

    return {"share_token": interview.share_token}


async def get_shared_report(db: AsyncSession, share_token: str) -> dict[str, Any]:
    token = (share_token or "").strip()
    if not token or len(token) < 16:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    result = await db.execute(select(Interview).where(Interview.share_token == token))
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    resp_result = await db.execute(
        select(InterviewResponse)
        .where(InterviewResponse.interview_id == interview.id)
        .order_by(InterviewResponse.created_at)
    )
    responses = resp_result.scalars().all()
    return {"interview": _serialize_interview(interview), "responses": [_serialize_response(r) for r in responses]}


async def save_session_analysis(
    db: AsyncSession,
    interview_id_raw: str,
    user_id: str,
    session_analysis: dict[str, Any],
) -> dict[str, Any]:
    interview_uuid = _parse_uuid(interview_id_raw, "interview_id")
    result = await db.execute(select(Interview).where(Interview.id == interview_uuid))
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    if interview.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to access this interview")

    def _norm_timeline(raw: Any) -> list[dict]:
        if not isinstance(raw, list):
            return []
        out = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                ts = float(item.get("timestamp", 0))
            except (TypeError, ValueError):
                continue
            out.append({
                "timestamp": max(0.0, ts),
                "label": str(item.get("label") or "").strip() or None,
                "payload": item.get("payload") if isinstance(item.get("payload"), dict) else {},
            })
        return out

    prosody = session_analysis.get("prosody") if isinstance(session_analysis.get("prosody"), dict) else None
    sanitized = {
        "voice_summary": session_analysis.get("voice_summary"),
        "key_moments": session_analysis.get("key_moments") or [],
        "confidence": session_analysis.get("confidence"),
        "clarity": session_analysis.get("clarity"),
        "nervousness": session_analysis.get("nervousness"),
        "posture_score": session_analysis.get("posture_score"),
        "gaze_score": session_analysis.get("gaze_score"),
        "fidgeting_score": session_analysis.get("fidgeting_score"),
        "dominant_emotion": session_analysis.get("dominant_emotion"),
        "duration_seconds": session_analysis.get("duration_seconds"),
        "video_timeline": _norm_timeline(session_analysis.get("video_timeline")),
        "voice_timeline": _norm_timeline(session_analysis.get("voice_timeline")),
        "prosody": prosody,
        "pace_wpm": session_analysis.get("pace_wpm") or (prosody or {}).get("pace_wpm"),
        "multi_face_ratio": session_analysis.get("multi_face_ratio"),
        "background_person_detected": session_analysis.get("background_person_detected"),
    }

    resp_result = await db.execute(
        select(InterviewResponse).where(InterviewResponse.interview_id == interview_uuid)
    )
    responses = resp_result.scalars().all()
    response_scores = [r.score for r in responses if r.score is not None]
    scoring = scoring_engine.calculate(response_scores=response_scores, session_analysis=sanitized)
    sanitized["component_scores"] = scoring["component_scores"]
    sanitized["overall_score"] = scoring["overall_score"]
    sanitized["grade"] = scoring["grade"]
    sanitized["score_weights"] = scoring["weights_used"]

    interview.session_analysis = sanitized
    await db.flush()

    # Invalidate cached results snapshot
    from app.models.results import ResultsAnalysisSnapshot
    snap_result = await db.execute(
        select(ResultsAnalysisSnapshot).where(ResultsAnalysisSnapshot.user_id == user_id)
    )
    snap = snap_result.scalar_one_or_none()
    if snap:
        await db.delete(snap)
        await db.flush()

    return {"status": "ok", "interview_id": str(interview.id), "overall_score": sanitized.get("overall_score")}