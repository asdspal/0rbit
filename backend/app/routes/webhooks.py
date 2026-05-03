"""Webhook endpoints (Section 8.5)."""

from __future__ import annotations

import hashlib
import hmac
import logging
from os import getenv
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.database import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])


def _extract_supabase_error(error: Any) -> tuple[str | None, str | None]:
    if not error:
        return None, None

    if isinstance(error, dict):
        return error.get("message"), error.get("code")

    return getattr(error, "message", str(error)), getattr(error, "code", None)


async def verify_0g_api_key(request: Request) -> None:
    """Validate API key for 0G webhooks (Section 8.5)."""

    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")

    expected = getenv("WEBHOOK_API_KEY")
    if not expected:
        logger.error("WEBHOOK_API_KEY not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Webhook API key not configured"
        )

    if api_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


async def verify_keeperhub_signature(request: Request) -> bytes:
    """Validate HMAC-SHA256 signature from KeeperHub using Section 13 secret."""

    signature = request.headers.get("X-Signature-256")
    if not signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing signature")

    secret = getenv("KEEPERHUB_WEBHOOK_SECRET")
    if not secret:
        logger.error("KEEPERHUB_WEBHOOK_SECRET not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Webhook secret not configured"
        )

    body = await request.body()
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    return body


@router.post("/0g-events", summary="0G onchain events webhook")
async def og_events_webhook(
    request: Request,
    api_key_checked: None = Depends(verify_0g_api_key),
) -> dict[str, str]:
    """Handle 0G/The Graph events → sync jobs/bids/reputation (Section 8.5)."""

    # Defensive: ensure API key verification runs even if called directly (tests bypass DI).
    await verify_0g_api_key(request)

    try:
        payload = await request.json()
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload structure")

    event_type_raw = payload.get("event") or payload.get("type")
    if not event_type_raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing event type")

    event_type = str(event_type_raw).lower()
    client = get_supabase_client()

    if event_type == "jobposted":
        job_id = payload.get("job_id")
        poster = payload.get("poster_address") or payload.get("poster")
        if not job_id or not poster:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing job fields")

        record: dict[str, Any] = {
            "onchain_job_id": job_id,
            "poster_address": poster,
            "title": payload.get("title"),
            "description": payload.get("description"),
            "job_spec_hash": payload.get("job_spec_hash") or payload.get("spec_hash"),
            "required_capabilities": payload.get("required_capabilities") or [],
            "payment_token": payload.get("payment_token"),
            "escrow_amount": payload.get("escrow_amount"),
            "deadline": payload.get("deadline"),
            "status": "posted",
        }

        upsert_response = client.table("jobs").upsert(record, on_conflict=["onchain_job_id"]).execute()
        error = getattr(upsert_response, "error", None)
        if error:
            message, code = _extract_supabase_error(error)
            logger.error("Supabase upsert job %s failed (code=%s): %s", job_id, code, message)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upsert job")

    elif event_type == "bidaccepted":
        bid_id = payload.get("bid_id")
        job_id = payload.get("job_id")
        agent_id = payload.get("agent_id")
        if not bid_id or not job_id or not agent_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing bid fields")

        bid_response = client.table("bids").update({"status": "accepted"}).eq("id", str(bid_id)).execute()
        bid_error = getattr(bid_response, "error", None)
        if bid_error:
            message, code = _extract_supabase_error(bid_error)
            logger.error("Supabase update bid %s failed (code=%s): %s", bid_id, code, message)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update bid")

        job_response = (
            client.table("jobs")
            .update({"assigned_agent_id": agent_id, "status": "assigned"})
            .eq("onchain_job_id", str(job_id))
            .execute()
        )
        job_error = getattr(job_response, "error", None)
        if job_error:
            message, code = _extract_supabase_error(job_error)
            logger.error("Supabase update job %s failed (code=%s): %s", job_id, code, message)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update job")

    elif event_type == "escrowreleased":
        job_id = payload.get("job_id")
        tx_hash = payload.get("tx_hash")
        if not job_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing job_id")

        update_response = (
            client.table("jobs")
            .update({"status": "completed", "uniswap_swap_tx": tx_hash})
            .eq("onchain_job_id", str(job_id))
            .execute()
        )
        error = getattr(update_response, "error", None)
        if error:
            message, code = _extract_supabase_error(error)
            logger.error("Supabase update job %s failed (code=%s): %s", job_id, code, message)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update job")

    elif event_type == "reputationupdated":
        agent_id = payload.get("agent_id")
        delta = payload.get("delta")
        new_score = payload.get("new_score")
        job_id = payload.get("job_id")
        tx_hash = payload.get("tx_hash")

        if agent_id is None or delta is None or new_score is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing reputation fields")

        reason = payload.get("reason") or "job_completed"
        allowed_reasons = {"job_completed", "job_disputed", "keeperhub_update", "slash"}
        if reason not in allowed_reasons:
            reason = "job_completed"

        insert_response = (
            client.table("reputation_events")
            .insert(
                {
                    "agent_id": agent_id,
                    "job_id": job_id,
                    "delta": delta,
                    "new_score": new_score,
                    "reason": reason,
                    "onchain_tx": tx_hash,
                }
            )
            .execute()
        )
        insert_error = getattr(insert_response, "error", None)
        if insert_error:
            message, code = _extract_supabase_error(insert_error)
            logger.error(
                "Supabase insert reputation for agent %s failed (code=%s): %s", agent_id, code, message
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to record reputation event"
            )

        update_response = (
            client.table("agents")
            .update({"reputation_score": new_score})
            .eq("id", str(agent_id))
            .execute()
        )
        update_error = getattr(update_response, "error", None)
        if update_error:
            message, code = _extract_supabase_error(update_error)
            logger.error("Supabase update agent %s failed (code=%s): %s", agent_id, code, message)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update agent reputation"
            )

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported event type")

    return {"status": "ok"}


@router.post("/keeperhub", summary="KeeperHub execution webhook")
async def keeperhub_webhook(
    request: Request,
    verified_body: bytes | None = Depends(verify_keeperhub_signature),
) -> dict[str, str]:
    """Handle KeeperHub execution events → update job + reputation (Section 8.5)."""

    # Defensive: if called directly (e.g., unit tests) ensure signature verification still runs.
    if not isinstance(verified_body, (bytes, bytearray)):
        verified_body = await verify_keeperhub_signature(request)

    try:
        payload = await request.json()
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload") from exc

    event_type = payload.get("type") if isinstance(payload, dict) else None
    if not event_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing event type")

    client = get_supabase_client()

    if event_type == "escrow_released":
        job_id = payload.get("job_id")
        tx_hash = payload.get("tx_hash")

        if not job_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing job_id")

        update_response = (
            client.table("jobs")
            .update({"status": "completed", "uniswap_swap_tx": tx_hash})
            .eq("id", str(job_id))
            .execute()
        )

        error = getattr(update_response, "error", None)
        if error:
            message, code = _extract_supabase_error(error)
            logger.error("Supabase update job %s failed (code=%s): %s", job_id, code, message)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update job")

    elif event_type == "reputation_updated":
        agent_id = payload.get("agent_id")
        delta = payload.get("delta")
        new_score = payload.get("new_score")
        job_id = payload.get("job_id")
        tx_hash = payload.get("tx_hash")

        if agent_id is None or delta is None or new_score is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing reputation fields")

        insert_response = (
            client.table("reputation_events")
            .insert(
                {
                    "agent_id": agent_id,
                    "job_id": job_id,
                    "delta": delta,
                    "new_score": new_score,
                    "reason": "keeperhub_update",
                    "onchain_tx": tx_hash,
                }
            )
            .execute()
        )

        insert_error = getattr(insert_response, "error", None)
        if insert_error:
            message, code = _extract_supabase_error(insert_error)
            logger.error(
                "Supabase insert reputation for agent %s failed (code=%s): %s", agent_id, code, message
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to record reputation event"
            )

        update_response = (
            client.table("agents")
            .update({"reputation_score": new_score})
            .eq("id", str(agent_id))
            .execute()
        )

        update_error = getattr(update_response, "error", None)
        if update_error:
            message, code = _extract_supabase_error(update_error)
            logger.error("Supabase update agent %s failed (code=%s): %s", agent_id, code, message)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update agent reputation"
            )

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported event type")

    return {"status": "ok"}
