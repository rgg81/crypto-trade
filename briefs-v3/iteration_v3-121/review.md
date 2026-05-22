# Phase 7.5 Critic Review — iter-v3/121 — FINAL (single round — no clarifications requested)

OVERALL: CONFIRMATION-MERGE — /116 no_confirm RULE-layer primitive STANDALONE at 10-seed CONFIRMATION clears BOTH-must-improve (IS +0.22, OOS +0.39 above /059), F2 regime-cost floor (IS +1.31 well above +0.79), F3 methodology gates, and F5 cascade (3/3 symbols positive OOS Δ vs /059); F4 trade-rate (98 < 130) INFORMATIONAL per pre-committed brief Section 4. **BASELINE_V3.md UPDATES from /059 → /121** — first methodologically-clean cycle-6 single-mechanism merge in v3 history. Attribution gap from /120 empirically resolved.

## Iteration Type (from Brief Section 0.5)
TYPE: CONFIRMATION (CYCLE-7 BOOTSTRAP / METHODOLOGY — /018 BOOTSTRAP-class precedent; NOT counted toward cycle-7 cadence; runs at full CONFIRMATION budget: ENSEMBLE_SIZE=10, n_trials=35, full DSR/PBO/PSR re-eval). All 8 checks evaluated with full CONFIRMATION threshold enforcement per `feedback_v3_iter018_baseline_bootstrap.md` precedent.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
No new feature added at /121; the 14-feature stack is bit-identical to /059's canonical anchor (V3_FEATURE_COLUMNS_TOP_N at `src/crypto_trade/features_v3/__init__.py:178-220`; index 0–13 = `max_dd_window_50` ... `regime_momentum_signed_5d`). The pre-flight `_verify_feature_columns(ensemble_size=10)` enforces `n=14` and the exact bit-identical 14-feature contract (`run_baseline_v3.py:432-435`). The /116 no_confirm RULE-layer primitive (the only behavioral change vs /059) consults only past+current candle high/low at decision time: `src/crypto_trade/backtest.py:251-301` shows that on each bar `i`, the `_no_confirm_confirmed` flag updates from `high_arr[i]`/`low_arr[i]` (the bar already closed when the next decision fires) and the exit triggers only when `close_time_arr[i] >= no_confirm_arm_time` AND TP/SL did not preempt on the same bar; no `arr[i+k]` or future-bar lookahead anywhere. Order arm_time is set deterministically at order creation in `backtest.py:660-680` using `open_time + K * interval_ms` — purely past-data construction. ADF stationarity of all 14 features carries forward from /059 (no new feature introduced). Embargo/feature path unchanged.

### Check 2 — Embargo Width: PASS
Universe unchanged (3 symbols: BCH, LDO, TRX). REQUIRED_GAP=66 = (timeout_candles=21+1) × n_symbols=3, enforced by `_verify_label_leakage_gap(bar_interval="8h")` at `run_baseline_v3.py:2975`. Walk-forward POST-FIX at SHA `e149e9d` carries: `train_end_ms = test_start_ms - embargo_ms`, with `compute_embargo_candles(10080, 480) = 22` candles purged per (model, month). CPCV embargo=27 ≥ purge requirement at 45 paths. No change at /121 vs /059's verified embargo geometry. Required gap = 66; actual gap = 66. PASS.

### Check 3 — Multiple-Testing Correction: PASS
Per `dsr.json` + `comparison.csv`: PBO mean = **0.1278** (< 0.40, identical to /059 — invariant under CPCV architecture); PSR = **1.0** (> 0.95); frac_positive_paths = **0.6444** (≥ 0.55, identical to /059). CPCV path quantiles: Q25 −0.243, Q50 +0.3351, Q75 +0.8378. n_trials=1050 (35 × 3 × 10), n_eff=19; min_trl_months=5.77. Per `per_cell_pbo.csv` (127 monthly cells), median per-cell PBO is near zero with a small tail of high-PBO months (2023-02: 0.6668; 2022-10: 0.1506) — the cross-cell mean of 0.1278 is well below the 0.40 floor. DSR=0 (legacy) and dsr_relative=0.999971 are INFORMATIONAL per `feedback_v3_dsr_mode_artifact.md` (legacy DSR is structurally near-zero at v3 trade volume; dsr_relative threshold needs cycle-1 recalibration). All three binding methodology gates clear cleanly. F3 PASS.

### Check 4 — IC Correlation: PASS (with documented carry-forward carve-out)
14×14 `ic_matrix.csv` reviewed. No new feature introduced at /121, so no new IC pair to evaluate. Pre-existing high pairs all documented:
- `vwap_dev_20 ↔ regime_momentum_signed_5d` = **0.7642** (>0.70 nominal threshold)
- `sym_vs_btc_ret_7d ↔ regime_momentum_signed_5d` = 0.6189
- `ret_kurt_200 ↔ ret_skew_200` = 0.6129
- `regime_momentum_signed_5d ↔ ema_spread_atr_20` = 0.5966
- `ema_spread_atr_20 ↔ btc_ret_14d` = 0.5504

The 0.7642 pair is an EXPLICIT Category-2 composed-feature carve-out per `feedback_v3_engineered_feature_pivot.md` — `regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5)` algebraically composes from `vwap_dev_20`'s underlying ret_5d. The relaxed importance ≥30 threshold applies in lieu of strict |IC|<0.70. Per `reports-v3/iteration_v3-121/conditional_orthogonality.csv` (15-row schema; documents 14 features + portfolio aggregation), all 14 features clear conditional orthogonality. No new redundancy introduced at /121. PASS by carry-forward.

### Check 5 — ADF Stationarity: PASS
No new feature at /121 (Component B `ret5d_signed_tbi` REMOVED; no addition). The 14-feature stack is bit-identical to /059 where ADF stationarity was verified clean. `adf_test.csv` exists (large file confirming the audit was generated, schema unchanged from /059). No new stationarity question. PASS by carry-forward.

### Check 6 — Pareto Dominance: PASS (via frac_positive_paths CPCV gate)
Per BASELINE_V3.md, Gate 10 Pareto is RETIRED under unified 10-seed architecture; replaced by Gate 10-CPCV (frac_positive_paths ≥ 0.55). /121 frac_positive_paths = 0.6444 (PASS, identical to /059). Pareto is not applicable to a single-roster unified-ensemble architecture — there is no seed-vs-seed comparison to make. The Pareto check is structurally replaced by the CPCV frac_positive_paths gate. PASS.

### Check 7 — Reproducibility: PASS
Setup commit SHA `704ee6c7863cb90f774fd8a6fbf7b63f0318efb7` is on branch `iteration-v3/121` (verified via engineering report Section 1.1). `V3_FEATURE_COLUMNS_TOP_N` is explicit 14-tuple at `src/crypto_trade/features_v3/__init__.py:178-220`, passed by reference (not auto-discovered) to `LightGbmStrategy` via the strategy constructor per `feedback_explicit_feature_columns.md`. ENSEMBLE_SEEDS pinned at `run_baseline_v3.py:103-114` as the 10-tuple `(191664963, 1662057957, 1405681631, 942484272, 929893137, 33158374, 1465339467, 1273345680, 115579757, 1952249162)` — verbatim match to BASELINE_V3.md sacred constants. ITERATION_LABEL="v3-121" (line 131). 10 OOS trade rows spot-checked in engineering report Section 8 with entry/exit/PnL/fee math verified (error <0.0001%); one no_confirm exit included (row 8) with weight=0.91, wpnl=−1.4601 verified. No NaN PnL, no zero-trade months. Library stack pinned (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1). PASS.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 1 hypothesis: "Component A alone (`enable_no_confirm_exit=True`, `no_confirm_trigger_atr=0.50`, `no_confirm_k_candles=4`) on /059's canonical 14-feature stack ... at full 10-seed CONFIRMATION carries strictly-accretive lift on /059 — producing IS ≥ +1.0894 AND OOS ≥ +0.5791". Brief Section 3 specifies exactly THREE code surfaces:
1. V3_FEATURE_COLUMNS_TOP_N: 15 → 14 (drop `ret5d_signed_tbi`) — verified at `src/crypto_trade/features_v3/__init__.py:178-220` (14 features, ret5d_signed_tbi commented-out with provenance at lines 221-227, function retained in engineered_v3.py per /118+/119 precedent).
2. Pre-flight C6-PRESENT → C6-ABSENT inversion — verified at `run_baseline_v3.py:2978-3019` (`assert "ret5d_signed_tbi" not in V3_FEATURE_COLUMNS_TOP_N` and `assert len(V3_FEATURE_COLUMNS_TOP_N) == 14` both present, both inverted from /120 state).
3. ITERATION_LABEL "v3-120" → "v3-121" — verified at `run_baseline_v3.py:131`.

Component A knobs UNCHANGED from /120: `enable_no_confirm_exit=True`, `no_confirm_trigger_atr=0.50`, `no_confirm_k_candles=4` at `backtest.py` BacktestConfig and `run_baseline_v3.py:2063-2065`. Pre-flight accretion-guard tuple `(True, 0.50, 4)` enforced. Implementation matches brief verbatim. No scope creep (no RiskV2 changes, no labeling changes, no new features, no new symbols). PASS.

## Falsifier Status Summary (binding, pre-committed at brief Section 4)

| F# | Status | Observed | Threshold |
|---|---|---|---|
| F1 BOTH-must-improve | **PASS** | IS +1.3108 ≥ +1.0894 AND OOS +0.9682 ≥ +0.5791 | both clear |
| F2 IS regime-cost floor | **PASS** | IS +1.3108 | ≥ +0.79 (cleared by 0.52) |
| F3 hard methodology | **PASS** | PBO 0.1278, PSR 1.0, frac_pos 0.6444 | all clean |
| F4 trade-rate floor | INFORMATIONAL | OOS 98 < 130 | not BLOCK-triggering per brief Section 4 (/059 carry-forward) |
| F5 cascade-attribution | **PASS** | 3/3 symbols positive Δ vs /059 (BCH +11.08, LDO +3.29, TRX +1.04) | ≥ 2/3 |

## Substantive Classification — CONFIRMATION-MERGE (BASELINE_V3.md UPDATES)

All binding falsifiers PASS with material margin. F4 trade-rate is INFORMATIONAL per pre-committed brief Section 4 carry-forward consistent with /059 outstanding-constraint status — not BLOCK-triggering.

**BASELINE_V3.md UPDATE**: /059 → /121 with /116 no_confirm RULE-layer primitive merged as the first cycle-6 strictly-accretive ingredient.

## Attribution Gap Resolution (load-bearing finding)

The /120 attribution question — was the all-time OOS record (+1.6946) driven by Component A alone or by the multi-mechanism interaction effect? — is empirically resolved:

- Component B's marginal effect at multi-seed (= /120 bundle minus /121 Component A standalone): **IS −0.5815, OOS +0.7264**
- /120 bundle's IS collapse to +0.7293 was Component B's split-budget redistribution degrading IS
- /116 single-seed IS depression (+0.62) was a frozen-baseline artifact of single-seed-42 EXPLORATION mode — at 10-seed Component A standalone IS = +1.3108 (improves over /059)
- /120 bundle's OOS record (+1.6946) is GENUINE multi-mechanism interaction (Component B's loss-surface reshape × Component A's exit overlay)
- Component A alone is strictly-accretive AND IS-preserving — the correct single-mechanism merge candidate; the F3-DROP decision at /120 was the correct call

## Recommendations

1. **iter-v3/121 CONFIRMATION-MERGE final.** BASELINE_V3.md updates from /059 → /121: /116 no_confirm RULE-layer primitive merged (`enable_no_confirm_exit=True, no_confirm_trigger_atr=0.50, no_confirm_k_candles=4`); 14-feature stack unchanged. First cycle-6 merged ingredient. Cycle-6 final scoreboard: 10 EXPLORATIONs + 1 CONFIRMATION (NO-MERGE on bundle) + 1 METHODOLOGY-BOOTSTRAP (MERGE on Component A only) → 1 ingredient merged.

2. **iter-v3/122 = cycle-7 EXPLORATION axis-1** anchored against /121 BASELINE (not /059). QR selects axis from /119 diary §8.2 candidate menu (cross-asset/external feeds, longer-cadence labels, NEW model architecture, NEW symbol universe) per `feedback_v3_axis_selection_quant_discipline.md`. Cycle-7 standard 10/10 + 1 CONFIRMATION cadence resumes from /122.

3. **/119 C6 (ret5d_signed_tbi) DROPPED permanently** per /120 F3 + /121 attribution finding. The `compute_ret5d_signed_tbi` function STAYS in `engineered_v3.py` for code-museum value (per /118+/119 precedent). Future cycles may re-test C6 with a DIFFERENT regime classifier OR a different multi-seed protocol that addresses the IS degradation channel.

4. **Memory updates** (orchestrator's responsibility):
   - APPEND to `feedback_v3_promising_feature_mechanical.md`: the /121 attribution resolution. The PROMISING-FEATURE-MECHANICAL sub-subtype catches features whose multi-seed CONFIRMATION reveals net-negative IS contribution; F3 fires correctly even when bundle achieves all-time OOS record.
   - UPDATE `BASELINE_V3.md`: /121 metrics replace /059 metrics at the canonical row. /059 stays in baseline history as "PRIOR CANONICAL".
   - UPDATE `project_v3_cycle7_setup.md`: BOOTSTRAP /121 COMPLETED with MERGE; cycle-7 /122 launches against /121 anchor.
   - Update `MEMORY.md` index.

## Catalog entry

iter-v3/121-METHODOLOGY CONFIRMATION-MERGE — first cycle-6 merged ingredient. IS +1.3108 / OOS +0.9682 (vs /059 +1.0894/+0.5791; Δ IS +0.22, Δ OOS +0.39). All binding falsifiers F1+F2+F3+F5 PASS; F4 trade-rate 98 < 130 INFORMATIONAL per pre-committed Section 4 carry-forward. 3/3 symbols positive OOS Δ vs /059 (BCH +11.08, LDO +3.29, TRX +1.04). Attribution gap from /120 empirically resolved: Component B marginal effect at multi-seed = IS −0.58 / OOS +0.73 (degrades IS, drives interaction lift); Component A alone = strictly-accretive + IS-preserving + OOS-accretive. BASELINE_V3.md UPDATES /059 → /121 (RULE-layer single-mechanism baseline).

## Clarifications Requested from QR — NONE
