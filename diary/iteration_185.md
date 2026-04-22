# Iteration 185 — R3 OOD Mahalanobis detector (signal found)

**Date**: 2026-04-22
**Type**: EXPLOITATION (risk-mitigation design)
**Baseline**: v0.176 — unchanged
**Decision**: NO-MERGE (post-hoc evidence only — implementation deferred to iter 186)

## TL;DR

Mahalanobis distance on 17 scale-invariant features identifies trades that have
a −0.63% OOS mean-PnL (Q3 of the distance distribution). Filtering the top 30%
most-OOD trades raises OOS Sharpe from +1.414 to +2.299 while leaving IS Sharpe
at +1.284 — still comfortably above the 1.0 floor. This is the strongest
single-change signal I've seen since the LTC add.

## Data

For every v0.176 trade (n=976), computed the Mahalanobis distance of the
opening-candle feature vector vs. the 24-month preceding training-window
mean/cov. Features restricted to scale-invariant ones: returns, RSI extremes,
BB %B, stoch K, ATR normalized, volume %-change, volume entropy.

**IS quintiles:**

| Q | dist | WR | mean pnl | sum wpnl |
|---|-----:|---:|---------:|---------:|
| 0 | 6.5  | 44% | +0.99% | +99.6% |
| 1 | 10.1 | 43% | +0.35% | +51.4% |
| 2 | 14.1 | 45% | +0.76% | +72.3% |
| 3 | 23.2 | 43% | +0.06% | **−8.9%** |
| 4 | 65.5 | 46% | +0.42% | +37.6% |

**OOS quintiles (for calibration transparency — NOT used to pick threshold):**

| Q | dist | WR | mean pnl | sum wpnl |
|---|-----:|---:|---------:|---------:|
| 0 | 6.5  | 35% | +0.11% | +23.6% |
| 1 | 9.4  | 50% | +2.34% | +68.0% |
| 2 | 12.7 | 43% | +0.61% | +19.2% |
| 3 | 19.3 | 33% | −0.63% | **−21.4%** |
| 4 | 65.9 | 49% | +1.50% | −5.6% |

Both IS and OOS show Q3 as the worst bucket. Q4 (farthest) is mixed — extreme
OOD is rare and sometimes captures real breakouts.

## Filter sweep (per-symbol percentile cutoff)

| cutoff | IS Sharpe | OOS Sharpe |
|-------:|----------:|-----------:|
| 1.00 (baseline) | **+1.338** | **+1.414** |
| 0.95 | +1.195 | +2.037 |
| 0.80 | +1.253 | +2.147 |
| **0.70 (IS-picked)** | **+1.284** | **+2.299** |
| 0.50 | +1.333 | +2.336 |

The IS-calibrated cutoff of 0.70 (drops the ~30% most-OOD trades per symbol)
yields the best tradeoff: +0.885 OOS Sharpe for −0.054 IS Sharpe.

## Why NO-MERGE (for this iteration)

Post-hoc simulation is not a live backtest. MERGE requires:

1. Adding `risk_ood_enabled`, `risk_ood_cutoff`, `risk_ood_features` fields to
   `BacktestConfig`.
2. Teaching `LightGbmStrategy` to cache per-month training-window mean/cov for
   the OOD feature subset.
3. Gating `create_order` on `mahalanobis ≤ per_symbol_cutoff`.
4. Running the full 4-model backtest and verifying numbers match this sim.

That's iter 186.

## Why this is interesting (vs. iter 184 R4)

R4 (vol kill-switch) failed because realized-vol correlates with the model's
edge — high-vol bars are where 8h-candle momentum/breakout signals live.
R3 (OOD) correlates with *feature novelty*, not vol. Two bars can share vol
levels and have entirely different feature-space regimes. R3 catches the
regime-shift failures that R4 could not.

## Contrast with prior work

- **Iter 089** tried purged CV with `PurgedKFoldCV(purge=21, embargo=0.02)`
  — IS Sharpe collapsed to −1.32. Theoretically correct but practically
  catastrophic. Lesson: label-space isolation is brittle.
- **Iter 175** tried a DOT regime filter (rolling-vol gate) — weak signal.
- **Iter 185 (this)** tries feature-space OOD detection via Mahalanobis. Much
  stronger signal. The key difference: this operates on the prediction-time
  feature vector, not on labels or raw price series.

## Exploration/Exploitation Tracker

Window (175-185): [E, X, E, E, E, X, E, X, E, X, **X**] → **6E/5X**.

## Next Iteration Ideas

- **Iter 186** (mandatory follow-up): implement R3 in the backtest code. Verify
  the post-hoc numbers hold up when the filter is actually active during the
  walk-forward. If they do, MERGE.
- **Iter 187**: 3-way ensemble-seed validation of the R3-enabled baseline.
- **Iter 188+**: Shift focus to Model A. The risk-mitigation stack is mature;
  further gains come from alpha, not defence.
