import { defineChain } from "viem";
import { http, createConfig } from "wagmi";
import { sepolia } from "wagmi/chains";

// 0G Testnet chain definition per blueprint (Section 14 Phase 3 Item 1)
export const orbitChain = defineChain({
  id: 16601,
  name: "0G Testnet",
  network: "0g-testnet",
  nativeCurrency: { name: "ETH", symbol: "ETH", decimals: 18 },
  rpcUrls: {
    default: {
      http: [process.env.NEXT_PUBLIC_OG_RPC_URL || "https://evmrpc-testnet.0g.ai"],
    },
  },
  blockExplorers: {
    default: {
      name: "",
      url: "",
    },
  }, // GAP: blueprint omitted explorer URL
});

export const config = createConfig({
  chains: [orbitChain, sepolia],
  transports: {
    [orbitChain.id]: http(),
    [sepolia.id]: http(),
  },
});
