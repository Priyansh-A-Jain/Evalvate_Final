"""
Auth service — PostgreSQL version.

Replaces every Motor/PyMongo call in the original app/auth/service.py.
The public API (function signatures) is unchanged so callers need no edits.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AuthExchangeCode, User, UserAuthProvider

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

VERIFICATION_TOKEN_TTL_HOURS = 24
EXCHANGE_CODE_TTL_SECONDS = 60


# ── Helpers ───────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _new_verification_token() -> tuple[str, str, datetime]:
    raw = secrets.token_urlsafe(32)
    return (
        raw,
        _hash_token(raw),
        datetime.now(timezone.utc) + timedelta(hours=VERIFICATION_TOKEN_TTL_HOURS),
    )


def serialize_user(user: User) -> dict[str, Any]:
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "auth_providers": user.provider_names(),
        "email_verified": user.email_verified,
        "created_at": user.created_at,
        "last_login": user.last_login or user.created_at,
    }


# ── User fetchers ─────────────────────────────────────────────────────────────

async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        return None
    result = await db.execute(select(User).where(User.id == uid))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.strip().lower()))
    return result.scalar_one_or_none()


# ── Password auth ─────────────────────────────────────────────────────────────

async def create_password_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    name: str | None,
) -> tuple[User, str]:
    normalized = email.strip().lower()
    existing = await get_user_by_email(db, normalized)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Sign in with its existing provider.",
        )

    raw_token, token_hash, token_expires = _new_verification_token()
    now = datetime.now(timezone.utc)

    user = User(
        email=normalized,
        name=name.strip() if name and name.strip() else None,
        password_hash=hash_password(password),
        email_verified=False,
        verification_token_hash=token_hash,
        verification_token_expires=token_expires,
        last_login=now,
    )
    db.add(user)
    await db.flush()  # get user.id before adding provider

    provider = UserAuthProvider(user_id=user.id, provider="password")
    db.add(provider)
    await db.flush()

    return user, raw_token


async def authenticate_password_user(
    db: AsyncSession, *, email: str, password: str
) -> User:
    user = await get_user_by_email(db, email)
    pw_hash = user.password_hash if user else None

    if not user or not pw_hash or not verify_password(password, pw_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Verify your email before signing in", "email_verified": False},
        )

    user.last_login = datetime.now(timezone.utc)
    await db.flush()
    return user


# ── Email verification ────────────────────────────────────────────────────────

async def issue_new_verification_token(
    db: AsyncSession, *, email: str
) -> tuple[User | None, str | None]:
    user = await get_user_by_email(db, email)
    if not user or user.email_verified:
        return user, None

    raw_token, token_hash, token_expires = _new_verification_token()
    user.verification_token_hash = token_hash
    user.verification_token_expires = token_expires
    await db.flush()
    return user, raw_token


async def verify_email_token(db: AsyncSession, raw_token: str) -> User:
    now = datetime.now(timezone.utc)
    token_hash = _hash_token(raw_token)

    result = await db.execute(
        select(User).where(
            User.verification_token_hash == token_hash,
            User.verification_token_expires > now,
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link is invalid or expired",
        )

    user.email_verified = True
    user.last_login = now
    user.verification_token_hash = None
    user.verification_token_expires = None
    await db.flush()
    return user


# ── Google OAuth upsert ───────────────────────────────────────────────────────

async def upsert_google_user(
    db: AsyncSession,
    *,
    email: str,
    name: str | None,
    picture: str | None,
) -> User:
    normalized = email.strip().lower()
    now = datetime.now(timezone.utc)

    user = await get_user_by_email(db, normalized)

    if user:
        # Update mutable fields
        user.name = name
        user.picture = picture
        user.email_verified = True
        user.last_login = now
        user.verification_token_hash = None
        user.verification_token_expires = None

        # Add 'google' provider if not already present
        existing_providers = {p.provider for p in user.auth_providers}
        if "google" not in existing_providers:
            db.add(UserAuthProvider(user_id=user.id, provider="google"))
    else:
        user = User(
            email=normalized,
            name=name,
            picture=picture,
            password_hash=None,
            email_verified=True,
            last_login=now,
        )
        db.add(user)
        await db.flush()
        db.add(UserAuthProvider(user_id=user.id, provider="google"))

    await db.flush()
    await db.refresh(user)
    return user


# ── Exchange codes ────────────────────────────────────────────────────────────

async def create_exchange_code(
    db: AsyncSession, *, user_id: str, redirect_path: str
) -> str:
    raw_code = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)

    code = AuthExchangeCode(
        code_hash=_hash_token(raw_code),
        user_id=uuid.UUID(user_id),
        redirect_path=redirect_path,
        created_at=now,
        expires_at=now + timedelta(seconds=EXCHANGE_CODE_TTL_SECONDS),
    )
    db.add(code)
    await db.flush()
    return raw_code


async def consume_exchange_code(
    db: AsyncSession, raw_code: str
) -> tuple[User, str]:
    now = datetime.now(timezone.utc)
    token_hash = _hash_token(raw_code)

    result = await db.execute(
        select(AuthExchangeCode).where(
            AuthExchangeCode.code_hash == token_hash,
            AuthExchangeCode.expires_at > now,
        )
    )
    code_row = result.scalar_one_or_none()
    if not code_row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code is invalid or expired",
        )

    redirect_path = code_row.redirect_path
    user_id = code_row.user_id

    # Delete the code (one-time use)
    await db.delete(code_row)
    await db.flush()

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user, redirect_path


# ── Periodic cleanup (replaces MongoDB TTL index) ─────────────────────────────

async def purge_expired_exchange_codes(db: AsyncSession) -> int:
    """
    Delete exchange codes past their expiry. Call from a background task
    or a startup hook — runs every few minutes is fine.
    """
    now = datetime.now(timezone.utc)
    result = await db.execute(
        delete(AuthExchangeCode).where(AuthExchangeCode.expires_at <= now)
    )
    await db.flush()
    return result.rowcount  # type: ignore[return-value]


# ── Index / schema helpers (Alembic handles the real DDL) ────────────────────

async def ensure_user_indexes(db: AsyncSession) -> None:
    """
    No-op in PostgreSQL — indexes are created by Alembic migrations.
    Kept so callers in main.py don't need to change.
    """
    pass