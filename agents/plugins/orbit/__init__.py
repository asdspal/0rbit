"""0rbit plugin scaffold (OpenClaw-compatible, standalone)

Blueprint binding
- Project: 0rbit — The Decentralized Labor Market for AI Agents
- Sections: 14 Phase 4 Item 1 (Add 0rbit plugin to OpenClaw fork), Section 4 (Agent Framework layer)

Purpose
- Provide a minimal, dependency-free plugin module layout for integration with agent frameworks
  including, but not limited to, an OpenClaw fork. This scaffold avoids importing any OpenClaw
  symbols so it can be imported and unit-tested in isolation.

GAP: OpenClaw plugin interface
- The OpenClaw plugin interface/API is not specified in the blueprint. This package documents the
  gap and exposes standalone, callable modules that future adapters can bind to the concrete
  OpenClaw plugin API when available.

Modules
- axl_client:     AXL HTTP client integration points (async, via httpx)
- storage:        0G Storage integration points (Python SDK GAP noted)
- keeperhub:      KeeperHub MCP integration points
- job_handler:    Job bidding and execution strategy hooks

Import safety
- All submodules are placeholders with minimal type signatures and docstrings; they perform no I/O
  at import time and raise NotImplementedError on use where relevant.
"""

from typing import Dict, Any

__version__ = "0.1.0"
__plugin_name__ = "orbit"
__description__ = (
    "0rbit plugin scaffold providing AXL, 0G storage, KeeperHub, and job handling stubs."
)

__all__ = [
    "__version__",
    "__plugin_name__",
    "__description__",
    "get_metadata",
]


def get_metadata() -> Dict[str, Any]:
    """Return plugin metadata for discovery and diagnostics.

    This mirrors common plugin discovery patterns without binding to a specific
    framework. Suitable for health checks and unit tests.
    """

    return {
        "name": __plugin_name__,
        "version": __version__,
        "description": __description__,
        "modules": [
            "plugins.orbit.axl_client",
            "plugins.orbit.storage",
            "plugins.orbit.keeperhub",
            "plugins.orbit.job_handler",
        ],
        "blueprint": {
            "sections": [
                "Section 14 Phase 4 Item 1",
                "Section 4 (Agent Framework layer)",
            ],
            "gaps": [
                "OpenClaw plugin interface/API not specified; modules are standalone",
            ],
        },
    }

