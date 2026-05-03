"use client";

import { useMemo } from "react";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/Button";

function truncateAddress(addr: string) {
  return `${addr.slice(0, 6)}…${addr.slice(-4)}`;
}

export function ConnectWallet() {
  const { address, connectors, connect, connectStatus, connectAndSign, walletSession } = useAuth();

  const primaryConnector = useMemo(() => connectors[0], [connectors]);

  const handleConnect = async () => {
    if (!primaryConnector) return;
    if (connectStatus === "pending") return;
    await connect({ connector: primaryConnector });
    await connectAndSign();
  };

  const label = walletSession?.address
    ? truncateAddress(walletSession.address)
    : address
    ? truncateAddress(address)
    : "Connect Wallet";

  return (
    <Button
      type="button"
      variant="primary"
      onClick={handleConnect}
      disabled={!primaryConnector || connectStatus === "pending"}
      className="min-w-[140px]"
    >
      {label}
    </Button>
  );
}
