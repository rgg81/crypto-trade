# Engineering Report — Iteration 105

## Results

**EARLY STOP** — Year 2022: PnL=-32.5%, WR=32.0%, 122 trades.

| Metric | Iter 105 (3-sym) | Baseline (093, 2-sym) |
|--------|-----------------|----------------------|
| IS Sharpe | -0.41 | +0.73 |
| IS WR | 31.7% | 42.8% |
| IS Trades | 123 (early stop) | 346 |

### Per-Symbol IS
| Symbol | Trades | WR | PnL |
|--------|--------|----|-----|
| ETHUSDT | 52 | 36.5% | +39.8% |
| BTCUSDT | 42 | 28.6% | -51.9% |
| BNBUSDT | 29 | 27.6% | -22.9% |

BNB fails Gate 4: WR 27.6% < break-even 33.3%. BTC also degraded from 43.2% to 28.6%.

## Label Leakage Audit
CV gap correctly computed as 66 = (21+1) × 3 symbols. Verified in logs.
