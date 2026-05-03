import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response

from app.auth.jwt import create_access_token
from app.auth.siwe import parse_siwe_message, verify_signature
from app.database import get_supabase_client
from app.deps import get_current_user
from app.redis import _get_client

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/nonce", summary="Create SIWE nonce")
async def auth_nonce():
    nonce = secrets.token_hex(16)
    redis = _get_client()
    redis.set(f"siwe:nonce:{nonce}", "1", ex=300)
    return {"nonce": nonce}


@router.post("/verify", summary="Verify SIWE signature")
async def auth_verify(payload: dict, response: Response):
    message = payload.get("message") if payload else None
    signature = payload.get("signature") if payload else None

    if not message or not signature:
        raise HTTPException(status_code=400, detail="message and signature are required")

    try:
        siwe_message = parse_siwe_message(message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    redis = _get_client()
    nonce_key = f"siwe:nonce:{siwe_message.nonce}"
    if not redis.get(nonce_key):
        raise HTTPException(status_code=401, detail="Invalid nonce")
    redis.delete(nonce_key)

    try:
        recovered = verify_signature(message, signature)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if recovered.lower() != siwe_message.address.lower():
        raise HTTPException(status_code=401, detail="Signature mismatch")

    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=86400)
    token_payload = {
        "sub": siwe_message.address,
        "jti": str(uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    token = create_access_token(token_payload)

    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=86400,
    )

    return {"jwt": token, "agent": None}


@router.get("/me", summary="Get current user")
async def auth_me(address: str = Depends(get_current_user)):
    client = get_supabase_client()
    response = (
        client.table("agents")
        .select("id", "ens_name")
        .eq("wallet_address", address)
        .limit(1)
        .execute()
    )
    error = getattr(response, "error", None)
    if error:
        raise HTTPException(status_code=500, detail="Failed to load agent")

    agent = None
    data = getattr(response, "data", None)
    if isinstance(data, list) and data:
        agent = data[0]

    return {
        "address": address,
        "agent_id": agent.get("id") if agent else None,
        "ens_name": agent.get("ens_name") if agent else None,
    }
