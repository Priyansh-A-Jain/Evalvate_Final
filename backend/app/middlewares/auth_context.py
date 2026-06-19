"""
Auth context middleware — PostgreSQL version.
"""

import uuid

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_token
from app.db import AsyncSessionLocal
from app.models.user import User


async def attach_auth_context(request: Request, call_next):
    request.state.user_id = None

    access_token = request.cookies.get("access_token")
    if access_token:
        try:
            payload = decode_token(token=access_token, expected_type="access")
            user_uuid = uuid.UUID(payload["user_id"])

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(User).where(User.id == user_uuid, User.email_verified.is_(True))
                )
                user = result.scalar_one_or_none()
                if user:
                    request.state.user_id = str(user.id)
        except (HTTPException, ValueError, Exception):
            request.state.user_id = None

    response = await call_next(request)
    return response


def get_authenticated_user_id(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return str(user_id)