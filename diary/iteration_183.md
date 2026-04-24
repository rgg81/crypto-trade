# Iteration 183 — XLM screen, year-1 fail-fast (rejected)

**Date**: 2026-04-22
**Type**: EXPLORATION (new candidate, low-correlation)
**Baseline**: v0.176 — unchanged
**Decision**: NO-MERGE

## What I tried

Screened XLMUSDT standalone with R1+R2 active from the start. XLM was selected for having the lowest correlation (ρ ≈ 0.47 with BTC) with any existing portfolio member — a genuine diversifier candidate.

Configuration: `BASELINE_FEATURE_COLUMNS` (193 features), ATR labeling (3.5/1.75 multipliers), 5-seed ensemble, vol-targeting, R1 (K=3, C=27), R2 (trigger=7%, anchor=15%, floor=0.33).

## What happened

Year-1 (2022) fail-fast triggered at 55 trades:

```
Year 1 (2022): PnL=-4.5% (WR=38.2%, 55 trades)
```

Full IS (2022 only, early-stopped): Sharpe +0.045, WR 37.5%, PF 1.019, MaxDD 18.81%, DSR −65.98.

## Why it failed

1. **Signal is too weak**. Sharpe +0.045 is statistical noise. WR 37.5% is barely above the 33.3% break-even for 2:1 RR. DSR −65.98 says the Optuna result is almost certainly overfit.
2. **R1+R2 are damage control, not alpha**. They kept the drawdown contained (18.81% vs. XLM underlying's −75.7% drawdown in 2022) but cannot produce edge where the features have none.

## What R1+R2 bought us (and what they didn't)

| Metric                       | Value   |
|------------------------------|--------:|
| XLM underlying 2022 PnL      | −73.3%  |
| XLM underlying 2022 MaxDD    | −75.7%  |
| Strategy 2022 PnL (with R1+R2) | −4.5%  |
| Strategy 2022 MaxDD          | 18.8%   |

Risk mitigation worked as designed: the portfolio contained a 4% drawdown in the
worst year of crypto history. Just… not profitably. The year-1 rule exists for
good reason: a strategy that bleeds money in the training window's worst year
has no evidence of generalizable edge.

## Contrast with v0.176 members

| Symbol | 2022 underlying | 2022 strategy PnL | Made it in? |
|--------|---------------:|-------------------:|:-----------:|
| BTC    | −64.2%         | positive*          | ✓           |
| ETH    | −67.5%         | positive*          | ✓           |
| LINK   | −71.4%         | positive           | ✓           |
| LTC    | −52.0%         | positive           | ✓           |
| DOT    | −83.8%         | positive (with R1+R2) | ✓        |
| **XLM**| **−73.3%**     | **−4.5%**          | ✗           |
| AVAX   | −90.0%         | −21% (even w/R1+R2)| ✗           |
| ATOM   | ~−65%          | fail               | ✗           |

*BTC+ETH pool not decomposed per-symbol in this write-up; full pool is positive.

XLM's 2022 behaviour sits between LTC (cleared) and ATOM/AVAX (failed). The −4.5%
is frustratingly close to passing, but the skill's rule is binary.

## Decision

NO-MERGE. v0.176 remains the production baseline.

## Exploration/Exploitation Tracker

Window (173-183): [X, E, E, X, E, E, E, X, E, X, E] → 7E/4X.

## Next Iteration Ideas

- **Exploitation first.** Five consecutive candidate-screen iterations (178-183)
  have all rejected on year-1 fail-fast. The marginal ROI of continuing to screen
  altcoins is low. We already have four symbols clearing year 1 with strong signal.
- **Iter 184**: Re-visit Model A (BTC+ETH). Current Sharpe ~+0.24 is the weakest
  component of v0.176. Try narrowing BASELINE_FEATURE_COLUMNS to just scale-invariant
  features that are known to work for majors (~60 features, ratio ~75). Rationale:
  iter 117's meme-model pruning proved that small, mature pools benefit from
  explicit pruning.
- **Iter 185**: Alternative R3 — instead of a feature-space OOD detector,
  compute **realized-vol kill-switch** per symbol (skip new entries when rolling
  30-day vol exceeds the training window's 95th percentile). Simpler than
  Mahalanobis and directly targets the 2022-style regime failure.
- **Iter 186**: Re-merge v0.176 with a 3-seed sweep to verify seed-robustness.
  The skill requires 5-seed validation before any MERGE; v0.176's merge has only
  been validated against seed=42 inside the ensemble. A post-hoc sweep of three
  different *ensemble* seed groupings (shuffle the 5 seeds) would show whether
  the +1.41 OOS Sharpe is the median or an outlier.
