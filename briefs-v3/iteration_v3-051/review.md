# Phase 7.5 Critic Review — iter-v3/051

OVERALL: **EXPLORATION-NULL-RESULT** — fracdiff_d05_close UNIVERSAL learned (ranks 11-12/15 across 3 syms) but produced NO IS lift (Δ -0.06 sits in the no-man's-land between brief's PATH A +0.05 ceiling and PATH C-clean -0.10 floor); OOS Δ +0.08 within single-seed lottery noise; LDO OOS -17.44 structural drag CONFIRMED at FULL REVERT to /028 architecture — LDO removal is now the highest-priority cycle 4 #2 axis.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION — Cycle 4 #1 of 10 (first post-iter-v3/050 NO-MERGE-CONFIRMATION). Spec: `--seeds 1 --n-trials 35 --clean-oof` LightGBM; ENSEMBLE_SIZE=5; outer_seed=42 single; 1.28h wall-clock under 2h cap.

## QR Response Considered (Round 2 only)

(Round 1 PRELIMINARY skipped — orchestrator dispatched directly with FINAL mode given the unambiguous EXPLORATION-classification gap. The verdict pathway is driven by adjudication of a brief-defect (the 4 LOCKED paths contain a no-man's-land between IS Δ -0.10 and IS Δ +0.05, exactly where the observed IS Δ = -0.0595 landed); no QR clarification could fill that pre-registration gap retroactively without violating `feedback_no_cheating.md` post-hoc renegotiation discipline. The Critic adjudicates within the brief's spirit-of-PATH-C-clean reading per the QR's own pre-registered saturation rule.)

## Per-Check Status (12 standard methodology checks)

### Check 1 — Look-Ahead Audit: PASS
`compute_fracdiff_d05_close` (`engineered_v3.py:264-327`) uses Fixed-Width Window FFD: at bar `t`, the output is `sum_{k=0}^{W-1} w_k × log_close[t-k]` for window length W. The window includes `close[t]` but `close[t]` is observable at bar `t`'s close, and v3's trading convention is to act on bar `t+1`'s open. The 5 adversarial tests verify no look-ahead. ADF stationarity at end-of-training-window (2025-03): BCH p=0.0, LDO p=0.0, TRX p=0.003.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP correctly recomputed for 3-sym universe: `validation_v3.py:54` = `(21+1) × 3 = 66`. Universe contraction 4→3 honored. Symmetric application via CPCV. 45 paths generated; PBO=0.1168 < 0.40.

### Check 3 — Multiple-Testing Correction: EXPLORATION-INFORMATIONAL
- DSR = 0.0 vs threshold 0.95 — structural artifact at n_trials=525 per `feedback_v3_dsr_mode_artifact.md`. EXPLORATION-mode DSR informational ONLY.
- PBO mean = 0.1168 PASS (threshold 0.40). frac_positive_paths = 0.644 (improvement vs iter-v3/050's 0.533 — REVERT to 3-sym restores path-level generalization).
- PSR = 1.0 PASS at saturation.
- n_trials = 525 = 3 syms × 5 inner × 35 trials. n_eff = 19.

### Check 4 — IC Correlation: PASS
Runtime `ic_matrix.csv` shows pooled cross-symbol IC for fracdiff_d05_close vs existing 14: max |IC| = **0.1803** with `range_realized_vol_50` (well below 0.70 strict gate). vs `vwap_dev_20`: 0.1178 (pooled). Category 2 carve-out conservatively applied at EDA stage; runtime confirms no carve-out needed at pooled IS level.

### Check 5 — ADF Stationarity: PASS
End-of-training-window per-symbol ADF for fracdiff_d05_close: BCH p=0.0, LDO p=0.0, TRX p=0.0031. All three symbols clear 0.05 threshold by wide margins.

### Check 6 — Pareto Dominance: PASS (single-seed trivially non-dominated)
EXPLORATION spec `--seeds 1`. Per `feedback_v3_single_seed_frozen_baseline.md`, single-seed=42 carries lottery caveat — BCH OOS +23.59 and LDO OOS -17.44 may be deterministic at this seed regardless of axis change.

### Check 7 — Reproducibility: PASS
Setup SHA `c0ebe21` stamped. ITERATION_LABEL = "v3-051". Explicit `feature_columns`. PnL formula spot-check confirmed.

### Check 8 — Hypothesis-Implementation Alignment: PASS (hypothesis tested, classification fails pre-registered paths)
Implementation verified:
- V3_FEATURE_COLUMNS_TOP_N element 15 = `fracdiff_d05_close`
- V3_MODELS = 3-sym BCH+LDO+TRX (ALGO dropped)
- V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (empty)
- `block_long_for=()` (REVERT)
- REQUIRED_GAP = 66 = (21+1)×3
- 5 adversarial tests in `test_fracdiff_d05_universal.py`

**HOWEVER**: The QR's pre-registered Section 8 LOCKED criteria contain a methodological defect — the 4 paths leave a no-man's-land for IS Δ ∈ (-0.10, +0.05). Observed IS Δ = -0.0595 sits exactly in this gap.

## Optional Checks 9-12

### Check 9 — Symbol Exclusion Enforcement: PASS
### Check 10 — Feature Isolation Enforcement: PASS
### Check 11 — Forming-Candle Audit: PASS
### Check 12 — Library Version Pinning: PASS (no new deps; pure numpy+pandas FFD)

## Brief Pre-Registration Defect — Adjudication

The QR's pre-registered 4 paths leave a no-man's-land for the actual outcome:

| Path | Trigger | Observed | Fired? |
|---|---|---|---|
| PATH A (PROMISING-clean) | IS Δ ≥ +0.05 AND OOS Δ ≥ -0.20 AND rank ≤ 12/15 in ≥1 sym | IS Δ -0.06 (FAIL IS Δ ceiling) | NO |
| PATH B (PROMISING-INERT) | rank > 13/15 in ALL 3 syms AND IS Δ ∈ [-0.10, +0.05] | ranks 12/11/11 (FAIL — feature LEARNED) | NO |
| PATH C-clean (NEGATIVE-clean) | IS Δ < -0.10 OR OOS Δ < -0.30 | IS Δ -0.06 (>-0.10); OOS Δ +0.08 (>-0.30) | NO |
| PATH C-suspicious (NEGATIVE-SUSPICIOUS-OOS) | IS-OOS daily ratio outside [0.5, 2.0] | 1.148 (in band) | NO |

**Critic decision: EXPLORATION-NULL-RESULT.** Rationale:
1. OOS Δ +0.08 is within single-seed=42 lottery noise. BCH OOS +23.59 and LDO OOS -17.44 may be deterministic at this seed regardless of axis change.
2. IS Δ -0.06 indicates fracdiff did NOT lift IS Sharpe — the central prediction of the brief's hypothesis.
3. Mapping to PROMISING-MARGINAL would inflate the count of cycle 4 PROMISING ingredients spuriously.
4. Mapping to NEGATIVE-MARGINAL would close the fracdiff axis prematurely.
5. EXPLORATION-NULL-RESULT (no lift, no clear regression, feature learned but inert at portfolio level) is the most honest classification.

**Action implication**: fracdiff_d05_close at universal scope is NOT carried forward. Drop from V3_FEATURE_COLUMNS_TOP_N at /052 setup. PARKED — INFORMATIONAL (not "CLOSED for cycle 4"); may be retested under different conditions (per-symbol scoping, n_trials=50+, multi-seed) if cycle 4 PROMISING ingredients accumulate.

## Critical Adversarial Findings

### 1. The iter-v3/035 BCH-only fracdiff precedent is misleading
The brief cited "iter-v3/035 BCH-only PROMISING precedent (+37.98 OOS swing for BCH at single-seed)" as basis for universal-scope retest. **This precedent does NOT generalize**:
- iter-v3/035 (BCH-only per-symbol fracdiff): IS Sharpe **-0.10** / OOS Sharpe **+2.85** — IS-OOS daily ratio = 27.88×, which is the iter-v3/026/027 anti-pattern PATH C-suspicious by today's taxonomy.
- iter-v3/034 (the ACTUAL universal-scope precedent at 4-sym): IS **-0.16** / OOS **+1.77** — ratio 10.82×, also PATH C-suspicious.
- Neither precedent is a valid PROMISING citation under `feedback_v3_engineered_features_dont_stack.md`. The brief's framing was anchored on a stale interpretation.
- iter-v3/051 universal-scope at /028-architecture (post-REVERT) gives IS Δ -0.06 / OOS Δ +0.08 — the cleanest fracdiff result in v3 history (ratio 1.15 in-band) but does NOT lift IS as predicted. The "PROMISING precedent" hypothesis is FALSIFIED in clean conditions.

### 2. LDO structural drag CONFIRMED at FULL REVERT — highest-priority cycle 4 #2 axis
- LDO OOS weighted_pnl = **-17.44** at FULL REVERT (default ATR (2.0, 1.0); no primitive 10; no per-sym customization).
- LDO IS PnL share = **-14.96%** (-5.99% net_pnl_pct, 27.3% WR over 11 IS trades).
- LDO OOS WR = **23.1%** (3 wins / 13 trades) — far below random walk 50%.
- The QR EDA at /051 rejected LDO removal based on LDO IS contribution at iter-v3/050 being near-zero (+0.85 wpnl). **The /051 result supersedes this**: at /028-reverted baseline, LDO IS is -14.96% PnL share (a drag).
- LDO removal investigation is now the highest-priority cycle 4 #2 axis. EDA priorities for /052:
  1. Quantify LDO IS+OOS PnL contribution at iter-v3/051 baseline.
  2. Compare 2-sym (BCH+TRX) vs 3-sym (BCH+LDO+TRX) IS aggregate Sharpe at /051 trade-roster level.
  3. If LDO removal lifts BOTH IS and OOS at single-seed → PROMISING for /052 axis.

### 3. regime_momentum_signed_5d displacement by fracdiff is noise, not signal
fracdiff_d05_close marginally outranks regime_momentum_signed_5d at all 3 symbols. Both features rank in bottom tier. Pairwise IC = 0.148 (very low), so NOT redundancy; model gives both features roughly equal low split-budget priority. regime_momentum_signed_5d regression from iter-v3/025 PROMISING is a separate cycle 4 axis (per /050 Critic rec #4).

### 4. ONE-variable rule judgment: REVERT is acceptable as system-level mandate
REVERT is acceptable as system-level state restoration, NOT a second axis. Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10 (second-cycle confirmation), the per-symbol customization REVERT is mandatory new cycle 4 starting baseline. Structurally identical to how iter-v3/049 mandated `vol_normalized_ret_5d` REVERT as setup.

**Sanity check**: /051 single-seed result (IS +0.45 / OOS +0.59) sits within the predicted /028-architecture single-seed band. The REVERT mechanically worked; fracdiff did not add lift.

## Recommendations to QR for iter-v3/052

1. **iter-v3/052 axis = LDO removal investigation** (highest priority per QE engineering report + this Critic). EDA priorities (mandatory before brief write per `feedback_v3_axis_selection_quant_discipline.md`):
   - Quantify LDO IS+OOS contribution at /051 baseline (`reports-v3/iteration_v3-051/in_sample/per_symbol.csv` shows LDO IS = -14.96% PnL share).
   - Show 3-sym BCH+LDO+TRX vs 2-sym BCH+TRX IS aggregate Sharpe at /051 multi-month walk-forward.
   - If LDO removal lifts BOTH IS and OOS at single-seed → PROMISING-clean candidate for /052 axis.
   - Fresh EDA on /051 trade roster supersedes /050 EDA (LDO calculus changed).

2. **Drop fracdiff_d05_close from V3_FEATURE_COLUMNS_TOP_N at /052 setup** (15 → 14). PARKED (not CLOSED). Retain `compute_fracdiff_d05_close` as dead-code at zero revert cost. Rationale: feature LEARNED (ranks 11-12) but produced no IS lift; keeping it would test stacking effects with /052's new axis, contaminating attribution per `feedback_v3_engineered_features_dont_stack.md`.

3. **Brief pre-registration tightening for /052 onward**: future EXPLORATION brief Section 8 must include 5th explicit BORDERLINE/NULL-RESULT path covering IS Δ ∈ (-0.10, +0.05) AND OOS Δ ∈ (-0.30, +0.20). Suggested: **PATH D (EXPLORATION-NULL-RESULT)**: IS Δ ∈ (-0.10, +0.05) AND OOS Δ ∈ (-0.20, +0.20) AND feature LEARNED (rank ≤ 12 in ≥1 sym) — classify as null result, drop axis, do NOT close for cycle.

## Catalog Row

`| iter-v3/051 | 2026-05-11 | EXPLORATION cycle 4 #1 of 10: ADD fracdiff_d05_close to V3_FEATURE_COLUMNS_TOP_N (14→15) at universal scope (broadcast to all 3 syms BCH+LDO+TRX) + SYSTEM-LEVEL REVERT to iter-v3/028 architecture (V3_MODELS=3-sym, V3_ATR_MULTIPLIERS_PER_SYMBOL={}, block_long_for=(), REQUIRED_GAP=66) per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10 second-cycle confirmation; --seeds 1 + ENSEMBLE_SIZE=5 + n_trials=35 + --clean-oof | -0.06 (vs iter-v3/028 baseline +0.5101 → +0.4506; no-man's-land between PATH A +0.05 and PATH C-clean -0.10) | +0.08 (vs iter-v3/028 baseline +0.5053 → +0.5891; within single-seed lottery noise; IS-OOS daily ratio 1.15 in band; BCH +23.59 / LDO -17.44 / TRX +11.28; fracdiff ranks 12/11/11/13 portfolio — LEARNED) | EXPLORATION-NULL-RESULT (brief pre-registration defect — 4 LOCKED paths left no-man's-land for IS Δ ∈ (-0.10, +0.05)) | NO — fracdiff_d05_close PARKED (not CLOSED); drop from V3_FEATURE_COLUMNS_TOP_N at /052 setup. LDO OOS -17.44 weighted_pnl + LDO IS PnL share -14.96% at FULL REVERT confirms LDO structural drag independent of per-symbol customizations; **iter-v3/052 axis = LDO removal investigation** (cycle 4 #2 HIGH-priority). iter-v3/035 BCH-only fracdiff +37.98 OOS precedent FALSIFIED in clean conditions. REVERT mechanism worked. Brief pre-registration tightening recommended (add PATH D NULL-RESULT). Cycle 4 cadence advances 1/10. Tag NOT issued. |`

## Files Audited

- `briefs-v3/iteration_v3-051/research_brief.md` (SHA `6697f95`)
- `briefs-v3/iteration_v3-051/phase5p5_gate.md` (SHA `c0ebe21`)
- `briefs-v3/iteration_v3-051/engineering_report.md` (SHA `13a6ec5`)
- `reports-v3/iteration_v3-051/comparison.csv` + `dsr.json` + `seed_summary.json` + `pareto_front.csv` + `per_cell_pbo.csv` + `cpcv_paths.csv` + `ic_matrix.csv` + `adf_test.csv`
- `reports-v3/iteration_v3-051/in_sample/` (per_symbol.csv + 4 model_importance_last_month CSVs) + `out_of_sample/` (trades.csv spot-checked + per_symbol.csv)
- `src/crypto_trade/features_v3/engineered_v3.py` (lines 264-327)
- `src/crypto_trade/features_v3/__init__.py` (V3_FEATURE_COLUMNS_TOP_N element 15 + V3_ATR_MULTIPLIERS_PER_SYMBOL = {})
- `run_baseline_v3.py` (ITERATION_LABEL, V3_MODELS, block_long_for, audits)
- `validation_v3.py` (REQUIRED_GAP=66)
- `tests/features_v3/test_fracdiff_d05_universal.py` (5 adversarial tests)
- `analysis/iteration_v3-051/synthesis.md` + `candidate_axes_ranking.md` (SHA `290f37b`)
- `reports-v3/iteration_v3-034/comparison.csv` + `iteration_v3-035/comparison.csv` (precedent verification)
- `briefs-v3/iteration_v3-050/review.md` (immediate predecessor)
- `BASELINE_V3.md` (iter-v3/028 anchor)
