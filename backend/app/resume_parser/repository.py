"""
Resume parser repository — PostgreSQL version.

Replaces the PyMongo sync repository. Note: the original used a sync
Database (get_sync_database) because UploadFile processing happened in a
sync context. We now use the same AsyncSession as everything else —
the resume_parser/router.py and service.py callers are updated accordingly.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume


async def ensure_resume_indexes(db: AsyncSession) -> None:
    """No-op — indexes managed by Alembic."""
    pass


def build_resume_document(
    *,
    parsed_resume: dict,
    ats_analysis: dict | None,
    raw_text: str,
    filename: str,
    content_type: str | None,
    user_id: str | None,
) -> Resume:
    return Resume(
        user_id=user_id,
        filename=filename,
        content_type=content_type,
        raw_text=raw_text,
        parsed_resume=parsed_resume,
        ats_analysis=ats_analysis,
        created_at=datetime.now(timezone.utc),
    )


def serialize_resume_document(doc: Resume) -> dict[str, Any]:
    return {
        "resume_id": str(doc.id),
        "parsed_resume": doc.parsed_resume,
        "ats_analysis": doc.ats_analysis,
        "created_at": doc.created_at,
        "filename": doc.filename,
        "content_type": doc.content_type,
    }


async def get_latest_resume_for_user(*, db: AsyncSession, user_id: str) -> Resume | None:
    result = await db.execute(
        select(Resume)
        .where(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def delete_resumes_for_user(*, db: AsyncSession, user_id: str) -> int:
    result = await db.execute(select(Resume).where(Resume.user_id == user_id))
    rows = result.scalars().all()
    count = len(rows)
    for row in rows:
        await db.delete(row)
    await db.flush()
    return count