# Engineering Report — Iteration 061

**Date**: 2026-03-28
**Status**: Full completion (no early stop)

## Implementation

Added `feature_columns: list[str] | None` parameter to `LightGbmStrategy`. In `compute_features()`, discovered features are filtered against the whitelist. 50 features selected by gain importance from a single IS LightGBM.

## Backtest Results

| Metric | Iter 061 IS | Baseline IS | Iter 061 OOS | Baseline OOS |
|--------|-------------|-------------|-------------|-------------|
| Sharpe | +1.40 | +1.60 | +0.51 | +1.16 |
| Win Rate | 43.3% | 43.4% | 39.7% | 44.9% |
| Profit Factor | 1.31 | 1.31 | 1.10 | 1.27 |
| Max Drawdown | 53.5% | 64.3% | 55.3% | 75.9% |
| Total Trades | 503 | 574 | 141 | 136 |
| PnL | +341.3% | +387.9% | +32.3% | +78.6% |
| OOS/IS Sharpe | 0.36 | 0.72 | — | — |

### Per-Symbol

**In-Sample** (balanced!):
- BTC: 224 trades, 43.8% WR, +173.6% PnL (50.9% of total)
- ETH: 279 trades, 43.0% WR, +167.7% PnL (49.1% of total)

**Out-of-Sample**:
- ETH: 88 trades, 39.8% WR, +38.9% PnL (120.2% of total)
- BTC: 53 trades, 39.6% WR, -6.5% PnL (-20.2% of total)

### Baseline Constraint Check

1. OOS Sharpe > baseline (1.16): 0.51 → **FAIL**
2. MaxDD ≤ baseline × 1.2 (91.1%): 55.3% → PASS
3. Min 50 OOS trades: 141 → PASS
4. Profit factor > 1.0: 1.10 → PASS
5. No symbol > 30% of OOS PnL: ETH=120%, BTC=-20% → **FAIL** (concentration)
6. OOS/IS Sharpe > 0.5: 0.36 → **FAIL**

## Trade Execution Verification

Verified 10 trades. All correct: entry prices, SL/TP calculations, PnL, and exit reasons consistent. No anomalies.

## Key Observations

1. **First full completion since baseline** — no early stop in any year
2. **IS MaxDD dramatically improved**: 53.5% vs 64.3% — pruning removed noisy features that caused drawdowns
3. **IS perfectly balanced**: BTC and ETH contribute ~50% each (vs 21%/79% in baseline)
4. **OOS degraded on BTC**: BTC went negative OOS (-6.5%) while ETH carried (+38.9%)
5. **Feature selection introduced researcher overfitting**: IS gains don't fully transfer to OOS (ratio 0.36)
