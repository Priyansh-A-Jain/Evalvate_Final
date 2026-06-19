"""
One-time data migration: MongoDB -> PostgreSQL (NeonDB).

Run AFTER `alembic upgrade head` has created all tables.

Usage:
    cd backend
    python scripts/migrate_mongo_to_postgres.py

Safe to re-run: uses INSERT ... ON CONFLICT DO NOTHING keyed on a
deterministic UUID derived from each Mongo ObjectId, so reruns skip
already-migrated rows instead of duplicating them.

Requires both MONGO_URI (old) and DATABASE_URL_SYNC (new) to be set
in backend/.env during the migration window. You can remove MONGO_URI
once this script has run successfully.
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

_BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND_DIR))
load_dotenv(_BACKEND_DIR / ".env")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker  # noqa: E402

from app.models import (  # noqa: E402
    AuthExchangeCode,
    GroupInterview,
    Interview,
    InterviewResponse,
    MeetingRoomSession,
    MeetingSession,
    Resume,
    ResultsAnalysisSnapshot,
    User,
    UserAuthProvider,
)

MONGO_URL = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
MONGO_DB_NAME = "airavat"
PG_URL = os.getenv("DATABASE_URL")  # async driver for this script

if not PG_URL:
    raise RuntimeError("DATABASE_URL is not set in backend/.env")

# Deterministic UUID5 namespace — every Mongo ObjectId maps to the SAME
# UUID every time this script runs, so re-running is idempotent and
# cross-collection references (user_id, interview_id) stay consistent.
NAMESPACE = uuid.UUID("a3f5e8c2-7b1d-4e6a-9f3c-1d2b4e6a8c0f")


def oid_to_uuid(oid) -> uuid.UUID:
    """Deterministically map a Mongo ObjectId (or any string) to a UUID."""
    return uuid.uuid5(NAMESPACE, str(oid))


def _aware(dt):
    if dt is None:
        return None
    if isinstance(dt, datetime) and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


async def migrate_users(mongo_db, pg_session_factory) -> dict[str, str]:
    """Returns mapping of mongo user_id (str) -> new UUID (str) for use by other migrators."""
    print("\n[1/9] Migrating users...")
    id_map: dict[str, str] = {}
    count = 0

    async with pg_session_factory() as session:
        async for doc in mongo_db["users"].find({}):
            new_id = oid_to_uuid(doc["_id"])
            id_map[str(doc["_id"])] = str(new_id)

            user = User(
                id=new_id,
                email=doc["email"],
                name=doc.get("name"),
                picture=doc.get("picture"),
                password_hash=doc.get("password_hash"),
                email_verified=bool(doc.get("email_verified", False)),
                verification_token_hash=doc.get("verification_token_hash"),
                verification_token_expires=_aware(doc.get("verification_token_expires")),
                last_login=_aware(doc.get("last_login")),
                created_at=_aware(doc.get("created_at")) or datetime.now(timezone.utc),
                updated_at=_aware(doc.get("updated_at")) or datetime.now(timezone.utc),
            )
            session.add(user)
            try:
                await session.flush()
            except Exception as exc:
                await session.rollback()
                print(f"    skip (exists) user {doc['email']}: {exc}")
                continue

            for provider in doc.get("auth_providers", []):
                session.add(UserAuthProvider(user_id=new_id, provider=provider))

            count += 1
        await session.commit()

    print(f"    migrated {count} users")
    return id_map


async def migrate_interviews(mongo_db, pg_session_factory, user_id_map: dict[str, str]) -> dict[str, str]:
    print("\n[2/9] Migrating interviews...")
    interview_id_map: dict[str, str] = {}
    count = 0

    async with pg_session_factory() as session:
        async for doc in mongo_db["interviews"].find({}):
            new_id = oid_to_uuid(doc["_id"])
            interview_id_map[str(doc["_id"])] = str(new_id)
            mapped_user_id = user_id_map.get(doc["user_id"], doc["user_id"])

            interview = Interview(
                id=new_id,
                user_id=mapped_user_id,
                role=doc.get("role", ""),
                difficulty=doc.get("difficulty", "medium"),
                persona=doc.get("persona", "mentor"),
                status=doc.get("status", "ongoing"),
                current_question=doc.get("current_question"),
                current_question_index=int(doc.get("current_question_index", 0)),
                max_questions=int(doc.get("max_questions", 5)),
                last_score=doc.get("last_score"),
                questions_bank=doc.get("questions_bank") or [],
                questions_meta=doc.get("questions_meta") or [],
                session_analysis=doc.get("session_analysis"),
                dynamic_budget=int(doc.get("dynamic_budget", 0)),
                dynamic_used=int(doc.get("dynamic_used", 0)),
                duration_minutes=doc.get("duration_minutes"),
                deadline_at=_aware(doc.get("deadline_at")),
                share_token=doc.get("share_token"),
                created_at=_aware(doc.get("created_at")) or datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(interview)
            try:
                await session.flush()
                count += 1
            except Exception as exc:
                await session.rollback()
                print(f"    skip (exists) interview {doc['_id']}: {exc}")
        await session.commit()

    print(f"    migrated {count} interviews")
    return interview_id_map


async def migrate_responses(mongo_db, pg_session_factory, user_id_map, interview_id_map):
    print("\n[3/9] Migrating interview responses...")
    count = 0
    async with pg_session_factory() as session:
        async for doc in mongo_db["responses"].find({}):
            mapped_interview_id = interview_id_map.get(str(doc["interview_id"]))
            if not mapped_interview_id:
                continue
            mapped_user_id = user_id_map.get(doc["user_id"], doc["user_id"])

            response = InterviewResponse(
                id=oid_to_uuid(doc["_id"]),
                interview_id=uuid.UUID(mapped_interview_id),
                user_id=mapped_user_id,
                question=doc.get("question", ""),
                answer=doc.get("answer", ""),
                score=doc.get("score"),
                feedback=doc.get("feedback"),
                strengths=doc.get("strengths") or [],
                weaknesses=doc.get("weaknesses") or [],
                contradiction_analysis=doc.get("contradiction_analysis"),
                created_at=_aware(doc.get("created_at")) or datetime.now(timezone.utc),
            )
            session.add(response)
            try:
                await session.flush()
                count += 1
            except Exception:
                await session.rollback()
        await session.commit()
    print(f"    migrated {count} responses")


async def migrate_resumes(mongo_db, pg_session_factory, user_id_map):
    print("\n[4/9] Migrating resumes...")
    count = 0
    async with pg_session_factory() as session:
        async for doc in mongo_db["resumes"].find({}):
            mapped_user_id = user_id_map.get(doc.get("user_id"), doc.get("user_id"))
            resume = Resume(
                id=oid_to_uuid(doc["_id"]),
                user_id=mapped_user_id,
                filename=doc.get("filename", "unknown"),
                content_type=doc.get("content_type"),
                raw_text=doc.get("raw_text", ""),
                parsed_resume=doc.get("parsed_resume") or {},
                ats_analysis=doc.get("ats_analysis"),
                created_at=_aware(doc.get("created_at")) or datetime.now(timezone.utc),
            )
            session.add(resume)
            try:
                await session.flush()
                count += 1
            except Exception:
                await session.rollback()
        await session.commit()
    print(f"    migrated {count} resumes")


async def migrate_group_interviews(mongo_db, pg_session_factory, user_id_map):
    print("\n[5/9] Migrating group interviews...")
    count = 0
    async with pg_session_factory() as session:
        async for doc in mongo_db["group_interviews"].find({}):
            mapped_user_id = user_id_map.get(doc.get("user_id"), doc.get("user_id"))
            row = GroupInterview(
                id=oid_to_uuid(doc["_id"]),
                user_id=mapped_user_id,
                status=doc.get("status", "ongoing"),
                role=doc.get("role", ""),
                difficulty=doc.get("difficulty", "medium"),
                total_turns=int(doc.get("total_turns", 9)),
                current_turn=int(doc.get("current_turn", 1)),
                active_interviewer=doc.get("active_interviewer") or {},
                current_question=doc.get("current_question"),
                turns=doc.get("turns") or [],
                result=doc.get("result"),
                created_at=_aware(doc.get("created_at")) or datetime.now(timezone.utc),
                updated_at=_aware(doc.get("updated_at")) or datetime.now(timezone.utc),
                completed_at=_aware(doc.get("completed_at")),
            )
            session.add(row)
            try:
                await session.flush()
                count += 1
            except Exception:
                await session.rollback()
        await session.commit()
    print(f"    migrated {count} group interviews")


async def migrate_meeting_sessions(mongo_db, pg_session_factory, user_id_map):
    print("\n[6/9] Migrating legacy meeting sessions...")
    count = 0
    async with pg_session_factory() as session:
        async for doc in mongo_db["meeting_sessions"].find({}):
            mapped_user_id = user_id_map.get(doc.get("user_id"), doc.get("user_id"))
            row = MeetingSession(
                id=oid_to_uuid(doc["_id"]),
                user_id=mapped_user_id,
                status=doc.get("status", "ongoing"),
                scenario_id=doc.get("scenario_id", ""),
                scenario_title=doc.get("scenario_title", ""),
                scenario_description=doc.get("scenario_description", ""),
                scenario_problem_statement=doc.get("scenario_problem_statement", ""),
                scenario_duration_sec=int(doc.get("scenario_duration_sec", 0)),
                participants=doc.get("participants") or [],
                messages=doc.get("messages") or [],
                metrics_snapshots=doc.get("metrics_snapshots") or [],
                interruptions=int(doc.get("interruptions", 0)),
                final_report=doc.get("final_report"),
                started_at=_aware(doc.get("started_at")) or datetime.now(timezone.utc),
                ended_at=_aware(doc.get("ended_at")),
                created_at=_aware(doc.get("started_at")) or datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(row)
            try:
                await session.flush()
                count += 1
            except Exception:
                await session.rollback()
        await session.commit()
    print(f"    migrated {count} legacy meeting sessions")


async def migrate_meeting_room_sessions(mongo_db, pg_session_factory, user_id_map):
    print("\n[7/9] Migrating team-fit meeting room sessions...")
    count = 0
    async with pg_session_factory() as session:
        async for doc in mongo_db["meeting_room_sessions"].find({}):
            mapped_user_id = user_id_map.get(doc.get("user_id"), doc.get("user_id"))
            row = MeetingRoomSession(
                id=oid_to_uuid(doc["_id"]),
                user_id=mapped_user_id,
                status=doc.get("status", "ongoing"),
                scenario=doc.get("scenario") or {},
                participants=doc.get("participants") or [],
                questions=doc.get("questions") or [],
                current_question_index=int(doc.get("current_question_index", 0)),
                conversation_log=doc.get("conversation_log") or [],
                final_result=doc.get("final_result"),
                created_at=_aware(doc.get("created_at")) or datetime.now(timezone.utc),
                updated_at=_aware(doc.get("updated_at")) or datetime.now(timezone.utc),
                completed_at=_aware(doc.get("completed_at")),
            )
            session.add(row)
            try:
                await session.flush()
                count += 1
            except Exception:
                await session.rollback()
        await session.commit()
    print(f"    migrated {count} team-fit meeting sessions")


async def migrate_results_snapshots(mongo_db, pg_session_factory, user_id_map):
    print("\n[8/9] Migrating results analysis snapshots...")
    count = 0
    async with pg_session_factory() as session:
        async for doc in mongo_db["results_analysis_snapshots"].find({}):
            mapped_user_id = user_id_map.get(doc.get("user_id"), doc.get("user_id"))
            payload = {k: v for k, v in doc.items() if k not in {"_id", "user_id", "updated_at"}}

            # JSON-safe: stringify any stray datetimes
            def _json_safe(value):
                if isinstance(value, datetime):
                    return value.isoformat()
                if isinstance(value, dict):
                    return {k: _json_safe(v) for k, v in value.items()}
                if isinstance(value, list):
                    return [_json_safe(v) for v in value]
                return value

            row = ResultsAnalysisSnapshot(
                id=oid_to_uuid(doc["_id"]),
                user_id=mapped_user_id,
                generated_at=_aware(doc.get("generated_at")) or datetime.now(timezone.utc),
                updated_at=_aware(doc.get("updated_at")) or datetime.now(timezone.utc),
                payload=_json_safe(payload),
            )
            session.add(row)
            try:
                await session.flush()
                count += 1
            except Exception:
                await session.rollback()
        await session.commit()
    print(f"    migrated {count} results snapshots")


async def main():
    print("=" * 70)
    print("MongoDB -> PostgreSQL (NeonDB) Data Migration")
    print("=" * 70)

    mongo_client = AsyncIOMotorClient(MONGO_URL)
    mongo_db = mongo_client[MONGO_DB_NAME]

    pg_engine = create_async_engine(PG_URL, pool_pre_ping=True)
    pg_session_factory = async_sessionmaker(bind=pg_engine, expire_on_commit=False)

    # Verify connectivity first
    try:
        await mongo_client.admin.command("ping")
        print("✓ MongoDB connection OK")
    except Exception as exc:
        print(f"✗ Cannot reach MongoDB: {exc}")
        return

    async with pg_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    print("✓ PostgreSQL connection OK")

    user_id_map = await migrate_users(mongo_db, pg_session_factory)
    interview_id_map = await migrate_interviews(mongo_db, pg_session_factory, user_id_map)
    await migrate_responses(mongo_db, pg_session_factory, user_id_map, interview_id_map)
    await migrate_resumes(mongo_db, pg_session_factory, user_id_map)
    await migrate_group_interviews(mongo_db, pg_session_factory, user_id_map)
    await migrate_meeting_sessions(mongo_db, pg_session_factory, user_id_map)
    await migrate_meeting_room_sessions(mongo_db, pg_session_factory, user_id_map)
    await migrate_results_snapshots(mongo_db, pg_session_factory, user_id_map)

    print("\n[9/9] Done.")
    print("=" * 70)
    print("Migration complete. Verify row counts in NeonDB, then run:")
    print("  python scripts/smoke_test_interview.py")
    print("=" * 70)

    mongo_client.close()
    await pg_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())