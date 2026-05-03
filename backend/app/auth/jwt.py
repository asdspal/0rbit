from __future__ import annotations

from os import getenv

from jose import jwt


def _require_secret() -> str:
    secret = getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET is required to sign tokens")
    return secret


def create_access_token(payload: dict) -> str:
    secret = _require_secret()
    return jwt.encode(payload, secret, algorithm="HS256")
