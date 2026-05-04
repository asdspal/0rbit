"""KeeperHub MCP client for the 0rbit agent plugin.

Blueprint binding
- Section 14 Phase 4 Item 5 (KeeperHub escrow automation)
- Section 10.4 (Tools: create_workflow, trigger_execution, check_execution_status)

Purpose
- Provide an async HTTP facade that the agent can call to invoke KeeperHub MCP tools.
- Enforce blueprint constraints: team account authentication (API key) and autonomous
  escrow release triggers.

GAP documentation
- KeeperHub MCP transport + REST surface are not published. This implementation follows the
  Section 10.4 tool naming and uses placeholder REST paths under ``/mcp``. Update
  ``KEEPERHUB_BASE_URL`` or the per-method paths once KeeperHub shares their production schema.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

__all__ = ["KeeperHubClient", "KeeperHubError", "WebhookVerifier"]


class KeeperHubError(RuntimeError):
    """KeeperHub client error placeholder."""


@dataclass
class KeeperHubClient:
    """Async HTTP client exposing the Section 10.4 KeeperHub tool surface."""

    api_key: Optional[str] = None
    base_url: str = os.getenv("KEEPERHUB_BASE_URL", "https://api.keeperhub.xyz")
    timeout: float = 15.0

    # GAP: Endpoint paths inferred from Section 10.4 tool names until KeeperHub publishes MCP schema
    _WORKFLOWS_PATH: str = "/mcp/workflows"
    _EXECUTIONS_PATH: str = "/mcp/executions"

    def __post_init__(self) -> None:
        if not self.api_key:
            self.api_key = os.getenv("KEEPERHUB_API_KEY")
        if not self.api_key:
            raise KeeperHubError("KeeperHub API key missing (set KEEPERHUB_API_KEY)")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _request(
        self, method: str, path: str, *, payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.request(method, path, json=payload, headers=self._headers())
                response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - network failures mocked in tests
            raise KeeperHubError(f"KeeperHub request failed for {method} {path}") from exc

        data = response.json()
        if not isinstance(data, dict):
            raise KeeperHubError("KeeperHub response must be a JSON object")
        return data

    @staticmethod
    def _require_field(data: Dict[str, Any], candidates: tuple[str, ...], label: str) -> str:
        for key in candidates:
            value = data.get(key)
            if value:
                return str(value)
        raise KeeperHubError(f"KeeperHub response missing {label}")

    async def create_workflow(self, name: str, trigger: str, actions: list[Any]) -> str:
        """Create a KeeperHub workflow (Section 10.4 create_workflow tool).

        Returns the workflow identifier provided by KeeperHub.
        """

        if not name:
            raise KeeperHubError("workflow name is required")
        if not trigger:
            raise KeeperHubError("workflow trigger is required")
        if not isinstance(actions, list) or not actions:
            raise KeeperHubError("workflow actions must be a non-empty list")

        payload = {"name": name, "trigger": trigger, "actions": actions}
        data = await self._request("POST", self._WORKFLOWS_PATH, payload=payload)
        return self._require_field(data, ("workflow_id", "id"), "workflow_id")

    async def trigger_execution(self, workflow_id: str, params: Dict[str, Any]) -> str:
        """Trigger a KeeperHub workflow execution (Section 10.4 trigger_execution tool)."""

        if not workflow_id:
            raise KeeperHubError("workflow_id is required")
        if params is None:
            raise KeeperHubError("params is required")

        path = f"{self._WORKFLOWS_PATH}/{workflow_id}/executions"
        payload = {"params": params}
        data = await self._request("POST", path, payload=payload)
        return self._require_field(data, ("execution_id", "id"), "execution_id")

    async def check_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Fetch KeeperHub execution status (Section 10.4 check_execution_status tool)."""

        if not execution_id:
            raise KeeperHubError("execution_id is required")

        path = f"{self._EXECUTIONS_PATH}/{execution_id}"
        data = await self._request("GET", path)
        return {
            "status": data.get("status"),
            "result": data.get("result"),
            # preserve entire payload for callers needing KeeperHub-specific fields
            "raw": data,
        }


@dataclass
class WebhookVerifier:
    """Verify KeeperHub webhook authenticity (e.g., HMAC).

    Mirrors backend webhook security (Section 8.5) on the client side for end-to-end tests.
    """

    secret: str

    def verify(self, payload: bytes, signature: str) -> bool:
        """Return True if the signature matches the payload using the shared secret."""

        if not isinstance(payload, (bytes, bytearray)):
            raise KeeperHubError("payload must be bytes for webhook verification")
        if not self.secret:
            raise KeeperHubError("KeeperHub webhook secret is required")
        if not signature:
            return False

        computed = hmac.new(self.secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        provided = signature.split("=", 1)[-1].lower()
        return hmac.compare_digest(computed, provided)
