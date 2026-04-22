# Iteration 189 — Cross-asset features: IS Sharpe collapse (rejected)

**Date**: 2026-04-22
**Type**: EXPLORATION (feature generation — first real feature-engineering iter in 25+)
**Baseline**: v0.186 — unchanged
**Decision**: NO-MERGE

## TL;DR

Added 7 BTC cross-asset features to LINK's feature set (193 → 200 features).
LINK standalone OOS Sharpe improved (+1.44 → +1.66), but **IS Sharpe
collapsed** (+1.01 → +0.68) — **below the 1.0 floor**. Classic overfitting
signature: the model caught OOS-specific patterns that don't exist in IS.

## Lesson

**Can't augment feature count on an already-strained model.** LINK
standalone at 193 features was already at samples/feature ratio 22
(well below the 50 skill-floor). Adding 7 more pushed the model past
the point where it can learn stable patterns.

Future cross-asset tests must **replace** baseline features, not add to them.

## What was built

Per-memory, feature generation had never been done in 25+ iterations.
This was the biggest gap on the exploration side.

Found that `src/crypto_trade/features/cross_asset.py` had 7 BTC-derived
features defined (`xbtc_return_{1,3,8}`, `xbtc_natr_{14,21}`, `xbtc_rsi_14`,
`xbtc_adx_14`) but the pipeline function `add_cross_asset_features()` was
**never called by anything** — pure dead code.

Materialized those features into 760 8h parquet files (100% match rate on
LINKUSDT). Created `XBTC_FEATURE_COLUMNS` and
`BASELINE_PLUS_XBTC_FEATURE_COLUMNS` constants in
`src/crypto_trade/live/models.py`.

## Numbers

| metric | v0.186 LINK | iter 189 LINK+xbtc |
|--------|------------:|-------------------:|
| IS Sharpe | **+1.011** | **+0.683** |
| IS trades | 134 | 146 |
| IS PnL | +128.37% | +86.53% |
| OOS Sharpe | +1.440 | +1.660 |
| OOS trades | 40 | 39 |
| OOS PnL | +49.19% | +54.39% |
| OOS WR | 50.0% | 56.4% |
| OOS/IS ratio | 1.43 | **2.43** |

The OOS/IS ratio of 2.43 is a red flag: the model is doing much better
in OOS than IS, the opposite of what we'd expect from genuine generalization.

## Why this is valuable exploration

Three concrete findings:

1. **xbtc features exist but nobody used them.** Dead-code discovery.
   Now materialized in all parquets for future iterations.
2. **Feature augmentation beyond 193 hurts LINK.** Skill's 50-sample
   floor isn't just theoretical — we're below it and crossing further
   breaks the model.
3. **Future tests need feature REPLACEMENT, not augmentation.** The
   skill's anti-pattern note — "Never exceed 200 features without
   explicit justification" — now has empirical backing on LINK.

## Exploration/Exploitation Tracker

Window (179-189): [X, E, X, E, X, X, X, X, X, X, **E**] → **3E/8X**
baseline, now **4E/7X** including this iteration. Still exploitation-heavy
but the new E is substantive, not a candidate rescreen.

## Next Iteration Ideas

- **Iter 190**: Feature REPLACEMENT test. Run MDI feature importance on
  v0.186's LINK model, identify the 7 least-important baseline features,
  replace them with the 7 xbtc features. Same 193-count, different mix.
  If this lifts IS Sharpe at all, the xbtc signal is real. If not,
  cross-asset features genuinely don't help LINK.
- **Iter 191**: Alternative cross-asset feature set. Compute non-BTC
  cross-asset features (ETH return 30d, crypto macro index), include
  as candidates for the replacement in iter 190.
- **Iter 192**: Try xbtc on a symbol with more headroom. Model A (BTC+ETH
  pooled) has 2× more training samples; xbtc features might not break
  it. Model A pooled-sample ratio is ~44 at 193 features; adding 7
  drops to 42 — still problematic but less so than LINK.
- **Iter 193**: Generate new in-house features. ATR-normalized body/wick
  ratios, volume z-score clusters, rolling-mean-of-rolling-std. Keep
  feature count at 193.
