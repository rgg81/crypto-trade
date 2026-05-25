# Phase 7.5 Critic Review — iter-v1/012

OVERALL: EXPLORATION-NEGATIVE — basin substrate REFUTED (F7=32.71% PARTIAL just 2.71pp above SEED-LOCKED threshold); OOS regresses from /011 +1.07 → +0.94 below +1.0 floor; F3 catastrophic-basin-shift class fires (IS Δ +0.52); engineering report missing in violation of Critic Rec #3 to /011; Section 8.1 matrix gap leaves observed cell unregistered

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-2 position 7/10; ≤2h wall-clock cap)

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

src/ diff for /012 is exclusively the `--ensemble-seeds-offset` flag wiring (run_baseline_v1.py `_derive_ensemble_seeds(size, offset=0)`; CLI; `_r5_kwargs` propagation to all 4 models). Foundation re-audit: `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` (iter-v3/057 fix). `labeling.py` σ_t past-only via `vol_natr_14`. `validation_v1.REQUIRED_GAP = (21+1)×5 = 110` matches V1_BASELINE_UNIVERSE × (timeout_candles+1).

All 4 mandated regression tests present in `tests/test_lookahead_embargo.py`. LightGBM scale-invariant; no scalers. No `fit_transform(combined)` patterns in v1.

### Check 2 — Embargo Width: PASS

label_timeout_minutes=10080 (7d) / 8h candles → 21 candles + 1 = 22 × 5 symbols = REQUIRED_GAP=110. Same helper feeds CV gap. Symmetric application verified. Unchanged from /008-/012.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)

DSR_IS=-43.83, DSR_OOS=-25.42, PSR_monthly_vs_0=0.935/0.934, PSR_monthly_vs_1=0.398/0.654, n_eff=13, n_trials=35. 12th-consecutive iteration at n_eff=13 architectural ceiling. PBO=null (CPCV not wired). PSR_monthly_vs_1 OOS 0.654 below 0.95 merge threshold.

Per skill, Check 3 axis FAILs at EXPLORATION are informational, NOT BLOCK-triggering. Recording for catalog continuity.

### Check 4 — IC Correlation: PASS (vacuous)

No new feature families. `ic_matrix.csv` byte-identical to /011. Pre-existing carry-over from /002 unchanged.

### Check 5 — ADF Stationarity: PASS

Feature set bit-identical to /011; ADF results carry forward. 40 features active in V1_FEATURE_COLUMNS_PRUNED.

### Check 6 — Pareto Dominance: N/A

EXPLORATION single-seed-window. 10-seed Pareto front is CONFIRMATION-only.

### Check 7 — Reproducibility: PASS

HEAD `538ff1c` resolvable. Explicit `feature_columns=active_feature_columns`. Ensemble seeds `[789, 1001, 2002]` literal. OOF parquet iter-stamped. A7 unlink guard active. Spot-check on trades.csv row 2 reproduces net_pnl_pct within rounding.

### Check 8 — Hypothesis-Implementation Alignment: FAIL

**Code-vs-brief**: PASS. `git diff iteration-v1/011..iteration-v1/012 -- src/` empty (only run_baseline_v1.py touched). Matches brief Section 3.1.

**Brief-vs-reality**: FAIL on three documented commitments.

1. **Engineering report MISSING.** Brief Section 3.5 (Critic /011 Rec #3 ADOPTED) explicitly stated "orchestrator hard-rejects Phase 7.5 dispatch without it". Section 10.2 Deliverable #4 reiterated. Neither `briefs-v1/iteration_v1-012/engineering_report.md` nor `reports-v1/iteration_v1-012/engineering_report.md` exists. Process-integrity violation of a Critic recommendation carried forward.

2. **F6/F7 artifact filename mismatch.** Brief Section 10.2 #3 committed to `f6_roster_overlap.csv`; actual committed artifact is `f7_roster_overlap.csv`. Content correct; name doesn't match brief. Cosmetic but inconsistent.

3. **Section 8.1 verdict-matrix GAP.** Observed cell (F1≥+0.05, F3≥+0.30, F7∈[30%, 70%]) NOT pre-registered. Row 1 requires F7>70%; Row 2 requires F3∈[+0.10, +0.30); other rows fail various dimensions. Brief's "no discretion at verdict time" promise breaks.

### Check 13 — Anti-Pattern Static Scan: PASS

A1/A2/A3/A4/A5/A6/A7/A8/A9/A10/A11/A12/A13 all PASS. Zero unexplained matches.

### Check 14 — Axis Family Validation: PASS-WITH-NOTE

`methodology-substrate-test` (NEW 8th family). Prior 5 EXPLORATIONs: feature-family (×2), methodology, risk-primitive (×2) — no saturation. Structurally orthogonal accepted.

**NOTE (process-integrity flag, not verdict-binding)**: 8 families in 12 iterations risks structurally circumventing Axis Rotation Discipline. Future NEW family declarations should require Critic + LM Master + QR 3-way convergence on orthogonality, not just QR self-declaration.

## Verdict Synthesis

- **OOS Sharpe +0.9363**: regression from /011's +1.0709 (Δ -0.13), **below +1.0 absolute merge floor** per `feedback_sharpe_floor.md`
- **F1 OOS Δ +0.27**: passes +0.05 PROMISING threshold but regresses from /011's +0.41
- **F3 IS Δ +0.52**: fires catastrophic-basin-shift class (>+0.30); same magnitude as /010/011 (~+0.48). Substrate-magnitude IS preserved across seed windows.
- **F7 LTC IS overlap = 32.71%**: PARTIAL DISSOLUTION — only 35/107 LTC IS trades survive seed window shift. LM Master Phase 4.5 P(F7>70%)=0.55 REFUTED.
- **DOT catastrophic reversal**: raw net PnL -210.85 swing between seed windows; basin has multiple local minima of comparable depth
- **Engineering report missing**: process-integrity violation; orchestrator-side hard-reject not enforced
- **Section 8.1 matrix gap**: brief's "no discretion at verdict time" promise breaks at the verdict moment

LM Master proposed `PARTIAL-DISSOLUTION-WITH-SUBSTRATE-MAGNITUDE-PRESERVATION` as new subtype. I endorse for future briefs Section 8 pre-registration but NOT as retroactive verdict-class for /012 (would be the discretion the brief promised to avoid). /012 verdict-class falls under nearest-spirit `BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP-PARTIAL`.

Final verdict: **EXPLORATION-NEGATIVE** subtype `BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP-PARTIAL`. Not BLOCK-PENDING-FIX (issue is process/discipline not backtest defect). Not BLOCK-FINAL (process lessons forward-looking, not iteration-corrupting).

## Recommendations to QR (process-level for FUTURE iterations)

1. **Section 8 verdict-matrix completeness audit at Phase 5.5.** Add checklist item: "verify Section 8.1 verdict-matrix exhaustively covers F1×F3×F7 cross-product. List every cell, including boundary cells." LM Master + Critic Phase 6.0 should both have flagged this gap; codifying audit at Phase 5.5 catches before compute is spent.

2. **Engineering report hard-reject enforcement.** Brief Section 3.5 Rec #3 stated "orchestrator hard-rejects Phase 7.5 dispatch without it". Orchestrator did NOT enforce. Codify hard-reject in `quant-engineer-v1` skill at Phase 6 closeout (file existence check) AND orchestrator Phase 7.5 dispatch precondition.

3. **Axis-family taxonomy extension discipline.** /012 added 8th family in 12 iterations. Future NEW family proposals should require Critic + LM Master + QR 3-way convergence on orthogonality (with explicit comparison to nearest existing family), not just QR Section 0.6 self-declaration. Add Critic Phase 6.0 axis-family veto path for novel-taxonomy iterations.

## Path Forward (mandatory on EXPLORATION-NEGATIVE)

Prior 5 EXPLORATIONs (excluding /012): /007 feature-family, /008 methodology, /009 feature-family, /010 risk-primitive, /011 risk-primitive. No saturation. UNUSED families: labeling, universe, model-arch, hyperparameter-region.

LM Master Phase 7.4 §7 recommends adhering to pre-registered /013 = offset=6 [3003, 4004, 5005] rule (substrate-test continuity, NOT new family). Critic weakly prefers Option 1 for catalog discipline.

**Option 1 — /013 = ENSEMBLE_SEEDS offset=6 [3003, 4004, 5005], R5-BINARY-KILL config BIT-IDENTICAL** (family `methodology-substrate-test`, 3rd consecutive). PRE-REGISTERED by LM Master + brief Section 11. With 3 seed-window samples, can compute Optuna-objective magnitude variance properly. IS-Δ predicted +0.48 ± 0.10 (substrate-property TESTABLE FALSIFIER); LTC IS roster overlap with /011 AND /012 predicted [15%, 40%] (seed-property TESTABLE FALSIFIER). /013 outcome conditional pre-commits /015 axis: F1 ≥ +0.05 → /015 = R5-BINARY-KILL CONFIRMATION; F1 ≤ 0 → /015 = UNUSED-family CONFIRMATION.

**Option 2 — /013 = LABELING axis (triple-barrier σ_t source: fixed-fraction ATR → past-only EWMA σ_t-scaled barriers, 14d window)** (family `labeling`, UNUSED in cycle-2). Critic /011 Path Forward Option 2 + LM Master Phase 4.5 §6 referenced. Highest-prior basin-escape probability (~60-70%). Changes IS label distribution per cell → different LightGBM loss surface. HIGH-RISK declaration required.

**Option 3 — /013 = METHODOLOGY axis (per-cell early-stop with inner hold-out)** (family `methodology`, UNUSED since /008). Diagnostic infrastructure; non-compoundable. Critic /011 Path Forward Option 1.

Critic adversarial recommendation: **Option 1 (offset=6) IF pre-registration discipline binding; Option 2 (labeling) IF cycle-2 catalog needs structural-axis breakout AND QR declares HIGH-RISK**. Weakly prefer Option 1 for LM Master argument that 3-sample variance is high-information at EXPLORATION budget.

## BLOCK-PENDING-FIX Rerun Protocol

N/A — verdict is EXPLORATION-NEGATIVE. Defects (missing engineering report, F6/F7 filename mismatch, matrix gap) are forward-looking process-discipline lessons, not backtest defects requiring re-run. /012 closed as EXPLORATION-NEGATIVE BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP-PARTIAL; /013 advances per Path Forward.
