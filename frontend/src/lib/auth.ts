import { type Address } from "viem";

type GenerateSiweMessageParams = {
  address: Address;
  nonce: string;
  chainId: number;
  issuedAt?: string;
  domain?: string;
  uri?: string;
  statement?: string;
};

/**
 * Build an EIP-4361 (Sign-In with Ethereum) message string.
 * Mirrors the format parsed by the backend at /v1/auth/verify.
 */
export function generateSiweMessage({
  address,
  nonce,
  chainId,
  issuedAt,
  domain,
  uri,
  statement = "Sign in with Ethereum.",
}: GenerateSiweMessageParams) {
  const nowIso = issuedAt ?? new Date().toISOString();
  const resolvedDomain =
    domain ?? (typeof window !== "undefined" ? window.location.host : "localhost");
  const resolvedUri =
    uri ?? (typeof window !== "undefined" ? window.location.origin : "http://localhost");

  return `${resolvedDomain} wants you to sign in with your Ethereum account:
${address}

${statement}

URI: ${resolvedUri}
Version: 1
Chain ID: ${chainId}
Nonce: ${nonce}
Issued At: ${nowIso}`;
}

export type VerifySiweResponse = {
  jwt: string;
  agent: {
    id?: string | null;
    ens_name?: string | null;
  } | null;
};

export async function verifySiwe(message: string, signature: string): Promise<VerifySiweResponse> {
  const response = await fetch("/v1/auth/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ message, signature }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Failed to verify SIWE signature");
  }

  return response.json();
}

