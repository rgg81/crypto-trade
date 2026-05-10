# Phase 7.5 Critic Review — iter-v3/049

OVERALL: **EXPLORATION-NEGATIVE — clean PATH C-clean** fires on both IS regression (Δ -0.32) and OOS regression (Δ -2.50); per-symbol ADX threshold axis CLOSED for cycle 3.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (Cycle 3 #10 of 10 — LAST EXPLORATION before iter-v3/050 SECOND CONFIRMATION)

## QR Response Considered (Round 2 only)

(Round 1 PRELIMINARY skipped — orchestrator dispatched directly with FINAL mode given the clean PATH C-clean classification, frozen-baseline pattern confirmation, and unambiguous per-pre-registered-thresholds verdict. No clarifications outstanding.)

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
The iteration adds a single RiskV2Config field `adx_threshold_per_symbol: dict[str, float] = field(default_factory=dict)` and modifies one method (`_adx_gate_fails`) at `src/crypto_trade/strategies/ml/risk_v2.py:407-411` to consult the dict. ADX is computed in `_compute_adx` snapshotted during `compute_features` and read at `get_signal` time via `np.searchsorted` on `lk["open_time"]` — past-only by construction. The new threshold is a constant per `(symbol)` lookup with no dependency on contemporaneous signal data. No new feature, no new label generation, no training-window touch. The 14-feature stack (vol_normalized_ret_5d DROPPED) is identical to iter-v3/047 — past-only discipline already audited there.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP=88 = (timeout_candles + 1) × n_symbols = (21+1) × 4 = 88 (`run_baseline_v3.py:140-141`, `:1023`, `:1908`). Universe is BCH+LDO+TRX+ALGO (4 symbols) per V3_MODELS — UNCHANGED from iter-v3/045. The gap is asserted at runtime via `_verify_label_leakage_gap()`. Per-symbol ADX gate is a predict-time filter; it does not modify label horizons or fold geometry. No CV embargo concern.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)
DSR=0.0000 (threshold > 0.95); PBO=0.0939 (threshold < 0.4 — PASS); PSR=1.0000 (threshold > 0.95 — PASS); n_trials=700 (= 4 syms × 5 ensemble seeds × 35 Optuna trials per seed); n_eff=18. DSR fails the merge gate, but per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode DSR is structural artifact at low n_trials and is INFORMATIONAL ONLY — does NOT trigger BLOCK for EXPLORATION iterations. PBO is the only Check 3 axis that is BLOCK-eligible for EXPLORATION; PBO=0.0939 PASSES cleanly.

### Check 4 — IC Correlation: PASS
The iteration adds NO new feature — only a per-symbol ADX threshold dict field. `ic_matrix.csv` shows 14×14 pairwise IC for the unchanged 14-feature stack. Highest cross-pair |IC| is regime_momentum_signed_5d × vwap_dev_20 = 0.779 (composed-feature carve-out per `feedback_v3_engineered_feature_pivot.md`). All other pairs are below the 0.7 threshold.

### Check 5 — ADF Stationarity: PASS
adf_test.csv contains 14 features × monthly rolling ADF for the 4-symbol universe. No NEW feature added in this iteration; ADF profile identical to iter-v3/047 carry-forward. Per-symbol ADX threshold dict is gate-config, not a feature, so ADF is N/A for the new axis.

### Check 6 — Pareto Dominance: PASS (single-seed EXPLORATION caveat)
Single seed=42 per EXPLORATION spec. Pareto dominance is meaningless at n=1; multi-seed Pareto deferred to iter-v3/050 CONFIRMATION (--seeds 2). Note: OOS concentration is high — ALGO at 78.55% — same frozen-baseline ALGO carried since iter-v3/044. CONFIRMATION concern, not EXPLORATION-blocking.

### Check 7 — Reproducibility: PASS
Engineering report stamps commit SHA `6eeff46`. Runner uses explicit `feature_columns=list(features_for_symbol(symbol))` (`run_baseline_v3.py:1328`). The frozen-baseline pattern is now forensically validated at OOS level: ALGO/BCH/LDO trade rosters bit-identical between iter-v3/047 and iter-v3/049 (verified row-level character-for-character; only TRX rows differ). Reproducibility is now categorically above iter-v3/047's standard.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 1 hypothesis enacted exactly:
- `risk_v2.py:127-137` adds field with iter-v3/049 docstring citing EDA SHA `ba8a3de`.
- `risk_v2.py:407-411` modifies `_adx_gate_fails` with two-line per-symbol override.
- 5 adversarial tests in `test_per_symbol_adx_threshold.py` PASS (88/88 total).
- IS TRX trade count delta (85 → 78, -7 net; 19 dropped + 12 added) consistent with EDA-predicted 9 structural ADX-21 blocks partially offset by Optuna roster additions.

QR Section 10 directly addresses the ADX-axis-closed rule conflict per `feedback_adx_axis_asymmetric_v3.md`: Critic FINAL `55fbadb` explicitly opened "ADX-conditional regime gate variant" as candidate (e); structural distinction of per-symbol field vs universal-knob retune; novel implementation paralleling block_long_for/regime_gate_symbols dispatch architecture. Phase 5.5 gate accepted with documented justification.

## Optional Checks 9-12

### Check 9 — Symbol Exclusion Enforcement: PASS
`run_baseline_v3.py:165-169` audits `set(symbols) & set(V3_EXCLUDED_SYMBOLS)` and asserts disjoint.

### Check 10 — Feature Isolation Enforcement: PASS
`grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` returns only docstring/comment matches in `funding_v3.py:3`, `__init__.py:7`, `fracdiff_v3.py:23` — all explicit "MUST NOT import" comments, not actual imports.

### Check 11 — Forming-Candle Audit: PASS
Phase 5.5 gate confirmed data freshness within 16h staleness window.

### Check 12 — Library Version Pinning: PASS
Brief Section 9 lists 8 libraries pinned UNCHANGED from iter-v3/045-048.

## Critical Verifications

### Frozen-baseline pattern validation
**CONFIRMED at OOS level for the first time across consecutive non-identical iterations.** Direct row-level comparison of `iteration_v3-049/out_of_sample/trades.csv` vs `iteration_v3-047/out_of_sample/trades.csv`:
- Lines 2-9 (BCH+ALGO trades from open_time 1743667199999 to 1746748799999): bit-identical (entry_price, exit_price, weight_factor, open_time, close_time, exit_reason, pnl_pct, weighted_pnl all match character-for-character).
- Lines 11-12 (BCH+ALGO non-TRX trades): bit-identical.
- TRX rows differ (line 10 of /049 = TRX open_time 1746835199999 LONG vs line 10 of /047 = TRX open_time 1746806399999 LONG; different roster).

Per-symbol ADX gate fired on TRX only (as designed); cross-symbol Optuna independence held: BCH, LDO, ALGO models train and predict identically when their feature stack and config are unchanged. This is the strongest direct validation of the REVISED `feedback_v3_single_seed_frozen_baseline.md` rule observed in v3 catalog. The iter-v3/047 engineering report's claim of "cross-run stochasticity from multiple process invocations" is now categorically falsified.

### ADX-axis-closed rule compliance
**PASS.** The closed-axis rule was authored at iter-v3/014 closure of GLOBAL universal ADX-25 knob-tuning. iter-v3/049 is a STRUCTURALLY DISTINCT axis: a NEW dataclass FIELD creating per-symbol asymmetric dispatch, parallel to existing `regime_gate_symbols`, `block_long_for`, `block_short_for` per-symbol overrides. Critic FINAL `55fbadb` explicitly opened this candidate. The Phase 5.5 gate accepted with documented justification.

**Recommendation: the closed-axis rule SHOULD be expanded post-/049 to cover per-symbol ADX as well**, since this iteration is the empirical test that resolved the question (verdict: per-symbol ADX raise also closes — the EDA-predicted "BOTH-must-improve" naive counterfactual did NOT survive Optuna response at single-seed).

### TRX trade rotation analysis
**CONFIRMED.** OOS TRX count UNCHANGED (46 → 46), but PnL Δ -11.53 driven by 6-trade roster swap. The 6 dropped trades had collective +11.27 weighted_pnl (including +4.23/+4.07/+3.25 take-profit cluster); the 6 new trades had -0.22 weighted_pnl. Net swap delta -11.49 ≈ the -11.53 observed regression. This is single-seed Optuna lottery-unfavorable swap driven by the modified IS training sample (9 fewer TRX IS trades from ADX 21 gate), NOT an OOS gate-physical-block effect. The EDA-predicted "near-zero OOS cost" was correct on the naive counterfactual axis but missed the secondary Optuna-response cost path.

### Cycle 3 closure
**Cycle 3 of 10 EXPLORATIONs is COMPLETE (10/10 done).** iter-v3/050 = SECOND v3 CONFIRMATION, per `feedback_v3_strict_10_to_1_cadence.md`.

## Recommendations to QR (Process-Level)

1. **Expand `feedback_adx_axis_asymmetric_v3.md`** to also cover per-symbol ADX dispatch. iter-v3/049 empirically tested the only remaining ADX axis variant (per-symbol asymmetric raise) and it FAILED at single-seed OOS despite passing naive EDA BOTH-must-improve. Memory rule expansion: "ADX axis CLOSED in BOTH global AND per-symbol forms; no further ADX EXPLORATIONs in any direction; pivot to NEW feature families or NEW model architectures."

2. **iter-v3/050 SECOND CONFIRMATION bundle composition (RECOMMENDED)**:
   - V3_FEATURE_COLUMNS_TOP_N = 14 features (regime_momentum_signed_5d PRESENT; vol_normalized_ret_5d ABSENT per /048 closeout)
   - V3_ATR_MULTIPLIERS_PER_SYMBOL = {ALGOUSDT: (2.0, 1.5), LDOUSDT: (2.0, 1.5)} (BCH+TRX use default)
   - RiskV2Config.block_long_for = ("BCHUSDT",) — primitive 10 carry-forward (iter-v3/047)
   - RiskV2Config.block_short_for = ()
   - RiskV2Config.adx_threshold_per_symbol = {} (EMPTY — TRX 21 DROPPED per this verdict)
   - Spec: --seeds 2, ENSEMBLE_SIZE=5, n_trials=35

   This bundle composition represents the union of all EXPLORATION-PROMISING ingredients in cycle 3 that survived their PATH-A pre-registration. Per-symbol ATR (ALGO+LDO) and primitive 10 (BCH LONG block) are the only edge ingredients. NO NEW axis variation; NO IS-only-validated mechanism (primitive 10 had IS-only evidence at iter-v3/047 but multi-seed validation falls under SECOND CONFIRMATION re-validation).

3. **LDO OOS structural concern requires CONFIRMATION investigation.** LDO OOS = -19.13 weighted_pnl is bit-identical between iter-v3/047 and iter-v3/049 (frozen baseline). This is single-seed=42 lottery carry-over from iter-v3/045. At iter-v3/050 multi-seed CONFIRMATION (seeds 42 + alternative), if LDO remains consistently negative, the QR should consider whether LDO's per-symbol ATR (iter-v3/045) is the iter-v3/039 anti-pattern (per-symbol architecture lifts OOS suspicious-divergence pattern) and whether the LDO-included bundle clears MERGE gates per `feedback_v3_strict_both_is_oos_baseline.md`. If LDO is the structural drag, the QR may need to consider LDO removal from V3_MODELS at iter-v3/051 EXPLORATION cycle (post-CONFIRMATION).

## Catalog Row

`| iter-v3/049 | 2026-05-10 | NEW per-symbol ADX threshold gate variant: adx_threshold_per_symbol={"TRXUSDT": 21.0}; 4-sym BCH+LDO+TRX+ALGO; QR EDA-driven cycle 3 #10 of 10 (LAST EXPLORATION before iter-v3/050 SECOND CONFIRMATION); primitive 10 BCH LONG block carry-forward; vol_normalized_ret_5d DROPPED per iter-v3/048 closeout; --seeds 1 + ENSEMBLE_SIZE=5 + n_trials=35 + --clean-oof | -0.32 | -2.50 | EXPLORATION-NEGATIVE-clean | NO — drop the per-symbol ADX field; per-symbol ADX threshold axis CLOSED for cycle 3 (saturated; complements iter-v3/014 global ADX closure); iter-v3/050 SECOND CONFIRMATION carries iter-v3/045 + primitive 10 + ALGO/LDO per-symbol ATR forward |`

Per-symbol Δ vs iter-v3/045 single-seed anchor: ALGO -25.70 wpnl OOS (frozen baseline carry-over from /047), BCH -3.08 wpnl OOS (frozen baseline carry-over), LDO -28.47 wpnl OOS (frozen baseline carry-over), TRX -4.84 wpnl OOS (Optuna lottery roster swap; -11.53 vs /047 anchor). All 4 symbols regressed; only TRX's regression is attributable to this iteration's axis.

Frozen-baseline pattern fully confirmed at OOS row-level for ALGO/BCH/LDO. iter-v3/050 = SECOND v3 CONFIRMATION (post-iter-v3/028 BASELINE_V3.md bootstrap). Per `feedback_v3_strict_both_is_oos_baseline.md`, BASELINE_V3.md updates ONLY when BOTH IS Sharpe AND OOS Sharpe (multi-seed mean) beat iter-v3/028 anchor (IS +0.51 / OOS +0.51).

## Files Audited

- `briefs-v3/iteration_v3-049/research_brief.md` (SHA `24f1f6c`)
- `briefs-v3/iteration_v3-049/phase5p5_gate.md` (SHA `524dde2`)
- `briefs-v3/iteration_v3-049/engineering_report.md` (SHA `d8998d9`; setup `6eeff46`)
- `reports-v3/iteration_v3-049/comparison.csv` + `dsr.json` + `seed_summary.json` + `pareto_front.csv` + `per_cell_pbo.csv` + `cpcv_paths.csv` + `ic_matrix.csv` + `adf_test.csv`
- `reports-v3/iteration_v3-049/in_sample/trades.csv` + `out_of_sample/trades.csv` (row-level vs /047 comparison)
- `analysis/iteration_v3-049/synthesis.md` + `candidate_axes_ranking.md` + 5 EDA scripts (SHA `ba8a3de`)
- `src/crypto_trade/strategies/ml/risk_v2.py` (lines 127-137 field, 407-411 gate)
- `tests/strategies/ml/test_per_symbol_adx_threshold.py` (5 adversarial tests)
- `briefs-v3/iteration_v3-047/` and `iteration_v3-048/` (precedents)
- `feedback_adx_axis_asymmetric_v3.md` + `feedback_v3_single_seed_frozen_baseline.md` (memory rules)
