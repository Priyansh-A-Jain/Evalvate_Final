"""
Meeting room service — PostgreSQL version.
Replaces Motor calls in app/meeting_room/service.py and meeting_engine.py.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.meeting_room.evaluation_engine import aggregate_session_result, evaluate_response
from app.meeting_room.scenario_manager import (
    build_participants,
    build_question_flow,
    build_scenario_payload,
    list_scenarios,
)
from app.meeting_room.scenarios import SCENARIOS
from app.meeting_room.speech_service import synthesize_text_to_data_uri, transcribe_audio_base64
from app.models.meeting import MeetingRoomSession, MeetingSession


def _parse_uuid(raw: str, field: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(raw)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field}") from exc


# ── Legacy meeting session (WebSocket chat) ───────────────────────────────────

async def ensure_meeting_indexes(db: AsyncSession) -> None:
    """No-op — indexes managed by Alembic."""
    pass


async def start_session(db: AsyncSession, scenario_id: str, user_id: str) -> dict[str, Any]:
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown scenario: {scenario_id}")

    session = MeetingSession(
        user_id=user_id,
        scenario_id=scenario.id,
        scenario_title=scenario.title,
        scenario_description=scenario.description,
        scenario_problem_statement=scenario.problem_statement,
        scenario_duration_sec=scenario.duration_sec,
        participants=[p.model_dump() for p in scenario.participants],
        messages=[],
        metrics_snapshots=[],
        interruptions=0,
        status="ongoing",
        started_at=datetime.now(timezone.utc),
    )
    db.add(session)
    await db.flush()

    return {
        "session_id": str(session.id),
        "scenario": {
            "id": scenario.id,
            "title": scenario.title,
            "description": scenario.description,
            "problem_statement": scenario.problem_statement,
            "duration_sec": scenario.duration_sec,
        },
        "participants": [p.model_dump() for p in scenario.participants],
    }


async def get_session(db: AsyncSession, session_id_raw: str, user_id: str) -> dict[str, Any]:
    session_uuid = _parse_uuid(session_id_raw, "session_id")
    result = await db.execute(select(MeetingSession).where(MeetingSession.id == session_uuid))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to access this session")

    return {
        "session_id": str(session.id),
        "user_id": session.user_id,
        "scenario": {
            "id": session.scenario_id,
            "title": session.scenario_title,
            "description": session.scenario_description,
            "problem_statement": session.scenario_problem_statement,
            "duration_sec": session.scenario_duration_sec,
        },
        "participants": session.participants,
        "status": session.status,
        "messages": session.messages,
        "metrics_snapshots": session.metrics_snapshots,
        "interruptions": session.interruptions,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
    }


async def append_message(
    db: AsyncSession,
    session_id: uuid.UUID,
    *,
    sender_id: str,
    sender_name: str,
    sender_role: str,
    text: str,
) -> dict[str, Any]:
    import uuid as _uuid
    result = await db.execute(select(MeetingSession).where(MeetingSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    msg = {
        "id": str(_uuid.uuid4()),
        "sender_id": sender_id,
        "sender_name": sender_name,
        "sender_role": sender_role,
        "text": text,
        "timestamp": datetime.now(timezone.utc).timestamp(),
    }
    # JSONB mutation: reassign to trigger SQLAlchemy change detection
    session.messages = list(session.messages or []) + [msg]
    await db.flush()
    return msg


async def append_metrics(db: AsyncSession, session_id: uuid.UUID, snapshot: dict) -> None:
    result = await db.execute(select(MeetingSession).where(MeetingSession.id == session_id))
    session = result.scalar_one_or_none()
    if session:
        session.metrics_snapshots = list(session.metrics_snapshots or []) + [snapshot]
        await db.flush()


async def increment_interruptions(db: AsyncSession, session_id: uuid.UUID) -> None:
    result = await db.execute(select(MeetingSession).where(MeetingSession.id == session_id))
    session = result.scalar_one_or_none()
    if session:
        session.interruptions = (session.interruptions or 0) + 1
        await db.flush()


async def end_session(db: AsyncSession, session_id: uuid.UUID, report: dict) -> None:
    result = await db.execute(select(MeetingSession).where(MeetingSession.id == session_id))
    session = result.scalar_one_or_none()
    if session:
        session.status = "completed"
        session.ended_at = datetime.now(timezone.utc)
        session.final_report = report
        await db.flush()


async def get_report(db: AsyncSession, session_id_raw: str, user_id: str) -> dict[str, Any]:
    session_uuid = _parse_uuid(session_id_raw, "session_id")
    result = await db.execute(select(MeetingSession).where(MeetingSession.id == session_uuid))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to access this session")
    if not session.final_report:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session has not been completed yet")
    return {"session_id": str(session.id), "report": session.final_report}


# ── Team-fit meeting (turn-based) ─────────────────────────────────────────────

def _serialize_question(question: dict, audio_data_uri: str | None = None) -> dict:
    return {
        "speaker": question["speaker"],
        "question": question["question"],
        "intent": question["intent"],
        "audio_data_uri": audio_data_uri,
        "suggested_delay_ms": random.randint(900, 1700),
    }


def _build_interruption(question: dict, participants: list[dict]) -> dict | None:
    if random.random() > 0.22:
        return None
    candidates = [p for p in participants if p.get("name") != question["speaker"]]
    if not candidates:
        return None
    interrupter = random.choice(candidates)
    return {
        "speaker": interrupter["name"],
        "question": "Quick follow-up before we move on: who owns the immediate next action?",
        "intent": "interruption",
        "audio_data_uri": None,
        "suggested_delay_ms": random.randint(500, 900),
    }


async def get_available_scenarios() -> list[dict[str, str]]:
    return list_scenarios()


async def start_teamfit_session(
    db: AsyncSession, user_id: str, scenario_id: str, custom_context: str | None = None
) -> dict[str, Any]:
    scenario = build_scenario_payload(scenario_id, custom_context)
    participants = build_participants()
    question_flow = build_question_flow(scenario_id, custom_context)

    if not question_flow:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Scenario question flow is empty")

    first_question = question_flow[0]
    first_audio = await synthesize_text_to_data_uri(first_question["question"])

    now = datetime.now(timezone.utc)
    session = MeetingRoomSession(
        user_id=user_id,
        scenario=scenario,
        participants=participants,
        questions=question_flow,
        current_question_index=0,
        conversation_log=[],
        status="ongoing",
        created_at=now,
        updated_at=now,
    )
    db.add(session)
    await db.flush()

    return {
        "session_id": str(session.id),
        "status": "ongoing",
        "scenario": scenario,
        "participants": participants,
        "question": _serialize_question(first_question, first_audio),
        "progress": {"answered": 0, "total": len(question_flow)},
    }


async def respond_teamfit_session(
    db: AsyncSession, user_id: str, session_id: str,
    answer_text: str | None = None, audio_base64: str | None = None, audio_mime_type: str | None = None,
) -> dict[str, Any]:
    session_uuid = _parse_uuid(session_id, "session_id")
    result = await db.execute(select(MeetingRoomSession).where(MeetingRoomSession.id == session_uuid))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to access this session")
    if session.status == "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is already completed")

    questions = session.questions or []
    idx = int(session.current_question_index or 0)
    if idx >= len(questions):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No remaining questions")

    transcript = (answer_text or "").strip()
    if not transcript and audio_base64:
        transcript = (await transcribe_audio_base64(audio_base64, audio_mime_type)).strip()
    if not transcript:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transcript is empty.")

    active_question = questions[idx]
    evaluation = await evaluate_response(
        question=active_question["question"],
        intent=active_question["intent"],
        answer=transcript,
    )

    now = datetime.now(timezone.utc)
    turn = {
        "question_index": idx,
        "speaker": active_question["speaker"],
        "question": active_question["question"],
        "intent": active_question["intent"],
        "answer_text": transcript,
        "evaluation": evaluation,
        "created_at": now.isoformat(),
    }
    turns = list(session.conversation_log or []) + [turn]
    next_index = idx + 1

    next_question_payload = None
    interruption = None
    status_value = "ongoing"

    if next_index >= len(questions):
        final_result = aggregate_session_result(turns)
        session.conversation_log = turns
        session.status = "completed"
        session.current_question_index = len(questions)
        session.completed_at = now
        session.final_result = final_result
        session.updated_at = now
        status_value = "completed"
    else:
        next_question = questions[next_index]
        next_audio = await synthesize_text_to_data_uri(next_question["question"])
        next_question_payload = _serialize_question(next_question, next_audio)
        interruption = _build_interruption(next_question, session.participants or [])
        session.conversation_log = turns
        session.current_question_index = next_index
        session.updated_at = now

    await db.flush()

    return {
        "session_id": session_id,
        "status": status_value,
        "transcript": transcript,
        "evaluation": evaluation,
        "next_question": next_question_payload,
        "progress": {"answered": len(turns), "total": len(questions)},
        "interruption": interruption,
    }


async def get_teamfit_result(db: AsyncSession, user_id: str, session_id: str) -> dict[str, Any]:
    session_uuid = _parse_uuid(session_id, "session_id")
    result = await db.execute(select(MeetingRoomSession).where(MeetingRoomSession.id == session_uuid))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to access this session")

    turns = list(session.conversation_log or [])
    final_result = session.final_result or aggregate_session_result(turns)
    questions = session.questions or []

    return {
        "session_id": session_id,
        "status": session.status,
        "progress": {"answered": len(turns), "total": len(questions)},
        "result": final_result,
        "conversation_history": turns,
    }