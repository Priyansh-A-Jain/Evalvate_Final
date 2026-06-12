from fastapi import Response

from app.auth.config import auth_settings


def _cookie_options() -> dict:
    return {
        "httponly": True,
        "secure": auth_settings.cookie_secure,
        "samesite": auth_settings.cookie_samesite,
        "path": "/",
    }


def set_auth_cookies(response: Response, *, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=auth_settings.access_token_expire_minutes * 60,
        **_cookie_options(),
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=auth_settings.refresh_token_expire_minutes * 60,
        **_cookie_options(),
    )


def set_access_cookie(response: Response, *, access_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=auth_settings.access_token_expire_minutes * 60,
        **_cookie_options(),
    )


def clear_auth_cookies(response: Response) -> None:
    options = {
        "path": "/",
        "secure": auth_settings.cookie_secure,
        "samesite": auth_settings.cookie_samesite,
        "httponly": True,
    }
    response.delete_cookie("access_token", **options)
    response.delete_cookie("refresh_token", **options)
