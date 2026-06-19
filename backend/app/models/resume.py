"""
Resume ORM model.

MongoDB collection replaced:
  - resumes → Resume
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)

    raw_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Full parsed resume dict (name, email, skills, experience[], education[], summary)
    parsed_resume: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # ATS analysis dict (overall_score, score_breakdown, strengths[], tips[])
    ats_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )