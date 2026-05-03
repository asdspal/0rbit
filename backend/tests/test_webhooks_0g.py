import json

import pytest
from fastapi import HTTPException

from app.routes import webhooks as webhooks_module


class _FakeSupabaseResponse:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error


class _FakeQuery:
    def __init__(self, table_name: str, store: dict[str, list[dict]]):
        self._table = table_name
        self._store = store
        self._rows = store.get(table_name, [])
        self._updates: list[dict] = []
        self._filters: list[tuple[str, str]] = []
        self._upsert_payload: dict | None = None
        self._on_conflict: list[str] | None = None

    def update(self, payload: dict):
        self._updates.append(payload)
        return self

    def insert(self, payload: dict | list[dict]):
        if isinstance(payload, list):
            self._rows.extend(payload)
        else:
            self._rows.append(payload)
        self._store[self._table] = self._rows
        return self

    def upsert(self, payload: dict, on_conflict: list[str] | None = None):
        self._upsert_payload = payload
        self._on_conflict = on_conflict
        return self

    def eq(self, column: str, value: object):
        self._filters.append((column, str(value)))
        return self

    def _apply_filters(self):
        rows = self._rows
        for column, value in self._filters:
            rows = [row for row in rows if str(row.get(column)) == value]
        return rows

    def _apply_upsert(self):
        if self._upsert_payload is None:
            return

        if self._on_conflict:
            conflicts = self._on_conflict
            match = None
            for row in self._rows:
                if all(str(row.get(col)) == str(self._upsert_payload.get(col)) for col in conflicts):
                    match = row
                    break
            if match:
                match.update(self._upsert_payload)
            else:
                self._rows.append(self._upsert_payload)
        else:
            self._rows.append(self._upsert_payload)

        self._store[self._table] = self._rows

    def execute(self):
        self._apply_upsert()
        rows = self._apply_filters()

        if self._updates:
            for row in rows:
                for update_payload in self._updates:
                    row.update(update_payload)
            self._store[self._table] = self._rows

        return _FakeSupabaseResponse(data=list(rows))


class _FakeSupabaseClient:
    def __init__(self, store: dict[str, list[dict]]):
        self._store = store

    def table(self, name: str):
        if name not in self._store:
            self._store[name] = []
        return _FakeQuery(name, self._store)


class _FakeRequest:
    def __init__(self, body: dict, api_key: str):
        self._body = json.dumps(body).encode("utf-8")
        self.headers = {"X-API-Key": api_key}

    async def body(self):
        return self._body

    async def json(self):
        return json.loads(self._body)


@pytest.mark.asyncio
async def test_og_events_valid_key_updates_job(monkeypatch):
    api_key = "secret"
    monkeypatch.setenv("WEBHOOK_API_KEY", api_key)

    store: dict[str, list[dict]] = {
        "jobs": [
            {
                "id": "uuid-job",
                "onchain_job_id": "1",
                "status": "assigned",
                "uniswap_swap_tx": None,
            }
        ],
        "bids": [],
        "agents": [],
        "reputation_events": [],
    }

    monkeypatch.setattr(webhooks_module, "get_supabase_client", lambda: _FakeSupabaseClient(store))

    payload = {"event": "EscrowReleased", "job_id": "1", "tx_hash": "0xtx"}
    request = _FakeRequest(payload, api_key)

    result = await webhooks_module.og_events_webhook(request)

    assert result == {"status": "ok"}
    assert store["jobs"][0]["status"] == "completed"
    assert store["jobs"][0]["uniswap_swap_tx"] == "0xtx"


@pytest.mark.asyncio
async def test_og_events_invalid_key(monkeypatch):
    monkeypatch.setenv("WEBHOOK_API_KEY", "correct")

    store: dict[str, list[dict]] = {"jobs": [], "bids": [], "agents": [], "reputation_events": []}
    monkeypatch.setattr(webhooks_module, "get_supabase_client", lambda: _FakeSupabaseClient(store))

    payload = {"event": "EscrowReleased", "job_id": "1", "tx_hash": "0xtx"}
    request = _FakeRequest(payload, api_key="wrong")

    with pytest.raises(HTTPException) as exc:
        await webhooks_module.og_events_webhook(request)

    assert exc.value.status_code == 401
