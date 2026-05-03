import { create } from 'zustand'

type Theme = 'dark'

export interface WalletSession {
  address: string | null
  ensName: string | null
}

export interface ActiveAgent {
  id: string
  ensName: string
  walletAddress: string
}

export interface UiPreferences {
  theme: Theme
}

export interface AppStore {
  walletSession: WalletSession | null
  activeAgent: ActiveAgent | null
  uiPreferences: UiPreferences
  setWalletSession: (session: WalletSession | null) => void
  setActiveAgent: (agent: ActiveAgent | null) => void
  setUiPreferences: (prefs: UiPreferences) => void
}

export const useStore = create<AppStore>((set) => ({
  walletSession: null,
  activeAgent: null,
  uiPreferences: { theme: 'dark' },
  setWalletSession: (session) => set({ walletSession: session }),
  setActiveAgent: (agent) => set({ activeAgent: agent }),
  setUiPreferences: (prefs) => set({ uiPreferences: prefs }),
}))
