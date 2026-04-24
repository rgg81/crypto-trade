# Iteration 167 Research Brief

**Date**: 2026-04-21
**Role**: QR
**Type**: **EXPLORATION** (symbol universe expansion — 4th portfolio candidate)
**Previous iteration**: 166 (NO-MERGE, seed sweep was a no-op)
**Baseline**: v0.165 (A+C+LTC, OOS Sharpe +1.27, LINK 77.5% of OOS PnL)

## Section 0 — Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Motivation

Baseline v0.165 concentrates 77.5% of OOS PnL in LINKUSDT. The portfolio's 30% concentration constraint is still not met and is being held open by the diversification exception. Adding a 4th profitable model would:
- Increase portfolio trade density (more diversifying signals)
- Reduce LINK's share of OOS PnL toward the 30% target
- Allow the diversification exception to be retired

Next candidate per iter-165/166 diaries: **ATOMUSDT** (Cosmos). Mid-cap L1 with ~6 years of history, established liquidity, macro cycle distinct from BTC/ETH/LINK/LTC (interchain-narrative-driven rather than payments or smart-contract-platform).

User exclusions still in effect: DOGE, SOL, XRP, NEAR.

## Research Analysis (post-NO-MERGE → 2 categories)

### B — Symbol Universe (ATOM candidate)

**Data quality (Gate 1)**: ATOM has 6,796 8h candles starting 2020-08-07. Well above the 1,095 IS candle floor, first candle before 2023-07-01. Data is current through 2026-04-20 16:00 UTC. Passes.

**Liquidity (Gate 2)**: ATOM is a top-30 cap asset with substantial spot and derivatives volume on Binance. Passes (verified by volume column if QE chooses to spot-check).

**Stand-alone profitability (Gate 3)** — subject of this iteration. Pass criteria:
- IS Sharpe > 0
- IS WR > 33.3% (break-even for effective 8%/4%)
- ≥ 100 IS trades
- Year-1 cumulative PnL ≥ 0 (fail-fast)

### E — Trade Pattern / Labeling rationale

ATOM realized volatility sits between BTC/ETH (3–6% NATR) and high-beta alts (5–10%). ATR multipliers from LINK/LTC (3.5 / 1.75) are the natural first choice for continuity. If ATOM Gate 3 fails at that setting, parameter retuning is banned in the next iteration (fail-fast protocol after early stop bans parameter tweaks <2×).

## Configuration

Runner: `run_iteration_167.py` — identical in structure to iter-165 except `symbols=("ATOMUSDT",)`. `yearly_pnl_check=True`. Same `ensemble_seeds=[42, 123, 456, 789, 1001]` as the baseline Model C/LTC (ensemble-level seed parity).

## Expected Outcomes

- **Strong pass**: IS Sharpe > 0.5, WR > 40%, ≥ 100 trades → ready to pool.
  Next step: iter 168 = pooled A+C+LTC+ATOM diagnostic + MERGE if hard constraints move closer to all-pass.
- **Marginal pass**: IS Sharpe 0–0.5 → borderline. Document and decide whether to pool.
- **Fail**: year-1 abort OR IS Sharpe ≤ 0 → NO-MERGE. Iter 168 screens DOT as the next candidate.

## Exploration/Exploitation Tracker

Window (158-167): [X, X, X, E, E, E, E, E, X, E] → **6E / 4X**, 60% — above the 30% floor.

## Commit Discipline

- Brief → `docs(iter-167): research brief`
- Runner → `feat(iter-167): ATOM Gate 3 runner`
- Engineering report → `docs(iter-167): engineering report`
- Diary (last) → `docs(iter-167): diary entry`
