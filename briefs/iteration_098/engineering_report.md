# Iteration 098 — Engineering Report

**EARLY STOP**: Year 2022 PnL=-109.6%, WR=31.0%, 100 trades.

## Results

| Metric | Iter 098 | Baseline (093) |
|--------|----------|----------------|
| IS Sharpe | **-1.44** | +0.73 |
| IS WR | 31.7% | 42.8% |
| IS PF | 0.69 | 1.19 |
| IS MaxDD | 157.3% | 92.9% |

Time decay (half-life=12mo) caused catastrophic failure in the first prediction year.

## Root Cause

The first training window (2020-01 to 2022-01) has 24 months of data. Time decay gives 2020-01 samples weight 0.25× and 2021-12 samples weight 1.0×. This means the model heavily weights late-2021 bull market patterns while down-weighting 2020 bear/recovery patterns. When predicting 2022 (bear market), the bull-biased model fails catastrophically.

The 24-month training window was specifically designed to include both bull and bear cycles. Time decay undermines this by making the window effectively ~12 months of "high-weight" data — losing the regime diversity that makes the baseline work.

## Label Leakage Audit

CV gap: 44 rows, verified. No leakage.
