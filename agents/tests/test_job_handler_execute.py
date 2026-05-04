from __future__ import annotations

import os
import sys
from typing import Any

import httpx
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from agents.plugins.orbit.job_handler import JobHandler
from agents.plugins.orbit.messages import JobAcceptedPayload


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

    def add_response(self, method: str, path: str, json: Any, status_code: int = 200) -> None:
        key = f"{method.upper()} {path}"
        self.responses[key] = httpx.Response(status_code, json=json)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:  # type: ignore[override]
        self.requests.append(request)
        key = f"{request.method} {request.url.path}"
        response = self.responses.get(key)
        if response is None:
            raise RuntimeError(f"No response stub for {key}")
        return response


def _install_http_client(monkeypatch, transport: DummyTransport) -> None:
    original_async_client = httpx.AsyncClient

    def _factory(**kwargs: Any) -> httpx.AsyncClient:
        kwargs = dict(kwargs)
        kwargs.pop("transport", None)
        return original_async_client(transport=transport, **kwargs)

    monkeypatch.setattr("agents.plugins.orbit.job_handler.httpx.AsyncClient", _factory)


@pytest.mark.asyncio
async def test_handle_job_accepted_executes_uploads_and_posts(monkeypatch):
    transport = DummyTransport()
    transport.add_response("GET", "/v1/jobs/job-1", {"id": "job-1", "title": "Demo"})
    transport.add_response("POST", "/v1/jobs/job-1/complete", {"status": "completed"})
    _install_http_client(monkeypatch, transport)

    axl = DummyAXLClient()
    handler = JobHandler(axl, "agent.eth", "peer-agent", ["code"])

    uploads: dict[str, Any] = {}

    def fake_upload(data: bytes, filename: str | None = None, *, client=None) -> str:
        uploads["data"] = data
        uploads["filename"] = filename
        return "og-root"

    async def fake_submit(data: bytes, *, client=None):
        uploads["verified_data"] = data
        return "out-hash", b"\x01\x02"

    send_calls: dict[str, Any] = {}

    async def fake_send_output_ready(axl_client, src, dst, job_id, output_hash, og_root):
        send_calls["args"] = (src, dst, job_id, output_hash, og_root)

    async def fake_execute(job):
        return b"result-bytes"

    monkeypatch.setattr("agents.plugins.orbit.job_handler.upload_data", fake_upload)
    monkeypatch.setattr("agents.plugins.orbit.job_handler.submit_for_verification", fake_submit)
    monkeypatch.setattr("agents.plugins.orbit.job_handler.send_output_ready", fake_send_output_ready)
    monkeypatch.setattr(handler, "execute_job", fake_execute)

    msg = JobAcceptedPayload(job_id="job-1", spec_hash="spec", deadline="2026-01-01T00:00:00Z")

    backend_response = await handler.handle_job_accepted(msg, "poster-peer", "https://backend")

    assert backend_response["status"] == "completed"
    assert uploads["data"] == b"result-bytes"
    assert uploads["filename"] == "job_job-1"
    assert send_calls["args"] == ("peer-agent", "poster-peer", "job-1", "out-hash", "og-root")
    assert [req.url.path for req in transport.requests] == ["/v1/jobs/job-1", "/v1/jobs/job-1/complete"]


@pytest.mark.asyncio
async def test_execute_job_returns_placeholder_bytes():
    handler = JobHandler(DummyAXLClient(), "agent.eth", "peer-agent", ["code"])
    payload = await handler.execute_job({"job_id": "job-42"})
    assert payload == b"Mock job output for job-42"
