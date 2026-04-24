# Iteration 164 Research Brief

**Date**: 2026-04-21
**Role**: QR
**Type**: **EXPLORATION** (symbol universe expansion — Gate 3 screen)
**Previous iteration**: 163 (NO-MERGE, entropy/CUSUM)
**Baseline**: v0.152 reproduction (OOS Sharpe +0.99, MaxDD 43.78%, 223 trades)

## Section 0 — Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

- IS = trades with `open_time < 2025-03-24`
- OOS = trades with `open_time >= 2025-03-24`
- The researcher sees OOS for the first time in Phase 7.

## Motivation

The baseline reproduction (2026-04-21) revealed that Model D (BNB) is a net drag on the portfolio — OOS Sharpe -0.59 alone, contributing -24.5% PnL in OOS. Removing D lifts portfolio Sharpe from +0.99 to +1.28, but the resulting A+C portfolio concentrates 131% of OOS PnL in LINK, failing the 30% concentration constraint.

To restore diversification *and* beat the baseline, BNB needs to be **replaced** by a candidate that carries its own predictive signal. User excluded DOGE, SOL, XRP, NEAR from new candidate exploration (already evaluated in past iterations). AVAX is the natural first pick: large-cap L1, comparable liquidity to LINK, distinct price action from BTC/ETH, not in the excluded list.

This iteration runs **only** the Gate 3 screen (stand-alone AVAX model) to decide whether AVAX is worth pooling. A positive Gate 3 result sets up iter 165 to run the pooled A+C+AVAX backtest. A negative result aborts AVAX and triggers iter 165 to try the next candidate (likely LTC or ATOM).

## Research Analysis (post-MERGE → 2 categories required)

### B — Symbol Universe (AVAX candidate)

**Data quality (Gate 1)**: AVAX has 6,109 8h candles starting 2020-09-23. Well above the 1,095 IS candle floor, first candle well before 2023-07-01, no known gaps.

**Liquidity (Gate 2)**: AVAX is top-20 by market cap. Reasonable assumption of > $10M daily volume across the IS window; will be verified by the QE during Phase 6 (read volume column from the parquet head).

**Stand-alone profitability (Gate 3)** — the subject of this iteration. Pass criteria:
- IS Sharpe > 0
- IS WR > 33.3% (break-even for 8%/4% effective TP/SL)
- At least 100 IS trades
- Year-1 cumulative PnL must not be negative (fail-fast checkpoint in the runner)

AVAX's volatility profile (NATR) is higher than BTC/ETH but comparable to LINK, so we reuse the LINK-style labeling: ATR 3.5×NATR / 1.75×NATR. This is identical to Model C and Model D's config, minimizing the number of variables changed.

### E — Trade Pattern (BNB diagnostic using IS-only)

Model D's IS numbers are OK (150 trades, 44.0% WR, +51% PnL) but the OOS collapse (64 trades, 35.9% WR, -24.5% PnL) shows the pattern did not generalize. The QR does not need deeper IS introspection on BNB to justify replacement — the OOS evidence is conclusive and was already surfaced in the baseline update on 2026-04-21.

## Configuration

**Runner**: `run_iteration_164.py` — new single-model runner for AVAX only.

| Parameter | Value |
|---|---|
| Symbols | `("AVAXUSDT",)` |
| Interval | 8h |
| Training window | 24 months |
| Label TP / SL | 8% / 4% (execution barriers) |
| ATR labeling | 3.5 × NATR TP, 1.75 × NATR SL |
| Timeout | 10,080 min (7 days) |
| Cooldown | 2 candles |
| Fee | 0.1% |
| Optuna trials | 50 per monthly model |
| Ensemble seeds | [42, 123, 456, 789, 1001] |
| Seed (constructor) | 42 |
| Feature columns | `BASELINE_FEATURE_COLUMNS` (193 explicit, from `live/models.py`) |
| Vol targeting | Enabled, target 0.3, lookback 45d, min_scale 0.33 |
| `yearly_pnl_check` | **True** — fail-fast if year-1 cumulative PnL < 0 |

Same config shape as Model C / D in the baseline — only the symbol changes. This keeps the comparison clean: if AVAX stand-alone clears Gate 3, we have a ready-to-pool candidate.

## Expected Outcomes

- **Strong pass** (IS Sharpe > 0.5, WR > 45%, 100+ trades): AVAX is a genuinely promising replacement. Iter 165 runs pooled A+C+AVAX. Portfolio has 4 models again, LINK concentration drops.
- **Marginal pass** (IS Sharpe 0 → 0.5): AVAX works but isn't obviously better than BNB. Document and decide in Phase 7.
- **Fail** (IS Sharpe ≤ 0 or year-1 abort): AVAX is not a fit. NO-MERGE. Iter 165 screens the next candidate (LTC likely).

## Hard Constraints

Standard baseline comparison rules apply only if/when iter 165 runs the pooled backtest. This iteration (iter 164) is a screen; merge/no-merge is judged by Gate 3 criteria alone.

## Exploration/Exploitation Tracker

Previous window (iters 154-163): 5E / 5X. Iter 164 = E → rolling window 155-164 = 5E / 5X (50% E, well above the 30% floor).

## Commit Discipline

- This brief → `docs(iter-164): research brief`
- Runner + eng report (after backtest) → `feat(iter-164): AVAX Gate 3 runner` + `docs(iter-164): engineering report`
- Diary → `docs(iter-164): diary entry` (LAST commit)
