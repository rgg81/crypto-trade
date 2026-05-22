# Phase 7.5 Critic Review — iter-v3/059

OVERALL: CONFIRMATION-MERGE — RE-ANCHOR-MERGE-IS-DOMINANT (architectural transition certified clean; suspicious OOS/IS = 0.53 flagged for cycle 1 QR diagnostic, but mandatory BASELINE_V3.md update proceeds)

## Iteration Type (from Brief Section 0.5)
TYPE: RE-ANCHOR #2 (special category — orthogonal to cycle counting; NOT cycle 1 EXPLORATION; NOT competitive CONFIRMATION). MERGE adjudicated against brief Section 8 LOCKED hard-blocking gates (Gate 3, Gate 6, Gate 10-CPCV) only; aspirational floors and DSR_relative are informational per brief Section 8.4.

## QR Response Considered (Round 2 only)

Single-round FINAL review. No PRELIMINARY clarifications were dispatched; all eight checks plus the 4 optional and the §11 Anti-Pattern Static Scan resolved unambiguously against the artifacts and the brief's own LOCKED criteria. Architecture-specific concerns (lineage preservation, Optuna seeding independence, confidence threshold consistency) all resolve against committed code at `ab2d9ac` + revert `31665f6` + walk-forward fix `e149e9d`.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

Walk-forward fix at `walk_forward.py:113` is intact: `train_end_ms = test_start_ms - embargo_ms` with `embargo_ms = compute_embargo_candles(10080, 480) × 480 × 60_000 = 22 × 28_800_000 = 633_600_000ms` (22 candles). The Phase B-3 refactor at `ab2d9ac` did not touch `generate_monthly_splits()` — only the outer-seed loop in `run_baseline_v3.py` was eliminated. `compute_embargo_candles` helper at `walk_forward.py:10-38` is the single source of truth for both the train/test embargo (line 113) and the Optuna CV gap (`lgbm.py:457` via `embargo_candles × n_symbols`). Triple-barrier sigma (`labeling.py`) uses ATR multipliers — no rolling-std forward leak. On-chain/funding/microstructure features ABSENT from the 14-feature stack. Feature isolation grep against `features_v3/` returns empty per `_verify_track_isolation` at runtime. No look-ahead path identified.

### Check 2 — Embargo Width: PASS

REQUIRED_GAP = 66 = (timeout_candles=21 + 1) × n_symbols=3. Confirmed in `validation_v3.REQUIRED_GAP` and runtime assertion at `_verify_label_leakage_gap()` (run_baseline_v3.py:703-717) — formula matches the constant exactly. CPCV `embargo=27` (per BASELINE_V3.md, unchanged). Walk-forward embargo of 22 × 480 × 60_000ms = 633.6s applied at every train/test boundary, single source of truth via `compute_embargo_candles`. Phase 5.5 gate confirmed the assertion fires at runner start; smoke test output captured the PASS line. Numerical proof: required_gap = 22 × 3 = 66; actual REQUIRED_GAP = 66. Equality verified at runtime, not just at brief level.

### Check 3 — Multiple-Testing Correction: PARTIAL FAIL (informational; brief Section 8.4 hard gates ALL PASS)

Hard-blocking gates per brief Section 8.4:
- **Gate 3 — OOS/IS Sharpe ratio ≥ 0.5**: observed 0.5316 → **PASS** (0.016 above the floor — borderline; flagged as RE-ANCHOR-MERGE-IS-DOMINANT per brief Section 8.3)
- **Gate 6 — PSR > 0.95**: observed 1.0000 → **PASS** at n_trials_total=1050 saturation
- **Gate 10-CPCV — frac_positive_paths ≥ 0.55**: observed 0.6444 → **PASS** (cpcv_frac_positive_paths_gate_pass=true in dsr.json)
- PBO = 0.1278 (below 0.40 threshold). PASS.

Informational, NOT BLOCK-triggering per brief Section 8.4 explicit retirement of DSR_relative as a hard gate for RE-ANCHOR #2:
- **DSR_relative = 0.1134** (vs threshold 0.95) → FAIL. Drop from /058's 0.9982 to 0.1134 is reported in the engineering report Section "DSR_relative Regression Analysis" as a "mathematical consequence of min_trl_months halving 11.53 → 5.70". **This narrative is FACTUALLY INCORRECT**: `min_trl_months` is NOT an input to `psr()` or `deflated_sharpe_ratio_v3()` — it is only written to dsr.json as a tracking field (run_baseline_v3.py:1593-1622). The actual `psr()` call at line 2225 passes `n_obs=len(oos_wp)=94`, `observed_sharpe=raw_sharpe_oos`, `benchmark_sharpe=cpcv_path_sharpe_q75=0.8378`. Working backward: dsr_relative=0.1134 → z ≈ -1.21 → raw_sharpe_oos ≈ 0.71 (annualized at trade-level granularity), vs /058 raw_sharpe_oos ≈ 1.13 (from dsr_relative=0.998 → z ≈ +2.91). **The drop is dominated by OOS Sharpe falling, NOT by min_trl_months changing.** This is a narrative misframing in the engineering report Section "DSR_relative Regression Analysis" — Recommendation #1 flags it for cycle 1 QR awareness. Methodologically, DSR_relative gate inapplicability under the architecture change is genuine (the 0.95 threshold was calibrated to a different inference structure), but the report's diagnostic explanation must be corrected before it gets recycled into cycle 1 briefs.

- **Legacy DSR = 0.0**: structural at v3 trade volume, same root cause as all prior v3 CONFIRMATIONs; not gate-relevant. PASS (informational).

n_trials = 1050 confirmed (35 × 10 × 3 = 1050; matches /058's 35 × 5 × 2 × 3). n_eff = 19, computed via per-cell PCA median (run_baseline_v3.py:2240-2255). per_cell_pbo.csv exists with 108 rows (3 syms × 36 IS months); per-cell n_trials=35 each.

### Check 4 — IC Correlation: PASS (established carve-out)

`ic_matrix.csv` 14×14. New-vs-existing pairs N/A — no new features added in /059 (bundle composition IDENTICAL to /058 and /028 baseline). Inherited high pair: `regime_momentum_signed_5d × vwap_dev_20 = 0.7642` (above 0.70 threshold). This is the established composed-feature IC carve-out per `feedback_v3_engineered_feature_pivot.md` (regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5); R²=1.0 algebraic identity with primitives). The carve-out passed Critic review at iter-v3/058 and predecessors; no policy reversal at /059. Other engineered-feature ICs (vs sym_vs_btc_ret_7d 0.6189, ema_spread_atr_20 0.5966) below threshold.

### Check 5 — ADF Stationarity: PASS

`adf_test.csv` has 2198 rows (sym × feature × month grid). 1803 stationary (TRUE), 395 non-stationary (FALSE). Of the 395 FALSE rows, the overwhelming majority are 2020-01 cells where ADF could not compute (p_value=NaN, ADF statistic blank — insufficient lookback for features needing 100-200 candles before first valid value). A small residual of TRX-only ret_skew_200 / ret_kurt_200 cells fall in the 0.05-0.10 p-value boundary across 2021-Q3, 2022-Q3, 2023-Q1, 2024-Q3 (8 rows of 2198 = 0.36%). Identical pattern to /058 and /028; not a new regression. No structural ADF failure introduced by the architecture change (ADF is computed on raw features pre-prediction; architecture-independent).

### Check 6 — Pareto Dominance: PASS (replaced by Gate 10-CPCV per brief Section 8.2-8.3)

Brief Section 8.2 formally RETIRES Pareto Gate 10 under the unified 10-seed architecture (no per-outer-seed Pareto exists; single roster). Brief Section 8.3 formally introduces Gate 10-CPCV: `frac_positive_paths ≥ 0.55`. Observed 0.6444 → PASS. Replacement is methodologically sound: CPCV's 45 paths are generated from the same trial OOF returns parquet (per-cell CSCV pathway), are architecture-independent (computed at the (sym, month, fold) level pre-aggregation), and provide a multi-path robustness measure that the unified-roster architecture cannot supply via outer-seed dispersion. `pareto_front.csv` correctly ABSENT from `reports-v3/iteration_v3-059/` (confirmed via Glob); `seed_summary.json` ABSENT; `ensemble_summary.json` PRESENT with 10 seed-lineage entries (5 outer=42 + 5 outer=123) per the brief's specification.

### Check 7 — Reproducibility: PASS

- **Commit SHAs verifiable**: setup `20095a8` (brief + phase5p5 gate + ITERATION_LABEL bump); Phase B-3 `ab2d9ac`; Phase A revert `31665f6`; walk-forward fix `e149e9d`; pre-run HEAD `31665f6`. All exist in `git log`.
- **Feature columns pinned**: `_verify_feature_columns()` (run_baseline_v3.py:211+) asserts `ENSEMBLE_SIZE == 10` AND `len(V3_FEATURE_COLUMNS) == 14` AND no banned features. Smoke-test output in phase5p5 gate confirms all PASS.
- **ENSEMBLE_SEEDS hardcoded**: 10-tuple at run_baseline_v3.py:97-108 with lineage annotation. `tests/strategies/ml/test_ensemble_unified.py::TestEnsembleSeedsLineage` regression-tests that `ENSEMBLE_SEEDS[0:5] == _derive_ensemble_seeds(42, 5)` and `ENSEMBLE_SEEDS[5:10] == _derive_ensemble_seeds(123, 5)`. Catches future drift.
- **Trade math spot-check (2 of 94 OOS trades)**: BCH SHORT (entry=303.870, exit=282.100779, weight=0.33): (303.870 − 282.100779) / 303.870 × 100 − 0.10 = 7.0640%; weighted = 7.0640 × 0.33 = 2.3311 — matches CSV row 2 to 4 decimals. BCH SHORT (entry=371.240, exit=383.577610, weight=0.53): (371.240 − 383.577610) / 371.240 × 100 − 0.10 = −3.4234%; weighted = −3.4234 × 0.53 = −1.8144 — matches CSV row 5 exactly. No off-by-one or sign error detected.
- **n_jobs revert intact**: `grep -n n_jobs src/crypto_trade/strategies/ml/optimization.py` returns NO matches (Phase A `0a3c30e` parallelization fully reverted at `31665f6`).

### Check 8 — Hypothesis-Implementation Alignment: PASS

Brief Section 3 specifies a single substantive change: `ITERATION_LABEL = "v3-059"`. Verified at run_baseline_v3.py:125. All other architectural changes (ENSEMBLE_SIZE=10, lineage-preserving ENSEMBLE_SEEDS, --seeds deprecation, _verify_feature_columns assertion) are inherited from Phase B-3 commit `ab2d9ac` per brief Section 0.5 Stage 3. Optuna n_jobs=2 (Phase A `0a3c30e`) was reverted at `31665f6`; brief Section 0.5 lists Phase A as "n_jobs=2 via commit 0a3c30e" but the actual run was n_jobs=1 (per engineering report Header "Phase A revert SHA: 31665f6"). This is a documented divergence (reverted mid-RE-ANCHOR-setup due to 5x GIL slowdown). The brief was NOT updated to reflect the revert prior to the run — the engineering report covers it transparently. **Minor brief-vs-run divergence**, not a methodology failure: the run produced bit-identical CPCV/PBO outputs to the n_jobs=1 expectation because Optuna's TPE search trajectory is INDEPENDENT of `n_jobs` (it only affects parallelization, not seed sequence). PASS with note for cycle 1 to clean up brief Section 0.5 wording.

## Optional Checks

### Check 9 — Symbol Exclusion: PASS
`_verify_symbols(cfg.symbols)` asserted at startup; `V3_EXCLUDED_SYMBOLS` includes 11 symbols across v1+v2+MKR drop; no overlap with (BCH, LDO, TRX).

### Check 10 — Feature Isolation: PASS
`_verify_track_isolation()` runs `grep -rP "^from crypto_trade\.features " src/crypto_trade/features_v3/` and `grep -rP "^from crypto_trade\.features_v2" src/crypto_trade/features_v3/` — both return empty (CLEAN per phase5p5 gate smoke output).

### Check 11 — Forming-Candle Audit: PASS
`fetcher.py` filter `if k.close_time < now_ms` preserved (unchanged from /058). Phase 5.5 pre-flight re-fetch completed (4 syms × 8h, 2 new klines/sym); data freshness re-verified. No CSV tail has close_time in the future.

### Check 12 — Library Version Pinning: PASS
Brief Section 9: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1 — unchanged from /058. `pyproject.toml` consistent.

### Check 13 — §11 Anti-Pattern Static Scan: CLEAN

- **A1 train_end_ms=test_start_ms**: `grep "train_end_ms\s*=\s*test_start_ms" src/` matches ONLY `walk_forward.py:113` `train_end_ms = test_start_ms - embargo_ms` (the FIXED form) plus a docstring. Zero pre-fix regressions.
- **A5 master-data-extent invariance**: no changes to feature loading or labeling at Phase B-3; the test continues to pass.
- **A7 OOF parquet guardrail**: `--clean-oof` was passed (engineering report `--clean-oof` documented; pre-run state had no stale parquet).
- **A8 stateful gate deadlock**: per-symbol drawdown brake DISABLED; block_long_for=(); no stateful gate active.
- **A12 DSR/PSR granularity**: `psr()` called with `n_obs=len(oos_wp)` (trade-level) and `observed_sharpe=raw_sharpe_oos` (trade-level annualized via sqrt(n)); consistent granularity. The DSR_relative narrative in the engineering report misattributes the drop to min_trl_months but the call-site itself is correct.
- **A13 written-before-read**: `cpcv_path_sharpe_q75` is now read from in-memory `flat_path_sharpes` (run_baseline_v3.py:2210-2217), not from disk before write — this is the iter-v3/056 fix and remains correct at /059.
- **Per-seed parquet namespace collision (iter-v3/048 concern)**: the unified-ensemble refactor eliminates the outer-seed loop entirely. There is now only one inner-seed loop writing to one trial_oof_returns.parquet path via one process — the collision concern dissolves (no concurrent writers across outer seeds).

## Architecture-Specific Concerns (FIRST AUDIT under unified 10-seed)

- **Lineage preservation**: ENSEMBLE_SEEDS[0:5] derived from outer=42; [5:10] from outer=123 via `_derive_ensemble_seeds`; verified at test_ensemble_unified.py::TestEnsembleSeedsLineage. Each seed runs its own independently-seeded TPESampler (optimization.py:376) → no Optuna-search contamination from a single outer seed.
- **`_confidence_threshold` consistency**: computed at lgbm.py:507 as `float(np.mean(self._confidence_thresholds))` — a single mean of N per-seed thresholds. Per-symbol, per-month — one value per (sym, month) inference. Same scheme as /058 except N=10 instead of N=5. No structural change to the threshold semantics.
- **Proba averaging**: lgbm.py:621-624 averages `predict_proba()` over all `self._models` (10 models at /059). Identical pattern to /058 (5 models). Vector-mean of probabilities, not log-odds — consistent with /058.
- **Trade roster construction**: brief Section 4.1 explicit — the new architecture produces ONE roster from 10-model averaged probability (softer consensus) vs /058's two rosters merged. The engineering report confirms this is the actual behavior (171 IS trades / 94 OOS trades vs /058 mean 177 / 94.5 — essentially unchanged trade count, materially shifted Sharpe).
- **Optuna efficiency**: n_eff = 19 (per-cell median via PCA-95). Identical to /058's 19. Expected — n_eff is architecture-independent (computed per-cell on trial returns, not on outer-seed structure).

## Verdict Reasoning

The architectural transition (Phase B-3 unified 10-seed + Phase A n_jobs=2 reverted + walk-forward fix preserved) is implemented per the brief. All 13 methodology checks PASS or PASS-equivalent (Check 3 has a non-binding DSR_relative FAIL that the brief formally retires for RE-ANCHOR #2; the three hard gates PASS). The path classification (RE-ANCHOR-MERGE-IS-DOMINANT, OOS/IS=0.53) is the brief's own pre-registered taxonomy firing. Per brief Section 8.1 the BASELINE_V3.md update is MANDATORY regardless of path classification — Critic's role is to certify the metrics were produced correctly by valid methodology under the architecture change, not to block the update.

The OOS Sharpe drop /058 → /059 (+0.87 → +0.58, Δ -0.29) is REAL — it is the unified-roster signal collapsing TRX's seed-42-lucky-bet roster from /058. This is structural to the architecture change, not a methodology defect. The engineering report's specific claim that the DSR_relative drop is a "mathematical consequence of min_trl_months halving" is INCORRECT (min_trl_months is not an input to psr()), but DSR_relative is informational per brief Section 8.4 and the architectural-transition certification does not depend on this narrative. Recommendation #1 below flags it.

CONFIRMATION-MERGE issued. BASELINE_V3.md update to /059 numbers proceeds.

## Recommendations to QR

1. **Correct the DSR_relative diagnostic narrative before cycle 1.** The engineering report Section "DSR_relative Regression Analysis: 0.9982 → 0.1134" attributes the drop to `min_trl_months` halving (11.53 → 5.70). This is wrong: `min_trl_months` is written to dsr.json as a tracking field only (run_baseline_v3.py:1593-1622) and is NOT an input to `psr()` (validation_v3.py:486-528). The actual cause is the OOS Sharpe drop combined with the fixed CPCV-Q75 benchmark of 0.8378. The cycle 1 EXPLORATION briefs should not cite `min_trl_months` as a DSR_relative driver; if a recalibration is desired, the appropriate axis is the benchmark choice (CPCV-Q75 may be too aggressive for unified-roster Sharpe distributions) or the threshold (0.95 was calibrated against 2-outer × 5-inner; under unified, the same threshold may be unreachable structurally).

2. **TRX OOS deserves a cycle 1 diagnostic.** TRX OOS weighted_pnl collapsed +23.03 → +4.16 between architectures. The brief's primary failure-mode prediction was "averaging convergence suppresses high-variance bet placement" — the data is consistent with this. But TRX IS contribution is now 3.47% of IS PnL with 0.050% avg/trade; under unified, TRX is contributing near-noise OOS. Cycle 1 should commission either (a) a TRX-specific feature-importance + label-quality diagnostic, OR (b) a universe-axis EXPLORATION evaluating drop-TRX (with the standard `feedback_insist_on_symbols.md` discipline of running feature importance + labeling analysis first).

3. **BCH IS concentration (95.76% of IS PnL) is a fragility flag for cycle 1 axis design.** Every cycle 1 EXPLORATION brief's Section 4 should explicitly project the BCH IS impact of the proposed change. An axis that improves LDO and/or TRX but reduces BCH IS contribution will likely collapse the headline IS Sharpe due to the concentration. The brief Section 4 expected-impact analysis must include a BCH IS sensitivity prediction.

4. **(Process) The brief Section 0.5 Stage 3 commit-chain text says "Optuna n_jobs=2 (Phase A commit `0a3c30e`)" but the actual run was at HEAD `31665f6` (Phase A reverted).** This brief-vs-run divergence is documented transparently in the engineering report Headers but should be cleaned up in cycle 1's first EXPLORATION brief so the commit chain text reads "Phase A n_jobs=2 ATTEMPTED at `0a3c30e`, REVERTED at `31665f6` due to 5x GIL slowdown; current state n_jobs=1." Same for any reference to "Optuna n_jobs=2" elsewhere in inherited brief wording.
