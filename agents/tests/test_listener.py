import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from agents.plugins.orbit.listener import AXLListener
from agents.plugins.orbit.messages import AXLMessage, BidPayload
from datetime import datetime

class DummyAXLClient:
    def __init__(self, messages):
        self._messages = messages
        self.recv_called = 0
    def recv(self):
        self.recv_called += 1
        return self._messages

@pytest.mark.asyncio
async def test_start_stop_and_message_routing():
    # Prepare a dummy message encoded
    payload = BidPayload(job_id="job1", proposed_amount="10", capabilities=["cap1"], agent_ens="agent.eth")
    msg = AXLMessage(type="bid", src_peer_id="src", dst_peer_id="dst", timestamp=datetime.utcnow(), payload=payload)
    raw_msg = msg.json().encode('utf-8')

    dummy_client = DummyAXLClient([raw_msg])
    listener = AXLListener(dummy_client)

    # Create a mock handler
    mock_handler = AsyncMock()
    listener.on("bid", mock_handler)

    # Run listener start in background task
    async def run_listener():
        await listener.start()

    task = asyncio.create_task(run_listener())

    # Wait a bit for the listener to process
    await asyncio.sleep(0.1)

    # Stop the listener
    await listener.stop()

    # Wait for task to finish
    await task

    # Check that handler was called once with the decoded message
    mock_handler.assert_awaited_once()
    called_arg = mock_handler.call_args[0][0]
    assert isinstance(called_arg, AXLMessage)
    assert called_arg.type == "bid"

@pytest.mark.asyncio
async def test_listener_handles_no_handler_and_exceptions():
    dummy_client = DummyAXLClient([])
    listener = AXLListener(dummy_client)

    # No handler registered, should not fail
    async def run_listener():
        await listener.start()

    task = asyncio.create_task(run_listener())
    await asyncio.sleep(0.1)
    await listener.stop()
    await task

    # Register a handler that raises
    async def bad_handler(msg):
        raise RuntimeError("fail")

    listener.on("bid", bad_handler)
    dummy_client._messages = [AXLMessage(type="bid", src_peer_id="a", dst_peer_id="b", timestamp=datetime.utcnow(), payload=BidPayload(job_id="j", proposed_amount="1", capabilities=[], agent_ens="e"))
                              .json().encode('utf-8')]

    task = asyncio.create_task(run_listener())
    await asyncio.sleep(0.1)
    await listener.stop()
    await task
