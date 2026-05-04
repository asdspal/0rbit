import hashlib
import hmac
import os
from typing import Any, Dict

import httpx
import pytest

from agents.plugins.orbit.keeperhub import KeeperHubClient, KeeperHubError, WebhookVerifier


class DummyResponse:
    def __init__(self, data: Dict[str, Any], status_code: int = 200):
        self._data = data
        self.status_code = status_code

    def json(self) -> Dict[str, Any]:
        return self._data

    def raise_for_status(self) -> None:
        if not 200 <= self.status_code < 300:
            raise httpx.HTTPStatusError(
                "error",
                request=httpx.Request("GET", "https://keeperhub.test"),
                response=httpx.Response(self.status_code),
            )


class DummyAsyncClient:
    calls: list[Dict[str, Any]] = []
    next_response: DummyResponse | Exception = DummyResponse({})

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.kwargs = kwargs

    async def __aenter__(self) -> "DummyAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def request(
        self, method: str, path: str, json: Dict[str, Any] | None = None, headers: Dict[str, str] | None = None
    ) -> DummyResponse:
        call = {
            "method": method,
            "path": path,
            "json": json,
            "headers": headers,
        }
        DummyAsyncClient.calls.append(call)
        response = DummyAsyncClient.next_response
        if isinstance(response, Exception):
            raise response
        return response


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    monkeypatch.delenv("KEEPERHUB_API_KEY", raising=False)


@pytest.fixture
def stub_http(monkeypatch):
    DummyAsyncClient.calls = []
    DummyAsyncClient.next_response = DummyResponse({})
    monkeypatch.setattr("agents.plugins.orbit.keeperhub.httpx.AsyncClient", DummyAsyncClient)
    return DummyAsyncClient


@pytest.mark.asyncio
async def test_create_workflow_returns_id(stub_http, monkeypatch):
    monkeypatch.setenv("KEEPERHUB_API_KEY", "kh_test")
    stub_http.next_response = DummyResponse({"workflow_id": "wf_123"})

    client = KeeperHubClient()
    workflow_id = await client.create_workflow(
        name="Escrow Release",
        trigger="job.complete",
        actions=[{"kind": "release_escrow", "job_id": "job_1"}],
    )

    assert workflow_id == "wf_123"
    assert stub_http.calls[-1]["path"] == "/mcp/workflows"


@pytest.mark.asyncio
async def test_trigger_execution_returns_execution_id(stub_http, monkeypatch):
    monkeypatch.setenv("KEEPERHUB_API_KEY", "kh_test")
    stub_http.next_response = DummyResponse({"execution_id": "exec_456"})

    client = KeeperHubClient()
    execution_id = await client.trigger_execution("wf_123", {"job_id": "job_9"})

    assert execution_id == "exec_456"
    assert stub_http.calls[-1]["path"] == "/mcp/workflows/wf_123/executions"


@pytest.mark.asyncio
async def test_check_execution_status_returns_payload(stub_http, monkeypatch):
    monkeypatch.setenv("KEEPERHUB_API_KEY", "kh_test")
    stub_http.next_response = DummyResponse({"status": "succeeded", "result": {"tx": "0x1"}})

    client = KeeperHubClient()
    status = await client.check_execution_status("exec_789")

    assert status["status"] == "succeeded"
    assert status["result"] == {"tx": "0x1"}


@pytest.mark.asyncio
async def test_create_workflow_missing_id_raises(monkeypatch, stub_http):
    monkeypatch.setenv("KEEPERHUB_API_KEY", "kh_test")
    stub_http.next_response = DummyResponse({"unexpected": True})

    client = KeeperHubClient()
    with pytest.raises(KeeperHubError):
        await client.create_workflow("Escrow Release", "job.complete", [{"kind": "noop"}])


def test_client_without_api_key_raises():
    with pytest.raises(KeeperHubError):
        KeeperHubClient(api_key=None)


def test_webhook_verifier_success():
    payload = b"{\"job_id\": \"123\"}"
    secret = "keeper_secret"
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    verifier = WebhookVerifier(secret=secret)

    assert verifier.verify(payload, f"sha256={digest}") is True


def test_webhook_verifier_rejects_invalid_signature():
    payload = b"{}"
    verifier = WebhookVerifier(secret="secret")

    assert verifier.verify(payload, "sha256=deadbeef") is False
