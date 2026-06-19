"""
Group interview service — PostgreSQL version.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.interview_agent.llm import invoke_llm_json
from app.meeting_room.speech_service import synthesize_text_to_data_uri, transcribe_audio_base64
from app.models.group_interview import GroupInterview

logger = logging.getLogger(__name__)

INTERVIEWERS: list[dict[str, str]] = [
    {"id": "panel-tech", "name": "Aarav", "track": "technical"},
    {"id": "panel-hr", "name": "Sana", "track": "hr"},
    {"id": "panel-mixed", "name": "Kabir", "track": "mixed"},
]


def _parse_uuid(value: str, field_name: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field_name}") from exc


def _total_turns() -> int:
    raw = os.getenv("GROUP_INTERVIEW_TOTAL_TURNS", "9")
    try:
        value = int(raw)
    except ValueError:
        value = 9
    return max(3, min(18, value))


def _next_interviewer(turn_number: int) -> dict[str, str]:
    return INTERVIEWERS[turn_number % len(INTERVIEWERS)]


def _format_context(turns: list[dict[str, Any]]) -> str:
    if not turns:
        return "No prior interviewer turns yet."
    lines = []
    for idx, turn in enumerate(turns[-6:], start=1):
        ev = turn.get("evaluation") or {}
        lines.append(
            f"Turn {idx} | {turn.get('interviewer_name')} ({turn.get('interviewer_track')})\n"
            f"Question: {turn.get('question')}\nAnswer: {turn.get('answer')}\n"
            f"Score: {ev.get('score', 5)}\nFeedback: {ev.get('feedback', '')}"
        )
    return "\n\n".join(lines)


async def _generate_question(*, role: str, difficulty: str, interviewer: dict, turns: list, current_turn: int, total_turns: int) -> str:
    track = interviewer["track"]
    system_prompt = "You are an expert interviewer in a 3-person group interview panel. You must return JSON only and no markdown."
    user_prompt = (
        f"Generate exactly one question for the candidate.\nRole: {role}\nDifficulty: {difficulty}\n"
        f"Interviewer name: {interviewer['name']}\nInterviewer track: {track}\nCurrent turn: {current_turn}/{total_turns}\n"
        f"Rules:\n1) Track technical: coding/system/debugging.\n2) Track hr: behavioral/communication/culture.\n"
        f"3) Track mixed: combine both.\n4) Avoid repeating recent topics.\n5) Keep question concise.\n"
        f"Recent context:\n{_format_context(turns)}\n\n"
        'Return JSON object: {"question": "string"}'
    )
    try:
        payload = await invoke_llm_json(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.55)
        question = str(payload.get("question") or "").strip()
        if question:
            return question
    except Exception:
        logger.exception("Failed to generate group interview question")
    if track == "technical":
        return "Walk me through how you would debug a production latency spike in a microservices backend."
    if track == "hr":
        return "Tell me about a time you handled conflict in a team and what outcome you drove."
    return "Describe a project trade-off where technical constraints impacted stakeholder expectations."


async def _evaluate_answer(*, role: str, difficulty: str, interviewer: dict, question: str, answer: str, turns: list) -> dict:
    system_prompt = "You are an expert interview evaluator. Return strict JSON only."
    user_prompt = (
        f"Evaluate the candidate answer.\nRole: {role}\nDifficulty: {difficulty}\n"
        f"Interviewer track: {interviewer['track']}\nQuestion: {question}\nAnswer: {answer}\n"
        f"Recent context:\n{_format_context(turns)}\n\n"
        'Return JSON: {"score": 1-10, "feedback": "string", "strengths": ["string"], "weaknesses": ["string"]}'
    )
    try:
        payload = await invoke_llm_json(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.2)
        score = max(1, min(10, int(payload.get("score", 5))))
        return {
            "score": score,
            "feedback": str(payload.get("feedback") or "Good effort. Keep improving.").strip(),
            "strengths": [str(i) for i in (payload.get("strengths") or []) if str(i).strip()][:4],
            "weaknesses": [str(i) for i in (payload.get("weaknesses") or []) if str(i).strip()][:4],
        }
    except Exception:
        logger.exception("Failed to evaluate group interview answer")
        return {"score": 6, "feedback": "Answer received.", "strengths": ["You addressed the prompt."], "weaknesses": ["Add more concrete examples."]}


def _summarize_result(turns: list[dict]) -> dict:
    if not turns:
        return {"overall_score": 1, "summary": "No responses were recorded.", "strengths": [], "weaknesses": ["Please answer interviewer questions."]}
    scores = [int((t.get("evaluation") or {}).get("score", 5)) for t in turns]
    avg = sum(scores) / len(scores)
    overall = max(1, min(100, round(avg * 10)))
    strengths: list[str] = []
    weaknesses: list[str] = []
    for t in turns:
        ev = t.get("evaluation") or {}
        strengths.extend(ev.get("strengths") or [])
        weaknesses.extend(ev.get("weaknesses") or [])
    return {
        "overall_score": overall,
        "summary": f"You completed {len(turns)} panel turns. Overall score: {overall}/100.",
        "strengths": list(dict.fromkeys(str(s) for s in strengths if str(s).strip()))[:4],
        "weaknesses": list(dict.fromkeys(str(w) for w in weaknesses if str(w).strip()))[:4],
    }


# ── Public service functions ──────────────────────────────────────────────────

async def ensure_group_interview_indexes(db: AsyncSession) -> None:
    """No-op — indexes managed by Alembic."""
    pass


async def start_group_interview(db: AsyncSession, user_id: str, role: str, difficulty: str) -> dict[str, Any]:
    total_turns = _total_turns()
    first_interviewer = _next_interviewer(0)

    question = await _generate_question(
        role=role, difficulty=difficulty, interviewer=first_interviewer,
        turns=[], current_turn=1, total_turns=total_turns,
    )
    question_audio = await synthesize_text_to_data_uri(question)

    now = datetime.now(timezone.utc)
    session = GroupInterview(
        user_id=user_id,
        role=role,
        difficulty=difficulty,
        status="ongoing",
        total_turns=total_turns,
        current_turn=1,
        active_interviewer=first_interviewer,
        current_question=question,
        turns=[],
        result=None,
        created_at=now,
        updated_at=now,
    )
    db.add(session)
    await db.flush()

    return {
        "session_id": str(session.id),
        "status": "ongoing",
        "interviewers": INTERVIEWERS,
        "question": {
            "interviewer_id": first_interviewer["id"],
            "interviewer_name": first_interviewer["name"],
            "interviewer_track": first_interviewer["track"],
            "question": question,
            "audio_data_uri": question_audio,
        },
        "progress": {"current_turn": 1, "total_turns": total_turns},
    }


async def submit_group_interview_answer(
    db: AsyncSession, user_id: str, session_id: str,
    answer_text: str | None, audio_base64: str | None, audio_mime_type: str | None,
) -> dict[str, Any]:
    session_uuid = _parse_uuid(session_id, "session_id")
    result = await db.execute(select(GroupInterview).where(GroupInterview.id == session_uuid))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group interview session not found")
    if session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to access this session")
    if session.status == "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group interview already completed")

    transcript = (answer_text or "").strip()
    if not transcript and audio_base64:
        transcript = (await transcribe_audio_base64(audio_base64, audio_mime_type)).strip()
    if not transcript:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transcript is empty.")

    active_interviewer = session.active_interviewer or _next_interviewer((session.current_turn or 1) - 1)
    question = str(session.current_question or "").strip()
    turns = list(session.turns or [])

    evaluation = await _evaluate_answer(
        role=session.role, difficulty=session.difficulty,
        interviewer=active_interviewer, question=question, answer=transcript, turns=turns,
    )

    now = datetime.now(timezone.utc)
    turn_doc = {
        "interviewer_id": active_interviewer["id"],
        "interviewer_name": active_interviewer["name"],
        "interviewer_track": active_interviewer["track"],
        "question": question,
        "answer": transcript,
        "evaluation": evaluation,
        "created_at": now.isoformat(),
    }
    turns.append(turn_doc)

    current_turn = int(session.current_turn or 1)
    total_turns = int(session.total_turns or _total_turns())
    next_question_payload: dict | None = None
    status_value = "ongoing"

    if current_turn >= total_turns:
        final_result = _summarize_result(turns)
        session.turns = turns
        session.status = "completed"
        session.completed_at = now
        session.result = final_result
        session.current_turn = current_turn
        session.updated_at = now
        status_value = "completed"
    else:
        next_turn = current_turn + 1
        interviewer = _next_interviewer(next_turn - 1)
        next_question = await _generate_question(
            role=session.role, difficulty=session.difficulty,
            interviewer=interviewer, turns=turns, current_turn=next_turn, total_turns=total_turns,
        )
        next_audio = await synthesize_text_to_data_uri(next_question)
        session.turns = turns
        session.current_turn = next_turn
        session.active_interviewer = interviewer
        session.current_question = next_question
        session.updated_at = now
        next_question_payload = {
            "interviewer_id": interviewer["id"],
            "interviewer_name": interviewer["name"],
            "interviewer_track": interviewer["track"],
            "question": next_question,
            "audio_data_uri": next_audio,
        }

    await db.flush()

    return {
        "session_id": session_id,
        "status": status_value,
        "transcript": transcript,
        "evaluation": evaluation,
        "next_question": next_question_payload,
        "progress": {
            "current_turn": min(current_turn + (1 if status_value == "ongoing" else 0), total_turns),
            "total_turns": total_turns,
        },
    }


async def get_group_interview_result(db: AsyncSession, user_id: str, session_id: str) -> dict[str, Any]:
    session_uuid = _parse_uuid(session_id, "session_id")
    result = await db.execute(select(GroupInterview).where(GroupInterview.id == session_uuid))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group interview session not found")
    if session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to access this session")

    turns = list(session.turns or [])
    final_result = session.result or _summarize_result(turns)

    return {
        "session_id": session_id,
        "status": session.status,
        "progress": {
            "current_turn": int(session.current_turn or 1),
            "total_turns": int(session.total_turns or _total_turns()),
        },
        "turns": turns,
        "result": final_result,
    }