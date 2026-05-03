from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import Response

from app.routes import auth as auth_module


def _sample_message(nonce: str, address: str = "0x1111111111111111111111111111111111111111") -> str:
    issued_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return "\n".join(
        [
            "example.com wants you to sign in with your Ethereum account:",
            address,
            "",
            "URI: https://example.com",
            "Version: 1",
            "Chain ID: 1",
            f"Nonce: {nonce}",
            f"Issued At: {issued_at}",
        ]
    )


@pytest.mark.asyncio
async def test_auth_verify_valid_signature_and_nonce(monkeypatch):
    nonce = "abc123"
    message = _sample_message(nonce)
    signature = "0xsig"

    redis_client = MagicMock()
    redis_client.get.return_value = "1"
    monkeypatch.setattr(auth_module, "_get_client", lambda: redis_client)
    monkeypatch.setattr(auth_module, "verify_signature", lambda msg, sig: "0x1111111111111111111111111111111111111111")
    monkeypatch.setattr(auth_module, "create_access_token", lambda payload: "jwt-token")

    response = Response()
    result = await auth_module.auth_verify({"message": message, "signature": signature}, response)

    assert result == {"jwt": "jwt-token", "agent": None}
    redis_client.get.assert_called_once_with(f"siwe:nonce:{nonce}")
    redis_client.delete.assert_called_once_with(f"siwe:nonce:{nonce}")
    assert any(cookie.startswith("token=") for cookie in response.headers.getlist("set-cookie"))


@pytest.mark.asyncio
async def test_auth_verify_invalid_nonce(monkeypatch):
    nonce = "missing"
    message = _sample_message(nonce)

    redis_client = MagicMock()
    redis_client.get.return_value = None
    monkeypatch.setattr(auth_module, "_get_client", lambda: redis_client)

    response = Response()
    with pytest.raises(Exception) as exc:
        await auth_module.auth_verify({"message": message, "signature": "0xsig"}, response)

    assert getattr(exc.value, "status_code", None) == 401
