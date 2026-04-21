# Iteration 169 Engineering Report

**Role**: QE
**Config**: BTC stand-alone (ATR 2.9/1.45, 24mo, 193 features, VT on)
**Status**: **EARLY STOP (year-1 checkpoint)**
**Elapsed**: 23 min (1,401 s)

## Trigger

```
Year 2022: PnL=-38.2% (WR=35.7%, 70 trades)
```

## Partial results (IS only; no OOS reached)

| Metric | Value |
|---|---:|
| Total trades | 71 |
| IS Sharpe | -0.57 |
| IS WR | 36.6% |
| IS Profit Factor | 0.84 |
| IS MaxDD | 31.64% |
| IS Net PnL | -11.38% |

Every Gate 3 criterion fails:
- IS Sharpe > 0? **FAIL** (-0.57)
- IS WR > 33.3%? ✓ (36.6%)
- ≥ 100 IS trades? **FAIL** (71)
- Year-1 PnL ≥ 0? **FAIL** (-38.2%)

## Interpretation

The **pooled** Model A (BTC+ETH) with the same 193 features produced +68.98% IS PnL at 46.4% BTC-WR in the baseline reproduction. Removing ETH from the training data collapses BTC's performance. This is the **samples/feature ratio** problem predicted by the skill:

- Pooled: BTC (2,200 samples) + ETH (2,200 samples) = 4,400 training rows × 193 features → ratio 22
- Per-symbol: BTC alone = 2,200 rows × 193 features → ratio 11

Ratio 11 is in the "catastrophic overfitting" zone (iter 078 territory). The model memorises training-period noise and generalises poorly.

## Label Leakage Audit

CV gap: `(10080/480 + 1) × 1 = 22`. Unchanged.

## Feature Reproducibility Check

193 explicit columns from `BASELINE_FEATURE_COLUMNS`. Confirmed by log.

## Summary

Per-symbol BTC with full feature set (193) is not viable. The signal is *crowded out* by feature noise in the per-symbol regime. Next iteration must either prune features (30–50 range) or abandon the per-symbol track.
