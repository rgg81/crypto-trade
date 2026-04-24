# Iteration 165 Research Brief

**Date**: 2026-04-21
**Role**: QR
**Type**: **EXPLORATION** (symbol universe expansion — Gate 3 screen, attempt 2)
**Previous iteration**: 164 (NO-MERGE EARLY STOP, AVAX fails Gate 3)
**Baseline**: v0.152 reproduction (OOS Sharpe +0.99)

## Section 0 — Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

- IS = trades with `open_time < 2025-03-24`
- OOS = trades with `open_time >= 2025-03-24`
- The researcher sees OOS for the first time in Phase 7.

## Motivation

Per iter-164's "Next Iteration Ideas", AVAX failed Gate 3 at the year-1 checkpoint (IS Sharpe -1.84, 2022 PnL -34.6%). The next candidate to screen for Model D' is **LTC (Litecoin)**: top-20 cap, ~13 years of history, considerably lower realized volatility than AVAX, and a macro/narrative cycle distinct from BTC/ETH/LINK (payments-oriented rather than smart-contract / DeFi).

This iteration runs only the Gate 3 stand-alone profitability screen. If it passes, iter 166 will run the pooled A+C+LTC backtest to check Gates 4–5. If it fails, iter 166 will screen the next candidate (ATOM, then DOT).

User-excluded symbols remain: DOGE, SOL, XRP, NEAR.

## Research Analysis (post-NO-MERGE → same 2 categories)

### B — Symbol Universe (LTC candidate)

**Data quality (Gate 1)**: LTC has 6,867 8h candles available. First candle is 2019-09-08 (before the 2023-07-01 floor). No known gaps. Data is current through 2026-04-20. Passes.

**Liquidity (Gate 2)**: LTC is a top-20 cap asset with daily volume comfortably above $100M even in bear markets. Passes (verified by QE if necessary from volume column of parquet).

**Stand-alone profitability (Gate 3)** — what this iteration tests. Same pass criteria:
- IS Sharpe > 0
- IS WR > 33.3%
- ≥ 100 IS trades
- Year-1 cumulative PnL ≥ 0 (fail-fast)

### E — Trade Pattern / Labeling rationale

LTC realized volatility (NATR) during 2022–2024 was in the 3–6% range on 8h candles, similar to BTC/ETH and lower than LINK/AVAX. Using the tighter Model A labeling (ATR TP 2.9, SL 1.45) is plausible, but for consistency and reduced variable count we will use the Model C/D config (ATR 3.5/1.75) first. If LTC fails that, iter 166 could try the 2.9/1.45 config — but that would be a second screen, not a retry.

## Configuration

Runner: `run_iteration_165.py` — identical in structure to iter-164 except `symbols=("LTCUSDT",)`.

All other parameters inherit from the baseline Model C/D config:
- ATR TP 3.5 / SL 1.75
- 24-mo training window
- `BASELINE_FEATURE_COLUMNS` (193 explicit features, auto-discovery disabled)
- 50 Optuna trials, 5-seed ensemble [42, 123, 456, 789, 1001]
- VT: target 0.3, lookback 45d, min_scale 0.33
- Cooldown 2 candles, fee 0.1%
- `yearly_pnl_check=True` (fail-fast)

## Expected Outcomes

- **Strong pass**: IS Sharpe > 0.5, WR > 40%, 100+ trades → LTC is a ready-to-pool candidate. Iter 166 runs pooled A+C+LTC.
- **Marginal pass**: IS Sharpe 0–0.5 → weak signal. Document and decide whether to continue screening (vs. proceed anyway).
- **Fail**: IS Sharpe ≤ 0 or year-1 abort → LTC rejected. Iter 166 screens ATOM.

## Exploration/Exploitation Tracker

Window (156-165): [X, X, X, X, X, E, E, E, E, E] → **5E / 5X**, 50% E, above the 30% floor.

## Commit Discipline

- Brief → `docs(iter-165): research brief`
- Runner → `feat(iter-165): LTC Gate 3 stand-alone runner`
- Engineering report → `docs(iter-165): engineering report`
- Diary (last) → `docs(iter-165): diary entry`
