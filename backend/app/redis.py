"""Redis helpers aligned with Section 4 cache layer tooling."""

from os import getenv
from urllib.error import URLError
from urllib.request import Request, urlopen

from redis import Redis

_redis_client: Redis | None = None


def _require_env(name: str) -> str:
    """Fetch a required redis configuration environment variable."""

    value = getenv(name)
    if not value:
        raise RuntimeError(f"{name} is required to configure Redis")
    return value


def _build_client() -> Redis:
    """Create the Redis client connected to Upstash Serverless (rediss)."""

    url = _require_env("UPSTASH_REDIS_URL")
    token = _require_env("UPSTASH_REDIS_TOKEN")

    return Redis.from_url(url, password=token, socket_timeout=5, decode_responses=True)


def _ping_upstash_rest(url: str, token: str) -> bool:
    """Ping Upstash REST API when only HTTPS endpoint is available."""

    request = Request(
        f"{url.rstrip('/')}/ping",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8", errors="ignore").lower()
            return response.status == 200 and ("pong" in body or "ok" in body)
    except URLError:
        return False


def _get_client() -> Redis:
    """Cache the Redis client after the first successful creation."""

    global _redis_client
    if _redis_client is None:
        _redis_client = _build_client()
    return _redis_client


def ping_redis() -> bool:
    """Helper to verify connectivity to the Redis instance."""

    url = getenv("UPSTASH_REDIS_URL") or getenv("UPSTASH_REDIS_REST_URL")
    token = getenv("UPSTASH_REDIS_TOKEN")
    if not url or not token:
        raise RuntimeError("UPSTASH_REDIS_URL/UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_TOKEN are required")

    if url.startswith("http://") or url.startswith("https://"):
        return _ping_upstash_rest(url, token)

    return _get_client().ping()
