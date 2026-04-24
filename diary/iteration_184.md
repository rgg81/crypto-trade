# Iteration 184 — R4 vol kill-switch (rejected)

**Date**: 2026-04-22
**Type**: EXPLOITATION (risk mitigation from the skill's R1-R5 list)
**Baseline**: v0.176 — unchanged
**Decision**: NO-MERGE

## What I tried

Post-hoc simulation of R4 (realized-volatility kill-switch). For every trade in the v0.176 baseline (976 trades total), computed the 30-day rolling vol of the underlying at trade-open time. Bucketed by per-symbol vol quintile; simulated a per-symbol cutoff that drops trades above the Nth percentile.

## What happened

The data flipped the theory upside down.

IS quintiles:

| Q | vol30 | WR | mean pnl | wpnl sum |
|---|------:|---:|---------:|---------:|
| 0 | 38% | 47% | +0.60% | +62.7% |
| 1 | 52% | 40% | −0.15% | −9.4% |
| 2 | 65% | 40% | +0.08% | +16.0% |
| 3 | 82% | **49%** | **+1.06%** | **+102.5%** |
| 4 | 112% | 46% | +0.99% | +80.3% |

OOS quintiles:

| Q | vol30 | WR | mean pnl | wpnl sum |
|---|------:|---:|---------:|---------:|
| 0 | 40% | 29% | −0.58% | −4.3% |
| 1 | 57% | 46% | +1.13% | +22.7% |
| 2 | 68% | 43% | +0.73% | +3.5% |
| 3 | 74% | 44% | +0.56% | +24.8% |
| 4 | 97% | **49%** | **+2.09%** | **+37.1%** |

**Higher vol quintiles are MORE profitable**, not less. In OOS, Q0 (low vol) is the only net-negative bucket.

Kill-switch sweep — every cutoff degrades both IS and OOS Sharpe:

| cutoff | IS Sharpe | OOS Sharpe |
|-------:|----------:|-----------:|
| 1.00 (baseline) | **+1.338** | **+1.414** |
| 0.95 | +1.163 | +1.301 |
| 0.80 | +1.037 | +1.041 |
| 0.50 | +0.661 | +1.148 |

## Why R4 was wrong

1. **Vol-targeting already de-risks high vol.** Each trade is already sized inversely to 45-day vol via `vt_scale`. A kill-switch stacked on top silences the *signal*, not just the *size*.
2. **The model's edge IS the volatile regime.** 8h candles catch breakouts, liquidation cascades, gamma squeezes — events that manifest as high realized vol. Cutting these off removes alpha, not risk.
3. **R4 is symmetric by construction.** It would need to know the *direction* of the vol (pro-model vs. against-model) to be useful — which is R3's job.

This is a clean disproof. R4 goes off the candidate list.

## What this teaches

- Risk mitigation is not a universal good. R1 helped LINK/LTC/DOT (consecutive-SL streaks are tail risk). R2 helped DOT (2022 regime shift). R5 hurt LINK (alpha reduction). R4 would hurt everyone.
- The remaining unchecked mitigations from R1-R5 are: R3 (OOD detector — complex, directly targets regime shift) and R5 variants (running-balance concentration cap — complex, LINK-specific).
- Mechanical risk mitigations from outside the model's feature space have diminishing returns. Any further defence should either live *inside* the feature set (OOD) or be a model-level change (improving Model A, which contributes only ~10% of OOS PnL).

## Exploration/Exploitation Tracker

Window (174-184): [E, E, X, E, E, E, X, E, X, E, **X**] → **7E/5X**. Tracker balancing out after six consecutive exploration rejections.

## Next Iteration Ideas

- **Iter 185**: R3 OOD detector post-hoc analysis. For each trade, compute Mahalanobis distance of the feature vector vs. the training-window mean/cov (on a small scale-invariant subset: RSI_14, returns_lags, vol ratios). Bucket trades by distance; measure if distance correlates with trade outcome. If yes, a simple percentile-based filter becomes R3.
- **Iter 186**: Seed-robustness sweep of v0.176 — rerun with 3 different ensemble seed groupings to get mean/std OOS Sharpe. The merge was validated against a single ensemble grouping; the skill requires seed-robustness before MERGE.
- **Iter 187**: Model A improvement. Model A is weakest (Sharpe ~+0.24, 10% of OOS PnL) but per the skill cannot be pruned without destroying co-optimization. Alternative: retrain Model A with the same BASELINE_FEATURE_COLUMNS but a tighter hyperparameter search space constrained to regions that performed well in the iter-152 Optuna log (exploit, don't re-explore).
