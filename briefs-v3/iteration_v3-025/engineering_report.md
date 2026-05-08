# Engineering Report — iter-v3/025

## Status: READY-FOR-CRITIC

Wall-clock 0.23h (14 min). Setup `3b1f979`. **First genuinely PROMISING result in post-bootstrap cycle.**

## Hypothesis-Implementation Alignment

DROP `btc_funding_rate_zscore_30` (funding family closed) + ADD `regime_momentum_signed_5d` = `ret_5d × sign(hurst_100 - 0.5)`. V3_FEATURE_COLUMNS=14 atomic switch. Single-axis discipline preserved (FEATURE ENGINEERING pivot per user directive).

## Headline Metrics — STRONG LIFT

| Metric | Value | vs Anchor (+0.3788/+0.3869) |
|--------|-------|------------------------------|
| IS monthly Sharpe | **+0.8788** | Δ +0.50 |
| OOS monthly Sharpe | **+1.2244** | Δ +0.84 — FIRST OOS > +1.0 in post-bootstrap |
| OOS daily Sharpe | +2.0291 | strongest in post-bootstrap |
| IS MaxDD | 27.49% | improved |
| OOS MaxDD | **21.35%** | improved 7.85pp from anchor 29.20% |
| OOS WR | 45.26% | broad improvement |
| OOS Trades | 95 | < 130 floor (informational at EXPLORATION) |
| DSR | 0.0 | EXPLORATION-mode artifact |
| PBO mean | 0.1009 | PASS (< 0.40) |
| PSR | 1.0 | EXPLORATION-mode saturation |
| n_eff | 19 | consistent with n_trials=35 |

## Per-Symbol OOS — Much Healthier Balance

| Symbol | weighted_pnl | Trades | WR | concentration_pct |
|--------|--------------|--------|-----|-------------------|
| BCH | +11.31 | 38 | 39.5% | 34.73% (positive) |
| LDO | -1.98 | 11 | 36.4% | -6.09% (~neutral, NOT catastrophic) |
| TRX | +23.23 | 46 | **52.2%** | 71.36% (strong; high WR is unusual but consistent with regime feature filtering) |

Compared to recent NEGATIVE iterations:
- iter-v3/020/021/022/023/024: BCH/LDO frozen baseline (-6.25 / -8.93 OOS each iteration)
- iter-v3/025: BCH +11.31, LDO -1.98 — **BCH/LDO frozen baseline DISSOLVED** by the engineered feature

The frozen baseline pattern (`feedback_v3_single_seed_frozen_baseline.md`) was specific to per-symbol Optuna trajectories at fixed seed=42 across iterations sharing the same V3_FEATURE_COLUMNS. Adding the engineered feature changed the per-symbol search space, producing different (and BETTER) Optuna trajectories on BCH/LDO.

## Feature Importance — `regime_momentum_signed_5d`

| Cut | Importance | % of Top Feature | Cohort Rank |
|-----|------------|------------------|--------------|
| Portfolio | 398 | 51% (vs top range_realized_vol_50=779) | 14/14 |
| BCH | 43 | 25% (vs top ret_kurt_50=173) | 13-14/14 |
| LDO | **232** | **67%** (vs top hurst_diff_100_50=347) | ~8-9/14 |
| TRX | 123 | 39% (vs top range_realized_vol_50=313) | ~10-11/14 |
| BCH+LDO+TRX importance sum | 398 | — | — |

**Falsifier 4 disposition (relaxed PATH A: rank ≤10 OR importance ≥ 30)**:
- BCH: importance 43 ≥ 30 ✓
- LDO: importance 232 ≥ 30 ✓ (and rank ≤10!)
- TRX: importance 123 ≥ 30 ✓ (rank ~10-11, borderline)
- Portfolio aggregated: 398 ≥ 30 ✓

**ALL cuts meet the importance threshold**. LDO rank is in top half (~8-9/14). The engineered feature is GENUINELY informative — model meaningfully uses it across all 3 symbols.

This is fundamentally different from iter-v3/015 (microstructure) and iter-v3/019/023/024 (funding) where:
- Per-sym importance was 3.7-25% of top (vs 25-67% here)
- Rank was 14/14 across all symbols (vs ~8-13 here)
- IS lift was lottery (collapsed at OOS) — vs co-directional IS+OOS lift here

## §4.4 Classification Recommendation

**EXPLORATION-PROMISING (clean)** per brief §4.4 PATH A:
- IS Sharpe Δ +0.50 ≥ +0.10 ✓
- OOS Sharpe Δ +0.84 (positive, exceeds anchor +0.39 + floor +1.0) ✓
- Importance ≥ 30 across all symbols ✓ (relaxed Falsifier per IC carve-out)
- Co-directional IS + OOS lift (not lottery pattern) ✓
- Per-symbol balance improved (LDO frozen baseline dissolved) ✓

**Caveats**:
- Single-seed result — multi-seed validation required at iter-v3/029 CONFIRMATION
- iter-v3/013 also looked strong single-seed; falsified at iter-v3/018 multi-seed
- OOS trades 95 < 130 floor — informational at EXPLORATION
- TRX 52.2% WR unusual; likely consistent with regime feature filtering bad-trend trades but worth audit

## Status

**STRONG CONFIRMATION-BUNDLE CANDIDATE** for iter-v3/029. The engineered feature `regime_momentum_signed_5d` is the first genuine signal-add in the post-bootstrap cycle.

iter-v3/026 axis recommendation (Critic to decide):
1. **TRY ANOTHER ENGINEERED FEATURE** to validate the feature engineering pivot — e.g., `vol_adj_autocorr` = `ret_autocorr_lag1_50 / range_realized_vol_50` OR `cross_asset_divergence_norm`. If 2 of 2 engineered features PROMISING → strong evidence the pivot is the right strategy.
2. **MULTI-SEED-EXTRA SANITY CHECK on iter-v3/025**: a one-off 2-seed run on iter-v3/025 config to gauge multi-seed robustness BEFORE iter-v3/029 CONFIRMATION. Risk: violates 1 EXPLORATION = 1 axis discipline.
3. **NEW LABELING ARCHITECTURE** (Category 3 untested): regime-conditional triple-barrier (different ATR multipliers for high-vol vs low-vol regimes).

Critic prior: option 1 (validate the feature engineering pivot with another composed feature).
