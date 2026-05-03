from fastapi import APIRouter

from app.database import get_supabase_client
from app.redis import ping_redis

router = APIRouter(tags=["health"])


def _check_supabase_connection() -> str:
    """Return whether Supabase responds to a lightweight query."""

    try:
        client = get_supabase_client()
        response = (
            client.table("agents")
            .select("id")
            .limit(1)
            .execute()
        )
        error = getattr(response, "error", None)
        if error:
            return "disconnected"
        return "connected"
    except Exception:
        return "disconnected"


def _check_redis_connection() -> str:
    """Return whether Redis responds to `ping`."""

    try:
        return "connected" if ping_redis() else "disconnected"
    except Exception:
        return "disconnected"


@router.get("/health", name="health-check")
async def health_check():
    """Report health for Supabase and Redis dependencies."""

    supabase_status = _check_supabase_connection()
    redis_status = _check_redis_connection()
    overall_status = (
        "ok" if supabase_status == "connected" and redis_status == "connected" else "degraded"
    )

    return {
        "status": overall_status,
        "supabase": supabase_status,
        "redis": redis_status,
    }
