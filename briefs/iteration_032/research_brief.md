# Research Brief: 8H LightGBM Iteration 032 — EXPLOITATION

## 0. Data Split: OOS cutoff 2025-03-24. Full data range, NO start_time changes.

## 1. Change: Raise confidence threshold floor from 0.50 to 0.60

### Rationale
The IS Sharpe is -0.96 because early walk-forward months (2021-2022) generate many low-quality trades. Optuna sometimes picks thresholds near 0.50 in these months, meaning almost no filtering. By raising the floor to 0.60, even weak months are forced to be selective — only trading when the model has ≥60% confidence.

This doesn't trim bad months — the model still predicts during them. It just requires HIGHER confidence to actually trade, which should reduce losses in weak periods.

### Research Checklist: E (Trade Patterns)
From iter 016 IS: Monthly trade count varies from 2 to 100. Months with many trades tend to lose. A 0.60 floor will cap the maximum trades per month.

## 2. Everything Else Unchanged
BTC+ETH, TP=4%/SL=2%, timeout=4320, threshold 0.60-0.85, 12mo, 50 trials, seed 42.

## Exploration/Exploitation Tracker
Last 10: [E, E, E, E, X, E, E, E, **X**, ?] → exploitation turn
