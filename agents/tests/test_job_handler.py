from __future__ import annotations

import asyncio
import os
import sys
from typing import Any

import httpx
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from agents.plugins.orbit.job_handler import JobHandler


class DummyAXLClient:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

    def send(self, dst_peer_id: str, data: bytes | str) -> dict[str, Any]:
        self.sent.append({"dst": dst_peer_id, "data": data})
        return {"message_id": "axl-123"}


class DummyTransport(httpx.AsyncBaseTransport):
    def __init__(self) -> None:
        self.responses: dict[str, httpx.Response] = {}
        self.requests: list[httpx.Request] = []

    def add_response(self, method: str, path: str, json: Any) -> None:
        key = f"{method.upper()} {path}"
        self.responses[key] = httpx.Response(200, json=json)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:  # type: ignore[override]
        self.requests.append(request)
        key = f"{request.method} {request.url.path}"
        response = self.responses.get(key)
        if response is None:
            raise RuntimeError(f"No response stub for {key}")
        return response


def _make_handler(monkeypatch, jobs_payload):
    axl = DummyAXLClient()
    transport = DummyTransport()
    transport.add_response("GET", "/v1/jobs", {"data": jobs_payload})
    client = httpx.AsyncClient(transport=transport, base_url="https://backend")
    monkeypatch.setattr("agents.plugins.orbit.job_handler.httpx.AsyncClient", lambda **_: client)
    handler = JobHandler(axl, "agent.eth", "peer-agent", ["code", "research"])
    return handler, transport, axl


@pytest.mark.asyncio
async def test_discover_jobs_filters_by_capabilities(monkeypatch):
    jobs = [
        {"id": "job-1", "required_capabilities": ["code"], "poster_peer_id": "poster"},
        {"id": "job-2", "required_capabilities": ["audit"], "poster_peer_id": "poster"},
    ]
    handler, transport, _ = _make_handler(monkeypatch, jobs)

    matched = await handler.discover_jobs("https://backend")

    assert len(matched) == 1
    assert matched[0]["id"] == "job-1"
    request = transport.requests[0]
    assert request.url.params.get("status") == "posted"


@pytest.mark.asyncio
async def test_bid_on_job_calls_axl_and_backend(monkeypatch):
    job = {"id": "job-1", "poster_peer_id": "poster", "required_capabilities": ["code"]}
    handler, transport, axl = _make_handler(monkeypatch, [job])
    transport.add_response("POST", "/v1/jobs/job-1/bids", {"id": "bid-1"})

    record = await handler.bid_on_job(job, "123", "poster", "https://backend")

    assert record["id"] == "bid-1"
    assert axl.sent[0]["dst"] == "poster"
    assert "job-1" in handler._bid_cache


@pytest.mark.asyncio
async def test_run_discovery_loop_handles_bid_errors(monkeypatch):
    handler, _, _ = _make_handler(monkeypatch, [])

    async def fake_discover(_):
        return [{"id": "job-1", "poster_peer_id": "poster", "required_capabilities": ["code"]}]

    async def fake_bid(*_args, **_kwargs):
        raise RuntimeError("fail")

    monkeypatch.setattr(handler, "discover_jobs", fake_discover)
    monkeypatch.setattr(handler, "bid_on_job", fake_bid)

    async def run_loop():
        await handler.run_discovery_loop("https://backend", interval=1, proposed_amount="123")

    task = asyncio.create_task(run_loop())
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
