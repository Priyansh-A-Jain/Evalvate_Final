import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorCollection
from passlib.context import CryptContext
from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError

from app.db import mongodb

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
VERIFICATION_TOKEN_TTL_HOURS = 24
EXCHANGE_CODE_TTL_SECONDS = 60


def get_users_collection() -> AsyncIOMotorCollection:
    if mongodb.db is None:
        raise RuntimeError("Database is not initialized")
    return mongodb.db["users"]


def get_exchange_codes_collection() -> AsyncIOMotorCollection:
    if mongodb.db is None:
        raise RuntimeError("Database is not initialized")
    return mongodb.db["auth_exchange_codes"]


async def ensure_user_indexes() -> None:
    users = get_users_collection()
    exchange_codes = get_exchange_codes_collection()
    await users.create_index("email", unique=True, name="uniq_email")
    await users.create_index(
        "verification_token_hash",
        name="idx_verification_token_hash",
        sparse=True,
    )
    await exchange_codes.create_index("code_hash", unique=True, name="uniq_exchange_code_hash")
    await exchange_codes.create_index(
        [("expires_at", ASCENDING)],
        expireAfterSeconds=0,
        name="ttl_exchange_code",
    )

    # Existing accounts predate provider and verification fields and were Google-only.
    await users.update_many(
        {"auth_providers": {"$exists": False}},
        {"$set": {"auth_providers": ["google"], "email_verified": True}},
    )


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def new_verification_token() -> tuple[str, str, datetime]:
    raw_token = secrets.token_urlsafe(32)
    return (
        raw_token,
        _hash_token(raw_token),
        datetime.now(timezone.utc) + timedelta(hours=VERIFICATION_TOKEN_TTL_HOURS),
    )


async def create_password_user(*, email: str, password: str, name: str | None) -> tuple[dict, str]:
    users = get_users_collection()
    now = datetime.now(timezone.utc)
    raw_token, token_hash, token_expires = new_verification_token()
    existing = await users.find_one({"email": email})

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Sign in with its existing provider.",
        )

    document = {
        "email": email,
        "name": name.strip() if name and name.strip() else None,
        "picture": None,
        "password_hash": hash_password(password),
        "auth_providers": ["password"],
        "email_verified": False,
        "verification_token_hash": token_hash,
        "verification_token_expires": token_expires,
        "created_at": now,
        "updated_at": now,
        "last_login": now,
    }
    try:
        result = await users.insert_one(document)
    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        ) from exc
    document["_id"] = result.inserted_id
    return document, raw_token


async def authenticate_password_user(*, email: str, password: str) -> dict:
    user = await get_users_collection().find_one({"email": email})
    password_hash = user.get("password_hash") if user else None
    if not user or not password_hash or not verify_password(password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.get("email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Verify your email before signing in", "email_verified": False},
        )
    now = datetime.now(timezone.utc)
    await get_users_collection().update_one({"_id": user["_id"]}, {"$set": {"last_login": now}})
    user["last_login"] = now
    return user


async def issue_new_verification_token(*, email: str) -> tuple[dict | None, str | None]:
    users = get_users_collection()
    user = await users.find_one({"email": email})
    if not user or user.get("email_verified", False):
        return user, None

    raw_token, token_hash, token_expires = new_verification_token()
    await users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "verification_token_hash": token_hash,
                "verification_token_expires": token_expires,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    return user, raw_token


async def verify_email_token(raw_token: str) -> dict:
    users = get_users_collection()
    now = datetime.now(timezone.utc)
    user = await users.find_one(
        {
            "verification_token_hash": _hash_token(raw_token),
            "verification_token_expires": {"$gt": now},
        }
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link is invalid or expired",
        )

    await users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"email_verified": True, "last_login": now, "updated_at": now},
            "$unset": {"verification_token_hash": "", "verification_token_expires": ""},
        },
    )
    user["email_verified"] = True
    user["last_login"] = now
    user.pop("verification_token_hash", None)
    user.pop("verification_token_expires", None)
    return user


async def upsert_google_user(
    *,
    email: str,
    name: str | None,
    picture: str | None,
) -> dict[str, Any]:
    users = get_users_collection()
    normalized_email = email.strip().lower()
    now = datetime.now(timezone.utc)

    await users.update_one(
        {"email": normalized_email},
        {
            "$set": {
                "name": name,
                "picture": picture,
                "email_verified": True,
                "last_login": now,
                "updated_at": now,
            },
            "$addToSet": {"auth_providers": "google"},
            "$setOnInsert": {
                "email": normalized_email,
                "password_hash": None,
                "created_at": now,
            },
            "$unset": {"verification_token_hash": "", "verification_token_expires": ""},
        },
        upsert=True,
    )

    user = await users.find_one({"email": normalized_email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load user",
        )
    return user


async def create_exchange_code(*, user_id: str, redirect_path: str) -> str:
    raw_code = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    await get_exchange_codes_collection().insert_one(
        {
            "code_hash": _hash_token(raw_code),
            "user_id": user_id,
            "redirect_path": redirect_path,
            "created_at": now,
            "expires_at": now + timedelta(seconds=EXCHANGE_CODE_TTL_SECONDS),
        }
    )
    return raw_code


async def consume_exchange_code(raw_code: str) -> tuple[dict, str]:
    codes = get_exchange_codes_collection()
    code = await codes.find_one_and_delete(
        {
            "code_hash": _hash_token(raw_code),
            "expires_at": {"$gt": datetime.now(timezone.utc)},
        }
    )
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code is invalid or expired",
        )

    from bson import ObjectId

    user = await get_users_collection().find_one({"_id": ObjectId(code["user_id"])})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user, code.get("redirect_path", "/dashboard")


def serialize_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user.get("name"),
        "picture": user.get("picture"),
        "auth_providers": user.get("auth_providers", []),
        "email_verified": bool(user.get("email_verified", False)),
        "created_at": user["created_at"],
        "last_login": user.get("last_login", user["created_at"]),
    }
