# Phase 7.5 Critic Review — iter-v3/079

OVERALL: MERGE

The NULL-RESULT (behavioral saturation) classification is CERTIFIED CLEAN. iter-v3/079 does NOT advance to the cycle-2 CONFIRMATION. The conviction-derate axis is recorded as **under-tested at these a-priori constants** (not genuinely dead) — see Adjudication #3. No look-ahead, no scope creep, pure-weight-scalar verified independently. MERGE here is a closeout-integrity certification of a non-advancing EXPLORATION, not an edge ingredient.

## Iteration Type (from Brief Section 0.5)

TYPE: EXPLORATION — cycle 2 EXPLORATION #9 of 10. Single-axis: conviction-derate sizing primitive (primitive 13). The `V3_MODELS` ADA→LDO revert is a baseline-restore of /078's closed universe-revision axis, not a second axis. Per the EXPLORATION protocol, Check 3 (DSR/PSR/PBO edge thresholds) is informational; only the PBO axis is meaningful at EXPLORATION mode.

## Foundation Audit (Boot Steps 9–11)

- **`walk_forward.py:113`** — `train_end_ms = test_start_ms - embargo_ms`. The embargo IS present (`embargo_ms = compute_embargo_candles(...) × interval_minutes × 60_000`). This worktree's `walk_forward.py` is the **FIXED** version — NOT the buggy `train_end_ms = test_start_ms` that MEMORY.md `feedback_v3_walkforward_lookahead_bug.md` describes as live. **The lookahead bug has been fixed in this worktree.** The engineering report line 239 and brief still cite the bug as live ("v3 worktree STILL HAS BUG"); this is a **stale citation** — harmless to the verdict (it only over-claims caution), but noted in Recommendations for hygiene. The split semantics are sound: train window `[month_start(M−24), month_start(M) − embargo)`, test window `[month_start(M), month_start(M+1))`.
- **`ITERATION_LABEL = "v3-079"`** — confirmed at `run_baseline_v3.py:128`.
- **`V3_MODELS`** — confirmed BCH/LDO/TRX at `run_baseline_v3.py:151–155`. LDOUSDT restored from /078's ADAUSDT. The revert comment at lines 144–150 correctly frames it as a baseline-restore.
- **`OOS_CUTOFF_DATE = "2025-03-24"`** (line 81), **`TRAINING_MONTHS = 24`** (line 83) — both IMMUTABLE, unchanged.
- **`REQUIRED_GAP = 66 = (21+1)×3`** — confirmed unchanged (3 symbols).
- **`efficiency_ratio_50` ban** — confirmed intact. Pre-flight assertion at `run_baseline_v3.py:349–365` and `features_v3/__init__.py:210,355` both reject the literal name. ABSENT from `V3_FEATURE_COLUMNS_TOP_N` (14-feature stack confirmed via `ic_matrix.csv` 14×14 header and `adf_test.csv` 2198 rows = BCH 63×14 + TRX 63×14 + LDO 31×14).
- Feature-importance output (engineering report) shows `regime_momentum_signed_5d` present at rank 14/14 — the BASELINE_V3 mandate feature is in the stack.

Foundation Audit: **PASS.**

## §11 Anti-Pattern Static Scan

- No `start_time` skip, no measurement-window manipulation — `OOS_CUTOFF_DATE`/`TRAINING_MONTHS` immutable and confirmed.
- No `feature_columns=None` — `LightGbmStrategy.__init__` (lgbm.py:173–178) raises `ValueError` on empty/None; auto-discovery is structurally impossible.
- No `min(REQUIRED_GAP, ...)` — runner line 175 explicitly documents and forbids the iter-v3/001 bug; `REQUIRED_GAP = 66` is a literal.
- No silent universe survivorship — `V3_EXCLUDED_SYMBOLS` audit present (`run_baseline_v3.py:197–203`, `_verify_symbols` hard-asserts the v1/v2 disjointness).
- The conviction-derate is unconditionally wired (`lgbm.py:754`) — no feature flag that would constitute a hidden second axis.

§11 scan: **PASS.**

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

This is Adjudication #2 (load-bearing — model code). The conviction-derate wiring is look-ahead-clean by full chain audit:

1. **`conviction_derate` (lgbm.py:114–137)** is a pure arithmetic function: `round(100 * np.clip((confidence − c_floor)/(c_ref − c_floor), w_min_frac, 1.0))`. No closures, no global state, no I/O. The test file `test_conviction_derate.py::TestLookAheadClean` independently verifies `__closure__ is None` and statically scans the source for forbidden refs (`self.`, `pd.`, `open_time`, `proba`, `models`) — all absent.
2. **`confidence` derivation (lgbm.py:663–676)** — `confidence` is computed from `proba = np.mean([m.predict_proba(feat_df)[0] for m in self._models])`. `feat_df` is built from `feat_row = self._month_features.get((symbol, open_time))`.
3. **`_month_features` provenance (lgbm.py:550–559)** — loaded via `load_features_range(symbols, ..., split.test_start_ms, split.test_end_ms, columns=selected_cols)`. These are the test-month features for the bar being decided — bar-close OHLCV-derived features, knowable at bar `t`'s close (the decision point). Standard bar-close pattern, not look-ahead.
4. **The models (`self._models`)** are trained inside `_train_for_month` exclusively on `train_indices = where((open_time ≥ train_start_ms) & (open_time < train_end_ms))` (lgbm.py:354–357) — strictly the past walk-forward window, with `train_end_ms` embargoed (Foundation Audit). The production model never sees a future bar.
5. The conviction-derate (line 754) reads `confidence` only AFTER it is already in scope from step 2 — it introduces ZERO new data dependency. It is a pure function of a value computed from past-only features on a past-only-trained model.

The de-rate consumes a value that was already look-ahead-clean and applies a constant-parameterized arithmetic transform. **No future-data dependence is introduced.** Section 8.6 BLOCK condition #3 (look-ahead wiring) does NOT fire.

### Check 2 — Embargo Width: PASS

`REQUIRED_GAP = 66`. Required = `(timeout_candles + 1) × n_symbols` = `(21+1)×3`. The walk-forward train/test embargo (`walk_forward.py:91–113`) uses the same `compute_embargo_candles` single source of truth. Symmetric. The conviction-derate adds/removes no trades (verified Check 8) — it cannot alter label horizons. Embargo unchanged from /060 anchor and correct.

### Check 3 — Multiple-Testing Correction: PASS (informational at EXPLORATION; PBO axis meaningful)

`dsr.json`: PBO = 0.1278, DSR = 0.0, PSR = 1.0, `n_trials = 315`, `n_eff = 19`, `frac_positive_paths = 0.6444`. Per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode DSR/PSR (`n_trials = 315`) are structural artifacts and informational only — DSR = 0.0 does NOT trigger a BLOCK for an EXPLORATION. The one Check-3 axis meaningful at any mode is **PBO = 0.1278 < 0.40 — PASSES**. `n_trials = 315 = 3 seeds × 3 symbols × 35 trials` — matches the EXPLORATION budget. `n_eff = 19` sensible. PBO is bit-identical to the /077/060 anchor (0.1278), consistent with a 7.5%-incidence weight scalar leaving the CPCV path distribution unmoved — a clean null signature.

### Check 4 — IC Correlation: PASS

`ic_matrix.csv` present, 14×14. No NEW feature family was added — the conviction-derate is a post-model weight scalar, not a feature; it does not enter the feature matrix. The 14-feature stack is unchanged from the /060 anchor. The highest off-diagonal pair is `vwap_dev_20` vs `regime_momentum_signed_5d` at 0.764 — but `regime_momentum_signed_5d` is the BASELINE_V3-merged Category-2 composed feature whose mechanical correlation with primitives is governed by the relaxed importance-≥30 gate (`feedback_v3_engineered_feature_pivot.md`), not the strict |IC|<0.70 gate. No NEW family, no IC failure.

### Check 5 — ADF Stationarity: PASS

`adf_test.csv` present, 2198 rows (BCH 882 + TRX 882 + LDO 434, within the expected [1302, 2646] band). The early-2020 rows show `stationary=False` with empty `p_value` — warm-up-window months with insufficient observations, the documented short-history artifact, not a feature defect. No NEW price-derived feature was added (the conviction-derate is not a feature). No `run.log` ADF warnings; the /077-committed ADF-falsifier removal (`20c65cd`) holds. The feature set is the unchanged /060 stack.

### Check 6 — Pareto Dominance: PASS (N/A at EXPLORATION)

No `pareto_front.csv` in `reports-v3/iteration_v3-079/` — correctly absent. Pareto dominance is a CONFIRMATION multi-seed artifact. This is a 3-seed EXPLORATION (`ensemble_summary.json`: `mode=exploration, ensemble_size=3, seeds=[191664963, 1662057957, 1405681631]`, outer=42 lineage). The missing file is the expected state, not a FAIL.

### Check 7 — Reproducibility: PASS

Commit SHA stamped: implementation `8c36e2a`, setup `3dbbd4b`, brief `b61c8a8`, gate `d93cfac`, EDA `0a54acd`. Explicit `feature_columns` enforced by the `LightGbmStrategy.__init__` ValueError guard. Ensemble seeds literal in `ensemble_summary.json`. Spot-check: the engineering report re-derived `weighted_pnl = net_pnl_pct × weight_factor` on 10 random OOS trades — 0 math errors; the TRX OOS de-rate reconciles arithmetically (`(0.64 − 0.76) × 3.50 = −0.42` wpnl). The pre-flight assertion (`run_baseline_v3.py:2392–2410`) verifies `f(0.50)=50, f(0.65)=100, f(1.00)=100` before the backtest loop.

### Check 8 — Hypothesis-Implementation Alignment: PASS

Brief Section 3.1 specifies a conviction-DERATE map = pure post-model per-trade weight scalar applied inside `LightGbmStrategy.get_signal`, replacing the hardcoded `weight=100`. The implementation at `lgbm.py:751–755` (`weight = conviction_derate(confidence)`) is exact alignment. The `conviction_derate` helper (lgbm.py:114–137) matches the brief formula and the Phase 5.5 gate's specified body byte-for-byte (C_FLOOR=0.50, C_REF=0.65, W_MIN_FRAC=0.50). **No scope creep**: `direction` (lines 721–726), `tp_pct`/`sl_pct` (the ATR block 728–739), and trade SELECTION (the confidence-threshold gate line 678, the OOD/regime gates 688–719) are all unchanged. The conviction-derate touches ONLY the `weight` field. The runner setup commit `3dbbd4b` modified only `run_baseline_v3.py` and one test file (V3_MODELS ADA→LDO revert) — no `src/` model code, correct role boundary. Hypothesis and implementation match exactly; no second axis.

## Special Adjudications

### Adjudication #1 — NULL-RESULT (behavioral saturation) classification: CERTIFIED CLEAN

Independently re-applying the brief Section 8 LOCKED disjunctive taxonomy (order SUSPICIOUS → NULL-RESULT → NEGATIVE → PROMISING → INERT, first match canonical). Anchor IS +0.8236 / OOS +0.2078. Observed: IS +0.8288 (Δ +0.0052), OOS +0.2791 (Δ +0.0713), OOS/IS ratio 0.3368, de-rate incidence 7.5% (12/159 IS trades).

- **SUSPICIOUS 8.4 — ratio gate**: 0.3368 > 3.0? NO. Does not fire.
- **SUSPICIOUS 8.4 — OOS-DOMINANT sub-mode**: requires IS shift < 0 AND OOS shift ≥ +0.20. IS shift = +0.0052 ≥ 0 — the `IS shift < 0` clause FAILS. Does not fire.
- **NULL-RESULT 8.5 — behavioral saturation**: pre-registered (brief lines 291–292, Section 4.3 line 210) as the `< 15%`-of-IS-trades-de-rated condition, with the explicit note that for a weight-scalar axis the key roster is bit-identical by construction so the discriminator is the **de-rated count**, not roster bit-identity. Observed de-rate = **7.5% (12/159) < 15%** — FIRES. (a) 8.5 correctly pre-registered as the <15% condition: confirmed. (b) 8.5 precedes 8.3 INERT in the disjunctive order: confirmed. (c) De-rate incidence 7.5% < 15%: confirmed (per-symbol BCH 6 + TRX 6 + LDO 0 = 12/159).
- **INERT 8.3** would otherwise be a candidate (both shifts in-band: IS +0.0052 ∈ [−0.10,+0.10], OOS +0.0713 ∈ [−0.20,+0.20]) — but 8.3 explicitly requires "≥ 15% of IS trades de-rated" (brief line 282). At 7.5%, INERT's own precondition FAILS. Even setting aside the disjunctive order, INERT cannot fire on its own terms.

**NULL-RESULT is the canonical first match. CERTIFIED CLEAN.**

**On the QE override of the dispatch's suggested "INERT"**: the task dispatch *suggested* INERT-AT-EXPLORATION; the QE overrode it and applied the LOCKED brief Section 8. This was **correct discipline.** The Section 8 taxonomy is the pre-registered contract, locked before the backtest; the orchestrator's dispatch suggestion is not the authority. The QE correctly identified that (i) Section 8.5 fires at <15% de-rated, (ii) Section 8.3 INERT's own clause requires ≥15% de-rated, (iii) 8.5 precedes 8.3 — three independent grounds, all converging on NULL-RESULT. A QE that rubber-stamped "INERT" would have misclassified on every one of those grounds. The QE was right to override.

### Adjudication #2 — Look-Ahead on the conviction-derate wiring: PASS

Full 5-step chain audit recorded under Check 1. The `confidence` value is the M1 model's past-only inference output (computed via `predict_proba` on test-month bar-close features, on a model trained strictly on the embargoed past walk-forward window). The de-rate is a pure arithmetic transform of an already-look-ahead-clean value.

**Pure-weight-scalar — independently verified and structurally guaranteed.** The QE reports the `(symbol, open_time)` IS+OOS key roster is bit-identical to /077's /060-config roster (0 added, 0 removed, all six symbol-split pairs). I confirm this is structurally necessary, not merely empirical: (1) the conviction-derate (line 754) is the LAST statement before `return Signal(...)` and modifies only the `weight` field; every trade-suppressing return path (`NO_SIGNAL` at lines 654/660/686/706/719) executes BEFORE line 754, unchanged; (2) `conviction_derate` returns an int in [50,100] — `test_conviction_derate.py::test_weight_never_zero` verifies across a 10001-point grid it never returns 0 (the only `Signal.weight` that could suppress a trade downstream); (3) therefore the set of bars emitting a `Signal` vs `NO_SIGNAL` is identical with or without the de-rate — the roster key set CANNOT change. IS mean-duration delta = 0.0000 candles (a weight scalar touches no barrier). The OOS +0.0194-candle delta is data-extent drift on the last LDO `end_of_data` trade (`close_time` extended ~16h between the /077 and /079 runs), not a barrier touch. Section 8.6 BLOCK condition #1 (trade added/removed) does NOT fire.

### Adjudication #3 — Did the conviction-derate axis get a FAIR test? UNDER-TESTED at these a-priori constants — NOT genuinely dead

Verdict: **(b) the axis is merely under-tested at these a-priori constants**, with a structural caveat that the engageable population may be intrinsically modest.

1. **A constant-placement miss, not a dead signal.** The de-rate window is `[C_FLOOR=0.50, C_REF=0.65)`. The `/067 _inference_threshold_floor = 0.60` guarantees every surviving signal has `confidence ≥ 0.60`, so the *effective* de-rate window is the narrow `[0.60, 0.65)` band. The engineering report establishes the walk-forward Optuna search at n_trials=35 concentrated per-(symbol,month) inference thresholds at or above 0.65 — above C_REF — collapsing the effective window toward empty. C_REF=0.65 was placed at the threshold-saturation point of the confidence distribution rather than its busy region. A parameter-placement defect, not evidence conviction carries no edge.
2. **The directional hypothesis has weak but real support.** The engineering report isolates the 12 de-rated trades: mean `net_pnl_pct` −0.019% (de-rated) vs +0.476% (non-de-rated), WR 33.3% vs 38.0%. Low-conviction trades DID underperform. The hypothesis "M1 confidence carries per-trade edge that flat sizing wastes" was directionally confirmed on the available sample — it just did not get enough trade population (7.5% incidence) to move the aggregate Sharpe (+0.0052 IS). A genuinely dead axis would show de-rated trades performing AT or ABOVE the non-de-rated group.
3. **The structural caveat.** If Optuna's IS-optimized thresholds intrinsically sit ≥0.65 for a hard 8h directional problem, the model's surviving signals ARE nearly all high-conviction by construction — a conviction-derate has structurally little to act on regardless of constant choice. A re-attempt at higher C_REF (0.70–0.75) would widen the window into the populated band, but the gain is bounded by whatever per-trade conviction edge exists above 0.65 — which this EDA could not measure (per-trade confidence is not persisted).

**Recorded recommendation**: the conviction-derate axis is **NOT closed** — it was under-tested because C_REF=0.65 sat at the Optuna threshold-saturation point. A re-attempt is permissible ONLY with re-designed constants and ONLY if the QR first persists the per-trade M1 `confidence` distribution across the walk-forward (so a re-attempt's C_REF is placed empirically, not by another a-priori guess). Given cycle 2 has one EXPLORATION slot remaining (/080) and the directional support is only weak, the QR should weigh this against a structural axis from the priority ladder. The axis is parked, not killed.

## Recommendations to QR

(Process-level, for future iterations. /079 is a NULL-RESULT EXPLORATION — final verdict is final.)

1. **Persist per-trade M1 `confidence` before re-attempting any conviction-driven axis.** The /079 EDA's central residual risk — and the root cause of the 7.5%-vs-25% prediction miss — is that per-trade confidence is not in any report artifact, so C_REF was an a-priori guess that landed at the Optuna threshold-saturation point. Adding a `confidence` column to `trades.csv` (a Phase-6 instrumentation change, ~one line) would let a future conviction-derate brief place C_REF in the empirically populated region.

2. **Tighten the behavioral-effect predictor for threshold-coupled axes.** The brief predicted ≥25% de-rated with a <15% falsifier; observed 7.5% — a 3× miss. The predictor did not account for `_inference_threshold_floor=0.60` + Optuna-tuned thresholds frequently landing ≥C_REF=0.65, which mechanically empties the de-rate window. Future behavioral-effect predictors for any axis gated on a model-internal threshold must explicitly model the interaction with the Optuna-tuned threshold distribution.

3. **Correct the stale `walk_forward.py` lookahead-bug citation.** The engineering report and brief still cite `feedback_v3_walkforward_lookahead_bug.md` as a live bug ("v3 worktree STILL HAS BUG"). `walk_forward.py:113` has the embargo (`train_end_ms = test_start_ms − embargo_ms`) — the bug is FIXED in this worktree. The stale citation is harmless to /079's deltas (it only over-claims caution) but should be corrected in the MEMORY topic file and future briefs to avoid downstream confusion about absolute-Sharpe validity.
