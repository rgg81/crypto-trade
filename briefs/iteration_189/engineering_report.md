# Iteration 189 — Engineering Report

**Date**: 2026-04-22
**Runner**: `run_iteration_189_link_xbtc.py`
**Model**: LINK standalone with R1+R3 and `BASELINE_PLUS_XBTC_FEATURE_COLUMNS` (200 features)
**Ensemble seeds**: `[42, 123, 456, 789, 1001]`

## Code changes

1. `src/crypto_trade/live/models.py`: added
   - `XBTC_FEATURE_COLUMNS`: 7-tuple of BTC-derived feature names
   - `BASELINE_PLUS_XBTC_FEATURE_COLUMNS`: 200-feature superset
2. `analysis/iteration_189/materialize_xbtc.py`: one-shot script that ran
   `add_cross_asset_features()` — first time ever called. Materialized
   7 xbtc_* columns in **760 8h parquet files** (100% open_time match).

## Runtime

- LINK standalone: 5484s (91 min)
- 185 trades total (146 IS, 39 OOS)

## Metrics

| metric | v0.186 LINK (baseline) | **iter 189 LINK+xbtc** | Δ |
|--------|------------------------:|------------------------:|--------:|
| IS Sharpe | **+1.011** | **+0.683** | **−0.328** |
| IS trades | 134 | 146 | +12 |
| IS PnL | +128.37% | +86.53% | −41.84 pp |
| IS MaxDD | — | 30.46% | — |
| OOS Sharpe | +1.440 | +1.660 | +0.220 |
| OOS trades | 40 | 39 | −1 |
| OOS PnL | +49.19% | +54.39% | +5.20 pp |
| OOS MaxDD | — | 12.68% | — |
| OOS WR | 50.0% | 56.4% | +6.4 pp |

## Finding

**IS Sharpe falls from +1.01 to +0.68 — below the 1.0 floor.**

The IS Sharpe drop of 32% (from 1.01 to 0.68) is larger than the OOS
Sharpe gain of 15% (from 1.44 to 1.66). This is the signature of
overfitting: the model is fitting OOS-specific patterns that don't
exist in IS data. OOS/IS Sharpe ratio is 2.43 — extremely high, well
above the skill's 0.5 floor but in the direction that indicates OOS
luck rather than generalization.

### Why this happened

**Samples/feature ratio dropped from 22 to 21.** With 146 IS trades on
LINK, the ratio is 146/200 = 0.73 per-trade or 4400/200 ≈ 22 per-bar.
Below the skill's 50-minimum by a factor of ~2.3.

Adding 7 features to a model that was already at the ratio limit
pushed it past the point where the model can learn stable patterns.
The new features capture noise specific to the walk-forward split rather
than generalizable cross-asset signal.

### What this means for cross-asset features

- **Can't just add 7 features on top of 193.** Need to displace baseline
  features or reduce them.
- **The xbtc features themselves may or may not be informative.** This
  iteration doesn't prove they're bad — it proves the feature-count
  discipline matters more than the feature identity.
- **Future tests should replace, not augment.** Iter 190+ should test:
  replace 7 least-important baseline features (MDI on v0.186) with the
  7 xbtc features. Same feature count, same ratio, different content.

## Test suite

No code changes under test (the constant addition is trivial). Existing
386 tests still pass.

## Commit plan

- `feat(iter-189): BASELINE_PLUS_XBTC_FEATURE_COLUMNS + LINK xbtc runner` (done)
- `docs(iter-189): research brief` (done)
- `docs(iter-189): engineering report` (this doc)
- `docs(iter-189): diary entry` (next)
