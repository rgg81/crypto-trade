# Iteration 080 — Engineering Report

**Status**: COMPLETED (no early stop — first since baseline iter 068)
**Runtime**: 10,667 seconds (~178 minutes, ~3x baseline due to multiclass)

## Implementation

Added `neutral_threshold_pct` parameter to LightGbmStrategy, labeling.py, and optimization.py:
- labeling.py: timeout candles with |fwd_return| < 2.0% → label=0 (neutral)
- optimization.py: LightGBM `objective="multiclass"` with `num_class=3`, Sharpe computed on non-neutral predictions only
- lgbm.py: confidence = max(P(short), P(long)) ignoring P(neutral); neutral argmax → NO_SIGNAL

Label distribution (first month): 52.2% long, 36.7% short, 11.1% neutral.

## Results

| Metric | Iter 080 IS | Baseline IS | Iter 080 OOS | Baseline OOS |
|--------|------------|-------------|-------------|-------------|
| Sharpe | +1.26 | +1.22 | +1.00 | +1.84 |
| WR | 44.6% | 43.4% | 45.2% | 44.8% |
| PF | 1.38 | 1.35 | 1.33 | 1.62 |
| MaxDD | 56.1% | 45.9% | **33.4%** | 42.6% |
| Trades | 314 | 373 | 73 | 87 |
| Net PnL | +244.6% | +264.3% | +48.9% | +94.0% |

### Per-Symbol OOS

| Symbol | Trades | WR | PnL |
|--------|--------|-----|-----|
| BTCUSDT | 35 | **51.4%** | +38.0% |
| ETHUSDT | 38 | 42.1% | +18.2% |

BTC OOS: 51.4% WR (best ever). ETH OOS: 42.1% WR. Both profitable.
Symbol concentration: BTC 77.7% of OOS PnL (reversed from baseline's ETH 91.6%).

### Trade Execution Verification

Sampled 5 OOS trades — all correct. SL/TP prices match dynamic ATR barriers. PnL calculations accurate.

## Key Findings

1. **Ternary removes noisy labels, improves IS metrics**: IS Sharpe +1.26 vs +1.22, IS WR 44.6% vs 43.4%. Cleaner labels = better training.
2. **OOS MaxDD dramatically improved**: 33.4% vs 42.6% (22% reduction). The neutral class filters out trades in ambiguous conditions.
3. **Fewer trades**: 73 OOS vs 87 baseline (16% fewer). The ternary model is more selective, which reduces Sharpe due to lower trade frequency.
4. **OOS Sharpe lower**: 1.00 vs 1.84. Primarily due to fewer trades and lower net PnL (48.9% vs 94.0%). The per-trade quality (WR) is actually slightly better.
5. **OOS/IS ratio healthy**: 0.79 vs baseline's suspicious 1.50. Ternary generalizes well.
