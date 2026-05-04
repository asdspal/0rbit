"""Orbit agent runner per Section 14 Phase 4 Item 6 blueprint binding.

This module wires the automated job discovery loop with the AXL listener so the
agent can react to `job_accepted` events end-to-end:

posted job → bid → job_accepted → execute → submit

GAP notes
- AXL HTTP base URL and auth are still TBD; the local stub client defaults to
  http://localhost:9002 until the blueprint specifies production endpoints.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable, Optional

from agents.plugins.orbit.axl_client import AXLClient
from agents.plugins.orbit.job_handler import JobHandler
from agents.plugins.orbit.listener import AXLListener
from agents.plugins.orbit.messages import AXLMessage, JobAcceptedPayload

logger = logging.getLogger(__name__)


class OrbitAgent:
    """Main agent orchestrator combining discovery loop and AXL listener."""

    def __init__(
        self,
        agent_ens: str,
        agent_peer_id: str,
        capabilities: list[str],
        api_base: str,
        *,
        axl_client: Optional[AXLClient] = None,
        job_handler_cls: type[JobHandler] = JobHandler,
        listener_cls: type[AXLListener] = AXLListener,
    ) -> None:
        self.axl = axl_client or AXLClient()
        self.handler = job_handler_cls(self.axl, agent_ens, agent_peer_id, capabilities)
        self.listener = listener_cls(self.axl)
        self.api_base = api_base
        self._bg_tasks: set[asyncio.Task[None]] = set()

    def setup_handlers(self) -> None:
        """Register listener callbacks for mission-critical message types."""

        async def _handle_job_accepted(msg: AXLMessage) -> None:
            if not isinstance(msg.payload, JobAcceptedPayload):
                logger.warning("Unexpected payload for job_accepted message: %s", msg.payload)
                return
            await self.handler.handle_job_accepted(msg.payload, msg.src_peer_id, self.api_base)

        async def _handle_ping(msg: AXLMessage) -> None:
            logger.info("Ping from %s at %s", msg.src_peer_id, msg.timestamp.isoformat())

        self.listener.on("job_accepted", _handle_job_accepted)
        self.listener.on("ping", _handle_ping)

    def _track_task(self, coro: Awaitable[None]) -> None:
        task = asyncio.create_task(coro)
        self._bg_tasks.add(task)
        task.add_done_callback(self._bg_tasks.discard)

    async def start(self) -> None:
        """Start discovery loop (background) and the blocking listener."""

        self.setup_handlers()
        self._track_task(self.handler.run_discovery_loop(self.api_base))
        await self.listener.start()

    async def stop(self) -> None:
        """Stop listener, cancel discovery loop, and close network handles."""

        await self.listener.stop()
        for task in list(self._bg_tasks):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self.axl.close()

