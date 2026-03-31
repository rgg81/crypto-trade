# Engineering Report — Iteration 103

## Change Summary

Enriched meta-labeling with 5 meta-features, increased model capacity, and lower threshold.

## Results

**EARLY STOP** — Year 2022: PnL=-43.3%, WR=34.9%, 64 trades.

| Metric | Iter 103 | Iter 102 | Baseline (093) |
|--------|----------|----------|----------------|
| IS Sharpe | -0.82 | +0.52 | +0.73 |
| IS WR | 34.4% | 49.0% | 42.8% |
| IS MaxDD | 99.1% | 29.3% | 92.9% |
| IS Trades | 64 (early stop) | 49 (full) | 346 |
| OOS Trades | 0 | 2 | 107 |

## Meta-Model Training Statistics

| Month | OOF Samples | Base WR | Pass Count | Pass % | Pass WR |
|-------|-------------|---------|------------|--------|---------|
| Early months | 3655 | 37.8% | 1238 | 34% | 63.9% |
| Mid months | 3655 | 33.5% | 986 | 27% | 63.3% |
| Late months | 3650 | 33.5% | 958 | 26% | 59.3% |

Training pass WR of 59-64% is promising — the meta-model DOES learn useful patterns. But these patterns don't survive the walk-forward into 2022.

## Label Leakage Audit

- Primary model: CV gap=44, unchanged
- Meta-model: trained on OOF predictions from primary model's CV folds — correct by construction
- No leakage between meta-training and meta-inference

## Trade Execution Verification

64 IS trades sampled — entry/exit mechanics correct. The early stop at 2022 is genuine.
