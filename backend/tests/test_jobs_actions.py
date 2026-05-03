import pytest
from uuid import uuid4

from app.routes import jobs as jobs_module


class _FakeSupabaseResponse:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error


class _FakeQuery:
    def __init__(self, store: dict[str, list[dict]], table_name: str):
        self._store = store
        self._table = table_name
        self._rows = store.get(table_name, [])
        self._order = None
        self._limit = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, column: str, value: object):
        self._rows = [row for row in self._rows if str(row.get(column)) == str(value)]
        return self

    def order(self, *_args, **_kwargs):
        # Order is not required for current tests.
        return self

    def limit(self, value: int):
        self._limit = value
        return self

    def update(self, payload: dict):
        for row in self._rows:
            row.update(payload)
        return self

    def execute(self):
        rows = self._rows
        if self._limit is not None:
            rows = rows[: self._limit]
        return _FakeSupabaseResponse(data=list(rows))


class _FakeSupabaseClient:
    def __init__(self, store: dict[str, list[dict]]):
        self._store = store
        self.table_name = None

    def table(self, name: str):
        self.table_name = name
        if name not in self._store:
            self._store[name] = []
        return _FakeQuery(self._store, name)


@pytest.mark.asyncio
async def test_get_job_returns_job_with_bids(monkeypatch):
    job_id = str(uuid4())
    store = {
        "jobs": [{"id": job_id, "title": "test", "poster_address": "0xposter"}],
        "bids": [
            {"id": "bid1", "job_id": job_id, "agent_id": "a1"},
            {"id": "bid2", "job_id": job_id, "agent_id": "a2"},
        ],
    }

    client = _FakeSupabaseClient(store)
    monkeypatch.setattr(jobs_module, "get_supabase_client", lambda: client)

    result = await jobs_module.get_job(job_id)

    assert result["id"] == job_id
    assert len(result["bids"]) == 2


@pytest.mark.asyncio
async def test_assign_job_updates_job_and_bid(monkeypatch):
    job_id = str(uuid4())
    agent_id = str(uuid4())
    bid_id = str(uuid4())
    store = {
        "jobs": [
            {"id": job_id, "poster_address": "0xPoster", "status": "posted", "assigned_agent_id": None}
        ],
        "bids": [
            {"id": bid_id, "job_id": job_id, "agent_id": agent_id, "status": "pending"},
        ],
    }

    client = _FakeSupabaseClient(store)
    monkeypatch.setattr(jobs_module, "get_supabase_client", lambda: client)

    payload = jobs_module.AssignJob(bid_id=bid_id)
    result = await jobs_module.assign_job(job_id, payload, address="0xposter")

    assert result == {"status": "assigned"}
    assert store["jobs"][0]["assigned_agent_id"] == agent_id
    assert store["jobs"][0]["status"] == "assigned"
    assert store["bids"][0]["status"] == "accepted"


@pytest.mark.asyncio
async def test_complete_job_requires_assigned_agent(monkeypatch):
    job_id = str(uuid4())
    agent_id = str(uuid4())
    store = {
        "jobs": [
            {"id": job_id, "assigned_agent_id": agent_id, "status": "assigned"}
        ],
        "agents": [
            {"id": agent_id, "wallet_address": "0xagent"}
        ],
    }

    client = _FakeSupabaseClient(store)
    monkeypatch.setattr(jobs_module, "get_supabase_client", lambda: client)

    payload = jobs_module.CompleteJob(output_hash="0xhash", compute_proof="proof")
    result = await jobs_module.complete_job(job_id, payload, address="0xagent")

    assert result["status"] == "completed"
    assert store["jobs"][0]["status"] == "completed"
    assert store["jobs"][0]["output_hash"] == "0xhash"
    assert store["jobs"][0].get("completed_at") is not None


@pytest.mark.asyncio
async def test_dispute_job_allows_poster(monkeypatch):
    job_id = str(uuid4())
    store = {
        "jobs": [
            {"id": job_id, "poster_address": "0xposter", "assigned_agent_id": None, "status": "assigned"}
        ],
    }

    client = _FakeSupabaseClient(store)
    monkeypatch.setattr(jobs_module, "get_supabase_client", lambda: client)

    result = await jobs_module.dispute_job(job_id, address="0xposter")

    assert result["status"] == "disputed"
    assert store["jobs"][0]["status"] == "disputed"
