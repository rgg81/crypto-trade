# Engineering Report: Iteration 050

## Configuration

- **Change**: Balanced class weights (retry of iter 048 approach)
- **Symbols**: BTCUSDT, ETHUSDT
- **Training**: 24 months, 5 CV folds, 50 Optuna trials
- **Barriers**: TP=8%, SL=4%, timeout=7 days (10080 min)
- **Confidence threshold**: Optuna 0.50–0.85
- **Seed**: 42
- **Code change**: `_balance_weights(y, w)` in optimization.py (from iter 048)

## Results

| Metric | IS | OOS | Ratio |
|--------|-----|-----|-------|
| Sharpe | +1.32 | +1.66 | 1.26 |
| Sortino | +1.83 | +2.07 | 1.13 |
| WR | 42.6% | 45.3% | 1.06 |
| PF | 1.27 | 1.38 | 1.09 |
| MaxDD | 55.3% | 30.8% | 0.56 |
| Trades | 564 | 137 | — |
| PnL | +335% | +110% | — |

OOS/IS Sharpe ratio 1.26 — suspiciously high (>0.9 threshold). Could indicate luck rather than genuine improvement.

## Per-Symbol (OOS)

| Symbol | Trades | WR | PnL | % of Total |
|--------|--------|-----|------|------------|
| ETHUSDT | 76 | 50.0% | +121% | 110.2% |
| BTCUSDT | 61 | 39.3% | -11% | -10.2% |

BTC net negative in OOS. ETH carries entire portfolio.

## Comparison with Iter 048 (same approach)

| Metric | Iter 048 OOS | Iter 050 OOS |
|--------|-------------|-------------|
| Sharpe | +0.10 | +1.66 |

Same code, same approach — vastly different OOS results. High variance suggests seed sensitivity or lucky OOS sample.
