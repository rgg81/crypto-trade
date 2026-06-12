# Phase 7.5 Critic Review — iter-v1/092 — XRP-IMPROVED (BTC-regime kill gate)

OVERALL: EXPLORATION-NEGATIVE — F1 IS-Sharpe falsifier FAILS HARD (0.3007 vs floor 0.578, and BELOW the ungated /088 anchor 0.3783); gate degrades IS even when verified armed. The exploration COMPLETED on a VALID test; the hypothesis was cleanly falsified. NOT a BLOCK.

## Iteration Type (from Brief Section 0.5)
TYPE: SPECIALIST (single-symbol XRPUSDT, risk-primitive axis, EXPLORATION). For SPECIALIST, Check 3-edge axis failures (DSR/PSR/PBO) are informational, NOT BLOCK-triggering.

## Validity Adjudication (the load-bearing question)

This is a corrected re-run of a previously-VOID iteration. Before scoring falsifiers, the Critic must rule whether the corrected run is a VALID test of the registered hypothesis. It is.

- **Gate verified ARMED.** `run.log` line 49 prints `[iter-v1/092] ... R6=ON BTC-regime kill thr=0.067 lookback=42b` (NOT the void run's `[iter-v1/088]`), and line 52 prints `[lgbm] BTC-regime kill gate: loaded 7061 BTC candles`. IS trade count 179 ≠ 219 (void clone) confirms the gate fired and suppressed entries. The void run's smoking-gun banner is gone.
- **Dispatch fix confirmed in source.** `run_baseline_v1.py:8191` (`v1-087`), `:8385` (`v1-088`), `:8990` (`v1-092`) all now carry the `iteration_label == "v1-NNN" and set(symbols) == ...` guard. The /088 short-circuit that produced the void run is closed. The /092 block (lines 9060-9092) wires `enable_btc_regime_kill=True, btc_regime_kill_thr=0.067, btc_regime_kill_lookback=42` as the single change vs /088.
- **F1 cleanly FAILS on a valid test → EXPLORATION-NEGATIVE is correct, NOT BLOCK.** A BLOCK is reserved for invalid/unevaluable tests or methodology violations. Here the test executed correctly and the pre-registered F1 floor was not cleared by a wide margin. That is a falsified hypothesis, which is a successful negative exploration. Per the task framing, BLOCK-PENDING-FIX was already consumed by the dispatch fix; the only live verdicts were EXPLORATION-NEGATIVE or BLOCK-FINAL. There is no second defect and no methodology breach, so BLOCK-FINAL does not apply.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
The new BTC-regime gate is past-only by construction. `_compute_btc_ret_42` (`lgbm.py:2016-2054`) does `idx_curr = searchsorted(ct_arr, candle_open_time, side="right") - 1` — the last BTC candle whose `close_time <= XRP open_time` — then looks back exactly `lookback` (42) bars and returns `close_curr/close_past - 1`. No BTC candle that closes after the XRP decision candle opens can enter the computation. Conservative pass-through (returns None) on missing index, `idx_curr<0`, `idx_past<0`, or non-finite/zero close. The gate consumes only `("close_time","close")` from `BTCUSDT_8h_features.parquet`; it adds NO model feature. FOUNDATION: `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` INTACT (the iter-v3/057 fix is not regressed). The active labeling path is `use_atr_labeling=True` (ATR barriers 2.9/1.45), not the sigma path; the sigma path (`labeling.py:344-374`) is documented past-only with `.shift(1)` upstream and is not exercised here. Regression test `tests/test_lookahead_embargo.py` present with all 4 mandated tests: `test_labels_are_invariant_to_master_data_extent`, `test_demonstrates_bug_without_embargo`, `test_walk_forward_embargo_matches_cv_gap_formula`, `test_time_series_split_with_gap_excludes_correct_rows`.

### Check 2 — Embargo Width: PASS
Foundation embargo discipline intact (`walk_forward.py:113`). The gate is a post-aggregator RULE layer and does not touch the train/test boundary, the CV gap, or the labeling horizon. Lock unchanged: training_months=24, OOS_CUTOFF 2025-03-24, PRUNED=48, single outer seed, 50 inner seeds × n_trials=30.

### Check 3 — Multiple-Testing Correction: FAIL (INFORMATIONAL for SPECIALIST)
`comparison.csv`: DSR=−70.30 (IS) / −34.96 (OOS), `n_effective_trials`=1, PSR_monthly_vs_0=0.714/0.802. These are far below the CONFIRMATION thresholds (DSR>0.95, PSR>0.95). Per Section 0.5 TYPE=SPECIALIST, Check 3-edge axis failures do NOT trigger BLOCK — edge significance is not the bar for a single-seed EXPLORATION still under development. Flagged for record only. The hugely-negative DSR is itself a symptom of the failed IS edge (Sharpe 0.30 with a deflation correction against the specialist trial budget), consistent with the F1 fail, not an independent problem.

### Check 4 — IC Correlation: INFORMATIONAL
`ic_matrix.csv` present (IS + OOS). No new feature family was added this iteration (PRUNED stays 48; the gate is a RULE layer, not a feature), so there is no new-vs-existing IC pair to evaluate. Artifact present → no artifact-missing FAIL. Per 2026-06-01 EDA Discipline revision, IC does not gate this iteration.

### Check 5 — ADF Stationarity: INFORMATIONAL
`adf_test.csv` present (IS + OOS). No new feature column introduced, so no new stationarity question arises. Artifact present → no artifact-missing FAIL. Per 2026-06-01 EDA Discipline revision, ADF does not gate this iteration.

### Check 6 — Pareto Dominance: PASS (single outer seed; not applicable)
This is a single-outer-seed SPECIALIST EXPLORATION (seed=42, 50 inner seeds collapsed to one mean prediction). `basin_diagnostics.json`: V1 cross_seed_sharpe_std=0.000 (single combined prediction, no per-outer-seed variance), V2 Spearman=NaN, V3 Jaccard=NaN (require ≥2 outer seeds). No 10-seed Pareto front exists for a NEGATIVE single-seed exploration, and none is required (`feedback_v1_basin_lottery_vigilance.md` mandates multi-seed re-validation only for PROMISING verdicts, not NEGATIVE). `specialist_dispersion.csv` was persisted as pre-registered. No dominance violation possible.

### Check 7 — Reproducibility: PASS
Commit SHA stamped (`89852828` pre-backtest; fix `77947a3d`). Runner passes explicit `feature_columns=active_feature_columns` (48-col PRUNED, asserted `len==48` at `run_baseline_v1.py:9012`), NOT None/auto-discovered. Gate params are literals in the dispatch block (thr=0.067, lookback=42). `decision_log.jsonl` is wired (`run_baseline_v1.py:9107` `_decision_log_092.configure(...)`) so the `btc_regime_kill_skip` events are persisted — the Phase 6.0 non-blocking wiring concern was resolved before launch. All expected report artifacts present (trades.csv IS/OOS, comparison.csv, dsr.json, ic_matrix.csv, adf_test.csv, basin diagnostics).

### Check 8 — Hypothesis-Implementation Alignment: PASS
The hypothesis (suppress XRP entries when BTC is in BTC_UP regime, `btc_ret_42 > +0.067`) maps exactly to the implemented gate at `lgbm.py:2348-2371` (fires `> self._btc_regime_kill_thr`, mode="regime" = kills ALL directions, logs `direction_pre_kill` without using it in the kill condition). One-variable discipline holds: the config diff vs /088 is precisely `enable_btc_regime_kill: False→True` plus the three gate params; PRUNED, seeds, trials, depth, leaves, ATR barriers, training_months, OOS_CUTOFF, R-stack all UNCHANGED (engineering report Section 3 table; corroborated by the dispatch block). No scope creep, no hypothesis-faking. The corrected run tests the registered hypothesis (the void run did not — that is the entire reason for the re-run).

### Check 13 — Anti-Pattern Static Scan: PASS
- **A1 (train/test boundary lookahead):** `train_end_ms = test_start_ms` raw signature returns ZERO matches in `strategies/ml/`; every occurrence is the corrected `- embargo_ms` form (walk_forward.py:113, cross_sectional.py:1345). INTACT.
- **A2 (labeling-window σ look-ahead):** no forward-window `.std()` in `labeling.py`; sigma path is `.shift(1)`-documented and not the active path here (ATR labeling active).
- **A3 (scaler fit on combined):** N/A — LightGBM scale-invariant; no scaler added.
- **A5 (master-extent dependency):** `test_labels_are_invariant_to_master_data_extent` present.
- **NEW gate scan:** default-OFF byte-identity confirmed (`enable_btc_regime_kill: bool = False` at lgbm.py:281; `_btc_regime_kill_idx` stays None on the OFF path; `_compute_btc_ret_42` returns None on None index → gate condition short-circuits). Fail-loud assertion (lgbm.py:644-658) raises `FileNotFoundError` ONLY when `enable_btc_regime_kill=True` AND parquet absent — this is the correct hardening against the exact silent-no-op class that produced the void run; the post-build None-guard (lgbm.py:672-677) backstops it. Gate site (lgbm.py:2348) is placed AFTER R-CONV and BEFORE NATR TP/SL build, no double-kill. Dispatch guards (8191/8385/8990) close the sibling-collision that caused the void run. No unexplained anti-pattern matches.

### Check 14 — Axis Family Validation: PASS
Brief Section 0.6 declares `FAMILY: risk-primitive` / `ROTATION_STATUS: VALID`. The src/ diff is a post-aggregator RULE-layer kill gate in `lgbm.py` (no feature add, no model-arch change, no labeling change, no universe change) — this is genuinely a risk-primitive. Declaration matches the observed change. Rotation ledger (prior 5: /086 universe, /087 universe, /088 universe, /090 sample-weighting, /091 risk-primitive) is NOT 5-of-the-same-family, so VALID under strict rotation, and the per-symbol regime-specialist mandate suspends strict rotation this cycle anyway. /091 (R-CONV) and /092 (BTC-trend) are both risk-primitive but mechanistically distinct (ensemble-conviction SNR filter vs cross-asset BTC-trend regime kill). Declaration is honest. No mis-declaration → no BLOCK-FINAL trigger.

## Projection-Falsification Finding — Critic Assessment: ATTRIBUTION CORRECT

The headline learning (the offline subtraction projected +0.81 IS Sharpe; the real backtest delivered −0.078) is correctly attributed to **sequential-position-model reshuffling**, and the supporting forensic is sound:

- The root cause is precisely identified: in a sequential single-symbol model, suppressing a BTC_UP entry at time T FREES the position slot, allowing a later entry that was previously blocked. The "0 concurrent overlaps" property the projection relied on is necessary but NOT sufficient for subtractive exactness — the missing second condition is "no position-slot cascades," which is structurally impossible in a slot-gated sequential backtest (`projection_divergence.md` conditions 1-2).
- The divergence is quantified and internally consistent (`projection_divergence.py`): gross removed 65 (not 57), 25 replacements generated (WR 0.280, well below the 0.447 gated mean), net −40 trades, net IS wpnl −7.23 vs projected +5.21 → projection error −12.44. The replacement losers (−24.33 wpnl) more than offset the suppressed-loser benefit (−17.10), explaining IS Sharpe falling 0.3783→0.3007 and IS MaxDD worsening 26.29%→41.82%. OOS happened to draw better replacements (WR 0.500), explaining the modest OOS rise — which does NOT override F1.
- **One honest scope note (not a defect):** the OOS replacement-WR asymmetry (0.500 IS-favorable) is the same displacement mechanism that drove the modest OOS Sharpe rise; the engineering report correctly refuses to treat that OOS improvement as a positive signal (Section 4/Anomaly-c). This is the right call — a single-seed OOS uptick from path-dependent reshuffling, on a gate whose IS edge failed, is not a mergeable result.

The generalizable rule ("never trust offline trade-subtraction projections for ENTRY gates in a path-dependent sequential backtest; the backtest is the only valid arbiter") is correct and vindicates the user's "no side scripts" directive. The pre-registration of the projection (committed before the run) is methodologically exemplary even though the projection itself was wrong — it converted a wrong prior into a clean falsification rather than a post-hoc rationalization.

## Lock Verification: INTACT

- **No OOS-tuning:** threshold 0.067 = IS abs-median of `btc_ret_42`, pre-registered in `rerun_projection.md` and Section 3.3, and bit-identical across the void run, the dispatch fix, and the corrected run (dispatch block lines 9090). The mechanism (i)-vs-(ii) choice was OOS-informed (adjudicated PASS-WITH-CAVEAT at Phase 6.0; design choice, not parameter tuning) but the threshold itself was never touched by any OOS number. PASS.
- **Gate opt-in / default-OFF:** `enable_btc_regime_kill: bool = False` default; OFF path is byte-identical to /088. PASS.
- **PRUNED stays 48:** `V1_FEATURE_COLUMNS_PRUNED` is 48 active entries; runner asserts `len(active_feature_columns)==48`; no feature add/drop. PASS.
- **Depth-5 / 50×30 / single outer seed / no multi-seed CONFIRMATION:** max_depth=5 FIXED, num_leaves=31 FIXED, 50 inner seeds × n_trials=30, single outer seed=42, EXPLORATION only. PASS.

## Recommendations to QR

1. The Phase 6.0 PASS-WITH-CAVEAT requirement stands: the diary must note that the mechanism (i)-vs-(ii) selection was OOS-informed. Given F1 hard-failed regardless, the caveat is now moot for merge purposes but should still be recorded for the catalog audit trail.
2. Record the generalizable rule in feedback memory: offline trade-subtraction projections for ENTRY gates are FORBIDDEN as evidence in any future v1/v2/v3 brief — entry-gate effects must be measured by backtest only. This is a reusable methodology hardening, not iteration-specific.
3. The dispatch-banner liveness check (verify `run.log` `[iter-v1/NNN]` banner FIRST, before any metric plausibility) should be added to the orchestrator's run-validation checklist so the void-run class is caught at launch, not by 3-agent forensic.

## Path Forward (mandatory)

The BTC-regime-binary-kill axis for XRP is CLOSED (gate degrades IS even verified armed; the path-dependent reshuffle replaces suppressed losers with worse entries). The last 5 XRP-adjacent SPECIALIST families were universe (/086-/088), sample-weighting (/090), and risk-primitive (/091, /092). Propose axes from families NOT in that recent set:

1. **btc_trend in-model composed feature (`ret_5d_xrp × sign(btc_ret_42 − thr)`)** — feature-family — encode the BTC-regime interaction INSIDE the model at training time rather than as a post-aggregator binary kill. The tree learns to down-weight (not hard-suppress) XRP signals in BTC_UP, avoiding the slot-cascade replacement pathology entirely because no entries are mechanically blocked — the model simply emits weaker conviction. This directly addresses the sequential-reshuffle root cause that killed the RULE-layer gate.
2. **XRP labeling-horizon / barrier re-derivation** — labeling — the OOS failure is "trend-wrong-way," i.e. directionally premature exits/entries. Test an asymmetric ATR barrier or a shorter timeout for XRP specifically (re-calibrated IS-only on XRP's own regime distribution) to see whether the trend-wrong-way drag is a horizon-mismatch rather than a regime-gating problem. Labeling has not been the SPECIALIST axis in the last 5.
3. **XRP model-architecture / depth-region probe** — model-arch — the /088 XRP head was tuned at the locked depth-5 / 31-leaf region inherited from the ETH cell. A one-off XRP-only re-derivation of the bounds profile (still within EXPLORATION budget, single change) tests whether XRP's edge is region-locked to a config borrowed from a different cohort — orthogonal to every risk-primitive/universe axis tried so far.

Constraints honored: feature-family, labeling, and model-arch are all absent from the last 5 XRP-adjacent SPECIALISTs (universe ×3, sample-weighting, risk-primitive ×2). Advisory only — QR may adopt, modify, or reject.
