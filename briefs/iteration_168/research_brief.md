# Iteration 168 Research Brief

**Date**: 2026-04-21
**Role**: QR
**Type**: **EXPLORATION** (symbol universe expansion — 4th portfolio candidate)
**Previous iteration**: 167 (NO-MERGE EARLY STOP, ATOM fails Gate 3)
**Baseline**: v0.165 (A+C+LTC, OOS Sharpe +1.27)

## Section 0 — Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Motivation

AVAX (iter 164) and ATOM (iter 167) both failed Gate 3 at year-1. LTC (iter 165) passed. The next candidate on the priority list is **DOTUSDT** (Polkadot) — top-25 L1 with 5+ years of history, interchain/parachain narrative (overlap with ATOM but distinct macro).

If DOT also fails, the screening strategy needs a pause to reconsider. Three consecutive candidate failures at the same ATR multipliers (3.5/1.75) would be a pattern — possibly pointing at the config being over-fit to LINK+LTC specifically, not broadly applicable.

User exclusions still active: DOGE, SOL, XRP, NEAR.

## Research Analysis

### B — Symbol Universe (DOT candidate)

**Data quality (Gate 1)**: DOT has 6,206 candles from 2020-08 through 2026-04-20. Passes.

**Liquidity (Gate 2)**: DOT is top-25 cap. Passes.

**Stand-alone profitability (Gate 3)** — subject of this iteration, same criteria as before.

### E — Pattern observation across rejected candidates

AVAX and ATOM both had negative year-1 PnL at ATR 3.5/1.75. The ATR-multiplier choice was inherited from LINK/BNB/LTC which have realized NATR in the 3–6% range. AVAX and ATOM have higher realized NATR (5–10%) which produces wider TP/SL barriers — trades may time out or hit SL more often because 8h price movements rarely cover the barrier width.

This is a hypothesis, not a validated conclusion. Testing it would require running AVAX/ATOM at a different multiplier — but that's banned by fail-fast post-EARLY-STOP rules (parameter tweaks < 2×). Instead, the next screened candidate (DOT) runs at the standard 3.5/1.75 one more time. If DOT also fails, the pattern is strong enough to justify architectural change.

## Configuration

Runner: `run_iteration_168.py`, identical to iter-167 except `symbols=("DOTUSDT",)`.

## Expected Outcomes

- **Pass**: iter 169 pools A+C+LTC+DOT → likely MERGE
- **Fail**: iter 169 does NOT screen more candidates. Instead, pivot to improving Model A (per iter-167 Next Ideas #3)

## Exploration/Exploitation Tracker

Window (159-168): [X, X, E, E, E, E, E, X, E, E] → **7E / 3X**, 70% exploration. Above the 30% floor (and trending high — next few iterations should lean X to balance).

## Commit Discipline

- Brief → `docs(iter-168): research brief`
- Runner → `feat(iter-168): DOT Gate 3 runner`
- Engineering report → `docs(iter-168): engineering report`
- Diary (last) → `docs(iter-168): diary entry`
