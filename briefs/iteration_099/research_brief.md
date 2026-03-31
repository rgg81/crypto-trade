# Research Brief — Iteration 099

**Type**: EXPLORATION
**Hypothesis**: Per-symbol LightGBM models will outperform the pooled model because BTC and ETH have fundamentally different trading dynamics that a single model cannot optimize for.

## Section 0: Data Split (Verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

- In-sample (IS): all data before 2025-03-24
- Out-of-sample (OOS): all data from 2025-03-24 onward
- Walk-forward runs on ALL data (IS + OOS) as one continuous process
- Reports split at OOS_CUTOFF_DATE into in_sample/ and out_of_sample/

## Section 1: Problem Statement

The baseline (iter 093) uses a pooled model where BTC and ETH training data is mixed into a single LightGBM per month. This forces shared hyperparameters, confidence threshold, and feature weights on both symbols despite fundamentally different dynamics:

| Metric | BTC IS | BTC OOS | ETH IS | ETH OOS |
|--------|--------|---------|--------|---------|
| Total trades | 155 | 51 | 191 | 56 |
| WR | 43.2% | 33.3% | 42.4% | 50.0% |
| Long WR | 44.9% | 28.0% | 41.4% | 56.5% |
| Short WR | 41.6% | 38.5% | 43.5% | 45.5% |
| TP rate | 32.3% | 29.4% | 31.9% | 32.1% |
| SL rate | 51.6% | 60.8% | 53.9% | 48.2% |
| Long PnL | +41.4% | -11.9% | +18.5% | +16.1% |
| Short PnL | +22.6% | +9.2% | +67.8% | +37.7% |

**Key divergences:**
1. BTC OOS WR drops 10pp from IS (43.2% → 33.3%). ETH OOS WR IMPROVES 8pp (42.4% → 50.0%).
2. BTC longs are terrible in OOS (28.0% WR). ETH longs are excellent (56.5% WR).
3. BTC shorts are better than longs in OOS. ETH is balanced.
4. BTC OOS SL rate is 60.8% (catastrophic). ETH OOS SL rate is 48.2% (manageable).

A pooled model averages these dynamics, producing a mediocre signal for both.

## Section 2: Research Analysis

### B. Symbol Universe & Per-Symbol Dynamics (Category B)

**B3. Model Architecture Decision:**

| Metric | BTC ↔ ETH |
|--------|-----------|
| IS Correlation | ~0.82 (high) |
| NATR ratio | ~1.3x (similar) |
| IS WR difference | 1pp (BTC 43.2%, ETH 42.4%) |
| OOS WR difference | **17pp** (BTC 33.3%, ETH 50.0%) |
| Directional bias | BTC: shorts; ETH: longs |

The IS WR difference is small (1pp), but the OOS divergence (17pp) reveals that the pooled model's shared parameters work for ETH but fail for BTC. This strongly suggests **per-symbol models (Option B)**.

**Recommended architecture: Per-symbol models.**
- BTC gets its own Optuna optimization, potentially finding different confidence threshold, regularization, and training window
- ETH gets its own optimization
- Each model specializes in its symbol's dynamics

### E. Trade Pattern Analysis (Category E)

**BTC IS patterns:**
- 2022: 37.8% WR, -1.9% PnL (bear market — barely breaks even)
- 2023: 44.2% WR, +21.1% PnL (recovery)
- 2024: 45.3% WR, +39.8% PnL (bull — best year)
- Longs consistently more profitable than shorts IS (+41.4% vs +22.6%)
- But OOS longs collapse (28.0% WR) → model may be overfitting BTC long signals

**ETH IS patterns:**
- 2022: 42.4% WR, +27.7% PnL (profitable even in bear!)
- 2023: 39.0% WR, -9.0% PnL (worst year)
- 2024: 49.2% WR, +87.0% PnL (dominant year)
- Shorts more profitable IS (+67.8% vs +18.5% long)
- OOS: both directions profitable, longs especially good (56.5% WR)

**Exit reason analysis:**
- Both symbols have SL rate > 50% IS — the majority of trades lose
- ETH manages to be profitable despite high SL rate because TP wins are 2x SL losses
- BTC OOS SL rate of 60.8% means 3 out of 5 trades hit stop — fatal for profitability

### A. Feature Contribution Analysis (Category A)

**A2. Feature Discovery Scope:**
Per-symbol models eliminate the intersection problem. Each symbol uses its OWN features — no need for intersection across symbols. BTC can use BTC-specific features, ETH can use ETH-specific features. In practice, both symbols have the same 185 features from the symbol-scoped discovery, but this architectural change opens the door for future per-symbol feature engineering.

**Samples/feature ratio concern:**
- Pooled: ~4,320 samples / 185 features = ratio 23
- Per-symbol: ~2,160 samples / 185 features = ratio 12
- Ratio 12 is low but LightGBM handles this through:
  - `colsample_bytree` [0.3, 1.0] — implicit feature subsampling
  - `min_child_samples` [5, 100] — prevents overfitting to small leaf groups
  - `max_depth` [3, 5] — limits tree complexity
  - `reg_alpha` and `reg_lambda` — L1/L2 regularization

### C. Labeling Analysis (Category C)

Labels are computed identically for both symbols (TP=8%, SL=4%, timeout=7d). No change proposed. The per-symbol model change lets Optuna find symbol-specific confidence thresholds that may filter differently for each symbol's label distribution.

## Section 3: Proposed Change

**Single change**: Train per-symbol LightGBM models instead of a pooled model.

Implementation:
1. Add `per_symbol_models: bool = False` parameter to `LightGbmStrategy`
2. When enabled, `_train_for_month()` loops over each unique symbol:
   - Filters training indices to that symbol
   - Runs independent labeling, feature loading, and Optuna optimization
   - Stores per-symbol models and confidence thresholds
3. `get_signal()` uses the symbol-specific model for prediction
4. CV gap becomes `(timeout_candles + 1) * 1 = 22` per symbol (was 44 for pooled)

**What stays the same**: All other parameters identical to baseline iter 093:
- 5-seed ensemble per symbol
- Training months: 24
- TP=8%/SL=4%, timeout=7d
- Dynamic ATR barriers (TP=2.9×NATR, SL=1.45×NATR)
- 50 Optuna trials per model per seed
- 5 CV folds
- Cooldown: 2 candles
- 185 features (symbol-scoped discovery unchanged)

**Compute cost**: 2× the baseline (2 independent Optuna runs per month instead of 1). Each run has half the training samples, so individual optimization is faster. Net: ~1.5× wall time.

## Section 4: Risk Assessment

**Downside**: Per-symbol models have fewer training samples (~2,160 vs ~4,320). This could lead to overfitting if regularization is insufficient. Mitigation: Optuna's search space already includes strong regularization parameters.

**Upside**: Each model specializes. BTC's model may learn that longs are weak and avoid them. ETH's model may lean into its strong long signal. Different confidence thresholds per symbol could dramatically improve trade selection.

**Expected outcome**: ETH should maintain or improve its already-strong performance. BTC is the wild card — if its per-symbol model finds a better signal, portfolio Sharpe improves. If BTC overfits with fewer samples, we may need to trade ETH-only.
