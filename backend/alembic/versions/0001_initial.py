"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("name", sa.String(120), nullable=True),
        sa.Column("picture", sa.Text(), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("verification_token_hash", sa.String(64), nullable=True),
        sa.Column("verification_token_expires", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_verification_token_hash", "users", ["verification_token_hash"])

    # ── user_auth_providers ───────────────────────────────────────────────
    op.create_table(
        "user_auth_providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )
    op.create_index("ix_user_auth_providers_user_id", "user_auth_providers", ["user_id"])

    # ── auth_exchange_codes ───────────────────────────────────────────────
    op.create_table(
        "auth_exchange_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("redirect_path", sa.String(512), nullable=False, server_default="/dashboard"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_auth_exchange_codes_code_hash", "auth_exchange_codes", ["code_hash"], unique=True)
    op.create_index("ix_auth_exchange_codes_expires_at", "auth_exchange_codes", ["expires_at"])

    # ── interviews ─────────────────────────────────────────────────────────
    op.create_table(
        "interviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("role", sa.String(256), nullable=False),
        sa.Column("difficulty", sa.String(32), nullable=False),
        sa.Column("persona", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="ongoing"),
        sa.Column("current_question", sa.Text(), nullable=True),
        sa.Column("current_question_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_questions", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("last_score", sa.Integer(), nullable=True),
        sa.Column("questions_bank", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("questions_meta", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("session_analysis", postgresql.JSONB(), nullable=True),
        sa.Column("dynamic_budget", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dynamic_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("share_token", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_interviews_user_id", "interviews", ["user_id"])
    op.create_index("ix_interviews_status", "interviews", ["status"])
    op.create_index("ix_interviews_share_token", "interviews", ["share_token"], unique=True)

    # ── interview_responses ──────────────────────────────────────────────
    op.create_table(
        "interview_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("interview_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("strengths", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("weaknesses", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("contradiction_analysis", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_interview_responses_interview_id", "interview_responses", ["interview_id"])
    op.create_index("ix_interview_responses_user_id", "interview_responses", ["user_id"])
    op.create_index("ix_interview_responses_created_at", "interview_responses", ["created_at"])

    # ── resumes ────────────────────────────────────────────────────────────
    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("content_type", sa.String(128), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("parsed_resume", postgresql.JSONB(), nullable=False),
        sa.Column("ats_analysis", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])
    op.create_index("ix_resumes_created_at", "resumes", ["created_at"])

    # ── meeting_sessions (legacy) ────────────────────────────────────────
    op.create_table(
        "meeting_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="ongoing"),
        sa.Column("scenario_id", sa.String(64), nullable=False),
        sa.Column("scenario_title", sa.String(256), nullable=False),
        sa.Column("scenario_description", sa.String(1024), nullable=False),
        sa.Column("scenario_problem_statement", sa.String(2048), nullable=False),
        sa.Column("scenario_duration_sec", sa.Integer(), nullable=False),
        sa.Column("participants", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("messages", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("metrics_snapshots", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("interruptions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("final_report", postgresql.JSONB(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_meeting_sessions_user_id", "meeting_sessions", ["user_id"])
    op.create_index("ix_meeting_sessions_status", "meeting_sessions", ["status"])

    # ── meeting_room_sessions (team-fit) ─────────────────────────────────
    op.create_table(
        "meeting_room_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="ongoing"),
        sa.Column("scenario", postgresql.JSONB(), nullable=False),
        sa.Column("participants", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("questions", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("current_question_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("conversation_log", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("final_result", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_meeting_room_sessions_user_id", "meeting_room_sessions", ["user_id"])
    op.create_index("ix_meeting_room_sessions_status", "meeting_room_sessions", ["status"])

    # ── results_analysis_snapshots ───────────────────────────────────────
    op.create_table(
        "results_analysis_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
    )
    op.create_index("ix_results_analysis_snapshots_user_id", "results_analysis_snapshots", ["user_id"], unique=True)

    # ── group_interviews ──────────────────────────────────────────────────
    op.create_table(
        "group_interviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="ongoing"),
        sa.Column("role", sa.String(256), nullable=False),
        sa.Column("difficulty", sa.String(32), nullable=False),
        sa.Column("total_turns", sa.Integer(), nullable=False),
        sa.Column("current_turn", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("active_interviewer", postgresql.JSONB(), nullable=False),
        sa.Column("current_question", sa.String(2048), nullable=True),
        sa.Column("turns", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_group_interviews_user_id", "group_interviews", ["user_id"])
    op.create_index("ix_group_interviews_status", "group_interviews", ["status"])


def downgrade() -> None:
    op.drop_table("group_interviews")
    op.drop_table("results_analysis_snapshots")
    op.drop_table("meeting_room_sessions")
    op.drop_table("meeting_sessions")
    op.drop_table("resumes")
    op.drop_table("interview_responses")
    op.drop_table("interviews")
    op.drop_table("auth_exchange_codes")
    op.drop_table("user_auth_providers")
    op.drop_table("users")