"""AXL integration stub for 0rbit plugin.

Blueprint binding
- Section 14 Phase 4 Item 1, Section 4 (Agent Framework layer)

Purpose
- Define a minimal, framework-agnostic async client surface for interacting with AXL endpoints.
- No hard dependency on external libraries at import time; httpx usage (if any) must be deferred
  to runtime to keep imports safe during structure-only verification.

GAP notes
- Concrete AXL endpoint schemas and authentication flows are defined elsewhere in the blueprint.
- This stub documents signatures and raises NotImplementedError where behavior depends on
  service specifics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

__all__ = ["AxlClient", "AxlError"]


class AxlError(RuntimeError):
    """AXL client error placeholder."""


@dataclass
class AxlClient:
    """Lightweight AXL HTTP client facade.

    Avoids importing httpx at module import time. Implementations should import httpx within
    methods to prevent dependency errors during structural tests.
    """

    base_url: str
    api_key: Optional[str] = None
    timeout: float = 10.0

    def _headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def send_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send an AXL message.

        Implementations should:
        - import httpx locally
        - POST to f"{self.base_url}/v1/axl/messages" (or configured path)
        - handle non-2xx responses by raising AxlError
        """

        raise NotImplementedError("AXL client not yet implemented — awaiting concrete API details")

