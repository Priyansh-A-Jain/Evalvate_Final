from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, Request, status

from app.auth.jwt import decode_token
from app.auth.service import get_users_collection


async def attach_auth_context(request: Request, call_next):
    request.state.user_id = None

    access_token = request.cookies.get("access_token")
    if access_token:
        try:
            payload = decode_token(token=access_token, expected_type="access")
            user = await get_users_collection().find_one({"_id": ObjectId(payload["user_id"])})
            if user and user.get("email_verified", False):
                request.state.user_id = payload["user_id"]
        except (HTTPException, InvalidId):
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
