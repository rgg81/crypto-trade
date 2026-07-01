# CONFIRMATION-001 — iter-013 (mom + LTR + controlled TSMOM + VIX)

**Date:** 2026-07-01 · **Verdict: CONFIRMED (favorable-regime OOS; edge generalizes, leak-free).**

## The book (promoted to BASELINE_TRADFI)
`(1−0.25)·[sector-relative multi-horizon momentum + 0.5·(3y-1y LTR value-proxy)] + 0.25·TSMOM` + hysteresis
band δ=0.005 + exogenous VIX brake (base=20/floor=0.50). 69 Binance-tradeable single-stock perps, Yahoo
split+dividend-adjusted total-return, daily, next-open fills, 6bps/side taker.

## Results (IS 2010→2025-03 ; OOS 2025-03-24→2026-06-30, revealed once)
| | Sharpe | maxDD | notes |
|--|--------|-------|-------|
| IS (through-cycle anchor) | **+0.61** | −28% | 13/16 years positive, net-β +0.12 (85% neutral) |
| OOS (15 months) | **+3.39** | −8% | +65% total; **favorable-regime realization — do NOT extrapolate** |

## OOS forensic (fd6f4f49) — the +3.39 is genuine but regime-inflated
- LEAK-FREE (same past-only path, committed self-checks pass).
- CONSISTENT months (13/16 up, best=17% of PnL, ex-best +3.23) + BROAD names (top-3=42%, ex-top +3.07, 42/69 up).
- β +0.19 OOS → tilt ≈35% of PnL; **~65% genuine market-neutral alpha** (resid Sharpe +2.2). Neutral core
  ALONE was OOS +2.95 (the tilt added only +0.44) — the reveal is the momentum CORE catching a great AI/memory
  tape (EW-69 +133%), not the beta bet.
- Small-N: 95% CI [+1.33, +5.46] — no precision. **Honest forward expectation = through-cycle ~+0.6, floor ~+1.3.**

## CONFIRMATION verdict
**CONFIRMED.** The market-neutral momentum edge is REAL and GENERALIZED out-of-sample (leak-free, broad, did
not degrade). Meets the user-ratified bar (net ≥0.5 at realistic cost, controlled β, ≥13/16 years). CAVEATS
(documented, not hidden): (1) forward expectation is ~+0.6 not +3.39 (regime luck + small-N); (2) **base-cost-
fragile** — net drops to +0.42 at 2× cost (12bps), so robust only at realistic ~6bps; (3) 13/16 years, not
16/16 (structurally unreachable — diversifier factors dead 2010-25, positive-every-year needs perfect timing).

## Deployable / next
This is a deployable paper/testnet candidate (like the metals track). Before real capital: perp-vs-underlying
basis reconcile (backtest = Yahoo underlying total-return; live = Binance perp), a live-parity engine, and the
cost-fragility means position sizing / venue-fee tier matter. Improvement axes (all honest, none forced): cut
turnover for 2×-cost-robustness; PIT-membership broad universe to re-test size/value un-biased.
