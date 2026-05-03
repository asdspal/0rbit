import pytest
from uuid import uuid4

from app.routes import bids as bids_module


class _FakeSupabaseResponse:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error


class _FakeQuery:
    def __init__(self, store: dict[str, list[dict]], table_name: str):
        self._store = store
        self._table = table_name
        self._rows = list(store.get(table_name, []))
        self._limit = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, column: str, value: object):
        self._rows = [row for row in self._rows if str(row.get(column)) == str(value)]
        return self

    def limit(self, value: int):
        self._limit = value
        return self

    def insert(self, record: dict):
        self._store.setdefault(self._table, []).append(record)
        self._rows = [record]
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
async def test_create_bid_inserts_pending(monkeypatch):
    job_id = str(uuid4())
    store = {
        "agents": [{"id": "agent-1", "wallet_address": "0xabc"}],
        "bids": [],
    }

    client = _FakeSupabaseClient(store)
    monkeypatch.setattr(bids_module, "get_supabase_client", lambda: client)

    payload = bids_module.BidCreate(
        proposed_amount="90",
        message="I can do this",
        axl_message_id="axl-1",
    )

    result = await bids_module.create_bid(job_id, payload, address="0xabc")

    assert result["status"] == "pending"
    assert store["bids"][0]["job_id"] == job_id
    assert store["bids"][0]["agent_id"] == "agent-1"
    assert store["bids"][0]["proposed_amount"] == "90"
    assert store["bids"][0]["message"] == "I can do this"


@pytest.mark.asyncio
async def test_withdraw_bid_updates_status(monkeypatch):
    bid_id = str(uuid4())
    store = {
        "agents": [{"id": "agent-1", "wallet_address": "0xabc"}],
        "bids": [
            {"id": bid_id, "agent_id": "agent-1", "job_id": str(uuid4()), "status": "pending"}
        ],
    }

    client = _FakeSupabaseClient(store)
    monkeypatch.setattr(bids_module, "get_supabase_client", lambda: client)

    result = await bids_module.withdraw_bid(bid_id, address="0xAbC")

    assert result["status"] == "withdrawn"
    assert store["bids"][0]["status"] == "withdrawn"
