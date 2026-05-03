from __future__ import annotations

from dataclasses import dataclass

from eth_account import Account
from eth_account.messages import encode_defunct


@dataclass(frozen=True)
class SiweMessage:
    domain: str
    address: str
    nonce: str
    chain_id: int
    issued_at: str


def parse_siwe_message(message: str) -> SiweMessage:
    if not message or not message.strip():
        raise ValueError("SIWE message is required")

    lines = [line.rstrip("\r") for line in message.split("\n")]
    if len(lines) < 2:
        raise ValueError("SIWE message is malformed")

    domain_line = lines[0].strip()
    if not domain_line:
        raise ValueError("SIWE domain line is missing")

    domain = domain_line.split(" wants you to sign in with your Ethereum account:", 1)[0].strip()
    if not domain:
        raise ValueError("SIWE domain is missing")

    address = lines[1].strip()
    if not address:
        raise ValueError("SIWE address is missing")

    fields: dict[str, str] = {}
    for line in lines[2:]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()

    nonce = fields.get("Nonce")
    chain_id_value = fields.get("Chain ID")
    issued_at = fields.get("Issued At")

    if not nonce:
        raise ValueError("SIWE nonce is missing")
    if not chain_id_value:
        raise ValueError("SIWE chainId is missing")
    if not issued_at:
        raise ValueError("SIWE issuedAt is missing")

    try:
        chain_id = int(chain_id_value)
    except ValueError as exc:
        raise ValueError("SIWE chainId is invalid") from exc

    return SiweMessage(domain=domain, address=address, nonce=nonce, chain_id=chain_id, issued_at=issued_at)


def verify_signature(message: str, signature: str) -> str:
    if not signature:
        raise ValueError("SIWE signature is required")

    recovered = Account.recover_message(encode_defunct(text=message), signature=signature)
    if not recovered:
        raise ValueError("SIWE signature recovery failed")
    return recovered
