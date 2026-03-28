# Iteration 068 — Engineering Report

## Implementation

Added `cooldown_candles` parameter to `BacktestConfig` (default=0, backward compatible). After a trade closes for a symbol, the backtest engine suppresses new signals for that symbol for `cooldown_candles × candle_duration` milliseconds.

### Files Changed
- `src/crypto_trade/backtest_models.py`: Added `cooldown_candles: int = 0` to BacktestConfig
- `src/crypto_trade/backtest.py`: Cooldown tracking via `cooldown_until: dict[str, int]`, checked before opening new orders

### Design Decision
Implemented at backtest level (not strategy level) for cleaner separation of concerns — no Strategy Protocol changes needed, works with any strategy.

## Backtest Configuration
- Ensemble: seeds [42, 123, 789], 3 models per month
- Training: 24 months, 50 Optuna trials, 5 CV folds
- Labeling: TP=8%, SL=4%, timeout=7 days
- Execution: Dynamic ATR barriers (2.9× TP, 1.45× SL)
- Features: 106 (global intersection)
- **cooldown_candles=2** (16h on 8h candles)
- Runtime: 3827s (~64 min)

## Results

| Metric | IS | OOS | OOS/IS |
|--------|-----|-----|--------|
| Sharpe | +1.22 | +1.84 | 1.50 |
| WR | 43.4% | 44.8% | 1.03 |
| PF | 1.35 | 1.62 | 1.20 |
| MaxDD | 45.9% | 42.6% | 0.93 |
| Trades | 373 | 87 | 0.23 |
| Net PnL | +264.3% | +94.0% | - |

## Cooldown Impact

| Metric | Baseline (cooldown=0) | Iter 068 (cooldown=2) | Change |
|--------|----------------------|----------------------|--------|
| IS Trades | 495 | 373 | -24.6% |
| OOS Trades | 114 | 87 | -23.7% |
| IS Sharpe | +1.23 | +1.22 | -0.8% |
| OOS Sharpe | +1.64 | +1.84 | +12.2% |
| IS MaxDD | 50.0% | 45.9% | -4.1pp |
| OOS MaxDD | 39.0% | 42.6% | +3.6pp |

Cooldown reduced trade count by ~24% while improving OOS Sharpe by 12% and IS MaxDD by 4pp.

## Trade Execution Verification

10 OOS trades verified:
- All entry/exit prices match direction calculations exactly
- All PnL calculations correct (max error < 0.01%)
- All fee deductions correct (0.1% per trade)

## Cooldown Verification

- Baseline: 81% immediate re-entry (gap ≤1 candle)
- Iter 068: **0% immediate re-entry**, minimum gap = 3 candles
- Cooldown works as designed

## Per-Symbol OOS Concentration

| Symbol | Trades | WR | Net PnL | % of Total |
|--------|--------|-----|---------|------------|
| ETHUSDT | 48 | 54.2% | +86.1% | **91.6%** |
| BTCUSDT | 39 | 33.3% | +7.9% | 8.4% |

**Single-symbol concentration is 91.6% — exceeds 30% limit.**
