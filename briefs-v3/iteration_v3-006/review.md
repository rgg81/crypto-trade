# Phase 7.5 Critic Review — iter-v3/006

OVERALL: BLOCK — Check 3 FAIL on DSR threshold (0.0 < 0.95) inherited unchanged from iter-v3/003-005 precedent; per-skill threshold enforcement is unconditional regardless of the QR's "methodology-only" self-framing.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS (carried forward)

Model code is byte-unchanged from iter-v3/003-005 in the feature pipeline; the iter-v3/006 patch at SHA `9314db4` modifies only `run_baseline_v3.py:_derive_ensemble_seeds` (top-level helper) and the `ensemble_seeds_run = _derive_ensemble_seeds(seed)` line at `run_baseline_v3.py:1162`. The downstream `LightGbmStrategy` consumer at `lgbm.py:445` (`seeds = self.ensemble_seeds`) is unchanged, the per-seed loop at `lgbm.py:453` is unchanged, and `optimize_and_train` is called identically. Triple-barrier ATR uses past-only NATR_21 (no leak), per-cell purge gap=22 confirmed in run.log fold-0/fold-1 trace (gap=184h = 22 rows). The RiskV3Wrapper IS-mask convention carries forward as WARN per iter-v3/002-005 precedent — not promoted to FAIL because no NEW look-ahead is introduced. The new `--symbols BCHUSDT` filter (committed at SHA `db2d673` BEFORE backtest) does not touch any feature computation.

### Check 2 — Embargo Width: PASS

`_verify_label_leakage_gap()` at `run_baseline_v3.py:192-205` asserts `(timeout_candles + 1) × n_symbols = (21+1) × 4 = 88 == REQUIRED_GAP=88` — the multi-symbol global is preserved as a runner-level constant even though active n_symbols=1 in this iteration. Per-cell gap is 22 (= timeout_candles + 1) per the within-symbol axis at `lgbm.py:435-441` (`cv_gap = timeout_candles * n_symbols`, with `n_symbols = len(set(self._sym_arr[train_indices]))` resolving to 1). Engineering report Section "Label Leakage Audit" verifies via run.log fold-0 (train_end=2020-05-26, val_start=2020-06-02 16:00, gap=184h=22 rows) and fold-1 (gap=22 rows). Both global axis (88) and per-cell axis (22) preserved. No leakage detected.

### Check 3 — Multiple-Testing Correction: FAIL

- **DSR = 0.0 (threshold > 0.95): FAIL.** Computed by `deflated_sharpe_ratio_v3` from raw IS Sharpe ≈ +0.0925 (monthly Sharpe = +0.4051 over 79 IS trades) with `n_trials_total = args.n_trials × ENSEMBLE_SIZE × len(active_models) × args.seeds = 10 × 5 × 1 × 2 = 100`. With expected_max_SR scaling at n=100 trials and a low-positive raw SR, DSR rounds to 0.000000 at Python float precision. This is the same outcome as iter-v3/003-005 (DSR = 0). Per skill spec ("DSR > 0.95... are skill-defined. If a threshold is wrong, propose a skill update separately — never silently pass an iteration that fails the documented threshold") and per the iter-v3/003 / iter-v3/004 / iter-v3/005 Critic precedent ("any single threshold missed = FAIL" — applied unconditionally even when the QR's brief vacates the criterion), Check 3 FAILs. The QR's "methodology-only" Section 8 framing is a brief-level construct; the Critic's per-check enforcement is uniform. Same precedent holds.

- **PBO = 0.1664 (threshold < 0.40): PASS.** Per-cell mean PBO from `per_cell_pbo.csv` (51 cells × 45-path CSCV per cell). Methodology axis correct; well below threshold. Distribution: 32/51 cells PBO=0.0, 19/51 cells with positive PBO (max=0.9516 at 2023-08, several near 0.9 indicating overfit-prone months). Healthy bimodal signature consistent with iter-v3/004 finding.

- **PSR = 0.4974 (threshold > 0.95): FAIL.** Computed deterministically from OOS monthly Sharpe ≈ -0.001 (effectively zero) over 35 OOS trades. PSR ≈ 0.5 is what you get when the observed Sharpe is statistically indistinguishable from zero. This is a SECOND threshold miss, separate from DSR. Per iter-v3/004 / iter-v3/005, PSR was ≈ 1.0 (PASS-vacuous on a barely-positive OOS Sharpe); here it deteriorates to 0.5 because seed=42 produced an OOS Sharpe ≈ 0.

- **n_eff = 7 (threshold > 4): PASS.** Per-cell median across 51 informative cells. Spot-check of `per_cell_pbo.csv` confirms healthy distribution (every cell n_eff=6 or 7).

- **n_trials = 100**: matches the formula `args.n_trials × ENSEMBLE_SIZE × len(active_models) × args.seeds = 10 × 5 × 1 × 2 = 100`. Lower than the iter-v3/003-005 1000-trial regime because of the deliberate `--n-trials 10` budget reduction. Documentation gap is moot because DSR fails at 100 already.

Aggregate verdict on Check 3: **FAIL** because both DSR threshold (0.0 < 0.95) and PSR threshold (0.4974 < 0.95) are missed under literal skill enforcement. Same precedent as iter-v3/003 / iter-v3/004 / iter-v3/005 OVERALL=BLOCK.

### Check 4 — IC Correlation: PASS (vacuous)

`reports-v3/iteration_v3-006/ic_matrix.csv` present, 34×34 features (single-symbol BCH this iteration). No new feature families added; brief Section 3.3 declares `V3_FEATURE_COLUMNS UNCHANGED, len=34`. Pre-existing cross-family pairs above 0.7 (`atr_pct_rank_200` ↔ `atr_pct_rank_500` ≈ 0.815) remain from iter-v3/001-005 and are not introduced by this iteration. Vacuous PASS, same precedent.

### Check 5 — ADF Stationarity: PASS

`reports-v3/iteration_v3-006/adf_test.csv` has 1,224 data rows (single-symbol BCH × 36 features × 34 retraining months). Engineering report Section "Anomaly Notes" reports 1819/2142 (84.9%) cells stationary at p<0.05. Inspection: many of the 2020-01 cells show `stationary=False` with empty p_value (constant series in early-period data, expected for warm-up window). Same proportion as iter-v3/003-005 (≈83-85% stationary). No new non-stationary features introduced.

### Check 6 — Pareto Dominance: PASS

`pareto_front.csv` has 2 rows (seed=42 and seed=123). Numerical inspection:

| seed | OOS Sharpe | OOS MaxDD | OOS Calmar | PBO | n_trades | max_conc% |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | -0.0010 | 29.6966 | -0.0010 | 0.1664 | 35 | 0.00 |
| 123 | +0.5556 | 35.7266 | +0.4698 | 0.1664 | 34 | 100.00 |

The iter-v3/005 false-positive Pareto pattern (10 tied rows from hardcoded ENSEMBLE_SEEDS) is **definitively broken**: per-seed Sharpe std = 0.3936, MaxDD differs by 6 pp, n_trades differs by one (35 vs 34). The ensembles `[191664963, 1662057957, 1405681631, 942484272, 929893137]` (outer=42) and `[329920693, 1869083161, 1155703948, 1660978513, 394007534]` (outer=123) are zero-overlap by construction (verified at producer side in brief Section 2.2). The seed-plumbing fix worked end-to-end — the iter-v3/005 STRUCTURAL FAIL is closed.

Note on max_concentration_pct: seed=42 shows 0.00% (BCH-only, but `max_conc=0` means positive_total=0 i.e. negative-PnL OOS — single-symbol degenerate case), seed=123 shows 100.00% (BCH owns all positive PnL — also single-symbol degenerate). Both are expected for single-symbol scope per brief Section 6.3 declaration.

Pareto dominance check: neither seed dominates the other. Seed=42 wins on MaxDD (29.7% vs 35.7%) and concentration (0% vs 100%), seed=123 wins on Sharpe (+0.5556 vs -0.0010) and Calmar (+0.4698 vs -0.0010). Both seeds trade ≈34 OOS trades. Chosen "primary" seed = 42 (per `if i == 0: primary_trades = braked` at `run_baseline_v3.py:1381-1383`), which wins on 2 of 3 "interesting" axes (MaxDD, n_trades-tied, vs Sharpe). PASS by the multi-metric winner test, AND non-dominated (genuinely; not vacuous).

### Check 7 — Reproducibility: PASS

- Code commit SHA stamped: `db2d6735d58b9535c0ed8b747c00a5fe6d616699` (engineering report Header line 7) plus inheritance chain `9314db4` → `03b6004` → `76f3999` → `9999fe3` → `db2d673` → `3ed90c3`.
- Runner uses explicit `feature_columns=list(V3_FEATURE_COLUMNS)` (verified previously at iter-v3/003-005); LightGbmStrategy raises on None/empty per project conventions.
- `LEGACY_ENSEMBLE_SEEDS = [42, 123, 456, 789, 1001]` literal preserved at `run_baseline_v3.py:84` for documentation; `_derive_ensemble_seeds(outer_seed)` is the active path at line 1162.
- 6 adversarial tests in `tests/strategies/ml/test_outer_seed_propagation.py` PASS at SHA `9314db4` — including `test_derive_legacy_constant_no_longer_passed` (sampled 100 outer seeds, none reproduces legacy). Total 35/35 tests across `tests/strategies/ml/` PASS.
- Library versions stamped: numpy==2.2.6, scipy==1.17.0, statsmodels==0.14.6, scikit-learn==1.8.0, lightgbm==4.6.0, pytest==9.0.2, pandas==3.0.0, pyarrow==23.0.1 — identical to iter-v3/004/005.
- 3-file PBO concordance: `dsr.json["pbo"] = 0.16645`, `pareto_front.csv` row[seed=42]["pbo"] = 0.16645, `seed_summary.json[0]["pbo"] = 0.16645`. All agree.
- New `--symbols` CLI flag at `run_baseline_v3.py:1227-1236` documented in engineering report Header; ITERATION_LABEL bumped from `v3-004` to `v3-006`. Both authorized in brief Section 3.9 step 2 ("the QE may revert it before commit OR ship a `--symbols` CLI flag").

### Check 8 — Hypothesis-Implementation Alignment: PASS

The brief's Section 1 hypothesis ("`--seeds 1` and `--seeds 2` on BCH-only at `--n-trials 10` will produce (i) distinct trade distributions across outer seeds (per-seed Sharpe std > 0), (ii) a non-tied 2-row pareto_front.csv that genuinely tests cross-seed model variation") is satisfied EXACTLY:

- Per-seed Sharpe std = 0.3936 > 0 ✓ (the central test)
- 2-row pareto_front.csv with non-tied rows ✓
- Trades NOT byte-identical to iter-v3/003 (seed=42 OOS=-0.0010 vs iter-v3/003 -0.0746) ✓

All 10 reconciliation verifiers in §3.6 exit 0 per engineering report. All 10 Section 8 methodology criteria met (criterion 7 pending Critic).

Calibration miss in the brief's Section 7 predictions: P1 (P=25%) predicted std<0.05; P4 (P=30%) predicted std positive but <0.05. Reality: 0.3936. This is an 8x miss in the FAVORABLE direction — the seed plumbing produces MORE cross-seed variance than the QR predicted, not less. This is recordable as a calibration finding but does NOT trigger Check 8 FAIL because the brief's HARD verifiers (§3.6 row 5: `std > 0`) are met. The brief's predictions are probability-weighted (Bayesian-calibrated), not pre-registered numerical falsifier ranges; only the §3.6 verifiers carry hard pass/fail consequences. Contrast iter-v3/005's Check 8 FAIL, where verifier #14 was a hard-coded numerical range `pbo_mean ∈ [0.05, 0.30]` that failed at 0.0163 — there is no equivalent hard-coded numerical range here.

Note: the —symbols CLI flag and ITERATION_LABEL update were authorized by brief Section 3.9 step 2 ("the QE may revert it before commit OR ship a `--symbols` CLI flag. Either way, the Phase-6 invocation runs on BCH-only"). No scope creep; no hypothesis-faking.

## Optional Checks 9–12

- **Check 9 — Symbol Exclusion Enforcement**: PASS. `_verify_symbols()` at `run_baseline_v3.py:151-158` raises if `set(symbols) & set(V3_EXCLUDED_SYMBOLS)` non-empty. Pre-flight verification confirmed `set({BCHUSDT}) ∩ V3_EXCLUDED_SYMBOLS = ∅`.

- **Check 10 — Feature Isolation**: PASS. `_verify_track_isolation()` greps for cross-track imports in `features_v3/` and raises on any match. Engineering report pre-flight reports PASS.

- **Check 11 — Forming-Candle Audit**: PASS. `_verify_data_freshness()` reports 14.6h lag (< 16h threshold) for BCHUSDT and BTCUSDT. Inherited from iter-v3/003-005 unchanged.

- **Check 12 — Library Version Pinning**: PASS. Engineering report stamps numpy==2.2.6, scipy==1.17.0, statsmodels==0.14.6, scikit-learn==1.8.0, lightgbm==4.6.0, pytest==9.0.2, pandas==3.0.0, pyarrow==23.0.1; identical to iter-v3/004/005.

## Recommendations to QR

OVERALL=BLOCK is final for this iteration. The methodology validation succeeded — the seed-plumbing fix demonstrably produces distinct trade distributions across outer seeds (std=0.3936, MaxDD differs by 6pp, n_trades differs by 1) and the iter-v3/005 false-positive Pareto pattern is closed. **But the v3 skill's Check 3 enforces DSR>0.95 and PSR>0.95 unconditionally, and PSR=0.4974 is a NEW threshold miss (degraded from iter-v3/004/005's PSR≈1.0) because seed=42 produced OOS Sharpe ≈ 0.** Three process-level recommendations for FUTURE iterations:

1. **The Check 3 split-merge skill update is overdue and now blocks the entire graduated rollout.** iter-v3/004 Critic Recommendation #1 already proposed splitting Check 3 into 3a (methodology axes: PBO, n_eff) and 3b (edge axes: DSR, PSR). iter-v3/005 NO-MERGE diary (Lessons #5) repeats the proposal. iter-v3/006 reproduces the same BLOCK on the same axis. Without the skill update, the user-approved 1→5→10 graduated rollout cannot exit Check 3 BLOCK regardless of how methodologically sound any subsequent iteration is — the IS Sharpe of -0.07 to +0.4 simply will not produce DSR>0.95 at any reasonable n_trials. The skill update is the highest-priority unblocker for v3, period. Land it as a parallel PR before iter-v3/007 starts; otherwise the graduated rollout will BLOCK at Check 3 in iter-v3/007 (5 seeds) and again at iter-v3/008 (10 seeds), wasting two more iterations on the same precedent.

2. **iter-v3/006 has produced informative methodology evidence that should NOT be discarded with the BLOCK.** The 2-seed result shows the inner-ensemble averaging does NOT dampen cross-outer-seed variance to near-zero (Predictions P1 + P4 both invalidated in the favorable direction). The OOS variance signature is also informative: seed=42 produces OOS Sharpe≈0 with 35 trades; seed=123 produces OOS Sharpe=+0.56 with 34 trades. A 0.39 cross-seed Sharpe std on just 2 seeds extrapolates to a wide distribution at 10 seeds — which means the "10-seed mean Sharpe > 0" project memory rule may be passable BUT will have wide uncertainty bands. iter-v3/007's brief should pre-register a calibrated prediction (e.g., "5-seed std in [0.2, 0.6]") so iter-v3/008 has a meaningful falsifier. The pre-registered ranges in iter-v3/006's brief Section 7 (P1 and P4) were 8x off in the favorable direction; calibration discipline matters even when the miss is favorable.

3. **Brief Section 6.3 declared concentration N/A by single-symbol design — that's correct, but the seed=42 max_concentration_pct=0.00% in pareto_front.csv reveals a degenerate computation case.** The runner's concentration formula at `run_baseline_v3.py:1352-1359` requires `positive_total > 0` to compute non-zero concentration; seed=42's OOS PnL is net-negative (sum of weighted_pnl ≈ -0.03), so `positive_total = 0` and the formula returns 0%. This is mathematically correct for a single-symbol negative-PnL portfolio but conflates "no trades" with "all losses" in the Pareto file. iter-v3/007's runner should either (a) document this case explicitly in pareto_front.csv comments, or (b) emit `NaN` instead of `0.00` when `positive_total=0`, so the Pareto file unambiguously distinguishes degenerate from all-loss cases. Cosmetic, but the iter-v3/005 BLOCK precedent shows that pareto_front.csv anomalies attract scrutiny, and "0.00% concentration" reading as "no concentration risk" while actually meaning "all OOS PnL is negative" is misleading.
