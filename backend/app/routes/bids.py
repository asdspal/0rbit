"""Bid routes implementing Section 8.4 POST/PATCH endpoints."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.database import get_supabase_client
from app.deps import get_current_user

logger = logging.getLogger(__name__)


class BidCreate(BaseModel):
    """Payload for POST /v1/jobs/{job_id}/bids (Section 8.4)."""

    proposed_amount: str = Field(min_length=1)
    message: str = Field(min_length=1)
    axl_message_id: str | None = Field(default=None)


router = APIRouter(prefix="/v1", tags=["bids"])


def _extract_supabase_error(error: Any) -> tuple[str | None, str | None]:
    if not error:
        return None, None

    if isinstance(error, dict):
        return error.get("message"), error.get("code")

    return getattr(error, "message", str(error)), getattr(error, "code", None)


def _fetch_single_record(response: Any, not_found_message: str) -> dict[str, Any]:
    error = getattr(response, "error", None)
    if error:
        message, code = _extract_supabase_error(error)
        logger.error("Supabase query failed (code=%s): %s", code, message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=not_found_message)

    data = getattr(response, "data", None)
    if not isinstance(data, list) or not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_message)

    return data[0]


@router.post("/jobs/{job_id}/bids", summary="Create bid", status_code=status.HTTP_201_CREATED)
async def create_bid(job_id: UUID, payload: BidCreate, address: str = Depends(get_current_user)) -> dict[str, Any]:
    """Insert a bid linked to the calling agent (Section 8.4)."""

    client = get_supabase_client()

    agent_response = (
        client.table("agents")
        .select("id,wallet_address")
        .eq("wallet_address", address)
        .limit(1)
        .execute()
    )
    agent = _fetch_single_record(agent_response, "Agent not found")

    record = {
        "job_id": str(job_id),
        "agent_id": agent.get("id"),
        "proposed_amount": payload.proposed_amount,
        "message": payload.message,
        "axl_message_id": payload.axl_message_id,
        "status": "pending",
    }

    response = client.table("bids").insert(record).execute()
    error = getattr(response, "error", None)
    if error:
        message, code = _extract_supabase_error(error)
        logger.error("Supabase insert bid failed (code=%s): %s", code, message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create bid")

    data = getattr(response, "data", None) or []
    if not isinstance(data, list) or not data:
        logger.error("Supabase insert returned no data for bid on job %s", job_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create bid")

    return data[0]


@router.patch("/bids/{bid_id}/withdraw", summary="Withdraw bid")
async def withdraw_bid(bid_id: UUID, address: str = Depends(get_current_user)) -> dict[str, Any]:
    """Withdraw a bid after verifying bidder ownership (Section 8.4)."""

    client = get_supabase_client()

    bid_response = (
        client.table("bids")
        .select("id,agent_id,status")
        .eq("id", str(bid_id))
        .limit(1)
        .execute()
    )
    bid = _fetch_single_record(bid_response, "Bid not found")

    agent_id = bid.get("agent_id")
    if not agent_id:
        logger.error("Bid %s missing agent_id", bid_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to withdraw bid")

    agent_response = (
        client.table("agents")
        .select("wallet_address")
        .eq("id", str(agent_id))
        .limit(1)
        .execute()
    )
    agent = _fetch_single_record(agent_response, "Agent not found")

    wallet = agent.get("wallet_address")
    if not wallet or wallet.lower() != address.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to withdraw bid")

    update_response = (
        client.table("bids")
        .update({"status": "withdrawn"})
        .eq("id", str(bid_id))
        .execute()
    )

    update_error = getattr(update_response, "error", None)
    if update_error:
        message, code = _extract_supabase_error(update_error)
        logger.error("Supabase withdraw bid %s failed (code=%s): %s", bid_id, code, message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to withdraw bid")

    updated = getattr(update_response, "data", None) or []
    if not isinstance(updated, list) or not updated:
        logger.error("Supabase withdraw returned no data for bid %s", bid_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to withdraw bid")

    return updated[0]
