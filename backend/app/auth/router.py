"""
Auth router — PostgreSQL version.

All Motor/PyMongo calls replaced with SQLAlchemy AsyncSession.
Rate-limiting logic and OAuth flow are unchanged.
"""

import os
import time
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.config import auth_settings
from app.auth.cookies import clear_auth_cookies
from app.auth.dependencies import get_current_user
from app.auth.email_service import send_verification_email
from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.auth.oauth_client import oauth
from app.auth.schemas import (
    AuthResponse,
    ExchangeRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    ResendVerificationRequest,
    UserOut,
)
from app.auth.service import (
    authenticate_password_user,
    consume_exchange_code,
    create_exchange_code,
    create_password_user,
    get_user_by_id,
    issue_new_verification_token,
    serialize_user,
    upsert_google_user,
    verify_email_token,
)
from app.db import get_db
from app.models.user import User

router = APIRouter(tags=["auth"])

_attempt_log: dict[str, list[float]] = {}
_AUTH_ATTEMPTS_PER_WINDOW = 5
_AUTH_WINDOW_SECONDS = 15 * 60
_DEMO_LOGINS_PER_HOUR = 10


def _demo_mode_enabled() -> bool:
    return (os.getenv("DEMO_MODE") or "").strip().lower() in {"1", "true", "yes", "on"}


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


def _enforce_rate_limit(
    request: Request, *, bucket: str, limit: int, window_seconds: int
) -> None:
    now = time.time()
    key = f"{bucket}:{_client_ip(request)}"
    recent = [t for t in _attempt_log.get(key, []) if t > now - window_seconds]
    if len(recent) >= limit:
        _attempt_log[key] = recent
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please try again later.",
        )
    recent.append(now)
    _attempt_log[key] = recent


def _safe_redirect_path(value: str | None) -> str:
    if value and value.startswith("/") and not value.startswith("//"):
        return value
    return "/dashboard"


def _tokens_for_user(user: User) -> tuple[str, str]:
    user_id = str(user.id)
    return (
        create_access_token(user_id=user_id, email=user.email),
        create_refresh_token(user_id=user_id, email=user.email),
    )


def _auth_payload(user: User, *, redirect_path: str | None = None) -> dict:
    access_token, refresh_token = _tokens_for_user(user)
    payload: dict = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": serialize_user(user),
    }
    if redirect_path is not None:
        payload["redirect"] = redirect_path
    return payload


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/auth/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    _enforce_rate_limit(request, bucket="register", limit=_AUTH_ATTEMPTS_PER_WINDOW, window_seconds=_AUTH_WINDOW_SECONDS)
    user, raw_token = await create_password_user(db, email=payload.email, password=payload.password, name=payload.name)
    await send_verification_email(email=user.email, name=user.name, raw_token=raw_token)
    return {"message": "Account created. Check your email to verify your account.", "email": user.email}


@router.post("/auth/login", response_model=AuthResponse)
async def password_login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    _enforce_rate_limit(request, bucket="login", limit=_AUTH_ATTEMPTS_PER_WINDOW, window_seconds=_AUTH_WINDOW_SECONDS)
    user = await authenticate_password_user(db, email=payload.email, password=payload.password)
    return _auth_payload(user)


@router.get("/auth/verify-email", response_model=AuthResponse)
async def verify_email(
    token: str = Query(min_length=20, max_length=256),
    db: AsyncSession = Depends(get_db),
):
    user = await verify_email_token(db, token)
    return _auth_payload(user)


@router.post("/auth/resend-verification")
async def resend_verification(
    payload: ResendVerificationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    _enforce_rate_limit(request, bucket="resend", limit=3, window_seconds=_AUTH_WINDOW_SECONDS)
    user, raw_token = await issue_new_verification_token(db, email=payload.email)
    if user and raw_token:
        await send_verification_email(email=user.email, name=user.name, raw_token=raw_token)
    return {"message": "If the account needs verification, a new email has been sent."}


@router.get("/demo/login")
async def demo_login(
    request: Request,
    redirect: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    if not _demo_mode_enabled():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo mode is not enabled")
    _enforce_rate_limit(request, bucket="demo", limit=_DEMO_LOGINS_PER_HOUR, window_seconds=60 * 60)
    user = await upsert_google_user(db, email="demo@evalvate.dev", name="Evalvate Demo", picture=None)
    code = await create_exchange_code(db, user_id=str(user.id), redirect_path=_safe_redirect_path(redirect))
    callback_url = f"{auth_settings.post_login_redirect_url.rstrip('/')}/auth/callback"
    return RedirectResponse(url=f"{callback_url}?{urlencode({'code': code})}", status_code=status.HTTP_302_FOUND)


@router.get("/login")
async def login(request: Request, redirect: str | None = None):
    request.session["post_auth_redirect"] = _safe_redirect_path(redirect)
    return await oauth.google.authorize_redirect(request, auth_settings.google_redirect_uri)


@router.get("/auth/callback")
async def auth_callback(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google authorization failed") from exc

    user_info = token.get("userinfo")
    if not user_info:
        try:
            user_info = await oauth.google.parse_id_token(request, token)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to verify Google identity token") from exc

    if not user_info:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google user info unavailable")
    if not user_info.get("email_verified"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google email is not verified")

    email = user_info.get("email")
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google email not provided")

    user = await upsert_google_user(db, email=email, name=user_info.get("name"), picture=user_info.get("picture"))
    redirect_path = _safe_redirect_path(request.session.pop("post_auth_redirect", None))
    code = await create_exchange_code(db, user_id=str(user.id), redirect_path=redirect_path)
    callback_url = f"{auth_settings.post_login_redirect_url.rstrip('/')}/auth/callback"
    return RedirectResponse(url=f"{callback_url}?{urlencode({'code': code})}", status_code=status.HTTP_302_FOUND)


@router.post("/auth/exchange")
async def exchange_code(payload: ExchangeRequest, db: AsyncSession = Depends(get_db)):
    user, redirect_path = await consume_exchange_code(db, payload.code)
    return _auth_payload(user, redirect_path=redirect_path)


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return serialize_user(current_user)


@router.post("/refresh")
async def refresh_access_token(
    payload: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    refresh_token = payload.refresh_token or request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

    decoded = decode_token(token=refresh_token, expected_type="refresh")
    user = await get_user_by_id(db, decoded["user_id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Email verification required", "email_verified": False},
        )

    access_token = create_access_token(user_id=str(user.id), email=user.email)
    return {"access_token": access_token}


@router.post("/logout")
async def logout():
    response = JSONResponse({"message": "Logged out"})
    clear_auth_cookies(response)
    return response