import json
from uuid import UUID

import pytest

from app.routes import agents as agents_module


class _FakeResponse:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error


class _FakeQuery:
    def __init__(self, data=None, error=None):
        self.data = data or []
        self.error = error
        self.filters: list[tuple[str, str, object]] = []
        self.range_args: tuple[int, int] | None = None

    def select(self, *_args):
        return self

    def order(self, *args, **kwargs):
        return self

    def eq(self, column: str, value: object):
        self.filters.append(("eq", column, value))
        return self

    def gte(self, column: str, value: object):
        self.filters.append(("gte", column, value))
        return self

    def contains(self, column: str, value: object):
        self.filters.append(("contains", column, tuple(value) if isinstance(value, list) else value))
        return self

    def range(self, start: int, end: int):
        self.range_args = (start, end)
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        return _FakeResponse(data=list(self.data) if self.data is not None else None, error=self.error)


class _FakeSupabaseClient:
    def __init__(self, queries: list[_FakeQuery]):
        self._queries = queries
        self.table_name_sequence: list[str] = []

    def table(self, name: str):
        if not self._queries:
            raise AssertionError("No remaining fake queries; Supabase accessed unexpectedly")
        self.table_name_sequence.append(name)
        return self._queries.pop(0)


class _FakeRedis:
    def __init__(self):
        self.storage: dict[str, tuple[str, int]] = {}

    def get(self, key: str):
        entry = self.storage.get(key)
        return entry[0] if entry else None

    def setex(self, key: str, ttl: int, value: str):
        self.storage[key] = (value, ttl)

    def delete(self, key: str):
        self.storage.pop(key, None)


@pytest.mark.asyncio
async def test_list_agents_applies_filters_and_paginates(monkeypatch):
    data = [
        {"id": "agent-1", "status": "active", "reputation_score": 800, "capabilities": ["code"]},
        {"id": "agent-2", "status": "active", "reputation_score": 700, "capabilities": ["code"]},
        {"id": "agent-3", "status": "inactive", "reputation_score": 650, "capabilities": ["chat"]},
    ]
    query = _FakeQuery(data=data)
    client = _FakeSupabaseClient([query])

    monkeypatch.setattr(agents_module, "get_supabase_client", lambda: client)

    result = await agents_module.list_agents(
        capabilities=["code"],
        min_rep=600,
        status="active",
        limit=2,
        cursor=None,
    )

    assert result["data"] == data[:2]
    assert result["cursor"] == "2"
    assert query.range_args == (0, 2)
    assert ("eq", "status", "active") in query.filters
    assert ("gte", "reputation_score", 600) in query.filters
    assert any(filter_tuple[0] == "contains" for filter_tuple in query.filters)
    assert client.table_name_sequence == ["agents"]


@pytest.mark.asyncio
async def test_get_agent_by_id_returns_record(monkeypatch):
    agent_id = UUID("12345678-1234-5678-1234-567812345678")
    query = _FakeQuery(data=[{"id": str(agent_id), "status": "active"}])
    client = _FakeSupabaseClient([query])

    monkeypatch.setattr(agents_module, "get_supabase_client", lambda: client)

    result = await agents_module.get_agent(agent_id=agent_id)

    assert result == {"id": str(agent_id), "status": "active"}
    assert ("eq", "id", str(agent_id)) in query.filters
    assert client.table_name_sequence == ["agents"]


@pytest.mark.asyncio
async def test_get_agent_by_ens_uses_redis_cache(monkeypatch):
    agent = {"id": "agent-ens", "ens_name": "atlas.0rbit.eth"}
    query = _FakeQuery(data=[agent])
    client = _FakeSupabaseClient([query])
    redis = _FakeRedis()

    monkeypatch.setattr(agents_module, "get_supabase_client", lambda: client)
    monkeypatch.setattr(agents_module, "_get_client", lambda: redis)

    first = await agents_module.get_agent_by_ens("Atlas.0rbit.eth")
    assert first == agent

    cache_key = "ens:cache:atlas.0rbit.eth"
    assert cache_key in redis.storage
    cached_payload, ttl = redis.storage[cache_key]
    assert ttl == 300
    assert json.loads(cached_payload) == agent

    client._queries.clear()

    second = await agents_module.get_agent_by_ens("atlas.0rbit.eth")
    assert second == agent
    assert json.loads(redis.get(cache_key)) == agent

