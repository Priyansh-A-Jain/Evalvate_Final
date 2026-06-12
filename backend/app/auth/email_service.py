import logging

import httpx
from fastapi import HTTPException, status

from app.auth.config import auth_settings

logger = logging.getLogger(__name__)


async def send_verification_email(*, email: str, name: str | None, raw_token: str) -> None:
    verification_url = (
        f"{auth_settings.post_login_redirect_url.rstrip('/')}/auth/verify?token={raw_token}"
    )
    if not auth_settings.resend_api_key:
        import os
        logger.warning("=" * 60)
        logger.warning(f"LOCAL DEV VERIFICATION EMAIL:")
        logger.warning(f"To: {email}")
        logger.warning(f"Verification Link: {verification_url}")
        logger.warning("=" * 60)
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env in {"development", "dev", "local"}:
            return
        logger.error("RESEND_API_KEY is not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Verification email service is not configured",
        )
    greeting = f"Hi {name.strip()}," if name and name.strip() else "Hi,"
    payload = {
        "from": auth_settings.auth_from_email,
        "to": [email],
        "subject": "Verify your Evalvate email",
        "html": (
            f"<p>{greeting}</p>"
            "<p>Verify your email to finish creating your Evalvate account.</p>"
            f'<p><a href="{verification_url}">Verify email</a></p>'
            "<p>This link expires in 24 hours.</p>"
        ),
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {auth_settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception("Failed to send verification email", extra={"email": email})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to send verification email",
        ) from exc
