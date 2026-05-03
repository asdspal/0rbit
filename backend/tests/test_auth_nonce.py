from unittest.mock import MagicMock

import pytest

from app.routes import auth as auth_module


@pytest.mark.asyncio
async def test_auth_nonce_stores_nonce_and_returns_value(monkeypatch):
    redis_client = MagicMock()
    monkeypatch.setattr(auth_module, "_get_client", lambda: redis_client)

    result = await auth_module.auth_nonce()

    assert "nonce" in result
    nonce = result["nonce"]
    assert isinstance(nonce, str)
    assert len(nonce) == 32
    redis_client.set.assert_called_once_with(f"siwe:nonce:{nonce}", "1", ex=300)
