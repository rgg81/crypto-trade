# Engineering Report: Iteration 075

## Implementation

1. Reverted the symbol-filtered discovery "fix" from iters 073/074
2. Restored original `_discover_feature_columns()` behavior: scans all 760 parquet files
3. Restored calendar/interaction feature group registrations (irrelevant — not in the 106-feature intersection)
4. Global intersection across 760 symbols = exactly 106 features
5. Runner matches iter 068 baseline parameters exactly

## Backtest Results — BASELINE REPRODUCED

| Metric | Iter 075 | Baseline (068) | Match? |
|--------|----------|----------------|--------|
| IS Sharpe | +1.2232 | +1.22 | YES |
| IS WR | 43.4% | 43.4% | YES |
| IS PF | 1.3458 | 1.35 | YES |
| IS MaxDD | 45.94% | 45.9% | YES |
| IS Trades | 373 | 373 | YES |
| OOS Sharpe | +1.8391 | +1.84 | YES |
| OOS WR | 44.8% | 44.8% | YES |
| OOS PF | 1.6190 | 1.62 | YES |
| OOS MaxDD | 42.61% | 42.6% | YES |
| OOS Trades | 87 | 87 | YES |
| OOS/IS ratio | 1.5035 | 1.50 | YES |

**Every metric matches the baseline exactly.** The backtest is fully deterministic with the ensemble seeds [42, 123, 789].

## Root Cause Confirmed

The failures in iters 073-074 were caused by the "symbol-filtered discovery fix" that increased features from 106→185/187. The global intersection (106 features) is what makes the model work. The discovery scanning all 760 parquets acts as implicit feature selection.

## Runtime

~3780s (~63 min) — full walk-forward completion, no early stop
