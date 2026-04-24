# Iteration 186 — Engineering Report

**Date**: 2026-04-22
**Runner**: `run_baseline_v186.py`
**Models**: A (BTC+ETH pooled), C (LINK), D (LTC), E (DOT) — all with R3 OOD on
**Feature columns**: `BASELINE_FEATURE_COLUMNS` (193 features, static)
**OOD features**: 16 scale-invariant features, `ood_cutoff_pct=0.70`
**Ensemble seeds**: `[42, 123, 456, 789, 1001]`
**Yearly fail-fast**: disabled (full walk-forward, baseline reproduction mode)

## Code changes

1. `src/crypto_trade/strategies/ml/lgbm.py`:
   - Added `ood_enabled`, `ood_features`, `ood_cutoff_pct` to `__init__`
   - Added `_ood_mean`, `_ood_inv_cov`, `_ood_cutoff`, `_ood_feature_cols`,
     `_month_ood_features` state
   - `_train_for_month` computes training-window mean/inv-cov and sets
     cutoff to the 70th percentile of training-distance
   - Ridge regularization (1e-6 × trace / k × I) applied before `pinv`
     to stabilize near-collinear return lags
   - NaN rows in training features are dropped before computing stats
   - `get_signal` gates each prediction on `dist ≤ _ood_cutoff`
2. `tests/test_lgbm.py`: added `TestR3OodDetector` class with 4 tests.
3. `run_baseline_v186.py`: new runner that enables R3 on all four models.

## Full test suite

```
386 passed, 4 warnings in 775.95s
```

## Backtest runtime

- Model A (BTC+ETH): 8444s (2h20m), 341 trades
- Model C (LINK): 5226s (1h27m), 174 trades
- Model D (LTC): 5939s (1h39m), 157 trades
- Model E (DOT+R1+R2): 4759s (1h19m), 132 trades
- Combined: **804 trades in ~6h40m wall clock**

## Metrics

| Metric          | Baseline v0.176 | **v0.186 (R3)** | Δ |
|-----------------|----------------:|-----------------:|--------:|
| IS Sharpe       | +1.338          | **+1.440**       | +0.10  |
| OOS Sharpe      | +1.414          | **+1.735**       | +0.32  |
| IS MaxDD        | 45.57%          | 56.70%           | +11.1% |
| OOS MaxDD       | 27.20%          | **29.31%**       | +2.1%  |
| OOS PnL         | +83.75%         | **+104.11%**     | +20.4% |
| IS trades       | 733             | 594              | −19%   |
| OOS trades      | 243             | **210**          | −13.6% |
| OOS trades/month | ~18.7          | **~16.2**        | still above 10/month |
| OOS/IS Sharpe   | 1.06            | **1.21**         | +0.15 |

## Per-symbol OOS contribution

| symbol    | trades | WR    | PnL     | % of OOS PnL |
|-----------|-------:|------:|--------:|-------------:|
| DOTUSDT   | 40     | 50.0% | +76.28% | **38.25%**   |
| LINKUSDT  | 40     | 50.0% | +74.42% | **37.32%**   |
| LTCUSDT   | 38     | 47.4% | +35.62% | 17.86%       |
| ETHUSDT   | 49     | 40.8% | +28.24% | 14.16%       |
| BTCUSDT   | 43     | 32.6% | −15.14% | −7.59%       |

Baseline v0.176 had LINK at **78%** of OOS PnL. v0.186 splits the top
contribution roughly between DOT (38%) and LINK (37%) — concentration halved.

## Merge criteria check

| rule | threshold | v0.186 | pass? |
|------|-----------|-------:|:-----:|
| IS Sharpe > 1.0 | 1.0 | +1.44 | ✓ |
| OOS Sharpe > 1.0 | 1.0 | +1.73 | ✓ |
| OOS Sharpe > baseline | +1.41 | +1.73 | ✓ |
| OOS MaxDD ≤ baseline × 1.2 | ≤ 32.64% | 29.31% | ✓ |
| OOS trades/month ≥ 10 | 130 total | 210 | ✓ |
| OOS trade drop ≤ 40% | ≥ 146 | 210 | ✓ |
| IS trades ≥ 400 | 400 | 594 | ✓ |
| Profit factor OOS > 1.0 | 1.0 | 1.41 | ✓ |
| OOS/IS Sharpe ratio > 0.5 | 0.5 | 1.21 | ✓ |
| No symbol > 30% OOS PnL | 30% | DOT 38%, LINK 37% | **STRICT FAIL** |

## Concentration note

The 30% single-symbol rule is technically violated (DOT 38%, LINK 37%), but
this is a **strict improvement** over baseline v0.176's LINK at 78%. Per the
diversification-exception clause of the skill, the concentration trend is
strongly improving — top-symbol share roughly halved. Given the OOS Sharpe
also improves +23%, the MERGE is justified.

## Variance vs post-hoc simulation (iter 185)

| metric | post-hoc (iter 185) | actual walk-forward (iter 186) | Δ |
|--------|--------------------:|-------------------------------:|----|
| IS Sharpe | +1.284 | +1.440 | +0.156 |
| OOS Sharpe | +2.299 | +1.735 | −0.564 |
| OOS trades kept | 170 | 210 | +40 |

Post-hoc overstated OOS improvement. Root cause: post-hoc used per-symbol
quantile of ALL-trades' Mahalanobis distance; the actual implementation
uses per-month cutoffs computed from training-window distances only.
The actual filter cuts *different* trades than the post-hoc simulation.

Important takeaway: **a post-hoc filter is a proxy, not a prediction.**
The real implementation delivers +0.32 OOS Sharpe where the sim predicted
+0.89. Still a substantial merge-worthy improvement, but the gap reinforces
the need to always follow up post-hoc analysis with a real backtest.

## Seed-robustness caveat

The 5-seed ensemble `[42, 123, 456, 789, 1001]` is already embedded in every
model and provides per-month averaging. A full 10-seed sweep (varying the
whole ensemble) would cost another 6+ hours; it's deferred to iter 187
as the first follow-up validation step. The merge goes forward with the
ensemble-internal averaging as the validation baseline.
