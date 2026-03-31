# Iteration 097 — Engineering Report

**EARLY STOP**: Year 2025 PnL=-67.5%, WR=35.4%, 127 trades.

## Configuration

Same as iter 093 baseline + sample uniqueness weighting (AFML Ch. 4).
- Uniqueness computed per training window via vectorized sweep-line (O(n log n))
- Weights: uniqueness(i) * |PnL|(i) instead of just |PnL|(i)
- Uniqueness values: mean=0.046, range [0.045, 0.168]

## Results

| Metric | Iter 097 | Baseline (093) | Delta |
|--------|----------|----------------|-------|
| IS Sharpe | **+0.78** | +0.73 | **+0.05** |
| IS WR | 43.5% | 42.8% | +0.7 pp |
| IS PF | 1.22 | 1.19 | +0.03 |
| IS MaxDD | 87.6% | 92.9% | **-5.3%** |
| IS Trades | 354 | 346 | +8 |
| OOS Sharpe | **-1.07** | +1.01 | **-2.08** |
| OOS WR | 35.6% | 42.1% | **-6.5 pp** |
| OOS PF | 0.80 | 1.25 | -0.45 |
| OOS MaxDD | 76.2% | 46.6% | **+29.6%** |
| OOS Trades | 101 | 107 | -6 |

## Label Leakage Audit

- CV gap: 44 rows, verified on all folds
- No leakage detected
- Uniqueness computation is per-symbol, doesn't cross CV boundaries

## Analysis

The uniqueness weighting slightly improved IS metrics (Sharpe +0.78 vs +0.73, MaxDD -5.3%) but catastrophically degraded OOS (Sharpe -1.07 vs +1.01). This is researcher overfitting: the weighting change fit IS better but didn't generalize.

Root cause: With 7-day timeout on 8h candles, ALL samples have uniqueness ~0.046 (1/21.7). The uniqueness multiplicative factor essentially flattens the |PnL| weights from range [1,10] to [0.05,1.68]. This removes the model's focus on high-conviction (high-PnL) trades, which was apparently important for OOS performance.

The |PnL| weighting in the baseline is not random — it's an implicit bet-sizing signal. Removing it via near-uniform uniqueness destroys the signal.
