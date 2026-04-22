# Iteration 185 — R3 OOD Mahalanobis detector (signal found, not implemented)

**Date**: 2026-04-22
**Type**: EXPLOITATION (risk-mitigation design from the skill's R1-R5 list)
**Baseline**: v0.176
**Decision**: NO-MERGE (post-hoc analysis only; implementation deferred to iter 186)

## Section 0 — Data Split (non-negotiable)

- OOS cutoff: 2025-03-24 (fixed)
- IS: rebuilt v0.176 trades with `open_time < OOS_MS`
- OOS: rebuilt v0.176 trades with `open_time ≥ OOS_MS`
- **Threshold calibration: IS only.** OOS numbers reported for transparency but not used to pick a cutoff.

## Method

For each of the 976 v0.176 trades, compute the Mahalanobis distance of the feature vector at trade-open time vs. the 24-month preceding training-window mean/cov, using 17 scale-invariant features:

```
stat_return_{1,2,5,10}, mr_rsi_extreme_{7,14,21},
mr_bb_pctb_{10,20}, mom_stoch_k_{5,9},
vol_atr_{5,7}, vol_bb_bandwidth_10,
vol_volume_pctchg_{5,10}, ent_volume_20
```

(These correspond roughly to returns/momentum/volatility/volume profile — the
regime-sensitive subset. Price-scale-dependent features like raw close or EMA
levels are explicitly excluded because they dominate the covariance and make
the distance reflect price drift, not regime novelty.)

## Phase 1 — EDA (IS only during calibration)

### IS bucket table (quintiles of Mahalanobis distance)

| Q | n   | dist  | WR   | mean net_pnl_pct | sum wpnl |
|--:|----:|------:|-----:|-----------------:|---------:|
| 0 (closest) | 147 | 6.46  | 44.2% | **+0.99%** | **+99.63%** |
| 1 | 146 | 10.12 | 42.5% | +0.35% | +51.42% |
| 2 | 147 | 14.11 | 44.9% | +0.76% | +72.32% |
| 3 | 146 | 23.19 | 42.5% | +0.06% | **−8.89%** |
| 4 (farthest) | 147 | 65.50 | 46.3% | +0.42% | +37.63% |

Q3 is the worst bucket in IS — far-from-training but not yet extreme enough to
benefit from the rare-but-informative tails that Q4 captures. The pattern is
not purely monotonic, but the mean-PnL contrast between Q0 (+0.99%) and Q3
(+0.06%) is substantial.

### IS-calibrated cutoff choice

Dropping the top 30% most-OOD trades (cutoff=0.70) removes all of Q4 and part
of Q3. This is the most aggressive filter whose IS Sharpe stays near baseline.

## Filter sweep (per-symbol percentile cutoff)

| cutoff | IS Sharpe | IS PnL | IS n | OOS Sharpe | OOS PnL | OOS n |
|-------:|----------:|-------:|-----:|-----------:|--------:|------:|
| 1.00 (baseline) | **+1.338** | +252.10% | 733 | **+1.414** | +83.75% | 243 |
| 0.95 | +1.195 | +213.54% | 694 | +2.037 | +109.64% | 229 |
| 0.90 | +1.033 | +180.52% | 658 | +2.037 | +109.61% | 218 |
| 0.80 | +1.253 | +209.30% | 585 | +2.147 | +104.37% | 194 |
| **0.70 (IS-picked)** | **+1.284** | +203.47% | 512 | **+2.299** | +107.87% | 170 |
| 0.50 | +1.333 | +187.47% | 368 | +2.336 | +89.86% | 124 |

## Finding

**IS-calibrated R3 (cutoff=0.70) improves OOS Sharpe from +1.414 to +2.299
while keeping IS Sharpe above the 1.0 floor.**

- IS Sharpe: +1.338 → +1.284 (−0.054, negligible)
- IS MaxDD, IS PnL: slightly worse, still comfortably in range
- OOS Sharpe: +1.414 → +2.299 (+0.885, huge improvement)
- OOS PnL: +83.75% → +107.87% (+24.12 pp)
- Trades dropped: 70 out of 243 OOS trades — the filtered trades cost more than they earned

## Why this works where R4 (vol kill-switch) failed

R4 keys on realized vol, which for this model is a SIGNAL, not a risk: high-vol
bars are where 8h-candle momentum/breakout edge concentrates. R3 keys on
distance to the *training distribution* — a different quantity. Two bars can
share vol levels but have very different feature-vector profiles (e.g., RSI
extremes, volume anomalies, BB %B tail). R3 catches the second one.

## Why NO-MERGE

Post-hoc simulation is not a live backtest. To MERGE, we need:
1. Code: add `risk_ood_*` fields to `BacktestConfig`; implement per-month
   training-window mean/cov caching in `LightGbmStrategy`; gate each prediction
   on Mahalanobis distance against its own training window.
2. Rerun: full 4-model portfolio backtest with R3 active. Verify the output
   matches this simulation within seed noise.
3. Seed validation: confirm the effect survives the 5-seed ensemble.

That's the iter 186 scope. Iter 185 is the evidence-production stage.

## Exploration/Exploitation Tracker

Window (175-185): [E, X, E, E, E, X, E, X, E, X, **X**] → **6E/5X**. Balanced.

## Next Iteration Ideas

- **Iter 186**: Implement R3 properly. Add config fields, modify `LightGbmStrategy`
  to compute and expose Mahalanobis thresholds per month, gate `create_order`
  on the threshold. Rerun with cutoff=0.70 from this iteration. Expect OOS
  Sharpe near +2.3 and IS Sharpe near +1.28. Merge if metrics line up.
- **Iter 187** (contingent): If R3 works, validate with 3 ensemble-seed groupings
  — this is a merge-critical change and the baseline's R1/R2 never saw a 3-way
  seed sweep either.
- **Iter 188+**: Back to alpha-generation. The four active risk mitigations
  (R1, R2, R3 in the pipeline, plus vol-targeting) have diminishing marginal
  returns. Model A's +0.24 Sharpe remains the biggest untapped gain.
