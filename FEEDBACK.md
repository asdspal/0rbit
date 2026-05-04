# FEEDBACK — Uniswap v4 Integration (0rbit)

## Integration Summary
- **Purpose.** 0rbit uses Uniswap v4 to guarantee that every job escrow on the 0G testnet lands in mock USDC, while still allowing posters to originate payment in *any* ERC-20, fulfilling Section 15 of the blueprint.
- **Flow.** The frontend fetches a Smart Order Router quote for the poster’s chosen ERC-20 → USDC path, executes the swap against the Uniswap v4 router, and then forwards the resulting USDC to `OrbittMarket.postJob()` along with the job spec hash.
- **Result.** Escrow accounting, KeeperHub releases, and ENS-linked agent payouts all operate on a single stable unit (USDC) even though inflows can be arbitrary tokens.

## Technical Details
### Swap → Escrow Path (Blueprint §6.2)
1. **Quote + approval.** The poster selects any ERC-20 in the job form; the frontend pulls a Uniswap v4 quote and prompts `approve()` for that token.
2. **Swap execution.** The frontend submits the v4 swap (testnet pools) so output arrives as mock USDC (see `contracts/contracts/MockUSDC.sol`). The router transaction hash is persisted in Supabase `jobs.uniswap_swap_tx` (Column documented in `memory-bank/blueprint.md` §7) for auditability.
3. **Escrow deposit.** With USDC in the poster’s wallet, we call `OrbittMarket.postJob(paymentToken, amount, specHash, deadline)` so the contract locks funds via `transferFrom` (`contracts/contracts/OrbittMarket.sol` §postJob). The `paymentToken` parameter stays configurable, but Section 15 forces USDC after the swap to keep escrow deterministic.

### Release & Settlement (Blueprint §6.2 / Section 14 Phase 4)
- `OrbittMarket.releaseEscrow()` (keeper-only) moves the exact USDC amount to the winning agent’s wallet once KeeperHub verifies the 0G Compute proof. Because all posters end up funding in USDC, KeeperHub’s workflow only needs to support a single payout asset even though the intake side is chain-agnostic.
- The backend mirrors every escrow in Postgres (`payment_token`, `escrow_amount`, `uniswap_swap_tx`) so audit logs can show: *ERC-20 in → Uniswap swap hash → OrbittMarket jobId*.

## Developer Experience Feedback
- **Quote parity on testnets.** The v4 Smart Order Router works well, but pool liquidity on 0G/Sepolia forks is thin; we pre-provisioned pairs against `MockUSDC` so quotes do not revert. Publishing canonical pool addresses for sponsor testnets would remove guesswork.
- **Stable escrow UX.** Having a single escrow asset simplified the frontend and KeeperHub logic tremendously—swapping before `postJob` is still the right trade-off even though it adds one transaction for posters.
- **SDK ergonomics.** The existing v4 TypeScript SDK was easy to embed inside the Next.js app; no custom backend proxy was needed for quote building.

## Issues / Requests
1. **GAP – On-chain swap hook.** `OrbittMarket.sol` currently assumes the caller already swapped to USDC (tracked in `progress.md` Step M.1.6). If Uniswap exposes a lightweight hook-on-transfer example for v4, we could enforce the swap on-chain and remove one manual step for posters.
2. **Testnet routing data.** A published registry of sanctioned pools/tokens for the Uniswap prize testnets would prevent mismatched quotes when liquidity providers recycle contracts between hackathons.

## GAP Tracking
- The blueprint explicitly calls out `[GAP: Exact FEEDBACK.md format requirements]`; this document follows a standard API feedback structure while noting the outstanding format ambiguity for compliance.
