"""
Interview ORM models.

MongoDB collections replaced:
  - interviews  → Interview
  - responses   → InterviewResponse
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Interview(Base, TimestampMixin):
    __tablename__ = "interviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    role: Mapped[str] = mapped_column(String(256), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(32), nullable=False)
    persona: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="ongoing", nullable=False, index=True)

    current_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_question_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_questions: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    last_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Arrays/nested docs stored as JSONB
    questions_bank: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    questions_meta: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    session_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Adaptive follow-up budget
    dynamic_budget: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dynamic_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timed sessions
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Public sharing
    share_token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)

    # Relationships
    responses: Mapped[list["InterviewResponse"]] = relationship(
        back_populates="interview",
        cascade="all, delete-orphan",
        order_by="InterviewResponse.created_at",
    )


class InterviewResponse(Base):
    """One answered question within an interview session."""
    __tablename__ = "interview_responses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)

    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    weaknesses: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Stores the full ContradictionAnalysis dict or null
    contradiction_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        nullable=False,
        index=True,
    )

    interview: Mapped["Interview"] = relationship(back_populates="responses")