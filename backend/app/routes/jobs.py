"""Job routes implementing Section 8.3 POST/GET /jobs."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.database import get_supabase_client
from app.deps import get_current_user

logger = logging.getLogger(__name__)


class JobCreate(BaseModel):
    """Payload for POST /v1/jobs as defined in Section 8.3."""

    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    capabilities: list[str] = Field(min_length=1)
    payment_token: str = Field(min_length=1)
    escrow_amount: str = Field(min_length=1)
    deadline: datetime


class AssignJob(BaseModel):
    """Payload for POST /v1/jobs/{id}/assign (Section 8.3)."""

    bid_id: str = Field(min_length=1)


class CompleteJob(BaseModel):
    """Payload for POST /v1/jobs/{id}/complete (Section 8.3)."""

    output_hash: str = Field(min_length=1)
    compute_proof: str = Field(min_length=1)


router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


def _extract_supabase_error(error: Any) -> tuple[str | None, str | None]:
    if not error:
        return None, None

    if isinstance(error, dict):
        return error.get("message"), error.get("code")

    return getattr(error, "message", str(error)), getattr(error, "code", None)


def _parse_cursor(cursor: str | None) -> int:
    if cursor is None:
        return 0

    try:
        offset = int(cursor, 10)
    except ValueError as exc:  # pragma: no cover - defensive branch
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cursor") from exc

    if offset < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cursor")

    return offset


def _compute_job_spec_hash(description: str) -> str:
    """Temporary placeholder hash until 0G storage integration is wired (Section 7)."""

    return hashlib.sha256(description.encode("utf-8")).hexdigest()


@router.post("/", summary="Create job", status_code=status.HTTP_201_CREATED)
async def create_job(payload: JobCreate, poster_address: str = Depends(get_current_user)) -> dict[str, Any]:
    """Insert a new job with status posted per Section 8.3.

    Note: job_spec_hash is derived from the description until the onchain + storage flow is implemented.
    """

    client = get_supabase_client()

    record = {
        "poster_address": poster_address,
        "title": payload.title,
        "description": payload.description,
        "job_spec_hash": _compute_job_spec_hash(payload.description),
        "required_capabilities": list(payload.capabilities),
        "payment_token": payload.payment_token,
        "escrow_amount": payload.escrow_amount,
        "deadline": payload.deadline,
        "status": "posted",
    }

    response = client.table("jobs").insert(record).execute()
    error = getattr(response, "error", None)
    if error:
        message, code = _extract_supabase_error(error)
        logger.error("Supabase insert job failed (code=%s): %s", code, message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create job")

    data = getattr(response, "data", None) or []
    if not isinstance(data, list) or not data:
        logger.error("Supabase insert returned no data for job poster %s", poster_address)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create job")

    return data[0]


@router.get("/", summary="List jobs")
async def list_jobs(
    status: str | None = Query(default=None),
    capabilities: list[str] | None = Query(default=None, alias="capabilities[]"),
    sort: str = Query(default="created_at"),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> dict[str, Any]:
    """Return paginated job list filtered per Section 8.3."""

    allowed_sorts = {"created_at", "deadline"}
    if sort not in allowed_sorts:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort field")

    offset = _parse_cursor(cursor)
    client = get_supabase_client()

    query = (
        client.table("jobs")
        .select("*")
        .order(sort, desc=True)
    )

    if status:
        query = query.eq("status", status)
    if capabilities:
        query = query.contains("required_capabilities", capabilities)

    end = offset + limit
    response = query.range(offset, end).execute()
    error = getattr(response, "error", None)
    if error:
        message, code = _extract_supabase_error(error)
        logger.error("Supabase list jobs failed (code=%s): %s", code, message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load jobs")

    data = getattr(response, "data", None) or []
    has_more = len(data) > limit
    if has_more:
        data = data[:limit]
        next_cursor: str | None = str(offset + limit)
    else:
        next_cursor = None

    return {"data": data, "cursor": next_cursor}


__all__ = [
    "create_job",
    "list_jobs",
    "get_job",
    "assign_job",
    "complete_job",
    "dispute_job",
]


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


@router.get("/{job_id}", summary="Get job by id with bids")
async def get_job(job_id: UUID) -> dict[str, Any]:
    """Return a single job enriched with its bids (Section 8.3)."""

    client = get_supabase_client()

    job_response = (
        client.table("jobs")
        .select("*")
        .eq("id", str(job_id))
        .limit(1)
        .execute()
    )
    job = _fetch_single_record(job_response, "Job not found")

    bids_response = (
        client.table("bids")
        .select("*")
        .eq("job_id", str(job_id))
        .order("created_at", desc=True)
        .execute()
    )

    bids_error = getattr(bids_response, "error", None)
    if bids_error:
        message, code = _extract_supabase_error(bids_error)
        logger.error("Supabase list bids for job %s failed (code=%s): %s", job_id, code, message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load bids")

    bids = getattr(bids_response, "data", None) or []

    enriched: dict[str, Any] = dict(job)
    enriched["bids"] = bids
    return enriched


@router.post("/{job_id}/assign", summary="Assign job to bid")
async def assign_job(job_id: UUID, payload: AssignJob, address: str = Depends(get_current_user)) -> dict[str, str]:
    """Assign a job to the bid's agent after verifying poster ownership (Section 8.3)."""

    client = get_supabase_client()

    job_response = (
        client.table("jobs")
        .select("id,poster_address,status")
        .eq("id", str(job_id))
        .limit(1)
        .execute()
    )
    job = _fetch_single_record(job_response, "Job not found")

    if job.get("poster_address", "").lower() != address.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to assign job")

    bid_response = (
        client.table("bids")
        .select("id,job_id,agent_id,status")
        .eq("id", payload.bid_id)
        .limit(1)
        .execute()
    )
    bid = _fetch_single_record(bid_response, "Bid not found")

    if str(bid.get("job_id")) != str(job_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bid does not belong to job")

    job_update = (
        client.table("jobs")
        .update(
            {
                "assigned_agent_id": bid.get("agent_id"),
                "status": "assigned",
            }
        )
        .eq("id", str(job_id))
        .execute()
    )

    job_update_error = getattr(job_update, "error", None)
    if job_update_error:
        message, code = _extract_supabase_error(job_update_error)
        logger.error("Supabase assign job %s failed (code=%s): %s", job_id, code, message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to assign job")

    bid_update = (
        client.table("bids")
        .update({"status": "accepted"})
        .eq("id", payload.bid_id)
        .execute()
    )

    bid_update_error = getattr(bid_update, "error", None)
    if bid_update_error:
        message, code = _extract_supabase_error(bid_update_error)
        logger.error("Supabase update bid %s failed (code=%s): %s", payload.bid_id, code, message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to assign bid")

    return {"status": "assigned"}


@router.post("/{job_id}/complete", summary="Complete job")
async def complete_job(job_id: UUID, payload: CompleteJob, address: str = Depends(get_current_user)) -> dict[str, str]:
    """Mark a job as completed by the assigned agent (Section 8.3)."""

    client = get_supabase_client()

    job_response = (
        client.table("jobs")
        .select("id,assigned_agent_id")
        .eq("id", str(job_id))
        .limit(1)
        .execute()
    )
    job = _fetch_single_record(job_response, "Job not found")

    assigned_agent_id = job.get("assigned_agent_id")
    if not assigned_agent_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is not assigned")

    agent_response = (
        client.table("agents")
        .select("wallet_address")
        .eq("id", str(assigned_agent_id))
        .limit(1)
        .execute()
    )
    agent = _fetch_single_record(agent_response, "Assigned agent not found")

    wallet = agent.get("wallet_address")
    if not wallet or wallet.lower() != address.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to complete job")

    update_response = (
        client.table("jobs")
        .update(
            {
                "output_hash": payload.output_hash,
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", str(job_id))
        .execute()
    )

    update_error = getattr(update_response, "error", None)
    if update_error:
        message, code = _extract_supabase_error(update_error)
        logger.error("Supabase complete job %s failed (code=%s): %s", job_id, code, message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to complete job")

    logger.warning("TODO Section 10.2: trigger KeeperHub escrow release workflow")

    return {"status": "completed", "output_hash": payload.output_hash}


@router.post("/{job_id}/dispute", summary="Open job dispute")
async def dispute_job(job_id: UUID, address: str = Depends(get_current_user)) -> dict[str, str]:
    """Mark a job as disputed by poster or assigned agent (Section 8.3)."""

    client = get_supabase_client()

    job_response = (
        client.table("jobs")
        .select("id,poster_address,assigned_agent_id")
        .eq("id", str(job_id))
        .limit(1)
        .execute()
    )
    job = _fetch_single_record(job_response, "Job not found")

    is_poster = job.get("poster_address", "").lower() == address.lower()
    is_assigned_agent = False

    assigned_agent_id = job.get("assigned_agent_id")
    if assigned_agent_id:
        agent_response = (
            client.table("agents")
            .select("wallet_address")
            .eq("id", str(assigned_agent_id))
            .limit(1)
            .execute()
        )
        agent = _fetch_single_record(agent_response, "Assigned agent not found")
        wallet = agent.get("wallet_address")
        if wallet:
            is_assigned_agent = wallet.lower() == address.lower()

    if not (is_poster or is_assigned_agent):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to dispute job")

    update_response = (
        client.table("jobs")
        .update({"status": "disputed"})
        .eq("id", str(job_id))
        .execute()
    )

    update_error = getattr(update_response, "error", None)
    if update_error:
        message, code = _extract_supabase_error(update_error)
        logger.error("Supabase dispute job %s failed (code=%s): %s", job_id, code, message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to dispute job")

    return {"status": "disputed"}
