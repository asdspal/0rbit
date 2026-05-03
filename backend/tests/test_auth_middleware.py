import pytest
from jose import jwt

from app import deps


@pytest.mark.asyncio
async def test_get_current_user_valid_token(monkeypatch):
    secret = "test-secret"
    address = "0x1111111111111111111111111111111111111111"
    token = jwt.encode({"sub": address}, secret, algorithm="HS256")

    monkeypatch.setattr(deps, "_require_secret", lambda: secret)

    result = await deps.get_current_user(token)
    assert result == address


@pytest.mark.asyncio
async def test_get_current_user_missing_token():
    with pytest.raises(Exception) as exc:
        await deps.get_current_user(None)

    assert getattr(exc.value, "status_code", None) == 401
