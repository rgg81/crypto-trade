# LightGBM Master Advisor — iter-v1/058 — Phase 4.5 (Pre-Design)

## Context Read

- Track: v1; cycle-7 EXP-2/N (pivot after /057 MULTI-SEED-WEAK-BASIN-LOTTERY on cross-asset
  return ratio family; max−min spread 0.67 across 3 outer seeds exceeded the 0.50 BASIN-LOTTERY
  threshold; ltc_vs_btc_ret_ratio_30 rank 38-46/48 = near-INERT across all seeds)
- Cohort: **BTCUSDT only** (BTC specialist head; the largest IS-headroom symbol in the bundle)
- Baseline BTC IS Sharpe: **−0.85** / OOS Sharpe: **+3.41** (113 IS trades / ~30 OOS trades)
  — IS-negative with OOS-positive: structural candidate for specialist conditioning.
  BTC was specialist target at /054 (funding-spread axis) but regressed at multi-seed in /056
  CONFIRMATION. The /054 feature (`btc_funding_spread_30_90`) was classified LEARNED-NEGATIVE-
  AT-CONFIRMATION per /056 Phase 7.4 Item 2. NEW axis required.
- NEW feature: `btc_oi_delta_5_z30` = (open_interest[t] − open_interest[t−5]) /
  open_interest[t−5], z-scored over 30 bars (rolling mean/std). Algebraic mirror of existing
  `oi_delta_30_z90` at 6× higher frequency: 5-bar delta = 40h horizon (vs 30-bar = 240h);
  30-bar z-score window = 10 calendar days (vs 90-bar = 30 days). Targets rapid BTC institutional
  positioning shifts not captured by the slower 30-bar accumulation/distribution window.
- Multi-seed BUILT IN from start: `--seeds 3` with `_OUTER_SEED_OFFSETS = (0, 3, 6)` → 9 disjoint
  inner seeds {42,45,48 / 123,126,129 / 456,459,462} — same pattern as /057 and /051.
- Verdict basis: **MULTI-SEED MEAN (n=3 outer seeds).** Single-seed=42 result is informational
  only. No single-seed verdict basis per /056+/057 basin-lottery lesson.
- Optuna: n_trials=20, EXPLORATION budget.

---

## Phase 4.5 — LM Master Pre-Design Advisory

### ML Perspective — Short-Window OI Delta and BTC Positioning Dynamics

`oi_delta_30_z90` captures the slow accumulation or distribution of BTC open interest: a 30-bar
(240h = 10-day) change normalized against 90-bar (30-day) mean/std. This timeframe aligns with
macro positioning cycles — institutions building or unwinding directional exposure across multiple
weeks. The baseline already includes this slow-cadence signal.

`btc_oi_delta_5_z30` targets a complementary, faster mechanism: the 5-bar (40h) OI change
normalized against 30-bar (10-day) context. At BTC's liquidity depth, rapid OI spikes in a 40h
window are dominated by two phenomena: (1) leveraged-futures cascades triggering forced
liquidations that subsequently reverse, and (2) institutional bracket orders placed around key
technical levels. The 30-bar z-score provides regime-local normalization — a 5-bar OI spike
during a high-absolute-OI regime (risk-on crowded) carries different directional implication
than the same spike during a low-absolute-OI regime (de-risked).

The LM Master's expectation is that this feature occupies a **different frequency bin** than
`oi_delta_30_z90`: their correlation should be moderate (estimate Pearson IC ≈ 0.30–0.55), making
them genuinely complementary rather than redundant. The existing 30-bar version functions as a
slow trend filter; the 5-bar version functions as a short-term positioning shock detector. Trees
at depth 3–5 can condition on both simultaneously without aliasing.

BTC's IS-negative baseline (−0.85) with OOS-positive (+3.41) suggests the pooled-head Model D
is applying features calibrated to aggregate-symbol dynamics that happen to be anti-predictive
for BTC specifically during IS. A BTC-specialist with an additional high-frequency positioning
feature may allow Optuna to discover a BTC-specific decision boundary that the pooled model
cannot find due to multi-symbol label noise.

---

## Top 3 Recommendations

### Rec 1 — Document IC overlap with oi_delta_30_z90; do NOT block on IC alone

`btc_oi_delta_5_z30` and `oi_delta_30_z90` are algebraic sisters: both derived from the same
open_interest series, same ticker, different window parameters. Expect moderate Pearson IC in the
range |IC| ≈ 0.30–0.55. Per the EDA-informational rule (established v3 analog; applies here by
v1-parity): IC overlap at |IC| < 0.80 is not a blocking condition for a sister OI feature. The
brief EDA MUST compute and report this IC number, but it informs the analyst (and Critic) rather
than blocking the iteration.

If measured IC exceeds |IC| = 0.70 (sister-correlation threshold), document this explicitly in
Section 2 and note that LightGBM's feature selection may preferentially route split budget to the
already-known `oi_delta_30_z90` and leave `btc_oi_delta_5_z30` at low importance. This would
manifest as a NEGATIVE-INERT verdict and should be pre-registered as a falsifier branch.

### Rec 2 — Multi-seed verdict mandatory; per-seed spread > 0.5 = BASIN-LOTTERY downgrade

/057's basin-lottery finding is the direct precedent: a 0.67 max−min spread across 3 outer seeds
on a cross-asset feature family produced a headline mean that appeared marginal-positive but masked
strong seed-to-seed divergence. Apply the same diagnostic discipline here:

- Report IS Sharpe for each of the 3 outer seeds individually before computing the mean.
- If max_seed IS Sharpe − min_seed IS Sharpe > 0.50 → verdict is BASIN-LOTTERY regardless of
  mean direction. The OI-delta axis would then be classified as not reliably learnable at
  EXPLORATION budget and downgraded accordingly.
- Expect BTC at 113 IS trades (vs LTC 124, ETH 145) to produce the highest per-seed variance of
  any specialist target. The 0.50 spread threshold is not relaxed for smaller cohorts — the
  threshold exists precisely because smaller cohorts are more lottery-exposed.
- Document max−min spread in the engineering report alongside the mean. If spread < 0.30 (tight),
  note this as favorable evidence for axis reliability.

### Rec 3 — BTC has 113 IS trades — trade-rate floor PASS expected but verify per seed

113 IS trades across the full 24-month IS window yields approximately 22–23 trades per walk-forward
fold at 5 folds. At n_trials=20 EXPLORATION budget, TPE warmup consumes ~15 random trials; only
~5 exploitation trials fire per cell. This is viable but at the lower boundary of Optuna convergence
reliability. For the BTC-specialist:

- Verify per-seed IS trade count does not fall below 70 (vs 113 baseline). If a specialist
  gating condition (e.g., a high OI delta z-score threshold) filters out too many IS candles,
  the trade count may collapse and the Sharpe estimate becomes unreliable (borne out at /050
  ETH-specialist where aggressive filtering dropped IS trades to 52).
- OOS trade floor: BTC baseline OOS ~30 trades. Per-seed OOS must be ≥ 15 to constitute a valid
  Sharpe estimate. Pre-register this floor in brief Section 8.
- The EXPLORATION verdict is IS-only per methodology. OOS trade rate is informational, not a
  blocker, but should be flagged if it falls below the minimum.

---

## Prior Distribution (8 verdict bands; multi-seed-aware)

| Verdict Band | Probability | Rationale |
|---|---|---|
| MULTI-SEED-SPECIALIST (mean IS Δ ≥ +0.50; max−min ≤ 0.50) | **10%** | High bar; /054 + /057 both failed as specialist; OI-delta is a new family but BTC IS −0.85 leaves room for lift |
| MULTI-SEED-PARTIAL (mean IS Δ ∈ [+0.20, +0.50)) | **20%** | Modal positive; short-window OI delta learns mid-table importance; BTC IS moves toward zero |
| MULTI-SEED-WEAK (mean IS Δ ∈ [+0.05, +0.20)) | **25%** | Feature learns but IS Δ marginal; 5-bar OI at 40h is noisy; z-score stable but split budget thin |
| NEGATIVE-INERT (mean IS Δ ∈ (−0.05, +0.05); any-seed importance rank > 40/48) | **25%** | Sister-IC with oi_delta_30_z90 causes LightGBM to route splits to the established 30-bar version; 5-bar version starved |
| NEGATIVE-CLEAN (mean IS Δ ≤ −0.05) | **15%** | Short-window OI delta anti-informative for BTC IS; high-frequency noise dominates at 40h horizon |
| BASIN-LOTTERY (mean IS Δ in any direction; max−min > 0.50) | **5%** | /057 pattern repeats; 113-trade cohort amplifies seed-to-seed variance above threshold |

**LM Master modal: NEGATIVE-INERT (25%) or MULTI-SEED-WEAK (25%).** The OI-delta family is
mechanically sound and represents a genuine pivot from the cross-asset return ratio family that
failed at /057. However, the sister-IC risk with `oi_delta_30_z90` at |IC| ≈ 0.30–0.55 means
LightGBM's allocation may already be partially explained by the slower version. The two most
likely outcomes are (a) the short-window version adds meaningful frequency-bin diversity and learns
mid-table importance (MULTI-SEED-PARTIAL / WEAK), or (b) the sister-IC routes splits to the
established feature and the new one remains near-INERT.

---

## Risk Flags

### RF-1: Short-window OI delta is noisier than 30-bar version

The 5-bar (40h) window is more susceptible to microstructure events — exchange maintenance windows,
partial liquidation cascades, weekend low-liquidity periods. A single large-position open/close
in a 40h window can dominate the delta calculation in a way that a 30-bar average absorbs. The
30-bar z-score normalization provides regime-local context but does not filter single-event
spikes. The EDA should confirm that `btc_oi_delta_5_z30` does not have a fat tail distribution
beyond ±4 standard deviations that could indicate event contamination. If the 99th percentile
z-score exceeds ±4, apply a ±4 clip in the feature computation and note this in Section 2.

### RF-2: Per-seed variance higher than ETH or LTC specialists

BTC has 113 IS trades, the smallest specialist cohort of the three targets tested so far
(LTC 124, ETH 145). Smaller cohort means each fold has fewer trades; Optuna's exploitation phase
makes decisions on noisier fold-level Sharpe estimates. Historical pattern: /054 BTC single-seed
showed IS Δ +0.30 that evaporated to −0.36 at multi-seed CONFIRMATION. The per-seed max−min
spread metric (Rec 2) is the primary protection against repeating this failure.

### RF-3: OI data quality risk — open_interest availability back to IS start

Verify that BTC open_interest data is available without gaps from the IS window start (24 months
before OOS cutoff 2025-03-24, i.e., from 2023-03-24). If OI data has early-window gaps, the
z-score computation will produce NaNs that propagate to the feature column and reduce effective
IS trade count. Document availability coverage in brief Section 2 EDA.

---

## Closing

This is cycle-7 EXP-2. /057 established the BASIN-LOTTERY classification for the cross-asset
return ratio family (ltc_vs_btc_ret_ratio_30 max−min spread 0.67 > 0.50 threshold across 3 seeds).
The pivot to OI-delta family is directionally correct: OI-derived features are in the same
asset-specific information domain as `oi_delta_30_z90` (already in V1_FEATURE_COLUMNS), so the
addition is an axis-adjacent exploration rather than a fresh axis-rotation. This keeps the
Section 0.6 architecture family stable (feature-family axis within the existing OI primitive
cluster) while testing a frequency-bin dimension not yet explored.

BTC is the correct specialist target: IS −0.85 offers the largest IS-headroom of any bundle
symbol. If the short-window OI delta resolves some of the BTC IS anti-prediction, even a modest
IS Δ toward zero would validate the frequency-bin hypothesis and justify a CONFIRMATION bundle
evaluation alongside the LTC and ETH specialists (whichever survive cycle-7).

The single most important diagnostic: **multi-seed mean BTC IS Sharpe Δ vs baseline −0.85 AND
`btc_oi_delta_5_z30` importance rank across all 3 outer seeds.** Both must be affirmative — mean
IS Δ ≥ +0.05 (moves IS above −0.80) AND rank ≤ 35/48 across ≥2 seeds — for any PROMISING verdict.
A positive IS Δ with importance rank > 40/48 is INERT by the /056 precedent; an importance rank
≤ 10 with flat IS Δ is a NULL finding. Concordance between the two metrics is required.

— Phase 4.5 advisor authored 2026-06-02
