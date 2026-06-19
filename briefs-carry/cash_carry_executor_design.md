# Cash-and-Carry Executor — design / build plan (pilot)

**Strategy (user spec):** open SPOT + PERP **limit (maker)** orders in sync; hold collecting funding;
close both in sync. Price legs hedge 1:1 → P&L = funding − (fixed maker fee) − basis slippage.

## 0. THE BINDING PRECONDITION — maker fee tier
The whole edge is `funding_collected_over_hold  >  round_trip_maker_fee`. Round-trip = 4 fills
(open: buy spot + sell perp; close: sell spot + buy perp). Spot maker fee DOMINATES:

| tier | spot maker | perp maker | ~round-trip cost | verdict (recent compressed-funding regime) |
|---|---|---|---|---|
| standard | 0.100% | 0.020% | ~0.24% | DEAD (OOS −3.3 to −4.8) |
| +BNB | 0.075% | 0.018% | ~0.19% | dead |
| top VIP / rebate | ~0.02% | ~0.00% | ~0.04% | ~breakeven OOS (no-floor); thin |

**Build only justified at a low-maker-fee tier.** The executor must enforce a per-trade gate:
enter a coin ONLY when `expected funding over the planned hold ≥ k × round_trip_maker_fee` (k≈2 for
margin). This makes the strategy self-gating on the fee reality.

## 1. The hard part — synchronized maker fills + leg risk
Maker limit orders DON'T fill simultaneously or guaranteed. The core risk: one leg fills, the other
doesn't → naked directional exposure (a squeeze on the unhedged perp short can lose >> the funding).
The executor is fundamentally a **two-leg fill-synchronization state machine**:

```
IDLE → QUOTING (post-only limit on BOTH legs at/near touch)
  ├─ both fill within window W      → HEDGED (the good path)
  ├─ one fills, other doesn't       → LEG_RISK:
  │     • re-quote the unfilled leg up to N times (chase the touch), OR
  │     • after timeout, CROSS the unfilled leg with a taker order (accept ~1 leg of taker
  │       cost to restore the hedge immediately) — bounded, known cost; never sit naked.
  └─ neither fills in W             → cancel, re-quote or skip
HEDGED → HOLD (collect funding each 8h) while trailing funding > exit_thresh
HOLD → UNWIND (same sync-limit dance, close both) when funding flips / decays
```
Leg risk is THE make-or-break operational risk; the backtest assumed it away. The "cross with taker
on the lagging leg" fallback is the safety valve — it caps the downside of a desync at one taker leg.

## 2. Architecture (NEW module, parallel to the directional engine — do NOT modify it)
The live engine today is MARKET-order / PERP-only / single-leg directional (`auth_client.py`:
`place_market_order` on `/fapi/v1/order`; SL/TP algo orders). Cash-and-carry needs a separate path:

- **SpotAuthClient** — signed `/api/v3/order` (Binance spot): post-only `LIMIT_MAKER` (or `LIMIT`
  `timeInForce=GTX`), cancel, query, balances. (New; engine has no spot trading.)
- **PerpAuthClient** — extend `auth_client.py` with a **post-only perp limit** (`LIMIT`,
  `timeInForce=GTX`) method alongside the existing market path. (Small add.)
- **BasisExecutor** — the state machine in §1: quotes both legs, tracks fills, enforces leg-risk
  fallback, holds, unwinds. Funding-aware (no SL/TP — the position is hedged).
- **FundingMonitor** — pulls live funding + the trailing-M signal; emits enter/hold/exit per coin
  through the §0 fee gate.
- **BasisLedger** — per-coin position state, realized funding, fees paid, basis P&L; reconciles
  spot balance vs perp short each tick.

## 3. Pilot scope (validate the assumptions the backtest can't)
Start TINY (e.g. $100–500/leg) on 3–5 high-funding *liquid* coins. Run in three stages:
1. **Paper/observe** — log where post-only orders WOULD fill vs the touch; measure fill rate +
   desync frequency WITHOUT real orders.
2. **Tiny live** — real post-only orders, smallest size. **Measure the unknowns:** maker fill rate,
   desync/leg-risk frequency, realized funding captured, actual fees, basis slippage on exit.
3. **Decide** — scale only if measured net (after REAL fills) is positive at your fee tier.

## 4. Honest expectations (from the backtest)
- Even at a top VIP fee tier, OOS (recent, compressed-funding) is ~breakeven; the fat returns
  (17–44%/yr) were 2020–21 bull-regime IS. So this is **regime-dependent income** — meaningful only
  when funding is rich — NOT a steady alpha. Deploy as an opportunistic income overlay, sized small.
- Tiny DD (−3 to −7% in backtest) is the genuine upside: it's market-neutral, no squeeze.
- The maker-fill + leg-risk realities can only be measured live (stage 1–2), not back-tested.

## 5. What I will NOT do without explicit sign-off
Write code that places REAL orders (spot or perp). This design + a paper-mode simulator are safe to
build; live-order code touches money and needs your go-ahead per-stage.

## Open decision for the user
**What maker-fee tier are you on (spot + perp), and do you have BNB-discount / any rebate?** That
single number decides whether this is worth building — it's the §0 precondition.
