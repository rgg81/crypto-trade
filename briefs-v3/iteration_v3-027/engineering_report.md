# Engineering Report — iter-v3/027

## Status: READY-FOR-CRITIC

Wall-clock 0.23h (14 min). Setup `b9b6f8d`. Same SUSPICIOUS pattern as iter-v3/026 but more extreme.

## Hypothesis-Implementation Alignment

DROP `vol_adj_autocorr` + ADD `cross_asset_divergence_norm`. KEEP `regime_momentum_signed_5d`. V3_FEATURE_COLUMNS net unchanged at 15. ITERATION_LABEL=v3-027.

## Headline Metrics

| Metric | iter-v3/025 ref | iter-v3/026 | **iter-v3/027** |
|--------|-----------------|-------------|----------------|
| IS Sharpe | +0.88 | +0.05 | **-0.28** (FIRST IS-negative in post-bootstrap) |
| OOS Sharpe | +1.22 | +1.45 | **+1.68** (highest in v3 catalog) |
| IS MaxDD | 27.5% | 51.4% | **62.9%** (worst ever) |
| OOS Trades | — | 79 | 105 (still < 130 floor) |
| IS daily Sharpe | 1.86 | 0.12 | -0.81 |
| OOS daily Sharpe | 2.03 | 3.36 | 1.81 |
| TRX OOS concentration | 71% | 16% | **91.6%** (extreme) |
| Portfolio PSR | 1.0 | 1.0 | 1.0 (saturated) |

## Per-Symbol OOS

| Symbol | weighted_pnl | Trades | WR |
|--------|--------------|--------|-----|
| BCH | -3.31 | 42 | 28.6% |
| LDO | +6.13 | 15 | 40.0% |
| TRX | **+30.64** | 48 | **50.0%** |

TRX carries 91.57% of portfolio. Highest single-symbol concentration in any post-bootstrap iteration.

## Feature Importance

Per-symbol cross_asset_divergence_norm + regime_momentum_signed_5d:
- BCH: cross_asset 10, regime 0 — both essentially IGNORED
- LDO: cross_asset 360, regime 309 — both MEANINGFULLY USED
- TRX: cross_asset 36, regime 38 — both modest
- Portfolio aggregate: cross_asset 406 (= 64% of top), regime 347 (= 55% of top)

Feature is USED, NOT INERT. Falsifier 4 PASSES.

## Structural Pattern Recognition

| Iteration | Engineered features | IS Sharpe | OOS Sharpe | IS MaxDD |
|-----------|---------------------|-----------|------------|----------|
| 025 | regime_momentum alone | +0.88 | +1.22 | 27.5% |
| 026 | + vol_adj_autocorr | +0.05 | +1.45 | 51.4% |
| 027 | + cross_asset_divergence | **-0.28** | +1.68 | **62.9%** |

**Monotonic pattern**: as engineered features stack on top of regime_momentum, IS DEGRADES while OOS INCREASES. This is structural single-seed lottery on overcomplicated loss surfaces — not a true signal-add pattern.

The increasing IS MaxDD (27% → 51% → 63%) is the diagnostic: model fits to IS noise more aggressively as feature space expands, producing IS PnL drawdowns that absorb most of the in-sample edge. The OOS bonanza is increasingly suspect — likely an OOS regime effect (TRX-specific 2025+ favorable conditions) that the model captures by accident.

## §4.4 Classification

PATH C fires unambiguously on IS axis (IS Δ -0.66 vs anchor +0.38; -1.16 vs iter-v3/025 reference +0.88). Both deltas exceed -0.10 threshold by huge margins.

OOS lift +1.68 is single-seed-untrustable. TRX 91.6% concentration fails gate 7 of BASELINE_V3.md. iter-v3/013's single-seed +2.70 OOS was falsified at multi-seed; iter-v3/027's +1.68 follows the same pattern with higher confidence.

## Verdict: EXPLORATION-NEGATIVE-SUSPICIOUS-OOS

Same as iter-v3/026 with even stronger anomaly signature.

## Critical Conclusion

Only **iter-v3/025 (regime_momentum_signed_5d ALONE)** survives as PROMISING in the post-bootstrap cycle. The CONFIRMATION bundle for iter-v3/029 is:
- iter-v3/013 baseline (BCH+LDO+TRX, 13 features, ATR labeling, 7 risk gates) +
- `regime_momentum_signed_5d` engineered feature (V3_FEATURE_COLUMNS=14)

No other engineered feature stacked successfully. NEW universe / NEW model arch / NEW labeling axes also failed. The bundle for iter-v3/029 is single-feature.

## Recommendations

iter-v3/028 (FINAL EXPLORATION before iter-v3/029 CONFIRMATION):

**Critic strong prior**: REPLICATE iter-v3/025 at multi-seed (--seeds 2) as a mini-validation BEFORE iter-v3/029 CONFIRMATION-bundle. This is essentially a 1.5-day pre-CONFIRMATION sanity check at lower budget. If iter-v3/025's IS +0.88 / OOS +1.22 holds at --seeds 2 + n_trials=35, we go into iter-v3/029 with confidence. If it falsifies (similar to iter-v3/013 → iter-v3/018 collapse), iter-v3/029 is dead-on-arrival and we know before spending CONFIRMATION budget.

Alternative axis: NEW labeling architecture (Category 3 untested in post-bootstrap). Different category from feature engineering. Could potentially add a second edge ingredient to the bundle.

Critic decides. Status: READY-FOR-CRITIC.
