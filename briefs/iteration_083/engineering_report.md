# Iteration 083 Engineering Report

## Configuration

- 198 features (185 base + 6 interaction + 7 xbtc, symbol-scoped discovery)
- Binary labeling, TP=8% SL=4%, timeout=7d
- Ensemble 3 seeds [42, 123, 789], cooldown=2
- Dynamic ATR barriers TP=2.9, SL=1.45
- Runtime: 5,880s (~1h38m) — faster than 3-class ternary

## Results

| Metric | IS | OOS | Ratio |
|--------|-----|-----|-------|
| Sharpe | +0.69 | +0.44 | 0.63 |
| WR | 43.6% | 42.2% | 0.97 |
| PF | 1.19 | 1.09 | 0.92 |
| MaxDD | 72.0% | 43.6% | 0.60 |
| Trades | 330 | 102 | 0.31 |
| Net PnL | +132.5% | +20.5% | 0.15 |

### Per-Symbol OOS

| Symbol | Trades | WR | PnL |
|--------|--------|-----|-----|
| BTCUSDT | 47 | 44.7% | +18.4% |
| ETHUSDT | 55 | 40.0% | +2.0% |

## Key Observations

1. **IS Sharpe collapsed**: +0.69 vs baseline +1.22 (-43%). The extra features add noise, not signal.
2. **IS MaxDD 72%**: Confirms iter 081's lesson — MaxDD > 60% = overfitting to noise.
3. **102 OOS trades** (vs 87 baseline): More trades but lower quality — PF 1.09 barely above break-even.
4. **OOS/IS ratio 0.63**: Acceptable generalization, but from a weak IS base.
5. **ETH degraded most**: OOS WR 40.0% (vs baseline 44.8%). The xbtc_ features may have confused the ETH model.

## Trade Execution Verification

Sampled 5 trades. Entry/exit prices, SL/TP levels, and PnL calculations all consistent. No anomalies.
