import pytest
from fastapi import HTTPException

from app.routes import agents as agents_module


class _FakeResponse:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error


class _FakeSelectQuery:
    def __init__(self, data=None, error=None):
        self.data = data or []
        self.error = error
        self.filters: list[tuple[str, str, object]] = []
        self.select_args: tuple | None = None
        self.limit_arg: int | None = None

    def select(self, *args):
        self.select_args = args
        return self

    def eq(self, column: str, value: object):
        self.filters.append(("eq", column, value))
        return self

    def limit(self, value: int):
        self.limit_arg = value
        return self

    def execute(self):
        return _FakeResponse(data=list(self.data), error=self.error)


class _FakeUpdateQuery:
    def __init__(self, data=None, error=None):
        self.data = data or []
        self.error = error
        self.updated_payload: dict | None = None
        self.filters: list[tuple[str, str, object]] = []

    def update(self, payload: dict):
        self.updated_payload = dict(payload)
        return self

    def eq(self, column: str, value: object):
        self.filters.append(("eq", column, value))
        return self

    def execute(self):
        return _FakeResponse(data=list(self.data), error=self.error)


class _FakeRangeQuery:
    def __init__(self, data=None, error=None):
        self.data = data or []
        self.error = error
        self.filters: list[tuple[str, str, object]] = []
        self.range_args: tuple[int, int] | None = None
        self.order_args: tuple | None = None

    def select(self, *_args):
        return self

    def eq(self, column: str, value: object):
        self.filters.append(("eq", column, value))
        return self

    def order(self, *args, **kwargs):
        self.order_args = (args, kwargs)
        return self

    def range(self, start: int, end: int):
        self.range_args = (start, end)
        return self

    def execute(self):
        return _FakeResponse(data=list(self.data), error=self.error)


class _FakeSupabaseClient:
    def __init__(self, queries):
        self._queries = list(queries)
        self.table_name_sequence: list[str] = []

    def table(self, name: str):
        if not self._queries:
            raise AssertionError("No remaining fake queries; Supabase accessed unexpectedly")
        self.table_name_sequence.append(name)
        return self._queries.pop(0)


@pytest.mark.asyncio
async def test_update_agent_success(monkeypatch):
    agent_id = agents_module.UUID("12345678-1234-5678-1234-567812345678")
    select_query = _FakeSelectQuery(data=[{"id": str(agent_id), "wallet_address": "0xabc"}])
    update_result = {"id": str(agent_id), "status": "inactive", "capabilities": ["code"]}
    update_query = _FakeUpdateQuery(data=[update_result])
    client = _FakeSupabaseClient([select_query, update_query])

    monkeypatch.setattr(agents_module, "get_supabase_client", lambda: client)

    payload = agents_module.AgentUpdate(capabilities=["code"], status="inactive")

    result = await agents_module.update_agent(agent_id=agent_id, payload=payload, address="0xAbC")

    assert result == update_result
    assert update_query.updated_payload is not None
    assert update_query.updated_payload["capabilities"] == ["code"]
    assert update_query.updated_payload["status"] == "inactive"

    # Ensure updated_at is a valid ISO timestamp
    updated_at = update_query.updated_payload["updated_at"]
    agents_module.datetime.fromisoformat(updated_at)

    # Ensure correct Supabase tables accessed
    assert client.table_name_sequence == ["agents", "agents"]


@pytest.mark.asyncio
async def test_update_agent_forbidden(monkeypatch):
    agent_id = agents_module.UUID("12345678-1234-5678-1234-567812345678")
    select_query = _FakeSelectQuery(data=[{"id": str(agent_id), "wallet_address": "0xowner"}])
    client = _FakeSupabaseClient([select_query])

    monkeypatch.setattr(agents_module, "get_supabase_client", lambda: client)

    payload = agents_module.AgentUpdate(capabilities=["code"], status="inactive")

    with pytest.raises(HTTPException) as exc:
        await agents_module.update_agent(agent_id=agent_id, payload=payload, address="0xother")

    assert exc.value.status_code == 403
    assert client.table_name_sequence == ["agents"]


@pytest.mark.asyncio
async def test_get_agent_reputation_paginates(monkeypatch):
    agent_id = agents_module.UUID("12345678-1234-5678-1234-567812345678")
    data = [
        {"id": "rep-1"},
        {"id": "rep-2"},
        {"id": "rep-3"},
    ]
    query = _FakeRangeQuery(data=data)
    client = _FakeSupabaseClient([query])

    monkeypatch.setattr(agents_module, "get_supabase_client", lambda: client)

    result = await agents_module.get_agent_reputation(agent_id=agent_id, limit=2, cursor="2")

    assert result["data"] == data[:2]
    assert result["cursor"] == "4"
    assert query.range_args == (2, 4)
    assert ("eq", "agent_id", str(agent_id)) in query.filters
    assert query.order_args is not None


@pytest.mark.asyncio
async def test_get_agent_jobs_paginates(monkeypatch):
    agent_id = agents_module.UUID("12345678-1234-5678-1234-567812345678")
    data = [
        {"id": "job-1"},
        {"id": "job-2"},
        {"id": "job-3"},
    ]
    query = _FakeRangeQuery(data=data)
    client = _FakeSupabaseClient([query])

    monkeypatch.setattr(agents_module, "get_supabase_client", lambda: client)

    result = await agents_module.get_agent_jobs(agent_id=agent_id, limit=1, cursor=None)

    assert result["data"] == data[:1]
    assert result["cursor"] == "1"
    assert query.range_args == (0, 1)
    assert ("eq", "assigned_agent_id", str(agent_id)) in query.filters
