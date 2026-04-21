# Iteration 170 Research Brief

**Date**: 2026-04-22
**Role**: QR
**Type**: **EXPLORATION** (symbol universe expansion — different sector)
**Previous iteration**: 169 (NO-MERGE EARLY STOP, per-symbol BTC collapse)
**Baseline**: v0.165 (A+C+LTC, OOS Sharpe +1.27, IS Sharpe +1.08)

## Section 0 — Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Motivation

Three alt-L1 candidates (AVAX iter-164, ATOM iter-167, DOT iter-168) failed Gate 3 at year-1. The shared failure mode is 2022 bear-market regime that these tokens' training windows couldn't generalise through. LTC (iter-165) — a payments L1 with a different macro cycle — succeeded.

This iteration tests whether the failure is about the alt-L1 cluster specifically vs. our configuration. **AAVEUSDT** (Aave) is in the DeFi sector — different narrative cycle, different beta, distinct from BTC/ETH (large-caps), LINK (infrastructure/oracle), LTC (payments), and the rejected L1 cluster.

Pass criteria (same Gate 3):
- IS Sharpe > 0
- IS WR > 33.3%
- ≥ 100 IS trades
- Year-1 cumulative PnL ≥ 0 (fail-fast)

User exclusions still in effect: DOGE, SOL, XRP, NEAR.

## New merge floor (applied from iter 170 onward)

Per skill update this iteration: **both IS Sharpe > 1.0 AND OOS Sharpe > 1.0** are absolute merge floors. Baseline v0.165 passes (IS +1.08, OOS +1.27). If the AAVE-pooled portfolio would push IS below 1.0 or OOS below 1.0, the merge fails even if other constraints improve.

The floor implication for this iteration: AAVE Gate 3 pass is necessary but not sufficient. The pooled A+C+LTC+AAVE portfolio must maintain both floors. LTC is a modest IS contributor (+48% of total weighted PnL) and adding AAVE at a similar profile should keep aggregate IS Sharpe above 1.0.

## Research Analysis

### B — Symbol Universe (AAVE candidate)

**Gate 1 (data quality)**: AAVE has 6,041 candles from 2020-10 through 2026-04-20. Well above the 1,095 IS candle floor, first candle before the 2023-07 cutoff.

**Gate 2 (liquidity)**: AAVE is a top-25 cap DeFi blue-chip with substantial Binance volume. Passes.

**Gate 3 (stand-alone profitability)** — subject of this iteration.

### E — Sectoral rationale

| Sector | Candidates | Gate 3 result |
|---|---|---|
| Large-cap (BTC, ETH) | Model A (pooled) | In baseline |
| Oracle / infrastructure | LINK | In baseline |
| Payments L1 | LTC | In baseline (iter 165) |
| Smart-contract L1 | AVAX, ATOM, DOT | All failed (iter 164, 167, 168) |
| DeFi blue-chip | AAVE | **THIS ITERATION** |

A pass here confirms that the screening config generalises beyond payments (LTC was the single exception); a fail suggests we need structural change (feature pruning, per-sector labeling, etc.).

## Configuration

Runner: `run_iteration_170.py`, identical to iter-167/168 runners with `symbols=("AAVEUSDT",)`. `yearly_pnl_check=True`. ATR 3.5/1.75. `BASELINE_FEATURE_COLUMNS` (193). Ensemble seeds [42, 123, 456, 789, 1001].

## Expected Outcomes

- **Pass**: iter 171 pools A+C+LTC+AAVE and evaluates merge. MUST check BOTH Sharpe floors.
- **Fail**: 4-of-5 candidates have now failed at 3.5/1.75. Iter 171 should be EXPLOITATION — for example, tighten VT or reduce Optuna confidence range — to rebalance the exploration rate.

## Exploration/Exploitation Tracker

Window (161-170): [E, E, E, E, E, X, E, E, E, E] → **9E / 1X**, 90% E (way over 30% floor). After iter 170, MUST run 2-3 exploitation iterations regardless of outcome.

## Commit Discipline

- Brief → `docs(iter-170): research brief`
- Runner → `feat(iter-170): AAVE Gate 3 runner`
- Engineering report → `docs(iter-170): engineering report`
- Diary (last) → `docs(iter-170): diary entry`
