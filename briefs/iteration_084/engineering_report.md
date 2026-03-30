# Iteration 084 Engineering Report

**Date**: 2026-03-30
**QE**: Claude (autopilot)

## Implementation Summary

Added two new parameters to `LightGbmStrategy`:
- `feature_columns: list[str] | None` — explicit feature list filter (restricts discovered features)
- `trading_symbols: list[str] | None` — symbol-scoped feature discovery

In `compute_features()`, the strategy now:
1. Discovers features using symbol-scoped intersection (BTC+ETH only, 198 features)
2. Filters to the 49 pruned features specified by the research brief
3. Logs any missing features as warnings

## Configuration

Identical to baseline (iter 068) except:
- Feature count: 49 (was 106 global intersection)
- Feature discovery: symbol-scoped (was global)
- All 49 features available in both BTC and ETH parquets

## Backtest Results

**EARLY STOP**: Year 2025 PnL=-21.1%, WR=37.4%, 99 trades. Triggered yearly checkpoint.

### In-Sample

| Metric | Iter 084 | Baseline (068) |
|--------|----------|----------------|
| Sharpe | +1.10 | +1.22 |
| WR | 43.8% | 43.4% |
| PF | 1.33 | 1.35 |
| MaxDD | 42.4% | 45.9% |
| Trades | 288 | 373 |
| Net PnL | +201.1% | — |

Per-symbol IS: BTC 48.0% WR (+109.2%), ETH 40.4% WR (+91.9%). Balanced.

### Out-of-Sample

| Metric | Iter 084 | Baseline (068) |
|--------|----------|----------------|
| Sharpe | **-0.03** | +1.84 |
| WR | 38.8% | 44.8% |
| PF | **0.99** | 1.62 |
| MaxDD | 45.4% | 42.6% |
| Trades | 85 | 87 |
| Net PnL | **-1.15%** | +94.0% |

Per-symbol OOS: BTC 30.6% WR (-19.7%), ETH 44.9% WR (+18.6%).

### Monthly OOS PnL

| Month | PnL | Trades |
|-------|-----|--------|
| 2025-03 | +6.7% | 1 |
| 2025-04 | **-24.0%** | 14 |
| 2025-05 | **-14.5%** | 9 |
| 2025-06 | +8.2% | 9 |
| 2025-07 | +3.7% | 1 |
| 2025-08 | -0.4% | 10 |
| 2025-09 | -6.9% | 13 |
| 2025-10 | +0.9% | 13 |
| 2025-11 | +23.5% | 5 |
| 2025-12 | -3.2% | 9 |
| 2026-01 | +4.8% | 1 |

## Trade Execution Verification

Sampled 5 trades from OOS trades.csv:

1. **ETHUSDT SHORT @ 2054.80**: TP at 1915.68. PnL = (2054.80-1915.68)/2054.80 = +6.77%, net +6.67% ✓
2. **BTCUSDT LONG @ 84389.80**: SL at 82203.12. PnL = (82203.12-84389.80)/84389.80 = -2.59%, net -2.69% ✓
3. **BTCUSDT LONG @ 83968.20**: SL at 81063.79. PnL = (81063.79-83968.20)/83968.20 = -3.46%, net -3.56% ✓
4. **ETHUSDT SHORT @ 1816.48**: TP at 1629.21. PnL = (1816.48-1629.21)/1816.48 = +10.31%, net +10.21% ✓
5. **BTCUSDT LONG @ 79560.20**: Timeout @ 84914.90. PnL = (84914.90-79560.20)/79560.20 = +6.73%, net +6.63% ✓

All exit prices, SL/TP distances, and PnL calculations are correct. Dynamic ATR barriers functioning properly.

## Key Observations

1. **IS improved on MaxDD**: 42.4% vs 45.9% baseline. Pruning reduced in-sample instability.
2. **IS Sharpe degraded 10%**: 1.10 vs 1.22. The 57 removed features contributed some IS signal.
3. **OOS collapsed**: Sharpe -0.03, essentially flat. The model's signal didn't generalize.
4. **BTC OOS disaster**: 30.6% WR, -19.7% PnL. Below break-even. The pruned features may have removed BTC-specific signal.
5. **ETH OOS OK**: 44.9% WR, +18.6% PnL. Similar to baseline's ETH performance.
6. **April-May 2025 was catastrophic**: -38.5% in 2 months, 23 trades. This period may be an OOS regime change that the pruned model couldn't adapt to.
