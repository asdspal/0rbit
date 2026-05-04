from datetime import datetime
from typing import Literal, Union
import json
from pydantic import BaseModel, ValidationError

class BidPayload(BaseModel):
    job_id: str
    proposed_amount: str
    capabilities: list[str]
    agent_ens: str

class JobAcceptedPayload(BaseModel):
    job_id: str
    spec_hash: str
    deadline: str

class OutputReadyPayload(BaseModel):
    job_id: str
    output_hash: str
    og_storage_root: str

class PingPayload(BaseModel):
    timestamp: str

class AXLMessage(BaseModel):
    type: Literal["bid", "job_accepted", "output_ready", "ping"]
    src_peer_id: str
    dst_peer_id: str
    timestamp: datetime
    payload: Union[BidPayload, JobAcceptedPayload, OutputReadyPayload, PingPayload]

def encode_message(msg: AXLMessage) -> bytes:
    # Serialize to JSON bytes
    return msg.json().encode('utf-8')

def decode_message(data: bytes) -> AXLMessage:
    # Deserialize from JSON bytes
    try:
        return AXLMessage.parse_raw(data)
    except ValidationError as e:
        raise e
