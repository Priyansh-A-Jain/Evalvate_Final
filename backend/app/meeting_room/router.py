"""
Meeting Room Router — HTTP endpoints + WebSocket for real-time meeting simulation.
PostgreSQL version.
"""

import asyncio
import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal, get_db
from app.middlewares.auth_context import get_authenticated_user_id
from app.auth.jwt import decode_token
from app.models.user import User

from app.meeting_room.schemas import (
    StartSessionRequest,
    StartSessionResponse,
    SessionDetailResponse,
    EndSessionResponse,
    SessionReportResponse,
)
from app.meeting_room.teamfit_schemas import (
    MeetingScenarioOut,
    StartTeamMeetingRequest,
    StartTeamMeetingResponse,
    RespondMeetingRequest,
    RespondMeetingResponse,
    MeetingResultResponse,
)
from app.meeting_room.service import (
    start_session,
    get_session,
    append_message,
    append_metrics,
    increment_interruptions,
    end_session,
    get_report,
)
from app.meeting_room.meeting_engine import (
    get_available_scenarios,
    start_teamfit_session,
    respond_teamfit_session,
    get_teamfit_result,
)
from app.meeting_room.ai_engine import get_ai_reply, generate_meeting_report
from app.meeting_room.metrics import MetricsAggregator
from app.meeting_room.scenarios import SCENARIOS
from app.models.meeting import MeetingSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meeting", tags=["Meeting Room"])
team_fit_router = APIRouter(prefix="/meeting-room", tags=["Meeting Room Team Fit"])


# ── HTTP Endpoints ───────────────────────────────────────────────────


@team_fit_router.get("/scenarios", response_model=list[MeetingScenarioOut])
async def list_teamfit_scenarios(
    user_id: str = Depends(get_authenticated_user_id),
):
    del user_id
    return await get_available_scenarios()


@team_fit_router.post("/start", response_model=StartTeamMeetingResponse)
async def start_teamfit(
    payload: StartTeamMeetingRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id),
):
    return await start_teamfit_session(
        db=db,
        user_id=user_id,
        scenario_id=payload.scenario_id,
        custom_context=payload.custom_context,
    )


@team_fit_router.post("/respond", response_model=RespondMeetingResponse)
async def respond_teamfit(
    payload: RespondMeetingRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id),
):
    return await respond_teamfit_session(
        db=db,
        user_id=user_id,
        session_id=payload.session_id,
        answer_text=payload.answer_text,
        audio_base64=payload.audio_base64,
        audio_mime_type=payload.audio_mime_type,
    )


@team_fit_router.get("/result", response_model=MeetingResultResponse)
async def teamfit_result(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id),
):
    return await get_teamfit_result(db=db, user_id=user_id, session_id=session_id)


# ── Legacy HTTP Endpoints ─────────────────────────────────────────────


@router.post("/start", response_model=StartSessionResponse)
async def start_meeting(
    payload: StartSessionRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id),
):
    return await start_session(db, payload.scenario_id, user_id)


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_meeting(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id),
):
    return await get_session(db, session_id, user_id)


@router.post("/{session_id}/end", response_model=EndSessionResponse)
async def end_meeting(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id),
):
    session_data = await get_session(db, session_id, user_id)

    if session_data["status"] == "completed":
        report = session_data.get("final_report")
        if not report:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session already completed",
            )
        return {
            "session_id": session_id,
            "status": "completed",
            "report": report,
        }

    metrics_snapshots = session_data.get("metrics_snapshots", [])
    final_metrics = metrics_snapshots[-1] if metrics_snapshots else {
        "confidence": 70, "helpfulness": 72, "engagement": 74
    }

    report = await generate_meeting_report(
        scenario_title=session_data["scenario"]["title"],
        scenario_prompt=session_data["scenario"]["problem_statement"],
        messages=session_data.get("messages", []),
        final_metrics=final_metrics,
        interruptions=session_data.get("interruptions", 0),
    )

    session_uuid = uuid.UUID(session_id)
    await end_session(db, session_uuid, report)

    return {
        "session_id": session_id,
        "status": "completed",
        "report": report,
    }


@router.get("/{session_id}/report", response_model=SessionReportResponse)
async def get_meeting_report(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id),
):
    return await get_report(db, session_id, user_id)


# ── WebSocket Helpers ────────────────────────────────────────────────


async def _get_ws_user(websocket: WebSocket) -> User | None:
    """Authenticate WebSocket user from cookie or query param."""
    access_token = websocket.cookies.get("access_token")
    if not access_token:
        access_token = websocket.query_params.get("token")

    if not access_token:
        return None

    try:
        payload = decode_token(token=access_token, expected_type="access")
        user_uuid = uuid.UUID(payload["user_id"])
    except Exception as e:
        logger.error(f"WS meeting auth error: {e}")
        return None

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_uuid))
        return result.scalar_one_or_none()


def _pick_responder(participants: list[dict], recent_messages: list[dict]) -> dict | None:
    if not participants:
        return None

    ai_participants = [p for p in participants if p.get("id", "").startswith("ai-")]
    if not ai_participants:
        return None

    recent_speaker_ids = set()
    for msg in recent_messages[-3:]:
        sid = msg.get("sender_id", "")
        if sid.startswith("ai-"):
            recent_speaker_ids.add(sid)

    candidates = [p for p in ai_participants if p["id"] not in recent_speaker_ids]
    if not candidates:
        candidates = ai_participants

    import random
    return random.choice(candidates)


# ── WebSocket Endpoint ───────────────────────────────────────────────


@router.websocket("/stream")
async def meeting_stream(websocket: WebSocket):
    await websocket.accept()

    user = await _get_ws_user(websocket)
    if not user:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Unauthorized",
        )
        return

    user_id = str(user.id)
    logger.info(f"[Meeting WS] User {user_id} connected")

    aggregator = MetricsAggregator()
    session_uuid: uuid.UUID | None = None
    session_data: dict[str, Any] = {}
    candidate_msg_count = 0
    total_interruptions = 0

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            # ── INIT: client sends session_id on connect ─────────
            if msg_type == "init":
                sid = msg.get("session_id", "")
                try:
                    async with AsyncSessionLocal() as db:
                        session_data = await get_session(db, sid, user_id)
                        await db.commit()
                    session_uuid = uuid.UUID(sid)
                    candidate_msg_count = len([
                        m for m in session_data.get("messages", [])
                        if m.get("sender_id") == "candidate"
                    ])
                    total_interruptions = session_data.get("interruptions", 0)
                    await websocket.send_text(json.dumps({
                        "type": "init_ok",
                        "session_id": sid,
                    }))
                except HTTPException as e:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "detail": e.detail,
                    }))
                continue

            if session_uuid is None:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "detail": "Send init with session_id first",
                }))
                continue

            # ── CHAT: candidate sends a message ──────────────────
            if msg_type == "chat":
                text = msg.get("text", "").strip()
                if not text:
                    continue

                candidate_msg_count += 1

                async with AsyncSessionLocal() as db:
                    await append_message(
                        db, session_uuid,
                        sender_id="candidate",
                        sender_name=user.name or "You",
                        sender_role="Candidate",
                        text=text,
                    )
                    await db.commit()

                    result = await db.execute(select(MeetingSession).where(MeetingSession.id == session_uuid))
                    sess = result.scalar_one_or_none()
                    all_messages = sess.messages if sess else []

                participants = session_data.get("participants", [])
                responder = _pick_responder(participants, all_messages)

                if responder:
                    await websocket.send_text(json.dumps({
                        "type": "ai_typing",
                        "participant_id": responder["id"],
                    }))

                    scenario = SCENARIOS.get(session_data.get("scenario", {}).get("id", ""))
                    scenario_prompt = scenario.problem_statement if scenario else ""

                    reply_text = await get_ai_reply(
                        responder_name=responder["name"],
                        responder_role=responder["role"],
                        responder_personality=responder.get("personality", ""),
                        scenario_prompt=scenario_prompt,
                        recent_messages=all_messages[-10:],
                    )

                    async with AsyncSessionLocal() as db:
                        ai_msg = await append_message(
                            db, session_uuid,
                            sender_id=responder["id"],
                            sender_name=responder["name"],
                            sender_role=responder["role"],
                            text=reply_text,
                        )
                        await db.commit()

                    await websocket.send_text(json.dumps({
                        "type": "ai_message",
                        "participant_id": responder["id"],
                        "sender_name": responder["name"],
                        "sender_role": responder["role"],
                        "text": reply_text,
                        "message_id": ai_msg["id"],
                        "timestamp": ai_msg["timestamp"],
                    }))

                continue

            # ── METRICS_TICK: frontend sends video/voice scores ──
            if msg_type == "metrics_tick":
                snapshot = aggregator.update(
                    elapsed_sec=msg.get("elapsed_sec", 0),
                    video_confidence=msg.get("video_confidence"),
                    video_engagement=msg.get("video_engagement"),
                    voice_confidence=msg.get("voice_confidence"),
                    voice_stress=msg.get("voice_stress"),
                    candidate_message_count=candidate_msg_count,
                    interruptions=total_interruptions,
                )

                elapsed = msg.get("elapsed_sec", 0)
                if elapsed % 10 == 0:
                    async with AsyncSessionLocal() as db:
                        await append_metrics(db, session_uuid, snapshot)
                        await db.commit()

                await websocket.send_text(json.dumps({
                    "type": "metrics_update",
                    **snapshot,
                }))
                continue

            # ── INTERRUPTION: client flagged an interruption ──────
            if msg_type == "interruption":
                total_interruptions += 1
                async with AsyncSessionLocal() as db:
                    await increment_interruptions(db, session_uuid)
                    await db.commit()
                continue

            # ── END: client ends the session ─────────────────────
            if msg_type == "end":
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(MeetingSession).where(MeetingSession.id == session_uuid))
                    sess = result.scalar_one_or_none()
                    all_messages = sess.messages if sess else []
                final_snap = aggregator.snapshot()

                report = await generate_meeting_report(
                    scenario_title=session_data.get("scenario", {}).get("title", ""),
                    scenario_prompt=session_data.get("scenario", {}).get("problem_statement", ""),
                    messages=all_messages,
                    final_metrics=final_snap,
                    interruptions=total_interruptions,
                )

                async with AsyncSessionLocal() as db:
                    await end_session(db, session_uuid, report)
                    await db.commit()

                await websocket.send_text(json.dumps({
                    "type": "final_report",
                    "report": report,
                }))
                break

    except WebSocketDisconnect:
        logger.info(f"[Meeting WS] User {user_id} disconnected")
    except Exception as e:
        logger.error(f"[Meeting WS] Error: {e}", exc_info=True)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass