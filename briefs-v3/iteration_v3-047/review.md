# Phase 7.5 Critic Review — iter-v3/047

OVERALL: **EXPLORATION-NEGATIVE** — multi-run-stochasticity-contaminated; PATH C fires on bundle-regression criterion (OOS Δ -2.36 < -0.20 threshold). Falsifiers 2 (BCH SHORT non-bit-identical) + 3 (LDO/TRX/ALGO non-bit-identical) fired as written; per QR A1 the LOCKED Section 8 thresholds are non-renegotiable.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle 3 #8 of 10)

## QR Response Considered (Round 2)

1. **Falsifier-renegotiation (A1)** → QR holds the LOCKED Section 8 thresholds. PATH C fires on pre-registered wording. The QE's "stochastic drift vs dispatch drift" distinction is forensic refinement (diary memory rule), NOT a carve-out. Verdict path resolved: PATH C — NEGATIVE-multi-run-stochasticity-contaminated subtype.
2. **Verdict-reliability (A2)** → QR confirms iter-v3/047 IS a valid NEGATIVE catalog row (NOT UNINTERPRETABLE/INVALID-RUN). PATH C fires unambiguously on pre-registered thresholds. Cycle cadence count preserved (#8 of 10).
3. **BCH-only restricted scope (A3)** → QR: NO new classification subtype. `feedback_promising_mechanical_subtype.md` requires bit-identical non-target rosters; that test failed. The 5 pre-registered Outcomes exhaust the classification space. Sub-classified as Outcome C "NEGATIVE-bundle-regression" + Outcome C "NEGATIVE-architecture-bug".
4. **iter-v3/048 disposition (A4)** → QR: NO re-run (peeking-at-OOS violation per `feedback_no_cheating.md`); accept-NEGATIVE; iter-v3/048 = NEW EXPLORATION axis (cycle 3 #9 of 10), QR-EDA-driven; iter-v3/050 CONFIRMATION carries primitive 10 forward as candidate bundle ingredient on IS-only basis. Resolves Critic uncertainty around primitive 10 fate.
5. **OOF parquet engineering fix (A5)** → QR endorses fail-loud check + `--clean-oof` flag at `optimization.py:423-428`, lands BEFORE iter-v3/048 setup as guardrail commit (does NOT violate cadence discipline). Resolves the "n_trials=700 vs true 140" reproducibility hazard for all future iterations.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
No new feature engineering in iter-v3/047. The setup commit (SHA `9b1293d`) added primitive 10 (`block_long_for` / `block_short_for` config fields + `RiskV3Wrapper.get_signal` extension) downstream of model inference (`risk_v3.py:279` fires AFTER `super().get_signal`), and reverted the iter-v3/046 BCH ATR (pre-commit SHA `f5f0fd6`). No feature computation chain is touched. REQUIRED_GAP=88=(21+1)×4 unchanged. Look-ahead surface unchanged from iter-v3/045 anchor.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP = 88 candles = (timeout_candles 21 + 1) × n_symbols 4. timeout = 7 days × 3 candles/day at 8h = 21 candles. Lopez de Prado purge formula correctly applied in `validation_v3.py`. No changes to gap parameters in iter-v3/047 per engineering report Label-Leakage Audit. PASS unchanged from iter-v3/045.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)
DSR computation contaminated by OOF parquet 5x duplication. n_trials=700 reported in `dsr.json` and `comparison.csv` vs true single-run n_trials=140 (4 symbols × 35 trials). PBO=0.0939 (PASS, computed from CPCV paths NOT affected by OOF duplication). PSR=1.000 (PASS, same). However n_trials=700 inflates the E[max_SR] denominator in DSR computation, mechanically depressing DSR — value as reported is unreliable. Per `feedback_v3_dsr_mode_artifact.md` this iteration is EXPLORATION-mode (single-seed n_trials=35) so DSR is INFORMATIONAL ONLY and does NOT trigger BLOCK. Critical engineering deficit: the OOF parquet append-on-existing behavior (`optimization.py:423-426`) is a cross-iteration reproducibility hazard (QR A5 fix endorsed).

### Check 4 — IC Correlation: PASS
No NEW features added in iter-v3/047. Feature stack = 14 features unchanged from iter-v3/045 (per Section 3 bundle state verification). primitive 10 is a SIGNAL-FILTER layer downstream of model inference; feature importance per se does not change. IC matrix not regenerated (no new feature family → not required).

### Check 5 — ADF Stationarity: PASS
Feature subspace unchanged from iter-v3/045 (14-D Mahalanobis space identical per Section 5). ADF re-test not required for this iteration.

### Check 6 — Pareto Dominance: N/A (single-seed EXPLORATION)
Single outer seed=42, ENSEMBLE_SIZE=5 per EXPLORATION-spec. Pareto-front analysis is reserved for CONFIRMATION multi-seed runs. Per `feedback_v3_outer_seed_cap_2_v3.md` and `feedback_v3_strict_10_to_1_cadence.md`, single-seed EXPLORATION verdicts are pre-registered classification path-fires (PATH A/B/C), not Pareto-dominance gates.

### Check 7 — Reproducibility: FAIL
Three reproducibility deficits identified:
1. **OOF parquet 5x duplication** (`trial_oof_returns.parquet` 55.78M rows = 5× expected ~11M; 44.6M dup rows confirmed). Engineering report attributes to 5 backtest re-runs without clearing. The runner's append-on-existing behavior (`optimization.py:423-426`) accumulates cross-run state. Per QR A5 the engineering fix is endorsed and lands BEFORE iter-v3/048 setup as a guardrail commit.
2. **LightGBM OpenMP non-determinism**: even at fixed seed=42, `model = lgb.LGBMClassifier(random_state=seed)` (`optimization.py:287`) does NOT seed LightGBM C++ OpenMP thread scheduling. Each fresh process invocation produces modestly different ALGO/LDO/TRX model weights → roster drift. The frozen-baseline pattern (`feedback_v3_single_seed_frozen_baseline.md`) was established within single-run comparisons (iter-v3/020/021/022), NOT across separate process invocations. Memory rule needs qualifier (per QR A5: "applies only to single-process-invocation comparisons").
3. **No run.log present** for iter-v3/047. Gate fire counts derived from trades.csv direction analysis (acceptable for primitive 10 verification, sub-optimal for general audit).

These three deficits explain Falsifiers 2 + 3 firing without primitive 10 dispatch error: the cause is NOT cross-symbol contagion but cross-run stochasticity. Verdict path is unchanged (PATH C fires per locked thresholds), but root-cause attribution matters for iter-v3/048 design (QR A4(b)+(c)).

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 1 hypothesis: "primitive 10 (direction-asymmetric kill switch) with `block_long_for=("BCHUSDT",)` suppresses ALL BCH LONG candidate signals". Engineering report confirms: BCH LONG IS 39 → 0 (100%), OOS 21 → 0 (100%); zero leakage; no false positives on SHORTs. Setup commit `9b1293d` implements per Section 3 sub-fixes 1-7 (RiskV2Config fields, GateStats counter, RiskV3Wrapper.get_signal extension, 7 adversarial tests, runner config, _verify_feature_columns assertion, ATR revert). Pre-commit revert `f5f0fd6` honors orchestrator + Critic FINAL `5dae6d6` mandate. Hypothesis-implementation alignment clean.

## Optional Checks (9-12)

### Check 9 — Symbol Exclusion Enforcement: PASS
V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT, ALGOUSDT) — 4 symbols UNCHANGED from iter-v3/045. V3_EXCLUDED_SYMBOLS audit per runner _verify_feature_columns confirms only BCH carries `block_long_for=("BCHUSDT",)`; ALGO/LDO/TRX configs verified empty.

### Check 10 — Feature Isolation Enforcement: N/A
No cross-track imports introduced in iter-v3/047 (no feature changes).

### Check 11 — Forming-Candle Audit: N/A
Data ingest unchanged from iter-v3/045.

### Check 12 — Library Version Pinning: PASS
Section 9 stack identical to iter-v3/045/046 (lightgbm 4.6.0, numpy 2.2.6, optuna 4.8.0, pandas 3.0.0, pyarrow 23.0.1, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6). No version drift.

## Lessons Refined

### Single-seed frozen-baseline assumption is single-process-invocation-only
Per `feedback_v3_single_seed_frozen_baseline.md`, single-seed=42 EXPLORATIONs were observed to produce bit-identical non-target symbol OOS rosters at iter-v3/020/021/022. iter-v3/047 reveals this assumption holds ONLY within single-process-invocation comparisons — re-running the backtest 5× from a fresh process produces 5 modestly different ALGO/LDO/TRX rosters (LightGBM OpenMP non-determinism not seeded by `random_state=seed`). Cross-process bit-identity is NOT guaranteed at single-seed=42. The CONFIRMATION multi-seed run remains the canonical test of any single-seed EXPLORATION result.

### Direction-asymmetric kill switch (primitive 10) IS-validated, OOS-untested at single-seed
BCH LONG suppression worked correctly (39 IS + 21 OOS blocked, zero leakage). BCH IS net_pnl improved +42pp (+23.62 → +65.77). BCH OOS net change small (-2.52 weighted_pnl). The headline -2.36 OOS Sharpe regression is attributable to ALGO (-25.70) + LDO (-28.47) cross-run stochasticity, NOT primitive 10 contagion (per QR A2 + Engineering report Frozen-Baseline-Pattern Investigation). Primitive 10 mechanism is NOT FALSIFIED but cannot be VALIDATED at single-seed OOS due to the multi-run contamination — it carries forward to iter-v3/050 CONFIRMATION as a candidate bundle ingredient on IS-only evidence basis (per QR A4(c)).

### OOF parquet append-on-existing is a cross-iteration reproducibility hazard
The runner's `trial_oof_returns.parquet` write semantics at `optimization.py:423-426` overwrite-with-append on existing file. Re-running an iteration silently inflates n_trials in dsr.json + comparison.csv (here 700 reported vs true 140). Future iterations need fail-loud check OR `--clean-oof` flag (per QR A5 endorsed engineering fix). Lands BEFORE iter-v3/048 setup as guardrail commit.

## Memory Rule Recommendations

1. **Update `feedback_v3_single_seed_frozen_baseline.md`** with explicit qualifier: "applies only to single-process-invocation comparisons; cross-process invocations of the same single-seed config can produce non-bit-identical non-target rosters via LightGBM OpenMP non-determinism. The frozen-baseline pattern dissolves at multi-seed CONFIRMATION; it ALSO dissolves across separate process invocations of single-seed EXPLORATIONs when LightGBM training is re-executed."

2. **NEW catalog NEGATIVE subtype: NEGATIVE-multi-run-stochasticity-contaminated.** Sister to existing NEGATIVE-no-effect / NEGATIVE-redistribution / NEGATIVE-architecture-bug. Diagnostic: PATH C fires on bundle-regression but root-cause attribution traces non-target-symbol drift to cross-run stochasticity (verified via OOF parquet duplication or fresh-process re-run analysis), NOT to dispatch error or freed-capacity contagion. Catalog row records "NEGATIVE-multi-run-stochasticity-contaminated" rather than "NEGATIVE-architecture-bug".

3. **Engineering guardrail: `optimization.py:423-428` fail-loud check + `--clean-oof` flag in `run_baseline_v3.py`.** Per QR A5: lands as separate guardrail commit BEFORE iter-v3/048 setup. Does not violate cadence discipline. Prevents future iterations from silently accumulating cross-run OOF state when re-run.

## Recommendations to QR

(Process-level for the NEXT iteration cycle. iter-v3/047 verdict is final.)

1. **iter-v3/048 = NEW EXPLORATION axis, NOT a re-run** (per QR A4(a)). Re-running iter-v3/047 cleanly = peeking at OOS twice; verboten per `feedback_no_cheating.md`. The contaminated single-seed observation stands as the verdict. Brief Section 2 must contain QR-EDA-driven numerical evidence per `feedback_v3_axis_selection_quant_discipline.md`. Cycle 3 #9 of 10.

2. **Carry primitive 10 forward as a CONFIRMATION-bundle candidate ingredient** at iter-v3/050 (per QR A4(c)). The CONFIRMATION QR brief MUST explicitly note "primitive 10 has no clean OOS evidence from EXPLORATION; iter-v3/050 CONFIRMATION multi-seed run is the first OOS test." If iter-v3/048 or iter-v3/049 produces a competing axis or NEGATIVE on primitive 10's mechanism, CONFIRMATION can revise bundle composition.

3. **Land OOF-parquet engineering guardrail BEFORE iter-v3/048 setup commit** (per QR A5). Standalone commit: fail-loud check at `optimization.py:423-428` (raise RuntimeError if OOF parquet exists for current iteration_label without `--clean-oof`); add `--clean-oof` CLI flag to `run_baseline_v3.py`; update memory rule per recommendation #1 above. This is a guardrail commit, not an axis change — does NOT consume an EXPLORATION slot.

## Catalog Row

`| iter-v3/047 | 2026-05-09 | REVERT iter-v3/046 BCH ATR + Primitive 10 (direction-asymmetric kill switch) block_long_for=("BCHUSDT",); 4-sym BCH+LDO+TRX+ALGO; QR EDA-driven; cycle 3 #8 | -0.26 (vs iter-v3/045 +0.7459) | -2.36 (vs iter-v3/045 +3.5259; bundle PATH C; BCH OOS only -2.52, ALGO -25.70 + LDO -28.47 cross-run stochasticity dominates) | EXPLORATION-NEGATIVE (multi-run-stochasticity-contaminated; new subtype) | NO — primitive 10 mechanism IS-validated (BCH +42pp IS net_pnl, 0 LONG leakage) but OOS-untested due to 5-run OOF parquet contamination + LightGBM OpenMP non-determinism; carry forward to iter-v3/050 CONFIRMATION as candidate bundle ingredient on IS-only evidence basis (per QR A4(c)); iter-v3/048 = NEW EXPLORATION axis, QR-EDA-driven; OOF-parquet engineering guardrail lands BEFORE iter-v3/048 setup |`

## Files Audited

- `briefs-v3/iteration_v3-047/research_brief.md` (SHA `3541997`)
- `briefs-v3/iteration_v3-047/engineering_report.md` (setup SHA `9b1293d`, brief backfill SHA `2b996fd`, engineering report SHA `af168c4`)
- `briefs-v3/iteration_v3-046/review.md` (format reference)
- Pre-commit revert SHA `f5f0fd6` (V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"] removed)
- EDA SHA `695fc8e` (`analysis/iteration_v3-047/bch_direction_diagnosis.py`)
- Phase 5.5 gate SHA `1236e3c` (PASS)
