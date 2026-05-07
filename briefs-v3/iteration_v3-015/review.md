# Phase 7.5 Critic Review — iter-v3/015 — FINAL (Round 2)

**OVERALL: EXPLORATION-NEGATIVE-no-effect**

**Iteration Type**: EXPLORATION (single-axis: NEW microstructure feature `tbr_zscore_30`; first NEW feature family in v3 catalog per `feedback_structural_over_knob_exploration.md` priority order Category 1)

**Round**: 2 FINAL (PRELIMINARY SHA `2c155da`; QR Response SHA `407954d` accepted in full)

## QR Response Considered

QR's 4 clarifications fold cleanly into the verdict:

1. **Clarification 1 (classification subtype)**: ACCEPTED. QR accepts Critic prior — classification = `EXPLORATION-NEGATIVE-no-effect`. §4.4 row 2 IS Sharpe band [+0.91, +1.11] is structurally load-bearing; realized +0.6445 sits +0.27 OUTSIDE the band lower bound (2.7× band half-width). PROMISING-INERT (per §4.3 verbatim) is structurally distinct from the realized outcome and would mislead future CONFIRMATION QRs into reading "feature added without harm" when reality is "feature added but model couldn't use it AND IS axis degraded by Δ-0.36 (magnitude similar to iter-v3/014's NEGATIVE Δ-0.35)."

2. **Clarification 2 (per-symbol importance disambiguation)**: RESOLVED. QR ran `analysis/iteration_v3-015/per_symbol_importance.py` and confirmed `tbr_zscore_30` rank = 14/14 across ALL 3 symbol models (BCH 16%, LDO 41%, TRX 20% of top feature importance). §4.3 falsifier "bottom-quartile across all 3 symbols" strictly fires. **BONUS FINDING**: QR identified a defect in `_write_feature_importance` at `run_baseline_v3.py:1110-1151` — the function reads only `primary_model_pairs[0]` (BCH last-month), so the engineering report's claim that `feature_importance.csv` is aggregated across all symbols/months was incorrect. The per-symbol script confirmed the verdict regardless. **Hygiene fix pre-committed for iter-v3/016 setup**: rename `_write_feature_importance` outputs to clarify single-symbol scope, OR aggregate properly.

3. **Clarification 3 (iter-v3/016 axis pre-commit)**: ACCEPTED. iter-v3/016 axis = **LightGBM → XGBoost head-to-head on iter-v3/013's 13-feature stack** (drop `tbr_zscore_30` as INERT). New memory rule `feedback_v3_iter016_xgboost_mandate.md` drafted. Justification: LightGBM's failure to learn TBR signal suggests model-architecture bottleneck; XGBoost's depth-wise tree growth + different regularization + different histogram binning is the natural compoundable axis to test before adding more features. Single-axis variation; cannot be renegotiated post-hoc at iter-v3/016 setup.

4. **Clarification 4 (TBR-raw column write-through)**: RESOLVED. QR confirmed: (a) `tbr_raw` excluded from LightGBM input vector (V3_FEATURE_COLUMNS = 14 with tbr_zscore_30 only; tbr_raw not listed); (b) `tbr_raw` excluded from RiskV3Wrapper z-score OOD gate at `risk_v3.py:72,101` (gate operates on V3_FEATURE_COLUMNS only). Low-priority hygiene note: add `tbr_raw` to `V3_NON_FEATURE_COLUMNS` for documentation parity, deferred to iter-v3/016 setup.

The classification flip from QE's PROMISING-INERT to Critic+QR's NEGATIVE-no-effect preserves the catalog discipline that PROMISING-class verdicts require IS Sharpe lift OR strict band-equivalence; INERT is reserved for true band outcomes (iter-v3/012 exemplar Δ-0.147 with bit-identical roster, NOT iter-v3/015's Δ-0.36 with non-bit-identical roster).

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
`compute_tbr_zscore` at `volume_micro_v3.py:94-132` strictly past-only via `s.shift(1)` then rolling on shifted series.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP = 66 = (21+1)×3 confirmed at runtime. CPCV n_paths=45, embargo=27 symmetric.

### Check 3 — Multiple-Testing Correction: WAIVED-INFORMATIONAL (EXPLORATION)
DSR=0.0, PSR=1.0 single-seed artifacts. PBO=0.1034 in-line with v3 norm. TRX/2025-Q4 carry-forward + 2 NEW high-PBO cells (LDO 2026-05, BCH 2024-01) at OOS frontier — informational, not blocking.

### Check 4 — IC Correlation: PASS
Max pairwise |IC| for `tbr_zscore_30` vs existing 13 = 0.0862 with `vwap_dev_20` (Pearson). Far below 0.70 redundancy gate. **Strong methodological win**: NEW feature is structurally orthogonal to existing stack — even though the model didn't use it, the feature was clean.

### Check 5 — ADF Stationarity: PASS (PROMOTED)
2199 ADF rows. `tbr_zscore_30` 4 non-stationary cells concentrate at symbol-listing months with insufficient rolling-window samples; all other cells p<0.01 (z-score is mean-zero by construction). Inherited 13-feature stack PASS.

### Check 6 — Pareto Dominance: PASS (vacuous, single-seed)

### Check 7 — Reproducibility: PASS
Setup commit `d2374a6`; HEAD `2c155da` (post-Critic-PRELIMINARY); brief `b9cc79b`; gate `c253e1d`; engineering report `3ce2572`; QR response `407954d`. ENSEMBLE_SIZE=1 explicit; outer_seed=42.

### Check 8 — Hypothesis-Implementation Alignment: PASS-WITH-FAILED-AXIS
Single-axis discipline honored. Three changes vs iter-v3/013: (1) tbr_zscore_30 added; (2) ADX reset 25→20 baseline restoration; (3) ITERATION_LABEL cosmetic. **Hypothesis NOT SUPPORTED**: realized IS Sharpe Δ-0.36 (vs iter-v3/013 +1.0088 baseline) is below predicted band median +0.90 by Δ-0.26 and below band lower +0.50 by Δ+0.14 (within band lower edge); Falsifier 4 (importance bottom-quartile across all 3 syms) FIRED.

### Check 9 — Symbol Exclusion: PASS
{BCH, LDO, TRX} ∩ V3_EXCLUDED_SYMBOLS = ∅.

### Check 10 — Feature Isolation: PASS
`features_v3` does not import from v1/v2 feature stacks. New `compute_tbr_zscore` in `volume_micro_v3.py` (track-isolated).

### Check 11 — Forming-Candle: PASS (inherited)

### Check 12 — Library Version Pinning: PASS
Stack identical to iter-v3/008-014. Zero new dependencies for `tbr_zscore_30` (numpy + pandas only).

## EXPLORATION-Specific Catalog Attribution

The NEGATIVE-no-effect verdict is the correct framing because:

- IS Sharpe Δ-0.36 vs iter-v3/013 baseline — **outside** §4.4 row 2's PROMISING-INERT band [+0.91, +1.11] by 7×_band_width on the unfavorable side.
- Trade roster non-bit-identical (209 → 205) — distinguishes from iter-v3/012's NULL-RESULT exemplar (which had bit-identical roster). The 4-trade reduction confirms the new feature DID enter the loss surface (added noise that re-routed Optuna), but did NOT produce signal-driven gating.
- `tbr_zscore_30` importance rank 14/14 across all 3 per-symbol models (BCH 16%, LDO 41%, TRX 20% of top) — feature is functionally near-discarded; the 13.2% of top in aggregate is misleading because it's a single-model snapshot per the QE-discovered defect.
- The OOS lift +2.12 is genuine but **not attributable to the new feature** — it attributes to (a) Optuna re-optimization landing in a different local minimum on the 14-column loss surface, (b) regime favorability in the OOS window, (c) ensemble noise. NOT a CONFIRMATION-bundle candidate.

## Recommendations to QR

1. **iter-v3/016 axis MANDATORY = LightGBM → XGBoost head-to-head** on iter-v3/013's 13-feature stack (drop `tbr_zscore_30` as INERT). Single-axis variation. Pre-committed per QR Clarification 3 disposition + new memory rule `feedback_v3_iter016_xgboost_mandate.md`.

2. **iter-v3/015 catalog row** must capture: subtype `EXPLORATION-NEGATIVE-no-effect` (NOT PROMISING-INERT); IS Sharpe Δ-0.36 (outside §4.4 band by 7× band-width); trade-count reduction 209→205 (non-bit-identical, distinguishes from iter-v3/012); per-symbol importance rank 14/14 across all 3 syms; NEW feature axis category 1 first attempted; 8 high-PBO cells with 2 new at OOS frontier (LDO 2026-05, BCH 2024-01).

3. **iter-v3/016 first commit must**:
   (a) Drop `tbr_zscore_30` from `V3_FEATURE_COLUMNS` (back to 13) — restore iter-v3/013 baseline before XGBoost integration. ITERATION_LABEL "v3-016".
   (b) Add `tbr_raw` to `V3_NON_FEATURE_COLUMNS` (low-priority hygiene from Clar. 4).
   (c) Fix `_write_feature_importance` at `run_baseline_v3.py:1110-1151` — either aggregate properly across all (sym, month) models, OR rename outputs to clarify single-symbol single-month scope. The QE-discovered defect must not propagate.
   (d) Add XGBoost as a runner-selectable model alternative (likely a `--model xgboost` flag or a parallel runner file). Match LightGBM's hyperparam search budget per Optuna config.

4. **Brief template fix for iter-v3/016+**: §4.3 (verbatim Falsifier rules) and §4.4 (outcome interpretation table) must be reconciled — they cannot present conflicting classification pathways. The QR pre-flights both sections together at brief-authoring time and runs a logic-consistency check.

## Methodology Verdict

OVERALL = **EXPLORATION-NEGATIVE-no-effect**. All 12 checks PASS / WAIVED-INFORMATIONAL per EXPLORATION carve-out. Methodology is clean. Classification flip (QE PROMISING-INERT → Critic+QR NEGATIVE-no-effect) preserves catalog discipline. No CONFIRMATION-bundle candidate produced; iter-v3/016 axis pre-committed to NEW model architecture (XGBoost head-to-head).
