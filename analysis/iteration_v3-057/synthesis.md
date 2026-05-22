# iter-v3/057 EDA Synthesis — Cycle 4 #7 of 10

**Iteration**: iter-v3/057 EXPLORATION (Cycle 4 #7 of 10)
**Date**: 2026-05-12
**EDA SHA**: (this commit)
**Anchor**: iter-v3/056 (= iter-v3/028 baseline, bit-identical strategy)

## Mandate

Per Critic /054 FINAL Rec #1 + Critic /055 FINAL Rec #3 + Critic /056 FINAL Rec #1:
"/057 axis: A4 base-stack reordering OR NEW feature family — QR EDA-driven choice".

The 6 consecutive PATH E (CPCV-INVARIANT NULL) firings (iter-v3/051..056) tell us
that the CPCV path distribution is STRUCTURALLY PINNED by the (base 14-feature stack,
BCH+LDO+TRX, 8h cadence, ENSEMBLE_SIZE=5, n_trials=35) tuple, INVARIANT to all axes
tested in cycle 4. To shift CPCV at single-seed EXPLORATION, a STRUCTURAL change to
one of these axes is required.

A4 base-stack reordering — DROP one feature from the 14 + ADD an orthogonal NEW
feature from an UNTESTED family — is the strongest single-axis option in cycle 4.
It changes both the stack composition AND adds a structurally distinct family signal
at the same time. It is NOT a 15th-slot extension (which Critic /054 closed at
"Category 2 composed features" scope).

## Section A — A4 drop ranking (per-symbol importance)

The /056 single-seed (= /028 single-seed=42) per-symbol feature importance shows
which V3_BASE_14 features are robust drop candidates (bottom-3 importance on at
least 2 of 3 symbols, NOT load-bearing):

Top candidates (sorted by drop suitability score):

| Rank | Feature | BCH rank | LDO rank | TRX rank | bottom3_count | Portfolio importance | Score |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | **ret_skew_50** | 12/14 | 8/14 | 12/14 | **2** | 137.6 | **286.2** |
| 2 | btc_ret_14d | 13/14 | 6/14 | 14/14 | 2 | 142.3 | 285.8 |
| 3 | sym_vs_btc_ret_7d | 9/14 | 11/14 | 13/14 | 1 | 132.7 | 186.7 |
| 4 | hurst_100 | 11/14 | 14/14 | 3/14 | 1 | 140.3 | 186.0 |
| 5 | ret_autocorr_lag1_50 | 7/14 | 12/14 | 6/14 | 1 | 153.0 | 184.7 |

**regime_momentum_signed_5d** is EXCLUDED from drop candidates per iter-v3/041
lesson + `feedback_v3_engineered_features_proven.md` MUST-be-present mandate
(per-symbol load-bearing for BCH despite rank 14 portfolio aggregate).

**Chosen drop target: ret_skew_50**
- Bottom-3 on BCH(12) + TRX(12); middle-low on LDO(8). Drop-risk = LDO regression possible.
- Lower load-bearing risk than btc_ret_14d (LDO rank 6 = MID), which has higher per-symbol contribution to LDO model.
- Per /041 Critic lesson: "iter-v3/041 dropped ALL 3 bottom features simultaneously; the failure was specifically attributed to regime_momentum_signed_5d (BCH load-bearing), NOT ret_skew_50 or sym_vs_btc_ret_7d."
- Dropping a SINGLE non-load-bearing feature (ret_skew_50) is per-feature SWAP, not
  multi-feature pruning. Different mechanism than /041.

## Section B — NEW feature family candidates

Candidates surveyed: 28 features computed in v3 parquets and NOT in V3_BASE_14 and
NOT in CLOSED_FEATURES (the 13 already-CLOSED features per catalog).

Gate filters applied:
- All 3 symbols ADF p < 0.05 (stationary)
- All 3 symbols n_valid > 1000 (data efficiency)
- max |IC| with V3_BASE_14 < 0.50 (strict Category-1 gate; no carve-out)
- At least 1 symbol Spearman p < 0.05 (univariate predictability)
- |skew| < 10 AND |kurt| < 50 (numerical stability)

**8 candidates pass all filters:**

| Rank | Feature | Family | mean |Spearman| | max |IC| | max IC partner |
|---:|---|---|---:|---:|---|
| 1 | **parkinson_gk_ratio_20** | price_efficient_vol | **0.0514** | 0.245 | ret_skew_200 (LDO) |
| 2 | obv_slope_50 | volume_micro | 0.0476 | 0.438 | ema_spread_atr_20 (BCH) |
| 3 | bb_width_pct_rank_100 | regime | 0.0433 | 0.199 | sym_vs_btc_ret_7d (TRX) |
| 4 | ret_autocorr_lag5_50 | momentum_accel | 0.0362 | 0.259 | ret_autocorr_lag1_50 (BCH) |
| 5 | hurst_200 | regime | 0.0354 | 0.440 | hurst_100 (TRX) |
| 6 | volume_mom_ratio_20 | volume_micro | 0.0301 | 0.377 | sym_vs_btc_ret_7d (BCH) |
| 7 | vol_return_divergence_30 | microstructure_v3 | 0.0292 | 0.062 | sym_vs_btc_ret_7d (LDO) |
| 8 | vol_transition_slope_20 | microstructure_v3 | 0.0266 | 0.205 | sym_vs_btc_ret_7d (TRX) |

**Chosen add target: parkinson_gk_ratio_20** (Section C details)

## Section C — Deep dive on parkinson_gk_ratio_20

### Mechanism

`parkinson_gk_ratio_20` = Parkinson high-low realized vol / Garman-Klass OHLC realized vol,
both 20-bar trailing windows.

- **Parkinson vol** (1980): uses only High-Low extremes (assumes no drift, no jumps).
- **Garman-Klass vol** (1980): uses Open, High, Low, Close (incorporates opening direction).
- **Ratio**: when prices trend strongly in one direction during a bar, GK estimates
  higher vol than Parkinson (because the open-to-close move is large). When prices
  oscillate around the open, GK estimates lower vol than Parkinson (because the HL
  range is wide but the open-to-close move is small).
- **Interpretation**:
  - Ratio > 1.0 (Parkinson > GK) → choppy / sideways bar with wide HL range but small
    net move → mean-reverting microstructure
  - Ratio < 1.0 (Parkinson < GK) → trending bar with directional close-to-open move
    → momentum microstructure
- This is a Category 1 (off-the-shelf indicator), NOT a Category 2 composed feature.

### Why this is a NEW family for v3 base stack

**V3_BASE_14 family composition**:
- tail_risk (5): max_dd_window_50, ret_kurt_50, ret_skew_200, ret_kurt_200, ret_skew_50
- momentum_accel (2): ema_spread_atr_20, ret_autocorr_lag1_50
- volume_micro (1): vwap_dev_20
- regime (2): hurst_diff_100_50, hurst_100
- tail_risk (vol): range_realized_vol_50
- cross_btc (2): btc_ret_14d, sym_vs_btc_ret_7d
- engineered (1): regime_momentum_signed_5d
- **ZERO from price_efficient_vol family.**

Adding parkinson_gk_ratio_20 (price_efficient_vol family) is a FIRST-IN-CATEGORY
addition. It captures intra-bar microstructure information that no other base-14
feature encodes (regime + tail risk + momentum + volume look at bar-level returns,
not OHLC efficiency).

### Statistics

**ADF stationarity** (all 3 symbols, p < 0.001):
- BCHUSDT: p = 1.3e-19
- LDOUSDT: p = 1.0e-11
- TRXUSDT: p = 4.3e-17

**Univariate Spearman ρ vs forward 5-bar log return**:
- BCHUSDT: ρ = -0.044, p = 0.0010
- LDOUSDT: ρ = -0.071, p = 0.0002
- TRXUSDT: ρ = -0.039, p = 0.0033
- All 3 statistically significant (p < 0.005), consistent NEGATIVE direction →
  mean-reverting signal (high vol-ratio precedes negative forward returns).

**Stability**:
- BCH: skew=0.66, kurt=0.69 (well-behaved)
- LDO: skew within ±2.0 (well-behaved)
- TRX: skew within ±2.0 (well-behaved)

**IC with V3_BASE_14** (max |IC| = 0.245 vs ret_skew_200 LDO):
- Top 10 pairs ALL below 0.245.
- Below strict 0.50 Category-1 gate per `feedback_v3_engineered_feature_pivot.md`
  (carve-out for Category 2 does NOT apply — this is off-the-shelf vol-ratio).

**IC with proposed drop (ret_skew_50)**:
- BCH: 0.093, LDO: 0.051, TRX: 0.110 → orthogonal, NOT shared variance.
- The SWAP captures genuinely orthogonal signal, not redirected variance.

### Historical context

parkinson_gk_ratio_20 was in the **V3_FEATURE_COLUMNS_FULL 34-feature initial set
at iter-v3/001-006**, then DROPPED at iter-v3/007 dimensionality reduction (ranked
17/34 in the top-N filter — fell outside top-14). It has NEVER been tested at a
dedicated EXPLORATION axis. The original drop rationale was dimensionality, not
NEGATIVE signal.

It also exists in `V2_FEATURE_COLUMNS` (v2 baseline) — so it's been part of v1+v2
production pipelines without being a known NEGATIVE feature.

## Section D — Final ranking + axis decision

**LOCKED AXIS for iter-v3/057**: A4 base-stack SWAP

**SWAP definition**: V3_FEATURE_COLUMNS_TOP_N transformation
- DROP: `ret_skew_50` (rank 12/14 portfolio, bottom-3 BCH+TRX, mid LDO)
- ADD: `parkinson_gk_ratio_20` (family `price_efficient_vol`; never tested at base-stack)
- Net feature count: **14 → 14** (1-for-1 SWAP, no expansion)

**Why this is the strongest axis option**:

1. **Per-symbol load-bearing safety** — ret_skew_50 is bottom-3 on 2 of 3 syms; not
   load-bearing per /041 lesson (which falsified regime_momentum_signed_5d drop,
   NOT ret_skew_50 drop).

2. **Structural family-level distinction** — parkinson_gk_ratio_20 is the FIRST
   price_efficient_vol feature in v3 base stack. Cycle 4 has tested risk primitives,
   methodology axes, and Category-2 composed features — but never a NEW family at
   the base-stack level.

3. **Statistical robustness** — All 3 syms univariate Spearman ρ p<0.005, ADF p<0.001,
   max |IC|<0.245. NO statistical red flags.

4. **Mechanism predicts CPCV shift** — Adding a structurally distinct family member
   should reach Optuna trajectories NOT reachable by base-14 alone. If it learns
   (importance ≥ 30 in ≥1 sym), CPCV path distribution should shift.

5. **NOT a 15th-slot extension** — Critic /054 + /055 + /056 closed the 15th-slot
   SWAP at Category-2 composed-features scope. This is a base-stack SWAP (Category-1
   feature replacing a Category-1 feature).

## Section E — Predicted outcome paths

Per cycle-4 single-seed EXPLORATION conventions (per BASELINE_V3.md anchor cheat-sheet):
- PATH A (PROMISING-clean): IS Δ ≥ +0.10 vs /056 anchor AND OOS Δ ≥ +0.10 AND
  importance ≥ 30 in ≥1 symbol AND CPCV shift detectable
- PATH B (PROMISING-INERT): |IS Δ| ≤ 0.10 AND OOS Δ within lottery band AND importance
  < 30 → feature learned at low signal-strength but no Sharpe lift (saturation evidence)
- PATH C-clean (NEGATIVE): IS Δ < -0.10 OR OOS Δ < -0.20 → drop the SWAP, revert at /058
- PATH C-suspicious: IS-OOS daily Sharpe ratio outside [0.5, 2.0] → engineered-features-like-
  suspicious pattern; tighten interpretation
- PATH D (NULL-RESULT): IS Δ in (-0.10, +0.10) AND OOS Δ in (-0.20, +0.20) AND
  importance learned but no Sharpe shift → expected if structural CPCV pin holds
- PATH E (CPCV-INVARIANT NULL): CPCV path distribution bit-identical to /051..056
  (29/45 positive, median +0.3351, Q25 -0.243, Q75 +0.838). 7th-consecutive firing.

### Probability assessment

Single-axis SWAP at single-seed EXPLORATION:

- **PATH E (CPCV-INVARIANT NULL)**: 50-60% probability. The cycle-4 architectural
  pin is strong; a single feature SWAP may not be sufficient to dislodge it. PATH E
  firing is COMPATIBLE with PATH A / B / D — it speaks to CPCV path distribution,
  not Sharpe outcome.
- **PATH D (NULL-RESULT)**: 25-30%. parkinson_gk_ratio_20 learns at mid-table importance
  (≥30 expected based on Spearman magnitude) but produces no Sharpe shift.
- **PATH A (PROMISING)**: 8-12%. The feature captures a genuinely orthogonal signal
  and lifts both IS and OOS by ≥ +0.10.
- **PATH B (PROMISING-INERT)**: 5-10%. Feature does not learn meaningfully (importance
  < 30); OOS within lottery band.
- **PATH C-clean (NEGATIVE)**: 5-8%. SWAP breaks BCH or LDO via unexpected redundancy
  with regime_momentum_signed_5d (BCH IC 0.158 — high enough to displace).
- **PATH C-suspicious**: <5%. Unlikely given Category-1 feature with all-3-sym
  consistent ρ direction.

### Mechanism prediction (does this axis structurally shift CPCV?)

**Expected**: Yes, MILDLY. The SWAP changes:
1. **Optuna search space** — colsample_bytree picks shift; new feature gets some
   tree splits at low Optuna budget.
2. **Per-symbol feature mix** — BCH gets a vol-ratio signal it didn't have; LDO/TRX
   similarly.
3. **Cross-fold variance** — CPCV path distribution may show modest shift in median
   or tail (Q25/Q75) if the feature provides genuine signal.

**Falsification trigger for "structural CPCV shift"**:
- If CPCV positive count remains 29/45 AND median remains +0.3351 ± 0.005 AND
  Q75 remains +0.838 ± 0.005 → PATH E confirmed 7th consecutive, MILD SHIFT
  hypothesis falsified.

## Section F — Catalog row alignment

If PATH A fires: catalog row notes "NEW PROMISING family `price_efficient_vol` at
base-stack level — first ever post-iter-v3/006".

If PATH D fires: catalog row notes "structural CPCV invariance PERSISTS through
A4 SWAP — confirms cycle-4 architectural pin; cycle-5 mass expansion mandate stands".

If PATH C-clean fires: catalog row recommends /058 = revert SWAP + try obv_slope_50
(2nd-ranked candidate) OR pivot to risk primitive axis.

## Section G — IS-only data discipline

All computations in this EDA:
- IS-only: filtered with `df["open_time"] < OOS_CUTOFF_MS` where
  OOS_CUTOFF_MS = 1742774400000 (2025-03-24 UTC, immutable).
- Per-symbol parquets from `data/features_v3/` — never touch trade-level
  performance metrics.
- Forward-5-bar return for univariate Spearman uses `log_close.shift(-15) - log_close`
  in IS window only (forward-looking but bounded to IS); never leaked to features.

## Section H — Files

- `analysis/iteration_v3-057/eda_a4_vs_new_family.py` — main EDA script
- `analysis/iteration_v3-057/deep_dive_top3.py` — deep dive on top-3 candidates
- `analysis/iteration_v3-057/a4_drop_ranking.csv` — drop candidate ranking
- `analysis/iteration_v3-057/new_feature_candidates.csv` — all 28 surveyed features
- `analysis/iteration_v3-057/ic_top3_vs_drop.csv` — IC of top-3 candidates vs ret_skew_50
- `analysis/iteration_v3-057/spearman_top3.csv` — univariate ρ per symbol
- `analysis/iteration_v3-057/parkinson_gk_ic_vs_base14.csv` — IC of chosen candidate vs V3_BASE_14
- `analysis/iteration_v3-057/axis_decision.json` — final decision JSON
- `analysis/iteration_v3-057/synthesis.md` — this document

## Conclusion

**iter-v3/057 axis = A4 base-stack SWAP**
- DROP: ret_skew_50 (tail_risk family; bottom-3 importance on BCH+TRX)
- ADD: parkinson_gk_ratio_20 (price_efficient_vol family; FIRST-IN-CATEGORY for v3 base stack)
- Net count: 14 → 14
- Expected outcome: PATH D NULL-RESULT or PATH E CPCV-INVARIANT NULL most likely;
  PATH A PROMISING possible with 8-12% probability.

This is the QR-EDA-driven choice per `feedback_v3_axis_selection_quant_discipline.md`.
