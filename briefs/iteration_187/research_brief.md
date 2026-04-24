# Iteration 187 — Drop BTC from portfolio? (rejected)

**Date**: 2026-04-22
**Type**: EXPLOITATION (post-hoc symbol-contribution analysis)
**Baseline**: v0.186
**Decision**: NO-MERGE

## Motivation

v0.186's per-symbol OOS contribution showed BTC at −7.6% of total PnL
(43 trades, WR 32.6%, PnL −15.14%). This prompted the question: is BTC
a net drag on the portfolio? Would Model A — currently pooling BTC+ETH
— generalize better if restricted to ETH only, or should Model A be
dropped entirely?

## Method

Post-hoc simulation from `reports/iteration_186/`: recompute IS and OOS
portfolio metrics for four slices:

1. All symbols (current v0.186)
2. Drop BTC
3. Drop BTC + ETH (LINK+LTC+DOT only)
4. Per-symbol standalone metrics for BTC and ETH

## Result

### OOS (entry ≥ 2025-03-24)

| slice           | trades | Sharpe    | PnL     | MaxDD  | WR    |
|-----------------|-------:|----------:|--------:|-------:|------:|
| All             | 210    | **+1.737**| +104.11%| 29.31% | 43.8% |
| Drop BTC        | 167    | +1.756    | +98.35% | 32.31% | 46.7% |
| Drop BTC + ETH  | 118    | +1.387    | +67.05% | 23.10% | 49.2% |
| BTC standalone  | 43     | +0.308    |  +5.76% | 13.34% | 32.6% |
| ETH standalone  | 49     | +1.110    | +31.30% | 25.21% | 40.8% |

### IS (entry < 2025-03-24)

| slice           | trades | Sharpe    | PnL     | MaxDD  | WR    |
|-----------------|-------:|----------:|--------:|-------:|------:|
| All             | 594    | **+1.440**|+297.99% | 56.70% | 43.4% |
| Drop BTC        | 511    | +1.370    |+269.19% | 57.26% | 43.2% |
| Drop BTC + ETH  | 345    | +1.435    |+257.57% | 58.31% | 44.3% |
| BTC standalone  | 83     | +0.496    | +28.80% | 20.74% | 44.6% |
| ETH standalone  | 166    | +0.163    | +11.63% | 24.54% | 41.0% |

### Per-year BTC / ETH

| symbol | year | n   | WR    | PnL    |
|--------|------|----:|------:|-------:|
| BTC | 2022 | 30 | 33.3% | −13.36% |
| BTC | 2023 | 28 | 50.0% |  +5.33% |
| BTC | 2024 | 23 | 47.8% | +26.63% |
| BTC | 2025 (full) | 35 | 38.3% | **+24.22%** |
| BTC | 2026 (partial) | 10 | 20.0% | −8.25% |
| ETH | 2022 | 55 | 38.2% |  +8.39% |
| ETH | 2023 | 55 | 41.8% |  +4.56% |
| ETH | 2024 | 48 | 43.8% |  +1.49% |
| ETH | 2025 (full) | 39 | 48.7% | +29.53% |
| ETH | 2026 (partial) | 18 | 22.2% |  −1.05% |

## Finding

Dropping BTC is essentially a wash (+0.019 OOS Sharpe) but costs:
- **−20% trade count** (210 → 167) — still above the 10/month floor but
  closer to it.
- **+3.00 pp MaxDD** (29.31% → 32.31%) — exceeds the 20% tolerance vs.
  v0.176 baseline, pushing outside the hard constraint.
- −5.76 pp OOS PnL (+104.11% → +98.35%).

Dropping BTC + ETH (both Model A contributions) is strictly worse:
OOS Sharpe drops from +1.737 to +1.387.

**Model A (BTC+ETH pool) is a net contributor** to portfolio Sharpe even
when individual BTC OOS is weak. The pooled training gives BTC signal
access to ETH's covariate structure and vice versa. Each symbol
standalone has OOS Sharpe well below 1.0 (BTC +0.31, ETH +1.11); pooling
lifts Model A's OOS Sharpe to a meaningful contribution.

## The 2026 partial-year weakness

Both BTC and ETH had weak 2026 Q1 performance (BTC WR 20%, ETH WR 22%).
Small sample (10 and 18 trades). This is likely noise, not a structural
break. If the weakness persists through Q2-Q3, revisit Model A.

## Decision

NO-MERGE. Portfolio stays as v0.186.

## Exploration/Exploitation Tracker

Window (177-187): [E, E, E, X, E, X, E, X, X, X, **X**] → **5E/6X**.
Balanced.

## Next Iteration Ideas

- **Iter 188**: Tighter OOD cutoffs (0.60 or 0.50). Post-hoc on v0.186
  trades — if we drop top-X%-most-OOD trades post-hoc and the IS Sharpe
  holds, motivate a new baseline run with the tighter cutoff.
- **Iter 189**: Per-symbol OOD cutoffs. Compute each model's Mahalanobis
  distribution separately; pick per-symbol cutoffs that minimize
  within-symbol OOS drawdown. BTC specifically might benefit from a
  tighter cutoff than altcoins.
- **Iter 190**: Drop BTC from Model A training (ETH-only Model A).
  Post-hoc analysis suggests this is not beneficial for pool-trained,
  but an ETH-only retrain could yield different results because the
  model would fit ETH specifically. Cost: one full Model A re-run
  (~2.5 hours).
- **Iter 191**: Cross-asset features. Add BTC's 30-day return and funding
  rate as features to LINK/LTC/DOT. Might improve LINK's OOS Sharpe
  (currently +1.1) by exploiting crypto-wide regime information.
