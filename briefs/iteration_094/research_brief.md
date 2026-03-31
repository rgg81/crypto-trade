# Iteration 094 — Research Brief

**Type**: EXPLOITATION
**Date**: 2026-03-31
**Previous**: Iteration 093 (MERGE, OOS Sharpe +1.01, 185 features, honest CV baseline)

## Section 0: Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

- IS data: before 2025-03-24 (used for all research analysis below)
- OOS data: from 2025-03-24 onward (seen ONLY in Phase 7)

## Hypothesis

185 features with ~4,400 monthly training samples gives a samples-per-feature ratio of ~24 — well below the 50 minimum and in the "dangerous" zone. Many features are trivially redundant (371 pairs with |Spearman correlation| > 0.9). Pruning to 40-50 high-quality features should:

1. Improve model stability by reducing noise dimensions
2. Improve OOS generalization (fewer spurious splits)
3. Reduce training time (~60% fewer features)
4. Keep the same or better IS Sharpe (bottom features contribute negligible importance)

**Single variable changed**: feature count (185 → ~50), via correlation dedup + MDA permutation importance.

## Research Checklist Categories

### Category A: Feature Contribution Analysis

#### A1. Correlation Dedup (IS data)

Computed pairwise Spearman correlation on pooled BTC+ETH IS data (11,256 samples × 185 features).

**Finding: 371 pairs with |r| > 0.9.** Key redundancy groups:

| Redundancy | Features affected | Action |
|-----------|------------------|--------|
| ROC ≡ return ≡ log_return | 18 features → keep 6 (ROC only) | Drop stat_return_*, stat_log_return_* |
| vol_bb_pctb ≡ mr_bb_pctb ≡ mr_zscore | 12 features → keep 4 (mr_zscore only) | Drop vol_bb_pctb_*, mr_bb_pctb_* |
| EMA ≡ SMA (similar periods) | 12 features → keep 3 (EMA 5, 21, 100) | Drop all SMA, EMA 9/12/50 |
| Stochastic K ≡ D (same period) | 8 features → keep 4 (K only) | Drop stoch_d_* |
| Various within-group | ~24 features | Drop lower-period duplicate |

After greedy correlation dedup (|r| > 0.9): **111 features** survive (dropped 74).

#### A3. MDA Permutation Importance

**Methodology**: The QE will:
1. Train a reference LightGBM on full IS data (24-month window, same hyperparams as baseline, 5 CV folds, gap=44)
2. For each feature, shuffle its values in the validation fold and re-compute Sharpe
3. MDA = mean(original_Sharpe - shuffled_Sharpe) across 5 CV folds
4. Features with MDA ≤ 0 are harmful/useless → DROP
5. Rank remaining by MDA, keep top 50

**Implementation plan**:
1. Add `feature_columns` parameter to `LightGbmStrategy` to accept a pre-selected feature list
2. Run MDA analysis script on IS data to rank all 185 features
3. Select top ~50 by MDA (after correlation dedup)
4. Run walk-forward backtest with pruned features
5. Compare to baseline

#### A4. Unsafe Features (price-scale dependent)

15 features in the 111 correlation-deduped set are price-scale dependent:
- `vol_ad`, `vol_obv` (cumulative, non-stationary)
- `vol_vwap`, `vol_atr_5` (raw price level)
- `mom_mom_*` (raw momentum, not percentage)
- `mom_macd_line_*`, `mom_macd_signal_*` (raw price level)
- EMA/SMA cross features are safe (binary 0/1)

**Decision**: Let MDA decide. If unsafe features have low MDA, they'll be pruned naturally. If they have high MDA (unlikely in pooled model), keep them but flag for future replacement with normalized alternatives.

### Category E: Trade Pattern Analysis (IS)

**IS Performance**: 346 trades, 42.8% WR, Sharpe +0.73, PF 1.19

**Exit reason breakdown**:
| Exit | Count | % | WR | Avg PnL |
|------|-------|---|-----|---------|
| TP | 111 | 32.1% | 100% | +7.37% |
| SL | 183 | 52.9% | 0% | -4.10% |
| Timeout | 52 | 15.0% | 71.2% | +1.57% |

**Key insight**: TP rate 32.1% vs SL rate 52.9%. The 2:1 RR (TP=8%, SL=4%) requires break-even WR of 33.3%. At 42.8% WR the strategy is profitable, but SL hits are the dominant exit. Timeouts are surprisingly positive (+1.57% avg).

**Direction balance**: Long 177 (42.9% WR), Short 169 (42.6% WR) — well balanced.

**Per-symbol IS**: BTC 155 trades (43.2% WR), ETH 191 trades (42.4% WR) — both profitable IS. The BTC OOS problem (33.3% WR) is OOS-specific, not structural.

**Yearly IS performance**:
| Year | Trades | WR | PnL |
|------|--------|----|-----|
| 2022 | 96 | 40.6% | +25.7% |
| 2023 | 102 | 41.2% | +12.2% |
| 2024 | 127 | 47.2% | +126.7% |
| 2025 (IS) | 21 | 33.3% | -14.4% |

2024 was the best year. Early 2025 IS (Jan-Mar) was weak. Feature pruning could help by removing features that overfit to 2024 patterns.

## Proposed Configuration (iter 094)

**UNCHANGED from iter 093**:
- Symbols: BTCUSDT + ETHUSDT
- Training: 24 months, walk-forward monthly
- Labeling: TP=8%, SL=4%, timeout=7 days, dynamic ATR barriers
- CV: 5 folds, gap=44, 50 Optuna trials
- Ensemble: 5 seeds [42, 123, 456, 789, 1001]
- Cooldown: 2 candles

**CHANGED**:
- Features: 185 → ~50 (MDA-pruned, correlation-deduped)
- Feature selection method: `feature_columns` parameter in strategy

## Expected Outcome

- IS Sharpe ≥ +0.62 (within 15% of +0.73 baseline — pruning validation threshold)
- OOS Sharpe improvement due to reduced overfitting
- Samples-per-feature ratio: ~4,400/50 = 88 (healthy, up from 24)
- Training speed improvement: ~60% fewer features

## Risk

If MDA shows most features contribute similarly (flat importance curve), aggressive pruning could remove genuine signal. Mitigation: use a conservative cutoff — keep any feature with MDA > 0.
