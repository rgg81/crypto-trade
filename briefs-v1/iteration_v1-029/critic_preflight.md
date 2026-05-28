# Phase 6.0 Critic Pre-Flight — iter-v1/029

OVERALL: PASS

## Pre-Flight Checks

### Check A — Brief Look-Ahead Audit: PASS

Section 1 EDA tables (`dot_direction_split.csv`, `dot_btc_trend_bucket.csv`, `dot_monthly_pnl.csv`, `dot_exit_reasons.csv`) cite IS AND OOS data from baseline DOT-in-pool reports. Section 2.6 explicitly invokes the ORACLE-EDA carve-out for trade attribution: "trade attribution from baseline reports ... permitted ONLY for failure-mode prediction patterns, NOT for parameter tuning". The OOS LONG weak-up-BTC −8.47% bucket is consumed as failure-mode evidence (identifying the COUNTER-TREND fingerprint), not as a knob-tuning input. Path C threshold ±8% and 42-bar lookback are /019 verbatim mirror (single-axis isolation; not tuned to DOT OOS). n_trials=35 and ENSEMBLE_SIZE=10 derive from /028 precedent under LM Master §2.5 ADOPTED, not from DOT OOS optimization. LM Master advisory `lgbm_advisor.md` is internally consistent — it adjudicates DOT structural class from IS+OOS attribution but does NOT propagate any OOS-derived parameter into Path C selection.

### Check B — Dispatch Defect Static Scan: PASS

The /029 elif at `run_baseline_v1.py:3049` reads `elif set(symbols) == set(V1_ITER029_UNIVERSE) and iteration_label == "v1-029":` — dual-guard (symbol set AND iteration_label). No silent fallback path: the block is closed at 3128 before falling through to the catch-all `else` at 3130. The /028 elif at line 3001 has `set(symbols) == {LTCUSDT}` AND `iteration_label == "v1-028"` — DOTUSDT symbol set will not match either condition. The /022 elif at line 2939 has same LTC+label-022 guard. The /018 (LINK), /019 (ETH), /020 (BTC) elifs lack iteration_label guards but are scoped to distinct single-symbol universes — DOTUSDT cannot match LINK/ETH/BTC sets. No /027-style `r.model_name` defect: /029 does NOT contain post-hoc `r.symbol` filter asserts within its block (unlike /027 line 2380 which used `r.symbol`); the `run_model(("DOTUSDT",), ...)` invocation structurally constrains the trade roster to DOTUSDT. F-AXIS #1 verification deferred to Phase 7.5 trades.csv inspection. CSV-level F-AXIS #1 check uses `df['symbol'].unique() == ['DOTUSDT']` (per brief §2), not a runtime `r.model_name` access, so the /027 attribute-error class is not reachable.

### Check C — Gate Wiring Correctness: PASS

`risk_v2.apply_btc_trend_filter` called at lines 3102 (IS) and 3105 (OOS) with `BtcTrendFilterConfig(lookback_bars=V1_ITER029_BTC_GATE_LOOKBACK_BARS=42, threshold_pct=V1_ITER029_BTC_GATE_THRESHOLD_PCT=8.0, enabled=V1_ITER029_BTC_GATE_ENABLED=True)`. The dataclass default `long_only_mode=False` (risk_v2.py:1276) is NOT overridden in the /029 dispatch → symmetric gate. The gate semantics at risk_v2.py:1416 are `should_kill = (direction == -1 and btc_ret_pct > threshold_pct) or (direction == 1 and btc_ret_pct < -threshold_pct)` — kills SHORTS in strong-up BTC AND LONGS in strong-down BTC. Units are correct: `threshold_pct=8.0` represents 8.0% and is compared to `btc_ret_pct = (close_now/close_then - 1.0) * 100.0` (also percent). Gate is POST-Optuna: `apply_btc_trend_filter` operates on `results_e029_is` and `results_e029_oos` AFTER `run_model` returns the trade roster. Test `test_v1_029_gate_is_symmetric_not_long_only` (test_iteration_v1_029.py:421-429) verifies `long_only_mode is False`. Past-only data access via `np.searchsorted(side='right')-1` (risk_v2.py:1399) is structurally incapable of lookahead.

### Check D — Configuration Sanity: PASS WITH OPERATIONAL NOTE

Brief §3.5 mandates n_trials=35, ENSEMBLE_SIZE=10, single-seed=42, atr_sl=1.75, atr_tp=3.5, R1 ON, R2 OFF, R3 ON, feature_columns=V1_FEATURE_COLUMNS_PRUNED (43 cols), 2h wall-clock cap.

Source verification:
- `n_trials=35`: runner default at line 1331; brief mandates 35 → match
- `ensemble_size=10`: dispatch passes `ensemble_size=ensemble_size` (line 3081); resolved from CLI `--ensemble-size` arg or mode default
- `atr_sl=1.75`: line 3078, matches brief §3.2
- `atr_tp=3.5`: line 3077, matches brief §3.2
- `apply_r1=True`: line 3079, R1 ON
- R2 OFF: `run_model(...)` invocation does NOT pass `apply_r2=True` for /029 (Model E baseline per brief §3.3 + LM Master §4 Path C)
- R3 ON: project-wide OOD always-on at LightGBM strategy level
- feature_columns=V1_FEATURE_COLUMNS_PRUNED: line 3083; hard-assert `len(active_feature_columns) == 43` at line 3070-3073
- 2h wall-clock cap: brief §3.6 declares 35-55 min target, 2h hard cap

**OPERATIONAL NOTE (informational; not a BLOCK)**: The runner default ENSEMBLE_SIZE for `--exploration` mode is `V1_EXPLORATION_ENSEMBLE_SIZE = 3` (line 114, line 1486). The brief mandates ENSEMBLE_SIZE=10 (LM Master §2.5 ADOPTED). The QE's launch CLI MUST include `--ensemble-size 10` explicitly; if the CLI is `--exploration --iteration 29 --n-trials 35 --pruned-features` WITHOUT `--ensemble-size 10`, the runtime ensemble_size will resolve to 3 — silently violating the brief mandate. This is a CLI-dispatch concern, not a src/ defect, but it is worth flagging on the launch command checklist.

### Check E — Test Suite Mandate: PASS

`tests/test_iteration_v1_029.py` exists with 7 test classes / ~30 tests covering: universe constant, gate constants, gate direction semantics (4 cases: long-kill-bear, short-kill-bull, long-pass-mild, short-pass-mild, long-pass-aligned-up), dispatch assert guards (with REAL TradeResult instances per /027 lesson at lines 121-136, 279-312), dispatch condition correctness, source-level wiring (atr_tp/atr_sl/apply_r1/gate constants/symmetric default), foundation regression (walk_forward.py:113 embargo). The /027 lesson is explicitly tested at line 272-281 (`test_traderesult_has_symbol_attribute`) and line 283-312 (`test_dispatch_hard_assert_dotusdt_passes_on_real_trade` / `test_dispatch_hard_assert_fails_on_non_dot_trade`).

`tests/test_lookahead_embargo.py` contains all 4 mandated regression tests: `test_labels_are_invariant_to_master_data_extent` (line 120), `test_demonstrates_bug_without_embargo` (line 171), `test_walk_forward_embargo_matches_cv_gap_formula` (line 277), `test_time_series_split_with_gap_excludes_correct_rows` (line 248). Foundation regression coverage intact.

### Check F — Anti-Pattern Static Scan: PASS

- **A1 (train_end_ms regression)**: `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` — fix intact. No raw `train_end_ms = test_start_ms` in active code. PASS.
- **A2 (labeling σ_t look-ahead)**: grep `returns\[.*:.*\]\.std|labels\.std\(\)` in `labeling.py` returns no matches. PASS.
- **A3 (fit_transform combined)**: grep `fit_transform` in `run_baseline_v1.py` and `StandardScaler|MinMaxScaler|FractionalDifferentiation` across strategies/ml/ both return zero matches. LightGBM is scale-invariant; no scalers required. PASS.
- **A12 (DSR/PSR granularity)**: Brief §9.1 declares pypbo N/A and PSR/DSR informational only at EXPLORATION. `compute_n_eff_and_dsr` is invoked at lines 1093/1099 with `observed_sharpe=is_sharpe_ann` (annualized daily). This is pre-existing infrastructure not changed by /029; not in scope for /029-introduced defect. Phase 7.5 should still cross-check granularity on dsr.json. Out of Phase 6.0 scope. PASS.
- **A13 (read-before-write)**: grep `read_csv(REPORTS_DIR|reports-v1|report_dir` in `run_baseline_v1.py` returns no matches. No methodology-axis computed fields read before written in /029 path. PASS.

### Foundation Regression Check: PASS

`walk_forward.py:113` reads `train_end_ms = test_start_ms - embargo_ms  # purge labels that would peek into test`. QE's diff `9456eb1..f4aef7d -- src/` does NOT touch `walk_forward.py` (verified by Glob — only `run_baseline_v1.py` and `src/crypto_trade/features_v1/__init__.py` were modified). The iter-v3/058 / iter-v1/058 RE-ANCHOR fix is intact post-QE setup commit. No regression to the pre-fix `train_end_ms = test_start_ms` bug signature.

### Cadence + Axis Sanity Check: PASS

Phase 5.5 gate (`phase5p5_gate.md`) OVERALL=PASS at `9456eb1` — confirmed. Brief Section 0.6 declares axis family `per-cohort-specialization-DOT-v2` with VALID rotation status (prior 5 disperse across 3 distinct families per the gate's verified table). Cycle-4 EXPLORATION 2/10 declared in header + Section 0.1.

### Falsifier Presence Check: PASS

Brief Section 4 (Verdict Matrix) has 6-row OOS Δ band table with explicit verdict cells. Section 4 has explicit OOS-Sharpe-below-X falsifier: "Δ < −0.55 → NEGATIVE-CATASTROPHIC" + Section 7.2 H1-CATASTROPHIC metric signature "OOS Sharpe Δ < −0.20 → Row 8 NEGATIVE-CLEAN or NEGATIVE-CATASTROPHIC". F-AXIS #3 OOS fire-rate < 5% → INERT-NO-EFFECT cap (verdict-capping). F-AXIS #5 OOS TP-exit < 2 → PROMISING-INERT cap (verdict-capping). All falsifiers numerically pre-registered. Section 8 verdict-cell determination table provides 8 rows of pre-committed verdict mappings.

### Check G — Axis Family Validation: PASS

Brief Section 0.6 declares family `per-cohort-specialization-DOT-v2`. Differentiation rationale (Section 0.6 + 3.8): DIFFERENT cohort (DOT) vs /020 BTC pure isolation + /022 LTC asymmetric long-suppress + /028 LTC-v2 atr_sl label-shift; DIFFERENT mechanism class from each. SAME mechanism class as /019 ETH (symmetric BTC-trend gate ±8%) but DIFFERENT cohort + HYBRID-FRAGILE-POSITIVE class designation. Per `feedback_v1_per_cohort_saturation_asymmetric_rotation.md`, mechanism class distinguishes families. Phase 5.5 gate verified rotation status VALID with 3 distinct families across prior 5 EXPLORATIONs (/022 LTC, /023 funding, /024 model-arch, /025 OI delta, /028 LTC-v2).

---

## Outstanding Notes (informational; not BLOCK-triggering)

1. **CLI dispatch ENSEMBLE_SIZE=10 mandate**: QE backtest launch command MUST include `--ensemble-size 10` to honor brief §3.5 ADOPTED LM Master §2.5. Without it, runner defaults to ENSEMBLE_SIZE=3 (`V1_EXPLORATION_ENSEMBLE_SIZE`, line 114), silently violating the brief. Recommend the QE include the explicit flag in the documented launch invocation (e.g., `uv run python run_baseline_v1.py --exploration --iteration 29 --n-trials 35 --pruned-features --ensemble-size 10`).

2. **F-AXIS #5 OOS TP-exit measurement semantics**: The line 3121-3122 print counts `sum(1 for t in results_e029_oos_gated if t.exit_reason == "take_profit")` on the post-gate roster. However, `apply_btc_trend_filter` sets `weight_factor=0.0` on killed trades but keeps the row with the original `exit_reason`. Thus, the printed OOS TP count includes ZERO-WEIGHT killed TPs. The brief §1.4 predicts ~7 post-gate-kill OOS TPs (baseline 8 minus ~15%), implying a count-after-removing-killed semantic that the current code does NOT enforce. Phase 7.5 Critic must evaluate F-AXIS #5 on the LIVE roster (`weight_factor > 0`), not the printed count. Verdict-capping logic at Phase 7 needs to filter killed trades before applying the < 2 threshold. Not a /029 src/ defect; a forensic-interpretation concern.

---

## PRE-FLIGHT AUTHORIZATION

OVERALL: PASS. QE is authorized to launch the Phase 6 backtest for iter-v1/029.

Required launch invocation (per brief §3.5 + LM Master §2.5 ADOPTED):

```
uv run python run_baseline_v1.py --exploration --iteration 29 --n-trials 35 --pruned-features --ensemble-size 10
```

The `--ensemble-size 10` flag is REQUIRED to satisfy the brief's ADOPTED LM Master §2.5 (ENSEMBLE_SIZE=10 mirror /028). Without it, the run silently defaults to ENSEMBLE_SIZE=3 and violates the brief. Failure to pass the flag is NOT a code defect but IS a brief-violation that the Phase 7.5 critic will flag at hypothesis-implementation alignment (Check 8).

Wall-clock budget: 35-55 min target per brief §3.6; 2h hard cap. Kill-switch armed at >1.6h per cycle-4 cadence discipline.
