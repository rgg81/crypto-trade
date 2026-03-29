# Iteration 081 Engineering Report

## Configuration

Same as iter 080 except `neutral_threshold_pct=1.0` (was 2.0).

- Ternary classification with 3 classes (short/neutral/long)
- neutral_threshold_pct: 1.0% (timeout candles with |return| < 1.0% become neutral)
- Ensemble: 3 seeds [42, 123, 789], averaged probabilities
- Walk-forward: monthly, 24mo window, 5 CV folds, 50 Optuna trials per model
- Dynamic ATR barriers: TP=2.9, SL=1.45
- Cooldown: 2 candles

## Backtest Results

**EARLY STOP**: Year 2025 PnL=-19.1% (WR=34.1%, 88 trades).

Runtime: 9,739 seconds (~2h42m).

### comparison.csv

| Metric | IS | OOS | Ratio |
|--------|-----|-----|-------|
| Sharpe | +1.26 | **-1.17** | -0.93 |
| WR | 44.9% | **30.8%** | 0.69 |
| PF | 1.38 | **0.74** | 0.53 |
| MaxDD | 87.9% | 53.4% | 0.61 |
| Trades | 343 | 65 | 0.19 |
| Net PnL | +263.8% | **-38.6%** | -0.15 |

### Per-Symbol OOS

| Symbol | Trades | WR | PnL |
|--------|--------|-----|-----|
| BTCUSDT | 31 | 29.0% | -13.8% |
| ETHUSDT | 34 | 32.4% | -24.8% |

### Exit Reasons OOS

- Stop-loss: 38 (58%), mean PnL -3.67%
- Take-profit: 14 (22%), mean PnL +6.96%
- Timeout: 13 (20%), mean PnL +0.26%

### Direction OOS

- SHORT: 42 trades, WR 31.0%
- LONG: 23 trades, WR 30.4%

## Trade Execution Verification

Sampled 5 OOS trades from trades.csv. Entry prices match signal candle close. SL/TP prices consistent with ATR-dynamic barriers. Exit reasons match PnL (SL trades have PnL ≈ -3.7%, TP trades ≈ +7.0%). No anomalies detected.

## Key Observations

1. **IS metrics are nearly identical to iter 080** (Sharpe +1.26 vs +1.26, WR 44.9% vs 44.6%). The 1.0% threshold produces similar IS quality to 2.0%.
2. **OOS collapsed completely**: Sharpe -1.17 (vs +1.00 in iter 080). Both symbols unprofitable. WR 30.8% is below break-even (33.3%).
3. **IS MaxDD 87.9%** is much worse than both iter 080 (56.1%) and baseline (45.9%). This suggests the lighter noise filtering allows more bad trades through in drawdown periods.
4. **SL rate 58%** in OOS is very high (vs 50.7% in iter 080). The model is less selective, hitting stop-losses more often.
5. **Neutral rate in training was ~4.8%** (first month) vs ~11.1% in iter 080. Fewer labels removed = noisier training data.
