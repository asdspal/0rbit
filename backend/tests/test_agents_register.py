import pytest
from fastapi import HTTPException

from app.routes import agents as agents_module


class _FakeSupabaseResponse:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error


class _FakeSupabaseInsert:
    def __init__(self, response):
        self._response = response
        self.last_record = None

    def insert(self, record):
        self.last_record = record
        return self

    def execute(self):
        return self._response


class _FakeSupabaseClient:
    def __init__(self, table_impl):
        self._table_impl = table_impl
        self.table_name = None

    def table(self, name):
        self.table_name = name
        return self._table_impl


@pytest.mark.asyncio
async def test_register_agent_success(monkeypatch):
    response = _FakeSupabaseResponse(data=[{"id": "agent-uuid"}], error=None)
    table_impl = _FakeSupabaseInsert(response)
    client = _FakeSupabaseClient(table_impl)

    monkeypatch.setattr(agents_module, "get_supabase_client", lambda: client)

    payload = agents_module.AgentRegister(
        ens_label="atlas",
        axl_peer_id="ed25519:abc",
        capabilities=["code"],
        encrypted_uri="0xhash",
    )

    result = await agents_module.register_agent(payload, address="0xabc")

    assert result == {"id": "agent-uuid"}
    assert client.table_name == "agents"
    assert table_impl.last_record == {
        "wallet_address": "0xabc",
        "ens_name": "atlas.0rbit.eth",
        "axl_peer_id": "ed25519:abc",
        "encrypted_uri": "0xhash",
        "capabilities": ["code"],
        "reputation_score": 500,
        "status": "active",
    }


@pytest.mark.asyncio
async def test_register_agent_conflict(monkeypatch):
    response = _FakeSupabaseResponse(
        data=[],
        error={"message": "duplicate key value violates unique constraint", "code": "23505"},
    )
    table_impl = _FakeSupabaseInsert(response)
    client = _FakeSupabaseClient(table_impl)

    monkeypatch.setattr(agents_module, "get_supabase_client", lambda: client)

    payload = agents_module.AgentRegister(
        ens_label="atlas",
        axl_peer_id="ed25519:abc",
        capabilities=["code"],
        encrypted_uri="0xhash",
    )

    with pytest.raises(HTTPException) as exc:
        await agents_module.register_agent(payload, address="0xabc")

    assert exc.value.status_code == 409
