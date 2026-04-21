# Iteration 171 Engineering Report

**Role**: QE
**Config**: DOT stand-alone with DOT-tuned 40-feature set (ATR 3.5/1.75, 24mo, VT on)
**Status**: **EARLY STOP (year-1 checkpoint)**
**Elapsed**: 4 min 36 s (276 s)

## Trigger

```
Year 2022: PnL=-44.4% (WR=23.8%, 21 trades)
```

## Partial results (IS only; no OOS reached)

| Metric                 | Value  |
|------------------------|-------:|
| Total trades           | 22     |
| IS Sharpe              | **−1.40** |
| IS Sortino             | −1.22  |
| IS WR                  | 27.3%  |
| IS Profit Factor       | 0.59   |
| IS MaxDD               | 35.31% |
| IS Net PnL             | −19.78%|

## Comparison to iter-168 (DOT with baseline 193 features)

| Metric       | Iter 168 (193 feats) | Iter 171 (40 feats, MDI-tuned) | Δ |
|--------------|---------------------:|--------------------------------:|---|
| Year-1 PnL   | −14.0%              | **−44.4%**                       | 3.2× worse |
| Year-1 trades| 16                  | 21                               | +31% |
| Year-1 WR    | 37.5%               | 23.8%                            | −13.7 pp |
| IS Sharpe    | +0.54               | **−1.40**                        | −1.94 |
| IS trades    | 17                  | 22                               | +5 |
| IS WR        | 41.2%               | 27.3%                            | −13.9 pp |

**The tuned feature set made everything worse.** More trades, lower WR, deeper loss, collapsed Sharpe. This is not a "small iteration", it's a directional contradiction of the hypothesis.

## Why the hypothesis failed

The DOT-tuned 40-feature list was built from:

1. MDI ranking on a reference LightGBM trained with 193 features on DOT IS alone. But this reference model was ALREADY in the catastrophic-overfit regime (samples/feature ≈ 11). Features that overfit noise most effectively get the highest MDI — pruning to them concentrates the overfitting.
2. A cheap label proxy (sign of next candle's close) instead of the production triple-barrier 8%/4% over 7-day horizon. Features predictive of one-step direction are not necessarily predictive of what the actual trading model cares about.
3. Spearman |corr|>0.90 dedup is defensible in isolation, but compounded with (1) and (2) the surviving set is noise-tilted.

The skill already warns about this:

> "For mature co-optimized models (100+ features, Optuna-tuned over many iterations): Explicit pruning destroys co-optimization. Use `colsample_bytree` for implicit selection instead. (Iter 094: pruning BTC/ETH to 50 features → IS Sharpe −1.46, catastrophic.)"

I hit the exact failure mode. Iter-094's IS Sharpe −1.46 and iter-171's IS Sharpe −1.40 are almost identical — the rhyme is unmistakable.

## What the data still tells us about DOT

The iter-168 DOT 2022 breakdown (from research brief) stands:

- 2022-09: 5 trades, 80% WR, +10.99%
- 2022-11: 5 trades, 40% WR, +1.63%
- 2022-12: 7 trades, **14.3% WR, −19.11%**

Without Dec 2022 alone, iter-168 DOT would have cleared year-1 at +12.62%. So the DOT signal is intact for ~11 of 12 months — the regime mismatch in Dec 2022 is the actual problem, not feature count.

## Label Leakage Audit

CV gap: `(10080/480 + 1) × 1 = 22`. Unchanged. No leakage.

## Feature Reproducibility Check

40 explicit columns from the curated `DOT_TUNED_FEATURES` tuple in the runner. The tuple is committed in `run_iteration_171.py`. Parquet column presence was verified before the run (no KeyError during training).

## Recommended next move for the QR

Stop trying to solve this with feature selection. The evidence now points firmly at a REGIME PROBLEM. Iter 172 should do evidence-backed regime-filter research:

1. Load BTC IS data.
2. Compute candidate regime metrics (30-day realised vol, rolling drawdown, BTC-dominance proxy) monthly.
3. Identify which metric(s) would have flagged Dec 2022 but not flagged the months when DOT was profitable.
4. Propose either (a) a regime feature added to `feature_columns` OR (b) a post-prediction regime veto in the backtest engine.
5. THEN re-run DOT.
