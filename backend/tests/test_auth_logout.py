import pytest
from jose import jwt

from app import deps
from app.auth import jwt as jwt_module
from app.routes import auth


class _FakeRedis:
    def __init__(self) -> None:
        self.records: list[tuple[str, str, int | None]] = []
        self.existing: set[str] = set()

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.records.append((key, value, ex))
        if ex is not None and ex > 0:
            self.existing.add(key)

    def exists(self, key: str) -> int:
        return 1 if key in self.existing else 0


@pytest.mark.asyncio
async def test_logout_blocks_token(monkeypatch):
    secret = "test-secret"
    address = "0x1111111111111111111111111111111111111111"
    payload = {"sub": address, "jti": "logout-jti", "exp": 9999999999}
    token = jwt.encode(payload, secret, algorithm="HS256")

    fake_redis = _FakeRedis()
    monkeypatch.setattr(auth, "_get_client", lambda: fake_redis)
    monkeypatch.setattr(deps, "_get_client", lambda: fake_redis)
    monkeypatch.setattr(deps, "_require_secret", lambda: secret)
    monkeypatch.setattr(auth, "_require_secret", lambda: secret)
    monkeypatch.setenv("JWT_SECRET", secret)
    monkeypatch.setattr(jwt_module, "_require_secret", lambda: secret)

    class _Response:
        def __init__(self) -> None:
            self.deleted = False

        def delete_cookie(self, *args, **kwargs) -> None:
            self.deleted = True

    response = _Response()
    result = await auth.auth_logout(response=response, token=token)

    assert result == {"status": "ok"}
    assert response.deleted is True
    assert any(record[0] == "jwt:blocklist:logout-jti" for record in fake_redis.records)
    with pytest.raises(Exception) as exc:
        await deps.get_current_user(token)
    assert getattr(exc.value, "status_code", None) == 401


@pytest.mark.asyncio
async def test_refresh_issues_new_token(monkeypatch):
    secret = "test-secret"
    address = "0x1111111111111111111111111111111111111111"
    payload = {"sub": address, "jti": "old-jti", "exp": 9999999999}
    token = jwt.encode(payload, secret, algorithm="HS256")

    monkeypatch.setattr(auth, "_require_secret", lambda: secret)
    monkeypatch.setenv("JWT_SECRET", secret)

    class _Response:
        def __init__(self) -> None:
            self.cookie_value = None

        def set_cookie(self, *, value: str, **kwargs) -> None:
            self.cookie_value = value

    response = _Response()
    result = await auth.auth_refresh(response=response, token=token)

    assert "jwt" in result
    assert result["jwt"] != token
    assert response.cookie_value == result["jwt"]
