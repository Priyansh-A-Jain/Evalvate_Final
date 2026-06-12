import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _parse_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class AppSettings:
    frontend_url: str
    backend_url: str
    interview_max_questions: int
    environment: str


def get_app_settings() -> AppSettings:
    return AppSettings(
        frontend_url=os.getenv("FRONTEND_URL", "http://localhost:3000"),
        backend_url=os.getenv("BACKEND_URL", "http://localhost:8000"),
        interview_max_questions=_parse_int(os.getenv("INTERVIEW_MAX_QUESTIONS"), 5),
        environment=os.getenv("ENVIRONMENT", "development"),
    )


app_settings = get_app_settings()
