
import os
import sys
import pytest
import asyncio
from unittest.mock import AsyncMock
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from agents.plugins.orbit.sender import send_bid, send_job_accepted, send_output_ready, send_ping
from agents.plugins.orbit.messages import AXLMessage

class DummyAXLClient:
    def __init__(self):
        self.send = AsyncMock()

@pytest.mark.asyncio
async def test_send_bid():
    axl = DummyAXLClient()
    await send_bid(axl, "src", "dst", "job1", "100", ["cap1", "cap2"], "agent.ens")
    assert axl.send.called
    args, kwargs = axl.send.call_args
    assert args[0] == "dst"
    msg = AXLMessage.parse_raw(args[1])
    assert msg.type == "bid"
    assert msg.payload.job_id == "job1"
    assert msg.payload.proposed_amount == "100"
    assert msg.payload.capabilities == ["cap1", "cap2"]
    assert msg.payload.agent_ens == "agent.ens"

@pytest.mark.asyncio
async def test_send_job_accepted():
    axl = DummyAXLClient()
    await send_job_accepted(axl, "src", "dst", "job1", "spec123", "deadline123")
    assert axl.send.called
    args, kwargs = axl.send.call_args
    assert args[0] == "dst"
    msg = AXLMessage.parse_raw(args[1])
    assert msg.type == "job_accepted"
    assert msg.payload.job_id == "job1"
    assert msg.payload.spec_hash == "spec123"
    assert msg.payload.deadline == "deadline123"

@pytest.mark.asyncio
async def test_send_output_ready():
    axl = DummyAXLClient()
    await send_output_ready(axl, "src", "dst", "job1", "outputhash", "ogroot")
    assert axl.send.called
    args, kwargs = axl.send.call_args
    assert args[0] == "dst"
    msg = AXLMessage.parse_raw(args[1])
    assert msg.type == "output_ready"
    assert msg.payload.job_id == "job1"
    assert msg.payload.output_hash == "outputhash"
    assert msg.payload.og_storage_root == "ogroot"

@pytest.mark.asyncio
async def test_send_ping():
    axl = DummyAXLClient()
    await send_ping(axl, "src", "dst")
    assert axl.send.called
    args, kwargs = axl.send.call_args
    assert args[0] == "dst"
    msg = AXLMessage.parse_raw(args[1])
    assert msg.type == "ping"
    assert "timestamp" in msg.payload.dict()

class DummyAXLClient:
    def __init__(self):
        self.send = AsyncMock()

@pytest.mark.asyncio
async def test_send_bid():
    axl = DummyAXLClient()
    await send_bid(axl, "src", "dst", "job1", "100", ["cap1", "cap2"], "agent.ens")
    assert axl.send.called
    args, kwargs = axl.send.call_args
    assert args[0] == "dst"
    msg = AXLMessage.parse_raw(args[1])
    assert msg.type == "bid"
    assert msg.payload.job_id == "job1"
    assert msg.payload.proposed_amount == "100"
    assert msg.payload.capabilities == ["cap1", "cap2"]
    assert msg.payload.agent_ens == "agent.ens"

@pytest.mark.asyncio
async def test_send_job_accepted():
    axl = DummyAXLClient()
    await send_job_accepted(axl, "src", "dst", "job1", "spec123", "deadline123")
    assert axl.send.called
    args, kwargs = axl.send.call_args
    assert args[0] == "dst"
    msg = AXLMessage.parse_raw(args[1])
    assert msg.type == "job_accepted"
    assert msg.payload.job_id == "job1"
    assert msg.payload.spec_hash == "spec123"
    assert msg.payload.deadline == "deadline123"

@pytest.mark.asyncio
async def test_send_output_ready():
    axl = DummyAXLClient()
    await send_output_ready(axl, "src", "dst", "job1", "outputhash", "ogroot")
    assert axl.send.called
    args, kwargs = axl.send.call_args
    assert args[0] == "dst"
    msg = AXLMessage.parse_raw(args[1])
    assert msg.type == "output_ready"
    assert msg.payload.job_id == "job1"
    assert msg.payload.output_hash == "outputhash"
    assert msg.payload.og_storage_root == "ogroot"

@pytest.mark.asyncio
async def test_send_ping():
    axl = DummyAXLClient()
    await send_ping(axl, "src", "dst")
    assert axl.send.called
    args, kwargs = axl.send.call_args
    assert args[0] == "dst"
    msg = AXLMessage.parse_raw(args[1])
    assert msg.type == "ping"
    assert "timestamp" in msg.payload.dict()

class DummyAXLClient:
    def __init__(self):
        self.send = AsyncMock()

@pytest.mark.asyncio
async def test_send_bid():
    axl = DummyAXLClient()
    await send_bid(axl, "src", "dst", "job1", "100", ["cap1", "cap2"], "agent.ens")
    assert axl.send.called
    args, kwargs = axl.send.call_args
    assert args[0] == "dst"
    msg = AXLMessage.parse_raw(args[1])
    assert msg.type == "bid"
    assert msg.payload.job_id == "job1"
    assert msg.payload.proposed_amount == "100"
    assert msg.payload.capabilities == ["cap1", "cap2"]
    assert msg.payload.agent_ens == "agent.ens"

@pytest.mark.asyncio
async def test_send_job_accepted():
    axl = DummyAXLClient()
    await send_job_accepted(axl, "src", "dst", "job1", "spec123", "deadline123")
    assert axl.send.called
    args, kwargs = axl.send.call_args
    assert args[0] == "dst"
    msg = AXLMessage.parse_raw(args[1])
    assert msg.type == "job_accepted"
    assert msg.payload.job_id == "job1"
    assert msg.payload.spec_hash == "spec123"
    assert msg.payload.deadline == "deadline123"

@pytest.mark.asyncio
async def test_send_output_ready():
    axl = DummyAXLClient()
    await send_output_ready(axl, "src", "dst", "job1", "outputhash", "ogroot")
    assert axl.send.called
    args, kwargs = axl.send.call_args
    assert args[0] == "dst"
    msg = AXLMessage.parse_raw(args[1])
    assert msg.type == "output_ready"
    assert msg.payload.job_id == "job1"
    assert msg.payload.output_hash == "outputhash"
    assert msg.payload.og_storage_root == "ogroot"

@pytest.mark.asyncio
async def test_send_ping():
    axl = DummyAXLClient()
    await send_ping(axl, "src", "dst")
    assert axl.send.called
    args, kwargs = axl.send.call_args
    assert args[0] == "dst"
    msg = AXLMessage.parse_raw(args[1])
    assert msg.type == "ping"
    assert "timestamp" in msg.payload.dict()

class DummyAXLClient:
    def __init__(self):
        self.send = AsyncMock()

@pytest.mark.asyncio
async def test_send_bid():
    axl = DummyAXLClient()
    await send_bid(axl, "src", "dst", "job1", "100", ["cap1", "cap2"], "agent.ens")
    assert axl.send.called
    args, kwargs = axl.send.call_args
    assert args[0] == "dst"
    msg = AXLMessage.parse_raw(args[1])
    assert msg.type == "bid"
    assert msg.payload.job_id == "job1"
    assert msg.payload.proposed_amount == "100"
    assert msg.payload.capabilities == ["cap1", "cap2"]
    assert msg.payload.agent_ens == "agent.ens"

@pytest.mark.asyncio
async def test_send_job_accepted():
    axl = DummyAXLClient()
    await send_job_accepted(axl, "src", "dst", "job1", "spec123", "deadline123")
    assert axl.send.called
    args, kwargs = axl.send.call_args
    assert args[0] == "dst"
    msg = AXLMessage.parse_raw(args[1])
    assert msg.type == "job_accepted"
    assert msg.payload.job_id == "job1"
    assert msg.payload.spec_hash == "spec123"
    assert msg.payload.deadline == "deadline123"

@pytest.mark.asyncio
async def test_send_output_ready():
    axl = DummyAXLClient()
    await send_output_ready(axl, "src", "dst", "job1", "outputhash", "ogroot")
    assert axl.send.called
    args, kwargs = axl.send.call_args
    assert args[0] == "dst"
    msg = AXLMessage.parse_raw(args[1])
    assert msg.type == "output_ready"
    assert msg.payload.job_id == "job1"
    assert msg.payload.output_hash == "outputhash"
    assert msg.payload.og_storage_root == "ogroot"

@pytest.mark.asyncio
async def test_send_ping():
    axl = DummyAXLClient()
    await send_ping(axl, "src", "dst")
    assert axl.send.called
    args, kwargs = axl.send.call_args
    assert args[0] == "dst"
    msg = AXLMessage.parse_raw(args[1])
    assert msg.type == "ping"
    assert "timestamp" in msg.payload.dict()
