"""
Group interview ORM model.

MongoDB collection replaced:
  - group_interviews → GroupInterview
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class GroupInterview(Base):
    __tablename__ = "group_interviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), default="ongoing", nullable=False, index=True)

    role: Mapped[str] = mapped_column(String(256), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(32), nullable=False)

    total_turns: Mapped[int] = mapped_column(Integer, nullable=False)
    current_turn: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Dict: {id, name, track}
    active_interviewer: Mapped[dict] = mapped_column(JSONB, nullable=False)
    current_question: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # List of turn dicts: {interviewer_id, interviewer_name, interviewer_track,
    #                      question, answer, evaluation, created_at}
    turns: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Final result dict once completed
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

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