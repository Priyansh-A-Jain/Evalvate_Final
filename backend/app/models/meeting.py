"""
Meeting room ORM models.

MongoDB collections replaced:
  - meeting_sessions      → MeetingSession        (legacy WebSocket chat)
  - meeting_room_sessions → MeetingRoomSession    (team-fit turn-based)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class MeetingSession(Base, TimestampMixin):
    """
    Legacy real-time chat meeting (WebSocket /meeting/stream).
    Replaces the meeting_sessions MongoDB collection.
    """
    __tablename__ = "meeting_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), default="ongoing", nullable=False, index=True)

    scenario_id: Mapped[str] = mapped_column(String(64), nullable=False)
    scenario_title: Mapped[str] = mapped_column(String(256), nullable=False)
    scenario_description: Mapped[str] = mapped_column(String(1024), nullable=False)
    scenario_problem_statement: Mapped[str] = mapped_column(String(2048), nullable=False)
    scenario_duration_sec: Mapped[int] = mapped_column(Integer, nullable=False)

    # Arrays stored as JSONB
    participants: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    messages: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    metrics_snapshots: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    interruptions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    final_report: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MeetingRoomSession(Base):
    """
    Turn-based team-fit meeting simulation.
    Replaces the meeting_room_sessions MongoDB collection.
    """
    __tablename__ = "meeting_room_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), default="ongoing", nullable=False, index=True)

    # Scenario + participant config
    scenario: Mapped[dict] = mapped_column(JSONB, nullable=False)
    participants: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Full question flow and conversation history
    questions: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    current_question_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conversation_log: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    final_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)