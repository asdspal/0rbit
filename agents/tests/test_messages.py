import pytest
from datetime import datetime
from agents.plugins.orbit import messages
from pydantic import ValidationError

def test_bid_payload_encode_decode():
    payload = messages.BidPayload(
        job_id="job123",
        proposed_amount="100",
        capabilities=["cap1", "cap2"],
        agent_ens="agent.eth"
    )
    msg = messages.AXLMessage(
        type="bid",
        src_peer_id="peer1",
        dst_peer_id="peer2",
        timestamp=datetime.utcnow(),
        payload=payload
    )
    encoded = messages.encode_message(msg)
    decoded = messages.decode_message(encoded)
    assert decoded.type == "bid"
    assert decoded.payload.job_id == "job123"
    assert decoded.payload.proposed_amount == "100"
    assert decoded.payload.capabilities == ["cap1", "cap2"]
    assert decoded.payload.agent_ens == "agent.eth"

def test_job_accepted_payload_encode_decode():
    payload = messages.JobAcceptedPayload(
        job_id="job456",
        spec_hash="hash123",
        deadline="2026-12-31T23:59:59Z"
    )
    msg = messages.AXLMessage(
        type="job_accepted",
        src_peer_id="peer1",
        dst_peer_id="peer2",
        timestamp=datetime.utcnow(),
        payload=payload
    )
    encoded = messages.encode_message(msg)
    decoded = messages.decode_message(encoded)
    assert decoded.type == "job_accepted"
    assert decoded.payload.job_id == "job456"
    assert decoded.payload.spec_hash == "hash123"
    assert decoded.payload.deadline == "2026-12-31T23:59:59Z"

def test_output_ready_payload_encode_decode():
    payload = messages.OutputReadyPayload(
        job_id="job789",
        output_hash="outputhash",
        og_storage_root="storageroot"
    )
    msg = messages.AXLMessage(
        type="output_ready",
        src_peer_id="peer1",
        dst_peer_id="peer2",
        timestamp=datetime.utcnow(),
        payload=payload
    )
    encoded = messages.encode_message(msg)
    decoded = messages.decode_message(encoded)
    assert decoded.type == "output_ready"
    assert decoded.payload.job_id == "job789"
    assert decoded.payload.output_hash == "outputhash"
    assert decoded.payload.og_storage_root == "storageroot"

def test_ping_payload_encode_decode():
    payload = messages.PingPayload(timestamp="2026-05-04T00:00:00Z")
    msg = messages.AXLMessage(
        type="ping",
        src_peer_id="peer1",
        dst_peer_id="peer2",
        timestamp=datetime.utcnow(),
        payload=payload
    )
    encoded = messages.encode_message(msg)
    decoded = messages.decode_message(encoded)
    assert decoded.type == "ping"
    assert decoded.payload.timestamp == "2026-05-04T00:00:00Z"

def test_invalid_message_type():
    # Create a dict with invalid type
    data = {
        "type": "invalid_type",
        "src_peer_id": "peer1",
        "dst_peer_id": "peer2",
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {}
    }
    import json
    raw = json.dumps(data).encode('utf-8')
    with pytest.raises(ValidationError):
        messages.decode_message(raw)
