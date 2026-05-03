import hashlib
import hmac
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

    def eq(self, column: str, value: object):
        self._filters.append((column, str(value)))
        return self

    def _apply_filters(self):
        rows = self._rows
        for column, value in self._filters:
            rows = [row for row in rows if str(row.get(column)) == value]
        return rows

    def execute(self):
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
        self.last_table = None

    def table(self, name: str):
        if name not in self._store:
            self._store[name] = []
        self.last_table = name
        return _FakeQuery(name, self._store)


class _FakeRequest:
    def __init__(self, body: dict, signature: str):
        self._body = json.dumps(body).encode("utf-8")
        self.headers = {"X-Signature-256": signature}

    async def body(self):
        return self._body

    async def json(self):
        return json.loads(self._body)


def _make_signature(secret: str, payload: dict) -> str:
    raw = json.dumps(payload).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()


@pytest.mark.asyncio
async def test_keeperhub_valid_signature_updates_job(monkeypatch):
    secret = "testsecret"
    monkeypatch.setenv("KEEPERHUB_WEBHOOK_SECRET", secret)

    store: dict[str, list[dict]] = {
        "jobs": [{"id": "job1", "status": "assigned", "uniswap_swap_tx": None}],
        "agents": [],
        "reputation_events": [],
    }

    monkeypatch.setattr(webhooks_module, "get_supabase_client", lambda: _FakeSupabaseClient(store))

    payload = {"type": "escrow_released", "job_id": "job1", "tx_hash": "0xtx"}
    sig = _make_signature(secret, payload)
    request = _FakeRequest(payload, sig)

    result = await webhooks_module.keeperhub_webhook(request)

    assert result == {"status": "ok"}
    assert store["jobs"][0]["status"] == "completed"
    assert store["jobs"][0]["uniswap_swap_tx"] == "0xtx"


@pytest.mark.asyncio
async def test_keeperhub_invalid_signature(monkeypatch):
    monkeypatch.setenv("KEEPERHUB_WEBHOOK_SECRET", "correct")

    store: dict[str, list[dict]] = {
        "jobs": [],
        "agents": [],
        "reputation_events": [],
    }

    monkeypatch.setattr(webhooks_module, "get_supabase_client", lambda: _FakeSupabaseClient(store))

    payload = {"type": "escrow_released", "job_id": "job1", "tx_hash": "0xtx"}
    bad_sig = "deadbeef"
    request = _FakeRequest(payload, bad_sig)

    with pytest.raises(HTTPException) as exc:
        await webhooks_module.keeperhub_webhook(request)

    assert exc.value.status_code == 401
