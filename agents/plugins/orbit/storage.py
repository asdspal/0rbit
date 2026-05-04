"""0G Storage integration for the 0rbit plugin.

Implements the blueprint requirement to shell out to the official TypeScript SDK
via `agents/scripts/0g_upload.js`, returning the Merkle root hash produced by the
SDK. This keeps hashing semantics inside the supported SDK while allowing the
Python agent runtime to remain lightweight.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional

__all__ = ["StorageClient", "StorageError", "upload_data"]


DEFAULT_ENDPOINT = os.getenv("OG_STORAGE_URL", "https://storage-testnet.0g.ai")
DEFAULT_API_KEY = os.getenv("OG_STORAGE_API_KEY")
DEFAULT_SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "0g_upload.js"


class StorageError(RuntimeError):
    """Raised when uploading to 0G storage fails."""


@dataclass
class StorageClient:
    """Lightweight 0G storage facade that shells out to a Node.js helper."""

    endpoint: str = DEFAULT_ENDPOINT
    api_key: Optional[str] = DEFAULT_API_KEY
    node_binary: str = "node"
    script_path: Path = field(default_factory=lambda: DEFAULT_SCRIPT_PATH)
    env: Optional[Mapping[str, str]] = None
    timeout: float = 300.0

    def upload_bytes(
        self,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
        object_name: Optional[str] = None,
    ) -> str:
        """Upload raw bytes to 0G storage and return the Merkle root hash."""

        if not isinstance(data, (bytes, bytearray)):
            raise StorageError("upload_bytes expects bytes-like data")

        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        try:
            tmp_file.write(bytes(data))
            tmp_file.flush()
            tmp_file.close()
            filename = object_name or f"upload-{uuid.uuid4().hex}"
            return self._run_upload(tmp_file.name, filename)
        finally:
            try:
                os.unlink(tmp_file.name)
            except FileNotFoundError:
                pass

    def upload_file(self, path: str, *, content_type: Optional[str] = None) -> str:
        """Upload a local file to 0G storage and return the Merkle root hash."""

        if not os.path.isfile(path):
            raise StorageError(f"File not found: {path}")

        absolute = os.path.abspath(path)
        filename = os.path.basename(absolute)
        return self._run_upload(absolute, filename)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_upload(self, file_path: str, filename: Optional[str]) -> str:
        script = Path(self.script_path)
        if not script.exists():
            raise StorageError(f"0G upload script not found at {script}")

        cmd = [self.node_binary, str(script), file_path]
        if filename:
            cmd.extend(["--filename", filename])

        env = self._build_env()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=self.timeout,
                check=False,
            )
        except FileNotFoundError as exc:
            raise StorageError(f"Executable not found: {self.node_binary}") from exc
        except subprocess.TimeoutExpired as exc:
            raise StorageError("0G upload timed out") from exc

        if result.returncode != 0:
            error = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
            raise StorageError(f"0G upload failed: {error}")

        output = result.stdout.strip()
        if not output:
            raise StorageError("0G upload produced no output")

        return output

    def _build_env(self) -> Mapping[str, str]:
        env: dict[str, str] = os.environ.copy()
        env.setdefault("OG_STORAGE_URL", self.endpoint)
        if self.api_key:
            env["OG_STORAGE_API_KEY"] = self.api_key
        if self.env:
            env.update(self.env)
        return env


def upload_data(data: bytes, filename: Optional[str] = None, *, client: Optional[StorageClient] = None) -> str:
    """Convenience helper for uploading raw job output bytes to 0G storage."""

    storage_client = client or StorageClient()
    return storage_client.upload_bytes(
        data,
        content_type="application/octet-stream",
        object_name=filename,
    )
