# Phase 7.5 Critic Review — iter-v3/071

OVERALL: MERGE

(Verdict certification: SUSPICIOUS-OOS-DOMINANT classification is methodologically clean and certified. PBO=NaN is adjudicated as a non-blocking known limitation — a runner WIRING DEFECT, not a structural impossibility, and PBO is informational (not a binding gate) for /071's LOCKED classification criteria. "MERGE" certifies closeout integrity ONLY; iter-v3/071 does NOT advance to cycle-2 CONFIRMATION and does NOT update BASELINE_V3.md — /059 stays canonical.)

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION — cycle 2 #1 of 10. Axis: META-LABELING (structural — model architecture, Category 2). Per `feedback_v3_dsr_mode_artifact.md` EXPLORATION carve-out, edge-significance gates (DSR/PSR/PBO) are INFORMATIONAL at EXPLORATION mode.

## Foundation Audit (Boot Steps 9-11)

- **Walk-forward lookahead fix INTACT**: `walk_forward.py:113` `train_end_ms = test_start_ms - embargo_ms`; `compute_embargo_candles(10080,480)=22`. `_verify_label_leakage_gap` runtime-asserts REQUIRED_GAP=66.
- Sacred constants immutable (OOS_CUTOFF 2025-03-24, TRAINING_MONTHS 24).
- ITERATION_LABEL="v3-071"; V3_MODELS 3-sym; EXPLORATION_ENSEMBLE_SIZE=3; ensemble_summary.json confirms 3-seed outer=42 lineage.
- MetaLabelingStrategy = existing /017 implementation (zero new strategy code; single-axis discipline confirmed).

## §11 Anti-Pattern Static Scan: CLEAN

No start_time/sacred-constant manipulation, no look-ahead shift, no fillna(method=). Track isolation clean. Single code change = cosmetic ITERATION_LABEL bump.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
M2 trains on `train_indices` bounded by `split.train_end_ms` — SAME embargoed window M1 uses. M2 binary label from `label_trades()` on training indices only; last-bar triple-barrier scan terminates at `train_end_ms + 21 candles < test_start_ms` (embargo of 22 correctly sized). No new leakage path. Trade-math spot-check verified.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP=66=(21+1)×3. Runtime-asserted. Per-cell embargo 22 candles. No change vs /060.

### Check 3 — PBO=NaN UNEVALUABLE (informational at EXPLORATION; non-blocking) / DSR_relative_B4=0.9845 PASS / PSR=1.0 PASS

**(a) PBO=NaN is a runner WIRING DEFECT, not a structural meta-labeling consequence.** The engineering report's root-cause hypothesis is FACTUALLY INCORRECT. The OOF-writing hook is in `optimization.py` (`optimize_and_train`), invoked by `lgbm.py:493` whenever `oof_persist_path` is non-None. MetaLabelingStrategy's M1 IS a LightGbmStrategy and `__init__` forwards `oof_persist_path` to it. The parquet is absent because `run_baseline_v3.py:1492` constructs `MetaLabelingStrategy(**common_kwargs)` with `common_kwargs` OMITTING `oof_persist_path` — the `lgbm` and `xgboost` branches both pass it explicitly (lines 1494, 1500); the `metalabeling` branch is the lone omission. One-line fixable gap.

**(b) PBO=NaN does NOT invalidate the verdict.** Brief Section 8.1 LOCKED PROMISING criteria lists exactly 4 conjuncts: IS ≥ +0.9325, OOS ≥ +0.3403, frac_positive_paths ≥ 0.50, no Critic methodology FAIL. PBO is NOT among them. Sections 8.2/8.3/8.4 reference only IS Δ / OOS Δ / OOS-IS-ratio / veto-rate. PBO appears in NO LOCKED classification criterion and NO Section-4 falsifier band. PBO=NaN is a known-limitation flag, not a BLOCK.

**(c) Surviving gates are legitimate computed values.** `dsr_relative_b4=0.9845` computed from OOS daily-PnL via `psr()` — code path INDEPENDENT of the OOF parquet machinery. `frac_positive_paths=0.6444` (29/45 — recounted) CPCV-architecture-invariant. PSR=1.0.

**(d) Two forensic inaccuracies in engineering report (non-verdict-altering)**: (i) `n_eff=5` is a computed SURROGATE (`n_effective_trials()` PCA-95), not a "hardcoded sentinel"; (ii) report silent on legacy `dsr_relative=0.00275` field (acceptable — Path B4 is the live metric).

### Check 4 — IC Correlation: PASS
ic_matrix max pair `vwap_dev_20 × regime_momentum_signed_5d = 0.7642` — inherited /059-baseline property; /071 adds ZERO features. /070 Critic already adjudicated this exact pair (WARN, no FAIL). No new IC exposure.

### Check 5 — ADF Stationarity: PASS
Standard per-(symbol,feature,month) schema; identical 14-feature set to /059 baseline; no new price-derived feature → no new ADF exposure.

### Check 6 — Gate 10-CPCV: PASS
frac_positive_paths=0.6444 ≥ 0.55 (recounted 29/45). IDENTICAL to /059/060/070 — CPCV architecture-invariant; M2-filtered trade roster doesn't move the IS-candle-sequence path distribution.

### Check 7 — Reproducibility: PASS
Commit SHAs verified. MetaLabelingStrategy validates non-empty feature_columns + ensemble_seeds. Explicit 14-feature list (no auto-discovery). `--clean-oof` active. Wall-clock 0.65h within cap. Caveat: the wiring defect makes the per-cell PBO pathway silently non-reproducible-as-intended for `--model metalabeling` (process Rec #1) — does not affect trade-roster reproducibility.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 1 hypothesis tested exactly (`--model metalabeling` activates M1+M2; single code change = ITERATION_LABEL bump; M2 threshold/features/label all inherited unchanged — single-axis discipline). Hypothesis honestly FALSIFIED on IS axis (IS Δ -0.150 < +0.10). QR pre-registered SUSPICIOUS at 10%; observed SUSPICIOUS-OOS-DOMINANT is the 10% tail — low-probability outcome correctly NOT predicted as most-likely. OOS lift 212.98%-concentrated in TRX; BCH OOS -5.98, LDO OOS -7.60 — "TRX-local precision, not cross-symbol quality signal."

## Adjudication of the Three QE Critic-Alert Items

**1 — PBO=NaN → NON-BLOCKING.** One-line runner wiring defect (`run_baseline_v3.py:1492` omits `oof_persist_path`). PBO informational at EXPLORATION + appears in no LOCKED criterion. SUSPICIOUS-OOS-DOMINANT verdict trustworthy despite PBO=NaN. **Caveat: if a cycle-2 CONFIRMATION ever runs `--model metalabeling`, PBO becomes a binding Gate 5 — the wiring defect MUST be fixed first.**

**2 — classification precedence → SUSPICIOUS-OOS-DOMINANT is the CORRECT canonical outcome.** Both NEGATIVE (Section 8.2: IS Δ < -0.10, i.e. IS < +0.7325; observed +0.6825 trips it) and SUSPICIOUS-OOS-DOMINANT (Section 8.4: IS Δ < 0 AND OOS Δ ≥ +0.20; observed -0.150 & +0.322 satisfy both) fire concurrently. Brief Section 8.4's LOCKED precedence rule — "SUSPICIOUS takes precedence over NEGATIVE when both fire" — has no magnitude qualifier. SUSPICIOUS-OOS-DOMINANT is canonical; NEGATIVE superseded.

**3 — trade-rate floor → informational at EXPLORATION; flagged for cycle-2 bundle decisions.** OOS 80 trades / 14 months = 5.71/month, below ≥10/month floor. Per `feedback_v3_trade_rate_floor_bundle_level.md` the floor applies at CONFIRMATION-bundle level, not per EXPLORATION row; brief Section 8.5 pre-registers this as informational (§8.5 hard-flag at OOS<52; observed 80>52 — does not trip). Material constraint on cycle-2 bundle assembly: meta-labeling structurally reduces trade count (35.7% veto rate) — any cycle-2 CONFIRMATION bundling meta-labeling would breach the 130-trade aggregate OOS floor.

## Recommendations to QR

1. **Fix the `--model metalabeling` OOF wiring defect before ANY meta-labeling CONFIRMATION.** `run_baseline_v3.py:1492` must pass `oof_persist_path` into `MetaLabelingStrategy(**common_kwargs)` — exactly as the `lgbm`/`xgboost` branches do. One-line gap. Until fixed, every `--model metalabeling` run produces PBO=NaN; at CONFIRMATION an unevaluable PBO would force a BLOCK.

2. **Correct two forensic inaccuracies in the engineering-report template**: (a) `n_eff=5` is a computed surrogate, not a hardcoded sentinel; (b) the PBO=NaN root-cause narrative ("OOF hook in LightGbmStrategy base path not triggered in MetaLabelingStrategy path") is false — the hook runs inside MetaLabelingStrategy's M1; the cause is the omitted constructor argument.

3. **Reconcile the engineering report's Label Leakage Audit with verified code.** The report states the walk-forward bug "is still present in this worktree" — FALSE. `walk_forward.py:113` reads `train_end_ms = test_start_ms - embargo_ms` (the FIXED state). Future reports must not assert a bug the live code + brief both contradict.

4. **A future meta-labeling EXPLORATION must use DISTINCT M2 features.** /071 is a clean unified-anchor data point that same-feature M2 (M1's 14 features + confidence) does NOT deliver a PROMISING lift — reproduces the SUSPICIOUS-OOS-DOMINANT pattern with TRX-concentrated OOS. This is the /017 lesson-#4 fix /071 intentionally deferred for single-axis discipline. A second meta-labeling EXPLORATION should pre-register an M2 feature set M1 does not use (funding, OI, basis, regime) with its own EDA + the trade-rate consequence for any downstream CONFIRMATION bundle.

5. **Carry forward the open /070 Rec #2 (Category-2 IC carve-out).** `vwap_dev_20 × regime_momentum_signed_5d = 0.7642` remains in the inherited baseline. Cycle 2 should restrict the Category-2 carve-out to feature-vs-own-primitive pairs OR grandfather inherited baseline correlations.
