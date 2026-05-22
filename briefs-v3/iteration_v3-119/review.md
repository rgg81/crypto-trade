# Phase 7.5 Critic Review — iter-v3/119

OVERALL: EXPLORATION-PROMISING — subclass PROMISING-FEATURE-MECHANICAL

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-6 slot #10 of 10 — FINAL EXPLORATION; iter-v3/120 is the mandatory CONFIRMATION)

## QR Response Considered (Round 2)

1. **Importance-15/15 vs Sharpe-+0.70 paradox** → CONCUR. QR's row-by-row /060 vs /119 portfolio importance comparison is load-bearing: Spearman ρ=0.7714 on the 14 anchor features documents moderate-high rank preservation (NOT chaotic shuffle), but the sister feature `regime_momentum_signed_5d` (C6's IC=−0.72 algebraic sister) cratered −65.3% (506.67 → 175.67). The C6+sister combined allocation NET DROPS 35.1% (506.67 → 328.67), and C6 alone is only **2.6% of total split-budget (153/5847)** — mechanically insufficient to produce a 5.0× OOS monthly Sharpe lift as direct edge. The 35% saved allocation redistributes to four rank-rising anchors (max_dd_window_50, ret_kurt_50, hurst_100, ret_skew_50). QR's "mixed signal/mechanical, dominant mechanical" reading is well-supported by the data and accepted.

2. **Mode 6 monthly-Sharpe canonical** → CONCUR. Monthly Sharpe is the canonical scale (matches brief Section 7 pre-registration and BASELINE_V3.md convention per `feedback_v3_cycle1_axis_pass_criteria.md`). Daily Sharpe view is INFORMATIONAL only. Mode 6 correctly does not fire because IS Δ = +0.1167 exceeds the +0.05 threshold — broad-based per-symbol IS movement (BCH +4.57 / LDO +18.75 / TRX +37.63) refutes the no-IS-movement lottery signature Mode 6 is calibrated to catch. The 0.067 knife-edge margin is acknowledged but Mode 6 is correctly inert.

3. **/116 PROMISING-MECHANICAL precedent — feature-form analog?** → CONCUR. /119 is the FEATURE-layer analog of /116's RULE-layer mechanism. /116 modifies what trades are kept (book composition via slot-freeing cascade); /119 modifies what features the model weights (split-budget redistribution via algebraic-sister cannibalization). Both share the load-bearing PROMISING-MECHANICAL invariant: **non-compoundable as a SIGNAL source** because the mechanism is mechanical rearrangement rather than new edge information. Mechanisms ARE at different layers — they can coexist as separate strictly-accretive component decisions, but cannot be expected to STACK linearly as independent edge ingredients. New sister-subtype designation `PROMISING-FEATURE-MECHANICAL` is established by this review.

4. **TRX OOS concentration falsifier pre-committed** → CONCUR with the three-tier gate. /116 single-seed had three positive carriers with the top carrier at 52.9% of positive total; /119 single-seed has only TWO positive carriers (LDO is drag at −24.03% portfolio share) with TRX at 52.05% of the positive total. The TRX concentration is materially worse than /116's structurally because the denominator shrinks. QR's pre-committed falsifier — TRX OOS PnL share > 50% of positive-symbol total → BLOCK; 50–65% → concentration-watch flag; > 65% → full BLOCK; LDO portfolio share worse than −25% → flag — is accepted as binding pre-registration for /120.

5. **/120 TWO-COMPONENT bundle** → CONCUR with refinement. QR's option (a) — TWO-COMPONENT /116+C6 with three pre-committed falsifiers (stacking-linearity, TRX-concentration, sister-redistribution stability) — is the correct adjudication. The two mechanisms operate at DIFFERENT layers (rule vs feature) so the "non-compoundable as signal source" invariant from `feedback_promising_mechanical_subtype.md` does not preclude their coexistence as separate strictly-accretive accretion decisions. Falsifier 1 (stacking-linearity: bundle Sharpe < max(component Sharpes) − 0.10 → drop C6) is the critical safeguard against an over-additive assumption. This is the FIRST multi-mechanism bundle in v3 history and is established as new catalog precedent by this review.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
`compute_ret5d_signed_tbi` at `src/crypto_trade/features_v3/engineered_v3.py:834-888` is past-only by construction (`ret_5d = log_close − log_close.shift(15)` and `taker_buy_imbalance_20` itself uses `tbr.shift(1).rolling(20).mean()`). The `GROUP_REGISTRY` ordering in `features_v3/__init__.py:71-127` places `microstructure_v3` before `engineered_v3`, so `taker_buy_imbalance_20` is available when C6 fires. Adversarial future-bar unit test passes (engineering report Section 1). Zero-imbalance edge case correctly NaN'd. The /015 `tbr_zscore_30` dead-path used the magnitude of the same primitive family; C6 uses only the DISCRETIZED `sign(taker_buy_imbalance_20)` regime label, structurally distinct from the magnitude-input failure mode.

### Check 2 — Embargo Width: PASS
`REQUIRED_GAP = 66 = (timeout_candles + 1) × n_symbols = (21+1) × 3` with `timeout_minutes=10080`, 8h candles. Runner enforces at `run_baseline_v3.py:1304-1313`. Walk-forward lookahead bug is FIXED post-/058 (`walk_forward.py:113` applies `train_end_ms = test_start_ms − embargo_ms`, per `feedback_v3_walkforward_lookahead_bug.md`). Unchanged from /118.

### Check 3 — Multiple-Testing Correction: PBO PASS / DSR-PSR INFORMATIONAL (EXPLORATION mode)
`dsr.json`: DSR=0.0 (EXPLORATION-budget structural artifact per `feedback_v3_dsr_mode_artifact.md`); PBO=0.0957 PASS (< 0.40); PSR=1.0000 PASS (> 0.95); frac_positive_paths=0.6444 PASS (> 0.55); n_trials=315 (3 seeds × 35 trials × 3 syms — matches EXPLORATION budget). PBO at 0.0957 is identical to /060/059 — a CPCV invariant of the universe + label. No Check 3 BLOCK; DSR/PSR at single-seed EXPLORATION budget are not comparable to CONFIRMATION-mode and are informational only.

### Check 4 — IC Correlation: PASS-CARVEOUT
C6 max |IC| = 0.7229 with `regime_momentum_signed_5d`. Per `feedback_v3_engineered_feature_pivot.md`, Category-2 composed features sharing a value primitive (`ret_5d`) MECHANICALLY correlate by construction; the strict 0.70 threshold is replaced by the importance-≥30% threshold. Brief R²=0.51 pre-disclosure at EDA T2 is consistent with production measurement. Secondary high-|IC| pairs (vwap_dev_20 −0.567, ema_spread_atr_20 −0.431) are algebraically inherited transitively through regime_momentum_signed_5d and do not constitute NEW high-IC pairs.

### Check 5 — ADF Stationarity: PASS
C6 stationary at IS-end across all three symbols (BCH ADF=−7.753, LDO=−8.128, TRX=−10.295; all p=0.0). Structurally guaranteed by `sign(tbi) ∈ {−1, +1}` × bounded log-return = stationary product. Early-window NaN-ADF artifacts cluster before training-window adequacy as expected for LDO's shorter history.

### Check 6 — Pareto Dominance: N/A (single-seed EXPLORATION)
EXPLORATION ENSEMBLE_SIZE=3, no 10-seed pareto front file exists. Pareto evaluation is deferred to /120 CONFIRMATION (10-seed unified ensemble). Not a Critic-actionable gap under cycle-6 EXPLORATION protocol; the 3-seed lottery risk is now encoded in the three pre-committed /120 falsifiers (Clarification 5).

### Check 7 — Reproducibility: PASS
Commit SHA `82baf43` verified. Runner enforces explicit `n != 15` guard at `run_baseline_v3.py:432-442` with iter-v3/119-specific error message. `V3_FEATURE_COLUMNS_TOP_N` enumerates 15 named columns (`features_v3/__init__.py:207-221`); auto-discovery is structurally blocked. Spot-check on `in_sample/trades.csv` row 2 (BCH long, entry 292.99, exit 279.019378, weight 0.46): pnl_pct −4.768% matches; net after 0.1% fee −4.868% matches; weighted_pnl −2.2394 matches. OOS row 1 (BCH short 303.87/282.10) → 7.1640% matches reported.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 3.5 specifies 6 substantive changes + 1 housekeeping revert. Engineering report Section 2 enumerates all 6 as DELIVERED. Direct verification: `compute_ret5d_signed_tbi` at `engineered_v3.py:834-888` matches docstring + math byte-equivalent; wired in `add_engineered_v3_features` at line 1055 after `compute_ema_signed_volregime` at line 1054; GROUP_REGISTRY reorder at `features_v3/__init__.py:78-89` places microstructure_v3 before engineered_v3; `V3_FEATURE_COLUMNS_TOP_N` 15th element is `"ret5d_signed_tbi"`; `ema_signed_volregime` ABSENT-ban added; `n != 15` guard updated. No scope creep into RiskV2 or labeling. Hypothesis-implementation byte-equivalent.

## Substantive Classification — PROMISING-FEATURE-MECHANICAL (NEW sister-subtype)

This review establishes a new v3-catalog classification: **PROMISING-FEATURE-MECHANICAL**, the FEATURE-layer sister to /116's RULE-layer **PROMISING-MECHANICAL**. The two subtypes share the load-bearing invariant — **non-compoundable as a signal source** — but operate at structurally distinct layers (loss-surface reorganization vs book composition). The diagnostic for PROMISING-FEATURE-MECHANICAL is the conjunction:

(a) **Sister-family redistribution > 30% with new feature < 5% of total split-budget**: /119's `regime_momentum_signed_5d` (C6's IC=−0.72 algebraic sister) lost 65.3% importance (506.67 → 175.67); C6's allocation is only 2.6% of total (153/5847); the combined sister-family allocation NET DROPS 35.1% (506.67 → 328.67). The new feature cannibalizes more than it adds to the sister-family.

(b) **Anchor-rank preservation Spearman > 0.50 (NOT chaotic shuffle)**: /119's 14 anchor features show Spearman ρ = 0.7714 vs /060 anchor — the model still finds the same dominant signals at rearranged weight, distinguishing this from the chaotic-shuffle signature of pure loss-surface destruction (which would produce ρ closer to 0.3–0.5).

(c) **Broad-based per-symbol IS positive Δ (NOT single-symbol carrier)**: /119 shows BCH +4.57 / LDO +18.75 / TRX +37.63 IS PnL Δ — the broad-based-cascade signature distinguishing this from /118-style single-carrier lottery outcomes (where ema_signed_volregime catastrophically failed via single-symbol regression).

/119 meets all three diagnostic conditions. The classification refines the standard EXPLORATION-PROMISING verdict: C6 is strictly-accretive on /059 as a feature-layer mechanical primitive, but is NOT a new edge ingredient and therefore CANNOT be compounded with other edge ingredients in future cycles as if it were a signal contribution. This classification is orthogonal to /116's RULE-layer PROMISING-MECHANICAL — the two mechanisms operate at different layers and can coexist in a single CONFIRMATION bundle as SEPARATE strictly-accretive component decisions.

## Recommendations for /120 CONFIRMATION

1. **TWO-COMPONENT bundle (/116 no_confirm + /119 C6 ret5d_signed_tbi)** at 10-seed unified ensemble validation. Both components are treated as strictly-accretive mechanical primitives at DIFFERENT layers (RULE-layer book composition + FEATURE-layer loss-surface reorganization). This is a NEW precedent — the first multi-mechanism bundle in v3 history. The /116-alone and C6-alone alternatives are inferior because they leave evidence on the table and the multi-seed budget cannot be re-spent.

2. **Three pre-committed falsifiers carried into /120 brief Section 4 (binding pre-registration)**:
   - **Falsifier 1 — Stacking-linearity**: bundle multi-seed OOS monthly Sharpe < max(/116-only multi-seed OOS Sharpe, C6-only multi-seed OOS Sharpe) − 0.10 → bundle is NEGATIVE-no-stacking; revert to /116-only for /120 MERGE.
   - **Falsifier 2 — TRX-concentration**: TRX multi-seed mean OOS PnL share > 50% of positive-symbol total → BLOCK C6 inclusion (keep /116 alone); 50–65% → concentration-watch flag; > 65% → full BLOCK; LDO portfolio share worse than −25% multi-seed → flag.
   - **Falsifier 3 — Sister-redistribution stability**: if `regime_momentum_signed_5d` importance falls > 50% in multi-seed mean (vs /060 anchor) AND `ret5d_signed_tbi` importance fails to exceed 5% of portfolio total importance → "allocation cannibal without contribution" → BLOCK C6 inclusion.

3. **Cycle-6 closure characterization**: cycle 6 produced **2 strictly-accretive mechanical primitives (/116 RULE-form + /119 FEATURE-form) and 0 new edge ingredients across 10 EXPLORATIONs** (/110–/119: 8 NEGATIVE/NULL + 2 PROMISING-MECHANICAL). The user's cycle-6 axis-menu hypothesis (symbol selection, pooled-vs-per-symbol, multi-freq features, risk management would surface new edge) is **FALSIFIED on the new-edge axis** but **PROMISING on the strictly-accretive mechanical-primitive axis**. If /120 bundles successfully (or even partially — i.e., /116-only survives the falsifiers), the cycle delivers a meaningful but non-revolutionary outcome: 1–2 strictly-accretive mechanical primitives on /059. The cycle-7 axis menu should structurally reorient toward fundamentally different edge sources (cross-asset, external feeds, non-LightGBM model classes already falsified at /109, or longer-cadence labels) rather than re-walking the cycle-6 NEGATIVE axes.

4. **C6 STAYS in V3_FEATURE_COLUMNS_TOP_N for /120**: do NOT revert as /118 C3 (`ema_signed_volregime`) was. The /120 setup-commit takes /119 head state (`V3_FEATURE_COLUMNS_TOP_N` at 15 features with `ret5d_signed_tbi` at index 14). The 10-seed CONFIRMATION evaluates C6 in its production form; the three falsifiers above are the gates that decide whether C6 remains in the production baseline post-/120. The single-axis-discipline revert of /116 no_confirm is partially undone by including /116 in the /120 bundle — this is correct per the QR's adjudication that mechanical-primitive bundles ARE the appropriate /120 vehicle and the cycle-6 closure event.

## Catalog Entry

iter-v3/119 EXPLORATION-PROMISING (subclass **PROMISING-FEATURE-MECHANICAL**) — IS Δ vs /060 anchor = **+0.1167** (0.8325 → 0.9492 monthly Sharpe), OOS Δ vs /060 anchor = **+0.7017** (0.1403 → 0.8420 monthly Sharpe). Frac positive paths = 0.6444. Confirmation candidate: **YES** — bundled with /116 no_confirm at /120 CONFIRMATION as a TWO-COMPONENT multi-mechanism bundle. Cycle-6 EXPLORATION sequence CLOSED at 10/10.

## Clarifications Requested from QR — NONE
