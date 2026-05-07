# Phase 7.5 Critic Review — iter-v3/017

OVERALL: EXPLORATION-NEGATIVE (clean) — PATH C sub-flavor (NEGATIVE-over-filter-quality-residual)

10/10 EXPLORATION cadence reached. First v3 CONFIRMATION (iter-v3/018) unblocked.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
M2 training operates EXCLUSIVELY on M1's `_split_map[month_str].train_*` window (verified at `metalabeling.py:386-471`). M2 reads `train_indices` defined by `(open_time_arr >= split.train_start_ms) & (open_time_arr < split.train_end_ms)` — strict past-only. M2 labels are derived by re-running `label_trades(self._m1._master, train_indices_kept, ...)` with the same triple-barrier parameters and gap as M1. The forward-walk inside `label_trades` is bounded by the timeout (21 candles) but the candidate index set is restricted to training-window indices, so even the forward walk does not cross into the test window. M2 features are concatenation of M1's training-window feature matrix + M1's training-window confidence — both past-only inputs. The M2 model is then queried at predict time on test-month candles using `self._m1._month_features` (M1's already-cached test-month feature row) plus M1's freshly-computed confidence on that same row — no peek into future test-month bars. No look-ahead found.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP = 66 = (timeout_candles=21 + 1) × n_symbols=3, verified from run.log. M2 inherits the same gap (training labels are derived from `label_trades` with identical timeout=10080min). The METALABELING layer does NOT introduce new label-leakage paths because M2's label is a function of M1's already-purged outcomes and M2's input features are within the same purged window.

### Check 3 — Multiple-Testing Correction: INFORMATIONAL (per EXPLORATION carve-out)
DSR=0.0, PBO=NaN, PSR=1.0, n_trials=30, n_eff=4. Per skill EXPLORATION carve-out, INFORMATIONAL not BLOCK. Recording diagnostically: (a) DSR=0.0 single-seed saturation; (b) PSR=1.0 single-seed saturation; (c) PBO=NaN structural under MetaLabelingStrategy — thin walk-forward cells produce zero M1-positive predictions surviving all 7 gates → M2 has no label training data → all-NaN paths → PBO matrix degenerate. Fallback proxy `pbo_frac_positive_paths=0.6444` (29/45 CPCV paths positive). (d) n_eff=4 is the LOWEST in v3 catalog — M2's Optuna search overlaps M1's hyperparameter dimensions, collapsing joint manifold rank under 30-trial budget. CONFIRMATION-bundling QR must NOT carry these single-seed numbers forward as evidence of edge.

### Check 4 — IC Correlation: PASS
No new feature added. Inherited 13-stack max |IC| = 0.685 < 0.70 with margin 0.015.

### Check 5 — ADF Stationarity: PASS (inherited from iter-v3/015 PROMOTED)
2041 cells, same 81.2% stationary pattern as iter-v3/015. No new feature; inherited audit.

### Check 6 — Pareto Dominance: PASS (vacuous, single-seed)
1 row (seed 42). max_concentration 74.36% (LDO) above 35% CONFIRMATION cap; LDO 6-trade lottery flag carries forward (4 wins; 95% CI [22.3%, 95.7%] too wide for signal claim).

### Check 7 — Reproducibility: PASS
Setup `c6ca96e`; brief `6a1e986`; gate `7ed27e5`; EDA `d47163b`. ITERATION_LABEL "v3-017" verified. Explicit `feature_columns=list(V3_FEATURE_COLUMNS)`. Single-seed pattern matches `--exploration` flag.

### Check 8 — Hypothesis-Implementation Alignment: PASS (with documented label-tolerance caveat)
Brief §1 hypothesis matches code: MetaLabelingStrategy at `metalabeling.py` (~580 lines); `--model metalabeling` argparse choice (line 1357); `_build_v3_model` routes correctly (886-891); 11 unit tests. M2 input vector 14-dim verified. M2 threshold 0.5 PINNED at `metalabeling.py:328`. Single-axis discipline preserved.

**Documented divergence (label-tolerance, non-blocking):** brief §2.4 specifies M2=1 iff TP-first-hit-within-timeout. Implementation at `metalabeling.py:488` uses `pnl > 0.0` which conflates "TP-hit" with "timeout-with-positive-forward-return". Engineering report's M2 positive-class prior 39.1% vs EDA's pre-registered 33.97% partially reflects this. Non-blocking because: (a) disclosed transparently in synthesis.md and brief comment "We use: long_pnl > 0"; (b) qualitative finding (M2 filters 42.7% but kept trades show no quality lift) is robust to either definition; (c) tightening to TP-first-strict would not flip the verdict. Future meta-labeling re-test should use strict TP-first labels.

### Check 9 — Symbol Exclusion Enforcement: PASS
{BCH, LDO, TRX} ∩ V3_EXCLUDED_SYMBOLS = ∅.

### Check 10 — Feature Isolation Enforcement: PASS
No actual cross-track imports.

### Check 11 — Forming-Candle Audit: PASS (inherited staleness guard)

### Check 12 — Library Version Pinning: PASS
M2 reuses existing LightGBM (binary objective + is_unbalance=True). No new external dep.

## Saturation Falsifier Audit

| Falsifier | Condition | Observed | Status |
|---|---|---|---|
| Falsifier 1 | IS Sharpe < +0.40 | +0.5288 | DOES NOT FIRE |
| Falsifier 2 | IS trades ≥ 157 (NULL-RESULT, M2 inactive) | 159 | NARROWLY-IN-BAND but M2 demonstrably ACTIVE |
| Falsifier 3 | IS trades > 261 (wiring bug) | 159 | DOES NOT FIRE |
| Falsifier 4 | IS trades < 80 (over-filter) | 159 | DOES NOT FIRE |
| Falsifier 5 | Per-symbol IS count INCREASE | All deltas negative | DOES NOT FIRE |

**Falsifier 2 disposition.** IS=159 sits 2 trades above lower bound 157. Brief §4.4 row 5 saturation falsifier gates NULL-RESULT on bit-identical roster + count ≥ 157. Roster non-bit-identical (209 → 159; BCH 100→73, LDO 21→16, TRX 88→70). M2 demonstrably active: 2,976/6,965 = 42.7% per-candle veto rate. Falsifier 2 narrowly does NOT fire.

## §4.4 Row 5 NEGATIVE-clean Classification Verification

| Condition | Threshold | Observed | Fires? |
|---|---|---|---|
| IS Sharpe < +0.91 | < 0.91 | 0.5288 (Δ -0.48) | YES |
| \|Δ trades\| ≥ 11 OR per-symbol > 5 | either | \|Δ\|=50, BCH -27, TRX -18, LDO -5 | YES |
| Axis propagated (non-bit-identical) | non-identical | 209 → 159 different roster | YES |

All three conditions satisfied. Classification: **EXPLORATION-NEGATIVE (clean)**, PATH C sub-flavor (NEGATIVE-over-filter-quality-residual). M2 filtered 42.7% per-candle but retained trades produced no per-trade economics lift.

## Recommendations to QR (process-level for iter-v3/018+)

1. **iter-v3/018 axis = MULTI-SEED VALIDATION OF iter-v3/013 BASELINE, NOT NEW INGREDIENT BUNDLING.** All 4 PROMISING-class candidates (iter-v3/007 top-13 features, iter-v3/010 ATR labeling 2.0/1.0, iter-v3/011 z-score 2.0, iter-v3/013 drop-MKR universe) are ALREADY cumulatively integrated in the current iter-v3/013 baseline. There is no NEW ingredient to bundle from iter-v3/014-017 — those iterations were all NEGATIVE/NULL (014 ADX-tighter NEGATIVE, 015 microstructure INERT-NULL, 016 XGBoost NEGATIVE-clean WORST-OOS-in-v3-history, 017 meta-labeling NEGATIVE-over-filter). The CONFIRMATION question is: *does iter-v3/013's IS +1.0088 / OOS +2.6970 hold under multi-seed cross-validation rigor?*

   Specific spec for iter-v3/018:
   - `--seeds 2 --n-trials 50` (per `feedback_outer_seed_cap_2_v3.md`: 5 inner × 2 outer = 10 models per cell)
   - ENSEMBLE_SIZE=5 (live-prediction variance reduction inherited from v1)
   - Full DSR/PBO/PSR re-evaluation with multi-seed n_eff > 10
   - Multi-seed feature importance for hyperparam stability
   - Multi-seed Pareto front for the first time
   - Wall-clock budget: 4h hard cap per CONFIRMATION cadence rule
   - Single-seed concentration artifacts (LDO 65.65% at iter-v3/013, 74.36% at iter-v3/017) need re-evaluation under 10-models-per-cell averaging
   
   **No NEW axis variation. No bundling. Just validate the baseline.**

2. **Pre-commit M2-related rules for any future meta-labeling re-test** (lowest priority per `feedback_structural_over_knob_exploration.md` after this NEGATIVE):
   (a) Tighten M2 label from `pnl > 0` to strict `TP-barrier-first-hit-within-timeout`
   (b) Explore M2 threshold ≠ 0.5 as knob axis (0.4 or 0.6 since 0.5 produced 42.7% veto without quality lift)
   (c) Increase M2 n_trials from 10 to ≥50 to address best-F1=0.4409 modest discrimination
   (d) Consider M2 input feature DIFFERENT from M1's 13 (e.g., microstructure or path-dependency features) since same-feature M2 had no incremental learnable signal

3. **PRE-COMMIT MEMORY RULE for iter-v3/018 (orchestrator must save)**: `feedback_v3_iter018_confirmation_baseline_validation.md` — "iter-v3/018 is the first v3 CONFIRMATION. The 4 PROMISING components are ALL already integrated in the current iter-v3/013 baseline. iter-v3/018 = MULTI-SEED VALIDATION RUN of the iter-v3/013 baseline at full CONFIRMATION rigor: `--seeds 2 --n-trials 50`, ENSEMBLE_SIZE=5, full DSR/PBO/PSR re-evaluation. The hypothesis being tested is: 'does the iter-v3/013 IS +1.0088 / OOS +2.6970 Sharpe hold under multi-seed cross-validation, with PBO < 0.4, DSR > 0.95, PSR > 0.95, multi-seed Pareto non-domination, and bundle-level OOS trade count ≥ 130?'. Wall-clock 4h hard cap. CONFIRMATION-MERGE updates BASELINE_V3.md only if all CONFIRMATION methodology checks pass at non-EXPLORATION thresholds. Cannot be renegotiated post-hoc."
