"""KeeperHub MCP integration stub for 0rbit plugin.

Blueprint binding
- Section 14 Phase 4 Item 1, Section 4 (Agent Framework layer)

Purpose
- Define lightweight interfaces for interacting with KeeperHub via MCP (Model Context Protocol)
  or equivalent RPC. This is framework-agnostic and avoids any import-time side effects.

GAP notes
- Concrete MCP transport, auth, and tool schemas are not specified in the blueprint.
- Implementations should bind to a concrete MCP client and map these interfaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

__all__ = ["KeeperHubClient", "KeeperHubError", "WebhookVerifier"]


class KeeperHubError(RuntimeError):
    """KeeperHub client error placeholder."""


@dataclass
class KeeperHubClient:
    """Thin facade for KeeperHub MCP operations.

    This client exposes tool registration and invocation surfaces that a concrete MCP
    implementation can bind to. No network actions occur at import time.
    """

    endpoint: str
    api_key: Optional[str] = None

    async def register_tool(self, name: str, schema: Dict[str, Any]) -> None:
        """Register a tool with KeeperHub.

        A concrete implementation should perform an authenticated MCP call to publish the
        tool and its JSON schema, handling idempotency.
        """

        raise NotImplementedError("KeeperHub tool registration not implemented — awaiting MCP details")

    async def call_tool(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a registered tool by name with parameters.

        Returns the tool's JSON result.
        """

        raise NotImplementedError("KeeperHub tool invocation not implemented — awaiting MCP details")


@dataclass
class WebhookVerifier:
    """Verify KeeperHub webhook authenticity (e.g., HMAC).

    Mirrors backend webhook security (Section 8.5) on the client side for end-to-end tests.
    """

    secret: str

    def verify(self, payload: bytes, signature: str) -> bool:
        """Return True if the signature matches the payload using the shared secret.

        A concrete implementation should compute the HMAC digest (e.g., sha256) and compare
        in constant time.
        """

        raise NotImplementedError("KeeperHub webhook verifier not implemented — provide HMAC impl")

