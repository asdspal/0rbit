"""0G Storage integration stub for 0rbit plugin.

Blueprint binding
- Section 14 Phase 4 Item 1, Section 4 (Agent Framework layer)

Purpose
- Define a minimal, framework-agnostic interface for uploading artifacts to 0G Storage.
- Python SDK availability is a GAP; this module documents the gap and provides signatures that an
  adapter can implement once a Python client is finalized.

GAP notes
- The referenced package "@0gfoundation/0g-storage-ts-sdk" is TypeScript; a Python equivalent is
  not specified. Implementors should select a Python client or bridge (e.g., REST gateway) and
  wire it here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

__all__ = ["StorageClient", "StorageError"]


class StorageError(RuntimeError):
    """0G storage client error placeholder."""


@dataclass
class StorageClient:
    """Lightweight 0G storage facade.

    Implementations may talk to a REST bridge or a native Python SDK when available.
    """

    endpoint: str
    api_key: Optional[str] = None

    async def upload_bytes(self, data: bytes, *, content_type: str = "application/octet-stream") -> str:
        """Upload raw bytes to 0G storage.

        Returns a content-addressed URI or a storage handle.
        """

        raise NotImplementedError("0G storage upload not implemented — awaiting Python SDK or REST bridge")

    async def upload_file(self, path: str, *, content_type: Optional[str] = None) -> str:
        """Upload a local file to 0G storage.

        Implementations should stream the file and avoid loading into memory when large.
        """

        raise NotImplementedError("0G storage file upload not implemented — awaiting Python SDK or REST bridge")

