# Iteration 079 — Engineering Report

**Status**: EARLY STOP (Year 2022 PnL = -46.0%, WR = 35.7%)
**Runtime**: 1280 seconds (~21 minutes)

## Implementation

Fixed iter 078's feature bloat: `compute_features()` now always discovers the global 106-feature intersection first, then assigns it to each per-symbol model. Confirmed: `[lgbm] 106 feature columns (per-symbol)`.

## Results: In-Sample (EARLY STOP)

| Metric | Iter 079 | Iter 078 | Baseline (068) |
|--------|----------|----------|----------------|
| Sharpe | **-0.49** | -0.61 | +1.22 |
| WR | **36.1%** | 38.6% | 43.4% |
| PF | **0.91** | 0.88 | 1.35 |
| MaxDD | **112.9%** | 90.4% | 45.9% |
| Trades | 155 | 132 | 373 |

### Per-Symbol

| Symbol | Iter 079 WR | Iter 078 WR | Baseline WR |
|--------|-------------|-------------|-------------|
| BTCUSDT | **37.7%** (77 trades) | 32.4% (74 trades) | 42.4% (172 trades) |
| ETHUSDT | **35.9%** (78 trades) | 46.6% (58 trades) | 44.3% (201 trades) |

**Key finding**: Fixing the feature count (106 vs 185) improved BTC (+5.3pp) but destroyed ETH (-10.7pp). With global features, ETH lost the specialization that made it work in iter 078. The 185-feature set apparently contained ETH-specific features that genuinely helped ETH but overfitted BTC.

## Trade Execution

Spot-checked 5 trades: all correct. SL exits match barrier distances, TP exits match barrier distances.

## Conclusion

Per-symbol models are definitively worse than pooled:
- **Iter 059**: per-symbol, early stop
- **Iter 078**: per-symbol 185 features, early stop (ETH 46.6% but BTC 32.4%)
- **Iter 079**: per-symbol 106 features, early stop (both ~36%)

Root cause: halved training data (~2,200 per symbol vs ~4,400 pooled) provides insufficient signal. Pooling BTC+ETH provides beneficial regularization.
