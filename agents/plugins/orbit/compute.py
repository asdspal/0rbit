"""0G Compute verification client for the 0rbit plugin.

Blueprint binding
- Section 14 Phase 4 Item 4 (0G Compute verification prior to escrow)
- Section 4 (Sealed Inference requirements)
- Section 3 Decision 2 (TEE via Phala Cloud)

Purpose
- Provide a lightweight async facade around the 0G Compute testnet endpoint so agents
  can submit inference payloads to a TEE-backed workflow and verify the resulting output
  hash before triggering financial flows.

GAP documentation
- The blueprint does not define the concrete REST paths nor the exact request/response
  schema for verification. This module encodes those details as placeholders that can be
  updated once 0G Compute publishes the production contract. Until then, the client
  focuses on shape validation, consistent encoding of binary payloads, and a single
  error surface (`ComputeError`).
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Optional, Tuple

import httpx

OG_COMPUTE_URL = os.getenv("OG_COMPUTE_URL", "https://compute-testnet.0g.ai")

# Placeholder REST paths – update when 0G publishes the official API surface.
VERIFY_PATH = "/v1/compute/verify"  # GAP: actual verification endpoint TBD
SUBMIT_PATH = "/v1/compute/submit"  # GAP: sealed inference submission endpoint TBD

__all__ = [
    "OG_COMPUTE_URL",
    "ComputeError",
    "ComputeClient",
    "verify_output",
    "submit_for_verification",
]


class ComputeError(RuntimeError):
    """Raised when communicating with 0G Compute fails."""


def _encode_bytes(value: bytes) -> str:
    if not isinstance(value, (bytes, bytearray)):
        raise ComputeError("Expected bytes-like compute proof or payload")
    return base64.b64encode(bytes(value)).decode("ascii")
@dataclass
class ComputeClient:
    """Async HTTP client wrapper for the 0G Compute verification surface."""

    base_url: str = OG_COMPUTE_URL
    timeout: float = 30.0

    async def verify_output(self, output_hash: str, compute_proof: bytes) -> bool:
        """Verify that an output hash matches a provided compute proof.

        Returns:
            True when 0G Compute vouches for the proof, False otherwise.
        """

        if not output_hash:
            raise ComputeError("output_hash is required")
        if not compute_proof:
            raise ComputeError("compute_proof is required")

        payload = {
            "output_hash": output_hash,
            "compute_proof": _encode_bytes(compute_proof),
        }

        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.post(VERIFY_PATH, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - network failure path
            raise ComputeError("0G Compute verification request failed") from exc

        data = response.json()
        verified = bool(data.get("verified"))
        return verified

    async def submit_for_verification(self, data: bytes) -> Tuple[str, bytes]:
        """Submit raw inference data for sealed execution.

        Returns the output hash and proof bytes as a tuple so callers can immediately
        persist the verification artifacts without waiting for another round-trip.
        """

        if not data:
            raise ComputeError("data payload is required")

        payload = {"payload": _encode_bytes(data)}

        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.post(SUBMIT_PATH, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - network failure path
            raise ComputeError("0G Compute submission request failed") from exc

        data = response.json()

        output_hash = data.get("output_hash")
        proof_b64 = data.get("compute_proof")

        if not output_hash or not isinstance(output_hash, str):
            raise ComputeError("0G Compute response missing output_hash")
        if not proof_b64 or not isinstance(proof_b64, str):
            raise ComputeError("0G Compute response missing compute_proof")

        try:
            proof_bytes = base64.b64decode(proof_b64, validate=True)
        except ValueError as exc:
            raise ComputeError("0G Compute returned invalid proof encoding") from exc

        return output_hash, proof_bytes


async def verify_output(output_hash: str, compute_proof: bytes, *, client: Optional[ComputeClient] = None) -> bool:
    """Module-level helper mirroring the blueprint signature."""

    client = client or ComputeClient()
    return await client.verify_output(output_hash, compute_proof)


async def submit_for_verification(data: bytes, *, client: Optional[ComputeClient] = None) -> Tuple[str, bytes]:
    """Submit data to 0G Compute and receive the output hash plus compute proof."""

    client = client or ComputeClient()
    return await client.submit_for_verification(data)
