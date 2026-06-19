"""
User-related ORM models.

MongoDB collections replaced:
  - users                 → User + UserAuthProvider
  - auth_exchange_codes   → AuthExchangeCode
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    picture: Mapped[str | None] = mapped_column(Text, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Email verification (null once verified)
    verification_token_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    verification_token_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    auth_providers: Mapped[list["UserAuthProvider"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    exchange_codes: Mapped[list["AuthExchangeCode"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def provider_names(self) -> list[str]:
        return [p.provider for p in self.auth_providers]


class UserAuthProvider(Base):
    """
    Replaces the auth_providers array field in MongoDB.
    Each row = one provider (e.g. 'google', 'password').
    """
    __tablename__ = "user_auth_providers"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)  # 'google' | 'password'

    user: Mapped["User"] = relationship(back_populates="auth_providers")


class AuthExchangeCode(Base):
    """
    Short-lived one-time codes issued after Google OAuth, consumed by the
    frontend to exchange for JWT tokens.

    Replaces the auth_exchange_codes MongoDB collection.
    TTL was handled by a MongoDB TTL index; here we check expires_at at
    query time and run a periodic cleanup (see app/db.py).
    """
    __tablename__ = "auth_exchange_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    redirect_path: Mapped[str] = mapped_column(String(512), default="/dashboard", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    user: Mapped["User"] = relationship(back_populates="exchange_codes")