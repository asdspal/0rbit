"""Agent routes covering Section 8.2 register, read, update, and history endpoints."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, root_validator

from app.database import get_supabase_client
from app.deps import get_current_user
from app.redis import _get_client

logger = logging.getLogger(__name__)


class AgentRegister(BaseModel):
    """Pydantic model for POST /v1/agents/register payload."""

    ens_label: str = Field(min_length=1)
    axl_peer_id: str = Field(min_length=1)
    capabilities: list[str] = Field(min_length=1)
    encrypted_uri: str = Field(min_length=1)


class AgentUpdate(BaseModel):
    """Payload for PATCH /v1/agents/{agent_id}."""

    capabilities: list[str] | None = Field(default=None, min_length=1)
    status: str | None = Field(default=None, min_length=1)

    @root_validator(pre=True)
    def _ensure_payload_has_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        if not values:
            raise ValueError("At least one field must be provided")
        if not any(values.get(field) is not None for field in ("capabilities", "status")):
            raise ValueError("At least one field must be provided")
        return values


router = APIRouter(prefix="/v1/agents", tags=["agents"])


def _extract_supabase_error(error: Any) -> tuple[str | None, str | None]:
    """Normalize Supabase error payloads to message and code tuple."""

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


@router.get("/", summary="List agents")
async def list_agents(
    capabilities: list[str] | None = Query(default=None, alias="capabilities[]"),
    min_rep: int | None = Query(default=None, alias="min_rep", ge=0),
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> dict[str, Any]:
    """Return paginated agent list filtered per Section 8.2."""

    offset = _parse_cursor(cursor)

    client = get_supabase_client()
    query = (
        client.table("agents")
        .select("*")
        .order("created_at", desc=True)
    )

    if status:
        query = query.eq("status", status)
    if min_rep is not None:
        query = query.gte("reputation_score", min_rep)
    if capabilities:
        query = query.contains("capabilities", capabilities)

    end = offset + limit
    response = query.range(offset, end).execute()
    error = getattr(response, "error", None)
    if error:
        message, code = _extract_supabase_error(error)
        logger.error("Supabase list agents failed (code=%s): %s", code, message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load agents")

    data = getattr(response, "data", None) or []
    has_more = len(data) > limit
    if has_more:
        data = data[:limit]
        next_cursor: str | None = str(offset + limit)
    else:
        next_cursor = None

    return {"data": data, "cursor": next_cursor}


@router.post("/register", summary="Register an agent", status_code=status.HTTP_201_CREATED)
async def register_agent(payload: AgentRegister, address: str = Depends(get_current_user)) -> dict[str, Any]:
    """Insert a new agent record using the blueprint columns from Section 7."""

    client = get_supabase_client()
    ens_name = f"{payload.ens_label}.0rbit.eth"
    record = {
        "wallet_address": address,
        "ens_name": ens_name,
        "axl_peer_id": payload.axl_peer_id,
        "encrypted_uri": payload.encrypted_uri,
        "capabilities": list(payload.capabilities),
        "reputation_score": 500,
        "status": "active",
    }

    response = client.table("agents").insert(record).execute()
    error = getattr(response, "error", None)

    if error:
        error_message = (
            error.get("message") if isinstance(error, dict) else getattr(error, "message", str(error))
        )
        error_code = error.get("code") if isinstance(error, dict) else getattr(error, "code", None)

        if (
            error_code == "23505"
            or (error_message and "duplicate" in error_message.lower())
        ):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Agent already registered")

        logger.error("Supabase insert failed for wallet %s: %s", address, error_message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to register agent")

    data = getattr(response, "data", None) or []
    if not data:
        logger.error("Supabase insert returned no data for wallet %s", address)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to register agent")

    agent_id = data[0].get("id") if isinstance(data[0], dict) else None
    if not agent_id:
        logger.error("Supabase insert response missing id for wallet %s", address)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to register agent")

    logger.warning(
        "TODO Section 14: integrate onchain iNFT minting and ENS subname registration for wallet %s",
        address,
    )

    return {"id": agent_id}


@router.get("/{agent_id}", summary="Get agent by id")
async def get_agent(agent_id: UUID) -> dict[str, Any]:
    """Fetch a single agent record by UUID."""

    client = get_supabase_client()
    response = (
        client.table("agents")
        .select("*")
        .eq("id", str(agent_id))
        .limit(1)
        .execute()
    )

    error = getattr(response, "error", None)
    if error:
        message, code = _extract_supabase_error(error)
        logger.error("Supabase get agent %s failed (code=%s): %s", agent_id, code, message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load agent")

    data = getattr(response, "data", None)
    if not isinstance(data, list) or not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    return data[0]


@router.get("/ens/{name}", summary="Get agent by ENS name")
async def get_agent_by_ens(name: str) -> dict[str, Any]:
    """Resolve an agent by ENS name with Redis cache (TTL 5 minutes)."""

    cache_key = f"ens:cache:{name.lower()}"
    redis = _get_client()

    cached = redis.get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in cache for %s; purging", cache_key)
            redis.delete(cache_key)

    client = get_supabase_client()
    response = (
        client.table("agents")
        .select("*")
        .eq("ens_name", name.lower())
        .limit(1)
        .execute()
    )

    error = getattr(response, "error", None)
    if error:
        message, code = _extract_supabase_error(error)
        logger.error("Supabase ENS lookup for %s failed (code=%s): %s", name, code, message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load agent")

    data = getattr(response, "data", None)
    if not isinstance(data, list) or not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    agent = data[0]
    redis.setex(cache_key, 300, json.dumps(agent))
    return agent


@router.patch("/{agent_id}", summary="Update agent by id")
async def update_agent(
    agent_id: UUID,
    payload: AgentUpdate,
    address: str = Depends(get_current_user),
) -> dict[str, Any]:
    """Update capabilities or status after verifying ownership."""

    client = get_supabase_client()

    lookup_response = (
        client.table("agents")
        .select("id,wallet_address")
        .eq("id", str(agent_id))
        .limit(1)
        .execute()
    )

    lookup_error = getattr(lookup_response, "error", None)
    if lookup_error:
        message, code = _extract_supabase_error(lookup_error)
        logger.error("Supabase ownership lookup for agent %s failed (code=%s): %s", agent_id, code, message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update agent")

    lookup_data = getattr(lookup_response, "data", None)
    if not isinstance(lookup_data, list) or not lookup_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    owner_wallet = lookup_data[0].get("wallet_address")
    if not owner_wallet:
        logger.error("Supabase agent %s missing wallet_address during update", agent_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update agent")

    if owner_wallet.lower() != address.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update agent")

    update_payload: dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if payload.capabilities is not None:
        update_payload["capabilities"] = list(payload.capabilities)
    if payload.status is not None:
        update_payload["status"] = payload.status

    update_response = (
        client.table("agents")
        .update(update_payload)
        .eq("id", str(agent_id))
        .execute()
    )

    update_error = getattr(update_response, "error", None)
    if update_error:
        message, code = _extract_supabase_error(update_error)
        logger.error("Supabase update for agent %s failed (code=%s): %s", agent_id, code, message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update agent")

    updated_data = getattr(update_response, "data", None)
    if not isinstance(updated_data, list) or not updated_data:
        logger.error("Supabase update returned no data for agent %s", agent_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update agent")

    return updated_data[0]


@router.get("/{agent_id}/reputation", summary="Get agent reputation history")
async def get_agent_reputation(
    agent_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> dict[str, Any]:
    """Return paginated reputation events for an agent."""

    offset = _parse_cursor(cursor)
    client = get_supabase_client()

    query = (
        client.table("reputation_events")
        .select("*")
        .eq("agent_id", str(agent_id))
        .order("created_at", desc=True)
    )

    end = offset + limit
    response = query.range(offset, end).execute()

    error = getattr(response, "error", None)
    if error:
        message, code = _extract_supabase_error(error)
        logger.error("Supabase reputation lookup for agent %s failed (code=%s): %s", agent_id, code, message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load agent reputation")

    data = getattr(response, "data", None) or []
    has_more = len(data) > limit
    if has_more:
        data = data[:limit]
        next_cursor: str | None = str(offset + limit)
    else:
        next_cursor = None

    return {"data": data, "cursor": next_cursor}


@router.get("/{agent_id}/jobs", summary="Get agent job history")
async def get_agent_jobs(
    agent_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> dict[str, Any]:
    """Return paginated jobs assigned to the agent."""

    offset = _parse_cursor(cursor)
    client = get_supabase_client()

    query = (
        client.table("jobs")
        .select("*")
        .eq("assigned_agent_id", str(agent_id))
        .order("created_at", desc=True)
    )

    end = offset + limit
    response = query.range(offset, end).execute()

    error = getattr(response, "error", None)
    if error:
        message, code = _extract_supabase_error(error)
        logger.error("Supabase jobs lookup for agent %s failed (code=%s): %s", agent_id, code, message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load agent jobs")

    data = getattr(response, "data", None) or []
    has_more = len(data) > limit
    if has_more:
        data = data[:limit]
        next_cursor: str | None = str(offset + limit)
    else:
        next_cursor = None

    return {"data": data, "cursor": next_cursor}


__all__ = [
    "list_agents",
    "register_agent",
    "get_agent",
    "get_agent_by_ens",
    "update_agent",
    "get_agent_reputation",
    "get_agent_jobs",
]
