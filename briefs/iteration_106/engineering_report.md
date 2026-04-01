# Engineering Report — Iteration 106

## Results

| Metric | Iter 106 (7 models) | Baseline (093, 5 LGBMs) |
|--------|---------------------|------------------------|
| IS Sharpe | **+0.80** | +0.73 |
| OOS Sharpe | +0.48 | **+1.01** |
| IS WR | 43.0% | 42.8% |
| OOS WR | 37.1% | 42.1% |
| IS MaxDD | **73.7%** | 92.9% |
| OOS MaxDD | 64.5% | **46.6%** |
| IS Trades | 300 | 346 |
| OOS Trades | 89 | 107 |

**EARLY STOP in 2025** — cumulative PnL went negative in Year 4.

### Per-Symbol OOS
| Symbol | Trades | WR | PnL |
|--------|--------|----|-----|
| ETH | 46 | 43.5% | +30.8% |
| BTC | 43 | 30.2% | -8.1% |

## Label Leakage Audit
CV gap=44, unchanged. XGB and CB use same training data as LGBMs — no additional leakage risk.

## Key Finding
IS improved 10% (Sharpe +0.80 vs +0.73, MaxDD 73.7% vs 92.9%) but OOS degraded 52%. The XGB/CB models overfit slightly to training data. When averaged with LGBMs, they pull predictions toward the training distribution, which doesn't generalize to 2025.
