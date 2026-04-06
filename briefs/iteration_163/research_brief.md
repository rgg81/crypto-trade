# Iteration 163 Research Brief

**Type**: EXPLORATION (retrain with novel entropy + CUSUM features)
**Model Track**: v0.152 baseline + 11 new features from iter 162
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

Iter 162 implemented 11 new entropy/CUSUM features (AFML Ch. 17-18) and
merged the code to main. The parquets have been regenerated with these
features. This iteration retrains the full A+C+D portfolio with the
expanded feature set to evaluate whether genuinely novel information
(market predictability + structural breaks) improves the baseline.

This is the first **primary model retrain** since iter 138. Every
iteration from 139-162 was either post-processing on iter 138's trades
or infrastructure additions. Iter 163 breaks the post-processing ceiling.

## Configuration

**Identical to iter 138** except feature set (auto-discovered from parquet):
- Model A: BTC+ETH, ATR labeling 2.9x/1.45x
- Model C: LINK, ATR labeling 3.5x/1.75x
- Model D: BNB, ATR labeling 3.5x/1.75x
- 24mo training window, 5 CV folds, 50 Optuna trials
- 5-seed ensemble per model
- Cooldown 2 candles, timeout 7 days

**New features** (auto-discovered from regenerated parquets):
- ent_shannon_10, ent_shannon_20, ent_shannon_50
- ent_volume_20
- cusum_since_1s, cusum_since_2s, cusum_since_3s
- cusum_norm_1s, cusum_norm_2s, cusum_norm_3s
- cusum_break_5

Total features: ~117 (106 existing + 11 new). Samples-per-feature ratio:
~4400/117 ≈ 38 (above the 22 danger zone from iter 078 but below the
ideal 50). LightGBM's `colsample_bytree` handles implicit selection.

## VT Config

Engine-integrated VT (iter 150-152):
- target_vol=0.3, lookback=45, min_scale=0.33, max_scale=2.0

## DSR Reporting

Reports include DSR at n_trials=163 (accumulated iteration count) via
the iter 160-161 infrastructure.

## Checklist Categories

- **A (Feature Contribution)**: A4 — 11 new features with AFML economic
  rationale. Auto-discovered, no pruning (mature model, colsample handles
  selection per iter 094 lesson).
- **D (Feature Frequency)**: Entropy at 3 timescales (10/20/50); CUSUM
  at 3 σ levels (1/2/3).

## Success Criteria

MERGE requires (from iter 159 DSR framework):
- OOS Sharpe > v0.152 baseline (+2.83) by ΔSharpe ≥ +0.10 (magnitude floor)
- OOS MaxDD ≤ 38.7% (1.2× baseline pre-VT)
- OOS trades ≥ 50
- OOS PF > 1.0
- IS/OOS Sharpe ratio > 0.5

## Expected Runtime

~5 hours for full 3-model walk-forward with 5-seed ensembles.

## Hypothesis

Entropy and CUSUM features provide genuinely new information:
1. **Entropy** tells the model when the market is predictable vs random —
   should improve trade timing (avoid high-entropy periods).
2. **CUSUM** tells the model whether a regime change just occurred —
   should improve regime-dependent positioning.

If the model learns to USE these features (non-zero importance), IS Sharpe
should improve or stay flat while OOS Sharpe rises (the features capture
real structure, not noise). If the model IGNORES them (zero importance
due to colsample or splits), the result will be identical to iter 138.
