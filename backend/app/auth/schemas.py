from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class EmailPayload(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        local, separator, domain = normalized.rpartition("@")
        if not separator or not local or "." not in domain:
            raise ValueError("Enter a valid email address")
        return normalized


class RegisterRequest(EmailPayload):
    password: str = Field(min_length=8, max_length=128)
    name: str | None = Field(default=None, max_length=120)


class LoginRequest(EmailPayload):
    password: str = Field(min_length=8, max_length=128)


class ResendVerificationRequest(EmailPayload):
    pass


class ExchangeRequest(BaseModel):
    code: str = Field(min_length=20, max_length=256)


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class UserOut(BaseModel):
    id: str
    email: str
    name: str | None = None
    picture: str | None = None
    auth_providers: list[str] = Field(default_factory=list)
    email_verified: bool
    created_at: datetime
    last_login: datetime


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserOut


class RegisterResponse(BaseModel):
    message: str
    email: str
