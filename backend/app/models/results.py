"""
Results analysis snapshot ORM model.

MongoDB collection replaced:
  - results_analysis_snapshots → ResultsAnalysisSnapshot
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ResultsAnalysisSnapshot(Base):
    """
    Cached results analytics per user. Invalidated and regenerated
    whenever a new session_analysis is saved or a refresh is forced.
    """
    __tablename__ = "results_analysis_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # One snapshot per user (unique index enforces this)
    user_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # The entire analysis result stored as JSONB (matches ResultsAnalysisResponse schema)
    # Keys: overview, score_trend, communication_trend, weaknesses, strengths,
    #       role_breakdown, session_snapshots, llm_insights
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)