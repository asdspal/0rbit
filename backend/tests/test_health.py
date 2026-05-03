import pytest

from app.routes import health as health_module


class _DummyResponse:
    error = None


class _DummyQuery:
    def select(self, *_) -> "_DummyQuery":
        return self

    def limit(self, *_) -> "_DummyQuery":
        return self

    def execute(self) -> "_DummyResponse":
        return _DummyResponse()


class _DummyClient:
    def table(self, *_) -> _DummyQuery:
        return _DummyQuery()


@pytest.mark.asyncio
async def test_health_endpoint_reports_all_connected(monkeypatch):
    monkeypatch.setattr(health_module, "get_supabase_client", lambda: _DummyClient())
    monkeypatch.setattr(health_module, "ping_redis", lambda: True)

    result = await health_module.health_check()

    assert result == {
        "status": "ok",
        "supabase": "connected",
        "redis": "connected",
    }


@pytest.mark.asyncio
async def test_health_endpoint_handles_service_failures(monkeypatch):
    def raise_error():
        raise RuntimeError("supabase down")

    monkeypatch.setattr(health_module, "get_supabase_client", raise_error)
    monkeypatch.setattr(health_module, "ping_redis", lambda: False)

    result = await health_module.health_check()

    assert result["status"] == "degraded"
    assert result["supabase"] == "disconnected"
    assert result["redis"] == "disconnected"
