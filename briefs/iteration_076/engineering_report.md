# Engineering Report: Iteration 076

## Implementation

Added `atr_label: bool = False` parameter to `LightGbmStrategy`. When enabled with ATR execution multipliers, the labeling phase loads NATR_21 values for all training candles, converts to raw ATR (`close × NATR / 100`), and passes them to `label_trades()` with `tp_pct=2.9, sl_pct=1.45` (matching execution barriers).

Changes made:
- `src/crypto_trade/strategies/ml/lgbm.py`: Added `atr_label` parameter, modified `_train_for_month()` to load NATR and compute ATR-aligned labels when enabled
- `run_iteration_076.py`: Runner script with `atr_label=True`

No changes to `labeling.py` — the existing ATR mode handled everything correctly.

## Deviations from Brief

None. Implementation matches the brief exactly.

## Trade Execution Verification

Sampled 5 trades from OOS trades.csv:

| Symbol | Dir | Entry | Exit | Reason | PnL | Net PnL | Verified |
|--------|-----|-------|------|--------|-----|---------|----------|
| BTCUSDT | LONG | 82377.30 | 86669.63 | TP | +5.21% | +5.11% | OK |
| ETHUSDT | SHORT | 1853.34 | 1928.37 | SL | -4.05% | -4.15% | OK |
| BTCUSDT | LONG | 83181.50 | 80194.46 | SL | -3.59% | -3.69% | OK |
| ETHUSDT | SHORT | 1794.47 | 1606.72 | TP | +10.46% | +10.36% | OK |
| BTCUSDT | LONG | 81561.60 | 84629.00 | TO | +3.76% | +3.66% | OK |

PnL calculations correct. Dynamic ATR barriers visible — TP/SL varies per trade (BTC TP ~5%, ETH TP ~10% reflecting different NATR levels).

## Results Summary

```
[report] IS:  Sharpe=1.3019  Trades=307  WR=47.2%  PF=1.3945  MaxDD=41.59%
[report] OOS: Sharpe=1.7182  Trades=93  WR=46.2%  PF=1.5689  MaxDD=21.64%
[report] OOS/IS Sharpe ratio: 1.3198
```

## Key Observations

1. **ATR-aligned labeling works as designed** — barriers vary per candle based on NATR_21
2. **99.1% ATR coverage** — 4346/4386 training candles had valid ATR values (first ~40 lack warmup)
3. **Label distribution shift** — ATR labels: 59.9% long / 40.1% short (vs baseline 54% / 46%). Dynamic barriers during volatile periods produce more directionally resolving labels.
4. **Backtest time**: 3894s (65 min) — similar to baseline
5. **OOS MaxDD dramatically reduced**: 21.64% vs 42.61% baseline — the aligned labeling produces more conservative trade selection during quiet markets
