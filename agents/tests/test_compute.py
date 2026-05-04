from __future__ import annotations

import base64
import pytest

import httpx

from agents.plugins.orbit import compute
from agents.plugins.orbit.compute import ComputeClient, ComputeError


class _DummyResponse:
    def __init__(self, json_data: dict, status_code: int = 200):
        self._json = json_data
        self.status_code = status_code

    def json(self) -> dict:
        return self._json

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise httpx.HTTPStatusError("boom", request=None, response=None)


class _DummyAsyncClient:
    def __init__(self):
        self.requests: list[tuple[str, dict]] = []
        self.responses: list[_DummyResponse] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, path: str, json: dict):
        self.requests.append((path, json))
        if not self.responses:
            raise AssertionError("No stubbed response available")
        return self.responses.pop(0)


@pytest.fixture
def dummy_client(monkeypatch):
    dummy = _DummyAsyncClient()

    class _FakeAsyncClient:
        def __init__(self, *_, **__):
            pass

        async def __aenter__(self):
            return dummy

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("agents.plugins.orbit.compute.httpx.AsyncClient", _FakeAsyncClient)
    return dummy


@pytest.mark.anyio
async def test_verify_output_encodes_proof(dummy_client):
    client = ComputeClient(base_url="https://example.test")
    dummy_client.responses.append(_DummyResponse({"verified": True}))

    proof = b"sealed-proof"
    verified = await client.verify_output("hash123", proof)

    assert verified is True
    path, payload = dummy_client.requests[0]
    assert path == compute.VERIFY_PATH
    assert payload["output_hash"] == "hash123"
    assert payload["compute_proof"] == base64.b64encode(proof).decode("ascii")


@pytest.mark.anyio
async def test_submit_for_verification_roundtrip(dummy_client):
    proof_bytes = base64.b64encode(b"proof-bytes").decode("ascii")
    dummy_client.responses.append(
        _DummyResponse({"output_hash": "hash456", "compute_proof": proof_bytes})
    )

    client = ComputeClient(base_url="https://example.test")
    output_hash, proof = await client.submit_for_verification(b"payload-data")

    assert output_hash == "hash456"
    assert proof == base64.b64decode(proof_bytes)
    path, payload = dummy_client.requests[0]
    assert path == compute.SUBMIT_PATH
    assert payload["payload"] == base64.b64encode(b"payload-data").decode("ascii")


@pytest.mark.anyio
async def test_missing_output_hash_raises():
    client = ComputeClient()
    with pytest.raises(ComputeError):
        await client.verify_output("", b"proof")


@pytest.mark.anyio
async def test_missing_proof_raises():
    client = ComputeClient()
    with pytest.raises(ComputeError):
        await client.verify_output("hash", b"")
