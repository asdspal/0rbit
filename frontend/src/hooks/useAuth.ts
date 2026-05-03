"use client";

import { useCallback } from "react";
import { useAccount, useConnect, useDisconnect, useSignMessage } from "wagmi";
import { type Address } from "viem";

import { generateSiweMessage, verifySiwe } from "@/lib/auth";
import { useStore, type WalletSession } from "@/lib/store";

type MeResponse = {
  address: string;
  agent_id: string | null;
  ens_name: string | null;
};

async function fetchNonce(): Promise<{ nonce: string }> {
  const res = await fetch("/v1/auth/nonce", { method: "POST", credentials: "include" });
  if (!res.ok) {
    throw new Error("Failed to fetch nonce");
  }
  return res.json();
}

async function fetchMe(): Promise<MeResponse> {
  const res = await fetch("/v1/auth/me", { credentials: "include" });
  if (!res.ok) {
    throw new Error("Failed to fetch session");
  }
  return res.json();
}

async function postLogout(): Promise<void> {
  const res = await fetch("/v1/auth/logout", { method: "POST", credentials: "include" });
  if (!res.ok) {
    throw new Error("Failed to logout");
  }
}

export function useAuth() {
  const { address, chain } = useAccount();
  const { connect, connectors, status: connectStatus } = useConnect();
  const { disconnect: wagmiDisconnect } = useDisconnect();
  const { signMessageAsync } = useSignMessage();

  const walletSession = useStore((s) => s.walletSession);
  const setWalletSession = useStore((s) => s.setWalletSession);

  const connectAndSign = useCallback(async () => {
    const currentAddress = address as Address | undefined;
    const currentChainId = chain?.id;
    if (!currentAddress || !currentChainId) {
      throw new Error("Wallet not connected");
    }

    const { nonce } = await fetchNonce();
    const message = generateSiweMessage({
      address: currentAddress,
      nonce,
      chainId: currentChainId,
    });

    const signature = await signMessageAsync({ message });
    await verifySiwe(message, signature);

    setWalletSession({
      address: currentAddress,
      ensName: null,
    });
  }, [address, chain?.id, setWalletSession, signMessageAsync]);

  const reloadSession = useCallback(async () => {
    const me = await fetchMe();
    const session: WalletSession = {
      address: me.address,
      ensName: me.ens_name,
    };
    setWalletSession(session);
  }, [setWalletSession]);

  const disconnect = useCallback(async () => {
    await postLogout();
    setWalletSession(null);
    wagmiDisconnect();
  }, [setWalletSession, wagmiDisconnect]);

  return {
    address,
    chainId: chain?.id,
    connectors,
    connect,
    connectStatus,
    walletSession,
    connectAndSign,
    disconnect,
    reloadSession,
  };
}
