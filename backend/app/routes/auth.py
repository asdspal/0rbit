import secrets

from fastapi import APIRouter

from app.redis import _get_client

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/nonce", summary="Create SIWE nonce")
async def auth_nonce():
    nonce = secrets.token_hex(16)
    redis = _get_client()
    redis.set(f"siwe:nonce:{nonce}", "1", ex=300)
    return {"nonce": nonce}
