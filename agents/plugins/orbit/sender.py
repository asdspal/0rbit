from datetime import datetime

from agents.plugins.orbit.axl_client import AXLClient
from agents.plugins.orbit.messages import (
    AXLMessage,
    BidPayload,
    JobAcceptedPayload,
    OutputReadyPayload,
    PingPayload,
    encode_message,
)


async def _send(axl: AXLClient, dst_peer_id: str, message: AXLMessage) -> None:
    payload = encode_message(message)
    axl.send(dst_peer_id, payload)


async def send_bid(
    axl: AXLClient,
    src_peer_id: str,
    dst_peer_id: str,
    job_id: str,
    proposed_amount: str,
    capabilities: list[str],
    agent_ens: str,
) -> None:
    message = AXLMessage(
        type="bid",
        src_peer_id=src_peer_id,
        dst_peer_id=dst_peer_id,
        timestamp=datetime.utcnow(),
        payload=BidPayload(
            job_id=job_id,
            proposed_amount=proposed_amount,
            capabilities=capabilities,
            agent_ens=agent_ens,
        ),
    )
    await _send(axl, dst_peer_id, message)


async def send_job_accepted(
    axl: AXLClient,
    src_peer_id: str,
    dst_peer_id: str,
    job_id: str,
    spec_hash: str,
    deadline: str,
) -> None:
    message = AXLMessage(
        type="job_accepted",
        src_peer_id=src_peer_id,
        dst_peer_id=dst_peer_id,
        timestamp=datetime.utcnow(),
        payload=JobAcceptedPayload(
            job_id=job_id,
            spec_hash=spec_hash,
            deadline=deadline,
        ),
    )
    await _send(axl, dst_peer_id, message)


async def send_output_ready(
    axl: AXLClient,
    src_peer_id: str,
    dst_peer_id: str,
    job_id: str,
    output_hash: str,
    og_storage_root: str,
) -> None:
    message = AXLMessage(
        type="output_ready",
        src_peer_id=src_peer_id,
        dst_peer_id=dst_peer_id,
        timestamp=datetime.utcnow(),
        payload=OutputReadyPayload(
            job_id=job_id,
            output_hash=output_hash,
            og_storage_root=og_storage_root,
        ),
    )
    await _send(axl, dst_peer_id, message)


async def send_ping(
    axl: AXLClient,
    src_peer_id: str,
    dst_peer_id: str,
) -> None:
    message = AXLMessage(
        type="ping",
        src_peer_id=src_peer_id,
        dst_peer_id=dst_peer_id,
        timestamp=datetime.utcnow(),
        payload=PingPayload(
            timestamp=datetime.utcnow().isoformat()
        ),
    )
    await _send(axl, dst_peer_id, message)
