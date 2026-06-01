# Phase 7.5 Critic Review — iter-v1/042

OVERALL: BLOCK-PENDING-FIX — Phase 7.4 Regime Attribution Table missing; `regime_attribution.csv` not authored; Check 3c MANDATORY artifact absent under new methodology.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-5 EXP-9/10; axis = MODEL-ARCH library swap LightGBM → XGBoost)

## Headline Observations (per-regime NOT aggregate per new methodology)

- IS Sharpe **+0.7438** (Δ vs baseline **+0.4609**) — large IS lift, but...
- IS MaxDD **97.20%** (vs baseline 73.06%) — **catastrophic IS drawdown inflation** that the brief's F-AXIS #7 only audited on OOS. Baseline IS MaxDD 73.06% → /042 IS MaxDD 97.20% = **+24.14pp inflation IN-SAMPLE**. F-AXIS #7 was scoped OOS-only; IS-side concentration amplification was not pre-registered, but it is the load-bearing evidence that the IS lift is driven by per-trade-weight concentration NOT by signal quality. The OOS MaxDD 42.45% only barely clears the +1.5× bar (42.45/40.94 = 1.037×) — but the IS side is the alarm.
- OOS Sharpe **+0.4011** (Δ vs baseline **−0.2626**) — within the [-0.45, -0.10] NEG-CLEAN band per brief Section 11.6.
- F-AXIS #5 Jaccard = **0.0897** vs LightGBM anchor — **BASIN-RELOCATION-ARTIFACT confirmed**. Per brief Section 4 F-AXIS #5 wording: "Jaccard < 0.10 → BASIN-RELOCATION-ARTIFACT (per /039 pattern at 0.0878); the library swap relocated the basin completely, dissolving the mechanism story regardless of F1 magnitude." 0.0897 < 0.10 → F-AXIS #5 explicit FAIL.
- Per-symbol OOS PnL share: BTC = **−61.69%** (catastrophic drag, single largest loser), LINK = **+82.83%** (single largest contributor). No regime tagging → Check 3c cannot decompose this.

## QR Response Considered (Round 2)

No Round 1 clarifications were raised — this is a single-pass review at the user's direction. The Round-2 disposition section is therefore N/A; verdict resolves on artifact state alone.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
`walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` (foundation regression intact). XGBoost training reuses the same `generate_monthly_splits` walk-forward as LightGBM — no parallel training-boundary code path. Labels, embargo, master-data-extent invariance all inherited. No new feature engineering. `tests/test_lookahead_embargo.py` present with the 4 expected regression tests; the iter-v1/042 dispatch test file also includes a walk-forward embargo regression test (T15). No leakage path detected.

### Check 2 — Embargo Width: PASS
Embargo width centralized via `compute_embargo_candles(label_timeout_minutes=10080, interval_minutes=480) × n_symbols = 22 × 5 = 110` candles for the 5-symbol baseline universe. No iteration-specific override; inherits the foundation-corrected value.

### Check 3a — DSR/PSR (methodology, INFORMATIONAL at EXPLORATION): FLAG
DSR_OOS = **0.0** (floored from negative); PSR_monthly_vs_0_OOS = **0.6393**; n_trials=18 below conventional DSR convergence threshold (~30). Per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode DSR/PSR are STRUCTURAL ARTIFACTS at sub-CONFIRMATION trial budget — INFORMATIONAL ONLY, not BLOCK-triggering. Recorded; not gating.

### Check 3b — PBO (selection-bias, INFORMATIONAL at EXPLORATION): FLAG
PBO = **null** in `out_of_sample/dsr.json` — CSCV not computable at single-seed EXPLORATION budget. INFORMATIONAL only; SKIPPED for EXPLORATION verdict per closeout checklist row "Check 3b — PBO: EXPLORATION: SKIP".

### Check 3c — Regime Attribution Clarity (MANDATORY, EXPLORATION+CONFIRMATION): **FAIL**
**This is the BLOCK-PENDING-FIX trigger.** The new methodology mandates:
- LM Master Phase 7.4 emits a Regime Attribution Table tagging IS+OOS months by regime AND computing per-regime metrics for THIS iter AND BASELINE_V1.
- QE Phase 6 deliverable: `reports-v1/iteration_v1-042/regime_attribution.csv` per closeout-checklist schema.
- One-time `briefs-v1/_meta/baseline_seed_regime_matrix.csv` + `briefs-v1/_meta/regime_catalog.md` to source σ_R.

Observed state:
- `briefs-v1/iteration_v1-042/lgbm_advisor.md` contains ONLY the Phase 4.5 section (lines 1-86). NO Phase 7.4 appended. NO Item-0 Regime Attribution Table.
- `reports-v1/iteration_v1-042/regime_attribution.csv` — **does not exist** (Glob confirms; only `comparison.csv`, `per_symbol.csv`, `per_regime.csv` present).
- `reports-v1/iteration_v1-042/in_sample/per_regime.csv` has a SINGLE row tagged `regime=unknown` (sharpe=0.0388 IS, sharpe=0.0340 OOS); no decomposition into bull/alt-rotation/chop/bear/vol-spike/etc.
- `briefs-v1/_meta/baseline_seed_regime_matrix.csv` does **not exist**; `briefs-v1/_meta/regime_catalog.md` does **not exist** (Glob confirms zero files matching `briefs-v1/_meta/baseline*` or `briefs-v1/_meta/regime_catalog.md`).

Per closeout-checklist row "Check 3c MANDATORY both EXP+CONF — BLOCK-PENDING-FIX if table missing or rows incoherent" → **FAIL**. The 9-band regime-aware verdict cannot be resolved (every band 1-8 in the decision tree references `Δ ≥ +σ_R` or `Δ ≤ −σ_R` thresholds requiring `baseline_seed_regime_matrix.csv` which does not exist; band 9 WALK-FORWARD-LEAKAGE is not active per Check 1 PASS). The decision tree is degenerate without the regime decomposition.

### Check 3d — BUNDLE-level per-regime Pareto-dominance vs BASELINE_V1: EXEMPT
iter-v1/042 is a COMPONENT EXPLORATION (single-axis library swap, not a bundle assembly). Per closeout-checklist row "Check 3d — BUNDLE-CONFIRMATION-only. EXPLORATIONs + component-CONFIRMATIONs EXEMPT" → EXEMPT.

### Check 4 — IC Correlation Between Feature Families: PASS
No new feature added in /042 (pure library swap). IC matrix carried forward from /040 feature stack. Critical pairs above 0.7 thresholds (`momentum × volume` = 0.738, `momentum × trend` = 0.718, `trend × volume` = 0.695) all carry forward from V1_FEATURE_COLUMNS_PRUNED — not introduced by this iteration. NEUTRAL on the axis under review.

### Check 5 — ADF Stationarity: PASS (with non-blocking caveat)
44 features in V1_FEATURE_COLUMNS_PRUNED carried forward; the populated ADF rows in `in_sample/adf_test.csv` (the rows with `n_obs > 0`) all show `p_value_raw = 0.0` and `bonferroni_pass=True` for the active features. The many empty/NaN rows correspond to features in the full v1 universe NOT in V1_FEATURE_COLUMNS_PRUNED (placeholder rows from the reporting layer). The active 44 cols are all stationary. PASS.

### Check 6 — Pareto Dominance: NOT-APPLICABLE
Single-seed=42 EXPLORATION. No 10-seed Pareto front to evaluate. Per v1 EXPLORATION discipline + closeout-checklist, Pareto evaluation is deferred to CONFIRMATION at /044+. NEUTRAL.

### Check 7 — Reproducibility: PASS
Brief Section 10.2 declares single outer seed=42 + ENSEMBLE_SIZE=3 inner (42, 123, 456) + XGBoost `n_jobs=1` + `random_state=outer_seed` + Optuna TPE `random_state=outer_seed`. Brief Section 11.7 pins `xgboost>=2.0,<3.0`. `run_baseline_v1.py:4471` carries the explicit `iteration_label == "v1-042"` dispatch and `XgboostStrategy` instantiation at lines 4543/4592/4641/4690. Bit-determinism contract honored per `feedback_deterministic_trade_match.md`.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 1 H1 hypothesis: "substituting XGBoost (depth-wise + `tree_method='hist'` + no GOSS) for LightGBM at constant data/labels/features/risk-gates pipeline". `git grep` confirms: `XgboostStrategy` is imported (`run_baseline_v1.py:107`); 4-cohort instantiation matches the brief's 4-model spec (A/C/D/E); all other parameters identical to baseline. No scope creep, no hypothesis-faking. Pre-flight asserts (lines 4481+) enforce `--model xgboost`. Wiring proof F-AXIS #2 documented in critic_preflight.md Check C.

### Check 13 — Anti-Pattern Static Scan (A1-A14): PASS
- A1 (`train_end_ms = test_start_ms` without subtraction): zero raw-assignment matches in src/; only legitimate `train_end_ms = test_start_ms - embargo_ms` at `walk_forward.py:113` and `cross_sectional.py:1325/1345`. Foundation regression intact.
- A2-A14: zero unexplained matches. Cross-track imports clean (no `features_v2/v3` imports in v1 code paths).

### Check 14 — Axis Family Validation (v1-only): PASS
Brief Section 0.6 declares FAMILY=`model-arch` REPEAT (counter 3/5 v1-wide). Prior 5 EXPLORATIONs going into /042 enumerated: /037 loss-function, /038 risk-primitive, /039 hybrid, /040 feature-family, /041 labeling — NONE are model-arch. Last model-arch use at /024 (18 iters ago); monoculture rule (5+ consecutive same-family) NOT armed. src/ diff matches: ONLY library swap (no feature/label/universe/risk-gate change). Mechanism orthogonality from /003 (cohort split) and /024 (regime sub-models) verified — /042 is a pure-library substitution at constant scaffolding.

## Regime Attribution Table Summary

**ABSENT.** No `briefs-v1/iteration_v1-042/lgbm_advisor.md` Phase 7.4 section. No `regime_attribution.csv`. `per_regime.csv` has only `regime=unknown`. Without this artifact, the diary cannot populate the per-regime comparison table mandated by the closeout-checklist QR mandate.

Per the new methodology, the natural verdict band for /042 absent the missing artifact would likely have been **REGIME-SPECIALIST-IS** (IS Δ ≥ +0.10 satisfied at +0.4609; OOS Δ at −0.2626 is OUTSIDE the +/−σ_R noise band band 2 requires "[−σ_R, +σ_R]" — without σ_R available, this cannot be definitively classified) OR **LEARNED-NEG** if mechanism congruence is broken (F-AXIS #5 Jaccard FAIL at 0.0897 < 0.10 + IS MaxDD inflation +24pp suggest the IS lift is basin-lottery, not signal-bearing). The artifact absence prevents discrimination between these two bands — which is precisely why Check 3c is BLOCK-PENDING-FIX.

## Observed Results — Per-Symbol (per-regime unavailable)

| Symbol | OOS Trades | OOS Win-Rate | OOS Net PnL % | OOS Share | vs baseline OOS share |
|---|---|---|---|---|---|
| BTC | 51 | 29.4% | −26.85% | −61.69% | 133.38% → −61.69% (catastrophic regression) |
| ETH | 44 | 43.2% | +13.94% | +32.01% | 11.08% → +32.01% (lifted) |
| LINK | 40 | 52.5% | +36.06% | +82.83% | 137.66% → +82.83% (regressed; was top contributor) |
| LTC | 48 | 43.8% | +7.57% | +17.40% | −189.99% → +17.40% (LTC catastrophic flip POSITIVE — this is the IS-lift artifact) |
| DOT | 41 | 43.9% | +12.82% | +29.45% | 7.88% → +29.45% (lifted) |

Per-symbol structure: LTC IS PnL went from baseline LTC IS = +3.27% → /042 LTC IS = **+160.33%** — that 49× LTC IS PnL inflation is the dominant signature. XGBoost's depth-wise + no-GOSS at single-seed surfaced a basin where the model dramatically over-attributes to LTC in IS. The Jaccard 0.0897 confirms this basin is **disjoint** from the LightGBM baseline. F-AXIS #5 explicit FAIL.

Without regime tagging, we cannot determine whether this LTC over-attribution clusters in a specific market regime (alt-rotation? chop?) — and that is the load-bearing decision the bundle composition for /044 needs to make.

## Path Forward

The current iteration cannot resolve verdict without Phase 7.4 Regime Attribution Table + `regime_attribution.csv` + `baseline_seed_regime_matrix.csv`. Per BLOCK-PENDING-FIX Rerun Protocol:

### BLOCK-PENDING-FIX Rerun Protocol

- **Specific defect**: Phase 7.4 LM Master post-mortem not appended to `briefs-v1/iteration_v1-042/lgbm_advisor.md`; Item-0 Regime Attribution Table absent; `reports-v1/iteration_v1-042/regime_attribution.csv` not authored; foundational `briefs-v1/_meta/baseline_seed_regime_matrix.csv` + `briefs-v1/_meta/regime_catalog.md` not yet bootstrapped (this is the FIRST closeout under new methodology; bootstrap is owed).
- **Required fix** (multi-part, but isolated to artifact generation; no code/data re-run):
  1. Bootstrap `briefs-v1/_meta/regime_catalog.md` with canonical regime tag definitions (BTC 90-day return quantile × 30-day realized vol quantile per skill §"Merge Principle — Relative Regime Pareto-Dominance"). One-time deliverable owed at this iteration per closeout-checklist §"Operational artifacts to author at /044 (and maintain thereafter)" — author it now at /042 since this is the first iteration under new methodology.
  2. Bootstrap `briefs-v1/_meta/baseline_seed_regime_matrix.csv` from the existing 5-seed baseline run at `reports-v1/iteration_v1-baseline/` — per-regime per-seed Sharpe / max_dd / trade_count for BASELINE_V1 across the 9 canonical regimes. One-time deliverable owed.
  3. Author `reports-v1/iteration_v1-042/regime_attribution.csv` per the closeout-checklist schema: `regime_tag, in_sample, candidate_sharpe, candidate_max_dd, candidate_trade_count, baseline_sharpe, baseline_max_dd, baseline_trade_count`. Use the same regime tagger from step 1 on the existing trades.csv.
  4. Append Phase 7.4 section to `briefs-v1/iteration_v1-042/lgbm_advisor.md` with Item-0 Regime Attribution Table (20-column schema per closeout-checklist) + Items 1-7 (importance triage, HP stability, gain concentration, suspicious patterns, next-iter tuning, Phase 4.5 predictions vs outcome, closing note).
- **Re-eval scope**: After artifacts are authored and committed, Critic performs single-pass re-evaluation focused on Check 3c only. Other PASS checks carry forward. Check 14 (Axis Family) re-validates against the new artifacts. The backtest itself is NOT re-run — this is an artifact-generation defect, not a code/data defect.
- **Final verdict after rerun**: ∈ {**REGIME-SPECIALIST-IS** (most likely if regime decomposition shows clean within-regime edge in bull or alt-rotation IS regimes with OOS within σ_R), **LEARNED-NEG** (if Jaccard 0.0897 + IS MaxDD inflation + per-symbol LTC over-attribution combine with regime decomposition showing mechanism falsification), **TAIL-CONTROL** (unlikely; OOS MaxDD barely below baseline), or **BLOCK-FINAL** (if regime decomposition is internally incoherent / per-regime PnL does not sum to bundle PnL ±2%)}.

### Path Forward — Alternative Axes (constructive Critic mandate)

For /043 (cycle-5 EXP 10/10, the LAST cycle-5 EXPLORATION before /044 CONFIRMATION) — proposals from families NOT among the prior 5 EXPLORATIONs (/037 loss-function, /038 risk-primitive, /039 hybrid, /040 feature-family, /041 labeling):

1. **Cross-symbol-correlation gate** — family `risk-primitive` (REPEAT but DIFFERENT mechanism class from /038's per-symbol vol ceiling). Add stateless gate that filters trades when BTC×LTC corr_30 > 0.85 (motivated by /024 cross-cohort overlap evidence + the /042 BTC catastrophic OOS regression sign that BTC and LTC may be in highly-correlated chop). Falsifier: OOS Sharpe Δ < −0.20 OR R5-fire-rate > 30% OR no symbol PnL reshape.
2. **Conformal prediction calibration** — family `methodology-pivot` (UNTOUCHED in v1 cycle-5). Replace XGBoost/LightGBM confidence_threshold tuning with conformal prediction intervals at α=0.05; turns basin-stability gain into a calibrated confidence interval. Mechanism orthogonal to all prior 5 families. Falsifier: per-month coverage rate outside [0.92, 0.98] AND OOS trade count < 130.
3. **Sample-weight isolation refresh at multi-seed** — family `model-arch` REPEAT under HIGH-RISK declaration; revisits /031's PROMISING-BASIN-RELOCATION-ARTIFACT outcome at 3-seed ENSEMBLE_SIZE budget. Not a knob-tuning re-attempt; tests whether basin-relocation is mechanism-stable across seeds when isolated to the sample-weight axis at constant feature/labeling stack. HIGH-RISK pre-commit to CONFIRMATION at /045 if PROMISING.

For /044 CONFIRMATION bundle composition (if /042 resolves REGIME-SPECIALIST-IS post-rerun):
- /042 candidate role: **IS-regime specialist for bull/alt-rotation IS regimes** (subject to regime decomposition outcome). Off-regime exclusion candidate for OOS-dominant regimes (recovery/post-bear) where Jaccard 0.0897 indicates the XGBoost basin is structurally different from LightGBM and the OOS regime mix favored LightGBM. Component substitution test at /044 must show /042's XGBoost contributes within-regime Pareto-positive on at least one regime where the baseline ties or loses.

## Closing Note

The methodology-integrity gates (Checks 1, 2, 7, 8, 13, 14) all PASS — this is NOT a leakage iteration. The walk-forward fix and XGBoost wiring are clean. The verdict suspension is **purely a missing-artifact issue** under the new methodology. Under the OLD framework this iteration would have been verdicted on aggregate OOS Δ alone (−0.26 OOS Δ → LEARNED-NEG band) — but per `feedback_is_oos_divergence_is_regime_not_overfit.md` and the new closeout-checklist mandate, IS-strong/OOS-modest with no regime attribution is precisely the case that REQUIRES regime decomposition before verdict, NOT after. This is the first closeout under the new skill; the bootstrap artifacts (`baseline_seed_regime_matrix.csv`, `regime_catalog.md`) are also owed at this iteration. Single-pass rerun authorized.
