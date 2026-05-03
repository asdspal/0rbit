from typing import AsyncGenerator

from fastapi import Cookie, HTTPException
from jose import JWTError, jwt

from app.auth.jwt import _require_secret
from app.redis import _get_client


async def get_db() -> AsyncGenerator[None, None]:
    yield None


async def get_current_user(token: str | None = Cookie(default=None)) -> str:
    if not token:
        raise HTTPException(status_code=401, detail="Missing auth token")

    try:
        payload = jwt.decode(token, _require_secret(), algorithms=["HS256"])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid auth token") from exc

    address = payload.get("sub") if isinstance(payload, dict) else None
    if not address:
        raise HTTPException(status_code=401, detail="Invalid auth token")

    jti = payload.get("jti") if isinstance(payload, dict) else None
    if jti:
        redis = _get_client()
        if redis.exists(f"jwt:blocklist:{jti}"):
            raise HTTPException(status_code=401, detail="Invalid auth token")

    return address
