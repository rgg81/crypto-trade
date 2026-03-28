# Research Brief — Iteration 059

**Type**: EXPLORATION (per-symbol model architecture)
**Date**: 2026-03-28

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

All analysis below uses IS data only (before 2025-03-24).

## Hypothesis

Train **separate LightGBM models for BTC and ETH** instead of a single pooled model. The pooled model forces the algorithm to learn patterns common to both symbols simultaneously, even though they exhibit substantially different trading dynamics. Per-symbol models can specialize in each asset's unique characteristics.

## Research Analysis (4 Categories)

### A. Feature Contribution Analysis

The baseline's 106 global intersection features are used by a single pooled model. Key per-symbol findings:

- **ETH dominates**: 78.9% of total IS PnL (306% vs 82%), Sharpe 3.57 vs 1.22
- **29/243 features** (12%) have Cohen's d > 0.5 between BTC and ETH distributions
- **40/243** (16%) have medium effect sizes (d = 0.2-0.5)
- The pooled model must learn to handle these distribution differences via tree splits, wasting capacity

**Economic hypothesis for per-symbol**: Price-level features (VWAP, OBV, A/D — identified as top-3 in iter 056) have completely different scales between BTC (~$80K) and ETH (~$3K). While LightGBM uses splits, the tree structure must bifurcate early to handle these scale differences, reducing effective depth for learning directional patterns.

**Feature decision**: Keep the same 106 global intersection features. This isolates the per-symbol model effect as the single variable changed.

### B. Symbol Universe Analysis

From baseline IS trades:

| Metric | BTCUSDT | ETHUSDT |
|--------|---------|---------|
| Trades | 257 | 317 |
| Win Rate | 40.5% | 45.7% |
| TP Rate | 27.2% | 36.3% |
| SL Rate | 51.0% | 52.4% |
| Timeout Rate | 21.8% | 11.4% |
| PnL | +81.8% | +306.1% |
| Sharpe | 1.22 | 3.57 |
| Profitable Months | 51% | 63% |

**Year-by-year divergence**:
- 2022: ETH massively outperforms (216% vs 40%) — ETH had more volatile moves in the bear market
- 2023: Comparable (45% vs 21%)
- 2024: ETH still leads (58% vs 4%) — BTC barely profitable
- Monthly PnL correlation: 0.417 — moderate, not high

**Conclusion**: BTC and ETH have fundamentally different predictability profiles. ETH has 9.2pp higher TP rate and 3.5x more PnL. A pooled model compromises ETH's signal to accommodate BTC's weaker signal.

### E. Trade Pattern Analysis

**Exit reason breakdown** shows structural differences:
- BTC timeouts: 21.8% — model is less decisive, holds positions longer without resolution
- ETH timeouts: 11.4% — model generates cleaner signals that resolve to TP/SL faster
- BTC TP rate: 27.2% — rarely catches the 8% moves
- ETH TP rate: 36.3% — 9.1pp higher, the key driver of ETH's outperformance

**Long/Short split**:
- BTC: balanced (shorts slightly better at 41.3% WR vs 39.7% for longs)
- ETH: shorts dominate (47.2% WR, PnL 196%) vs longs (44.2% WR, PnL 110%)

**Streak analysis**:
- BTC: max 6 wins, 8 losses, avg 1.7/2.4 — skewed toward losses
- ETH: max 7 wins, 8 losses, avg 2.0/2.4 — slightly better win clustering

### F. Statistical Rigor

Per-symbol bootstrap analysis (1000 resamples):

| Metric | BTCUSDT | ETHUSDT |
|--------|---------|---------|
| WR | 40.5% | 45.7% |
| 95% CI | [34.2%, 46.3%] | [40.7%, 51.4%] |
| p vs 50% | 0.999 (not sig.) | 0.942 (not sig.) |
| p vs break-even (34.2%) | 0.021 | 0.000014 |
| Mean PnL | 0.318% | 0.966% |

**Critical finding**: BTC's 95% CI lower bound (34.2%) TOUCHES break-even. ETH's lower bound (40.7%) is well above. In the pooled model, BTC's marginal signal dilutes ETH's strong signal during training.

**Per-symbol model expectation**: ETH should improve (model focuses entirely on its patterns). BTC is the risk — with ~2160 training samples and 106 features (ratio 0.049), there's adequate data for LightGBM, but the signal itself is weaker.

## Design Specification

### Architecture Change

**Before** (baseline): One LightGBM per month, trained on pooled BTC+ETH data (~4400 samples)
**After**: Two LightGBMs per month, each trained on its own symbol's data (~2200 samples each)

### Implementation Details

1. **Model storage**: Dict keyed by symbol → (model, selected_cols, confidence_threshold)
2. **Training**: For each month, iterate over unique symbols, filter training indices by symbol, train independently
3. **Prediction**: In `get_signal`, look up the symbol-specific model
4. **Feature loading**: Per-symbol feature lookup during training; per-symbol month cache

### What Stays the Same
- 106 global intersection features (NOT per-symbol feature sets)
- TP=8%, SL=4%, timeout=7 days
- 24-month training window
- 50 Optuna trials, 5 CV folds
- Seed=42
- Walk-forward monthly splits
- Yearly fail-fast checkpoints

### Risk Assessment
- **Lower sample count** (2200 vs 4400): Mitigated by ratio still being 0.049 — well within LightGBM's capabilities
- **2x training time**: Each month trains 2 models instead of 1. Acceptable given smaller datasets
- **BTC might underperform**: Its weak signal may not support a standalone model. This is valuable information regardless.

### Expected Outcome
- ETH model should match or exceed baseline ETH performance (less noise from BTC data)
- BTC model is uncertain — could improve (specialized patterns) or degrade (insufficient signal)
- Combined Sharpe likely dominated by ETH, as in baseline

## References
- Iter 056 research: feature contribution, trade patterns, statistical rigor
- Iter 057-058: slow features disproved, feature set is locally optimal
- Iter 049-054: symbol expansion disproved, BTC+ETH optimal pair
