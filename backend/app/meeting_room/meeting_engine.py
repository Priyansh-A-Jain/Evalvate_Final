"""
Meeting engine — PostgreSQL version.

NOTE: All logic now lives in app/meeting_room/service.py (start_teamfit_session,
respond_teamfit_session, get_teamfit_result, get_available_scenarios,
ensure_teamfit_indexes). This file re-exports them so existing imports
(`from app.meeting_room.meeting_engine import ...`) keep working unchanged.
"""

from app.meeting_room.service import (
    ensure_meeting_indexes as ensure_teamfit_indexes,  # Alembic handles both now
    get_available_scenarios,
    get_teamfit_result,
    respond_teamfit_session,
    start_teamfit_session,
)

__all__ = [
    "ensure_teamfit_indexes",
    "get_available_scenarios",
    "start_teamfit_session",
    "respond_teamfit_session",
    "get_teamfit_result",
]