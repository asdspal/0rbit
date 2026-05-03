import { describe, expect, it } from 'vitest'

import { useStore, type ActiveAgent, type WalletSession } from '../lib/store'

describe('store', () => {
  it('sets wallet session', () => {
    const session: WalletSession = { address: '0xabc', ensName: null }
    useStore.getState().setWalletSession(session)
    expect(useStore.getState().walletSession).toEqual(session)
  })

  it('clears wallet session', () => {
    useStore.getState().setWalletSession(null)
    expect(useStore.getState().walletSession).toBeNull()
  })

  it('sets active agent', () => {
    const agent: ActiveAgent = { id: 'agent-1', ensName: 'agent.eth', walletAddress: '0x123' }
    useStore.getState().setActiveAgent(agent)
    expect(useStore.getState().activeAgent).toEqual(agent)
  })

  it('clears active agent', () => {
    useStore.getState().setActiveAgent(null)
    expect(useStore.getState().activeAgent).toBeNull()
  })

  it('updates UI preferences', () => {
    useStore.getState().setUiPreferences({ theme: 'dark' })
    expect(useStore.getState().uiPreferences).toEqual({ theme: 'dark' })
  })
})
