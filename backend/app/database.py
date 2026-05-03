"""Supabase client helpers backed by Section 4/7/13 of the blueprint."""

from functools import lru_cache
from os import getenv
from urllib.parse import urlparse

from supabase import Client, create_client


def _infer_supabase_url(database_url: str) -> str:
    """Derive the Supabase HTTP endpoint from the PostgreSQL host."""

    parsed = urlparse(database_url)
    host = parsed.hostname
    if not host:
        raise RuntimeError("DATABASE_URL is missing a hostname")

    if host.startswith("db."):
        host = host[3:]

    return f"https://{host}"


def _resolve_supabase_url() -> str:
    """Return the Supabase REST URL configured for this environment."""

    explicit_url = getenv("SUPABASE_URL")
    if explicit_url:
        return explicit_url

    database_url = getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set to infer Supabase URL")

    return _infer_supabase_url(database_url)


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Return a cached Supabase service-role client defined by environment variables."""

    supabase_url = _resolve_supabase_url()
    supabase_key = getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is required for Supabase access")

    return create_client(supabase_url, supabase_key)


__all__ = ["get_supabase_client"]
