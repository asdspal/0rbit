"use client";

import { ReactNode, useMemo } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { WagmiProvider as BaseWagmiProvider } from "wagmi";

import { config } from "@/lib/wagmi";

type Props = {
  children: ReactNode;
};

export function WagmiProvider({ children }: Props) {
  const queryClient = useMemo(() => new QueryClient(), []);

  return (
    <BaseWagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </BaseWagmiProvider>
  );
}

