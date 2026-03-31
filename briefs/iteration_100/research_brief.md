# Research Brief — Iteration 100

**Type**: EXPLORATION
**Hypothesis**: Fractional differentiation features (AFML Ch. 5) add price-level memory while maintaining stationarity, providing information that raw returns and price-level features cannot.

## Section 0: Data Split (Verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Section 1: Problem Statement

Current features face the stationarity-memory tradeoff:
- **Returns (d=1.0)**: Stationary but memoryless — yesterday's return says nothing about price level
- **Raw SMA/EMA (d=0.0)**: Maximum memory but non-stationary — splits learned at BTC $40K don't apply at $70K

Fractional differentiation finds the minimum d (typically 0.3-0.5 for crypto) that achieves stationarity while preserving price-level memory. At d=0.4, a fracdiff series retains information about the price trajectory over the last ~33 days while being stationary.

## Section 2: Research Analysis

### G. Stationarity & Memory Analysis (Category G)

The current feature set includes returns (stationary, d=1.0) and z-scores (stationary, normalized). These are all memoryless — they don't retain information about WHERE the price is relative to its recent trajectory.

Fracdiff features at d=0.4 preserve ~60% correlation with the original log-price series while being stationary (ADF test p < 0.05). This means the model can learn patterns like "price has been trending up for 3 weeks" — information currently only available through raw SMA/EMA features which are non-stationary.

### A. Feature Contribution Analysis (Category A)

**New features (2):**
- `stat_fracdiff_close_04`: fracdiff(log(close), d=0.4, window=100)
- `stat_fracdiff_volume_04`: fracdiff(log(volume), d=0.4, window=100)

These are scale-invariant (log transform + differentiation) and stationary. Window=100 candles = 33 days on 8h candles — captures monthly price memory.

**Net feature change**: +2 features (193 existing → 195 total after regeneration). The 2 new fracdiff features are genuinely novel — they capture price memory that no other feature in the set provides.

### E. Trade Pattern Analysis (Category E)

Baseline IS patterns (from iter 099 analysis):
- BTC IS: 43.2% WR, profitable in 2023-2024, break-even in 2022
- ETH IS: 42.4% WR, profitable in 2022 and 2024, negative in 2023
- ADX filter analysis: does NOT generalize IS→OOS
- Direction persistence analysis: does NOT generalize IS→OOS
- The model is at a genuine local optimum — post-hoc trade filters don't help

Fracdiff is different: it provides NEW information to the model rather than filtering existing predictions.

### F. Statistical Rigor (Category F)

With 100+ iterations, any observed improvement could be due to chance. The fracdiff change adds only 2 features with clear theoretical justification (AFML Ch. 5 — the stationarity-memory tradeoff). This is not a shotgun approach adding dozens of arbitrary features.

## Section 3: Proposed Change

**Single change**: Add 2 fractional differentiation features to the feature set.

Implementation:
1. New module `src/crypto_trade/features/fracdiff.py` with fixed-window fracdiff algorithm
2. Features: `stat_fracdiff_close_04` (d=0.4, window=100), `stat_fracdiff_volume_04` (d=0.4, window=100)
3. Registered in features `__init__.py`
4. Parquet files regenerated for BTC and ETH (195 features total)

**What stays the same**: All model params identical to baseline iter 093:
- 5-seed ensemble, 24mo training, TP=8%/SL=4%, timeout=7d
- Dynamic ATR barriers, cooldown=2, 50 Optuna trials, 5 CV folds
- Pooled model (per-symbol proved inferior in iter 099)

## Section 4: Risk Assessment

**Downside**: Adding features has failed in every prior attempt (iters 070, 072, 083, 086). The 185-feature model seems resistant to modification.

**Why this might be different**: Fracdiff features provide genuinely novel information (price memory) rather than redundant indicators. They're 2 features, not 85. They address a theoretical gap, not an empirical hunch.

**Expected outcome**: Likely no improvement (given history), but important to validate whether the stationarity-memory tradeoff matters for this model. If fracdiff doesn't help, we can conclude the model's feature set is saturated and future improvements must come from architecture changes.
