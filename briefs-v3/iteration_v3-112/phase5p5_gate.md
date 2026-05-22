# Phase 5.5 Gate — iter-v3/112

OVERALL: PASS

Iteration type: EXPLORATION (cycle-6 slot #3 of 10)
Cadence check: wall-clock declared ≤ 2h; run config `--exploration --n-trials 35`,
ENSEMBLE_SIZE=3; single axis (model architecture: pooled vs per-symbol). PASS.

---

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24` and
  `training_months = 24` stated as immutable in the Appendix's NO CHEATING block.
  IS window (2022-09 → 2025-03-24) and OOS window (2025-03-24 → 2026-05) named in
  Section 6's "Regime coverage" paragraph. Note: there is no standalone "Section 0"
  header; the declaration is distributed across the Appendix and Section 6. The
  content is present and correct; the missing dedicated header is a style gap, not a
  substantive gap. PASS.

- Section 0.5 (Iteration Type Declaration): PASS — TYPE=EXPLORATION, run command,
  ENSEMBLE_SIZE=3, seed lineage, n_trials=35, wall-clock budget ≤ 2h, and single-axis
  discipline all stated and confirmed consistent with current runner defaults.

- Section 1 (Hypothesis): PASS — one specific sentence: pooled cross-symbol LightGBM
  lifts OOS monthly Sharpe by rescuing the sample-starved LDO (10.3× sample expansion
  via pooling) at a small dilution cost to the sample-rich BCH/TRX. Specific mechanism,
  specific causal pathway. PASS.

- Section 2 (IS-Only Numerical Evidence): PASS — committed EDA at SHA `2cead80`
  (`analysis/iteration_v3-112/`): 3 scripts + `_shared.py`, 18 result tables T1–T14.
  All evidence strictly IS-only (`_shared.load_labeled_is()` asserts `close_time <
  OOS_CUTOFF_MS` per symbol and on assembled frame). Tables T2/T5 (aggregate horse
  race), T3/T11/T12/T13 (per-symbol breakdown), T6 (sample sizes), T9 (starvation
  gradient) cited with concrete numbers. T11 permutation null is the central
  evidence table: LDO pooled AUC 0.5432 clears LDO's own permutation q95 (0.5162)
  while per-symbol AUC 0.4528 is sub-null. Scripts confirmed to exist in the worktree.
  PASS.

- Section 3 (Proposed Changes): PASS — enumerated table: ONE axis (per-symbol →
  pooled model architecture), mechanical universe revert (BCH/LDO/TRX), REQUIRED_GAP
  88 → 66, ITERATION_LABEL "v3-112". Feature stack, labels, risk gates, ensemble
  seeds all UNCHANGED. Configuration diff table with "Changed?" column is present
  and complete. PASS.

- Section 3.5 (Implementation Scope — see detailed feasibility note below): PASS
  WITH CAVEATS. The 5 logical changes are correctly specified and the codebase
  investigation confirms the pooled-architecture feasibility claims. Caveats noted
  below are implementation reminders, not blocking gaps.

- Section 4 (Expected OOS Impact): PASS — point estimate OOS Δ +0.10, 80% interval
  [−0.30, +0.55]; IS Δ −0.05, interval [−0.40, +0.20]. Three pre-registered
  falsifiers: (1) OOS < −0.10, (2) LDO OOS net_pnl_pct does not improve vs
  per-symbol anchor, (3) aggregate IS < +0.40. SUSPICIOUS gate (OOS/IS > 3.0) present
  per `feedback_v3_oos_is_ratio_gate.md`. PASS.

- Section 5 (Risk Mitigation): PASS — 7-gate RiskV2 stack unchanged table, two
  architecture-specific risk notes (BCH/TRX dilution quantified from EDA; concentration
  analysis). Correctly notes no new gate is added, no new IS-calibrated threshold
  simulation required. OOD covariance architecture consequence (pooled covariance)
  noted as consequence, not new gate. PASS.

- Section 6 (Risk Management Design): PASS — 7-primitive table with /059 state,
  iter-v3/112 state, and predicted fire-rate change per primitive. Regime coverage
  paragraph (FTX/LUNA crash, 2023 chop, 2024 recovery, 2025 uptrend). PASS.

- Section 7 (Pre-Registered Failure-Mode Prediction): PASS — two failure modes with
  forward-looking narrative: (1) BCH/TRX dilution outweighs LDO rescue
  (trade-count-weighted net negative); (2) LDO rescue does not transfer through
  production machinery. NEGATIVE probability pre-registered at ~50%. EXPLORATION-mode
  DSR/PSR correctly flagged as structural artifact per
  `feedback_v3_dsr_mode_artifact.md`. PASS.

- Section 8 (Pre-Registered MERGE/NO-MERGE Criteria): PASS — locked thresholds
  pre-registered before Phase-6 backtest. Four outcome categories: PROMISING (IS Δ ≥
  +0.10 AND OOS Δ ≥ +0.20 AND frac_positive_paths ≥ 0.50 AND LDO OOS net_pnl_pct
  improves AND OOS/IS ≤ 3.0), PROMISING-PARTIAL, SUSPICIOUS, NEGATIVE. EXPLORATION
  confirmed as non-BASELINE_V3.md-updating. PASS.

- Section 9 (Library Stack Declaration): PASS — 8-library table with versions
  (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0,
  scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1). No new library introduced.
  CPCV/PBO/PSR/DSR via existing `validation_v3.py` unchanged. Walk-forward embargo
  fix `e149e9d` confirmed inherited unchanged. PASS.

- Section 10 (QR Audit Trail): PASS — EDA commit SHA `2cead80` cited, 3 scripts
  named, NO-GO aggregate result honestly documented (T5: pooled AUC lift −0.0008),
  axis call justified via PRIME DIRECTIVE (mixed EDA → sharpen hypothesis → run
  backtest). No prior orchestrator setup commit was superseded. PASS.

---

## Section 3.5 Pooled-Model Feasibility Assessment

**The Section 3.5 feasibility claim (LOW-RISK) is CONFIRMED by code inspection.**
The brief's core architectural assertions are correct:

1. `LightGbmStrategy.compute_features(master)` (lgbm.py:253) stores `_master`,
   `_sym_arr`, `_open_time_arr` directly from whatever panel it receives — no
   per-symbol assumption at this layer. CONFIRMED.

2. `LightGbmStrategy._train_for_month` (lgbm.py:333) selects training rows by
   time window (`_open_time_arr >= train_start_ms`), NOT by symbol. Already logs
   `"{n} training samples from {n_unique_syms} symbols"` (lgbm.py:371-372).
   Multi-symbol-panel path is already implemented and exercised. CONFIRMED.

3. `backtest.build_master(config.symbols, ...)` (backtest.py:428) already builds a
   multi-symbol concatenated panel sorted by `(open_time, symbol)` when
   `config.symbols` has multiple symbols. CONFIRMED.

4. A pooled model = ONE `_build_v3_model` call with a 3-symbol `BacktestConfig`
   instead of THREE single-symbol calls. NO new strategy class required. CONFIRMED.

**Implementation reminders for Phase 6 (not blocking — the brief correctly identifies
all of them in Section 3.5 change 5):**

A. `_build_v3_model` currently takes `symbol: str` (single string). The function
   calls `atr_multipliers_for_symbol(symbol)` with that single-string param. The
   pooled build must either (a) pass a canonical single-symbol placeholder
   (acceptable: `V3_ATR_MULTIPLIERS_PER_SYMBOL={}` means all 3 symbols fall back to
   the global (2.0, 1.0) default — passing any BCH/LDO/TRX symbol to
   `atr_multipliers_for_symbol` returns the same default), or (b) accept a tuple.
   The brief's Section 3.5 change 4 recommends the simplest path: set
   `cfg = BacktestConfig(symbols=("BCHUSDT","LDOUSDT","TRXUSDT"))`. The QE must
   resolve the single `atr_multipliers_for_symbol(symbol)` call — this is a 1-line
   decision, not a structural issue.

B. Seven `_build_v3_model(symbol="CRVUSDT", ...)` probe calls in
   `_verify_model_config()` (lines 778, 929, 954, 985, 1024, 1084) AND the
   `_canonical_v059` guard (line 1039) hard-code CRVUSDT/AAVEUSDT/GRTUSDT/ADAUSDT.
   After the `V3_MODELS` revert, `_build_v3_model("CRVUSDT", ...)` will still
   execute (it calls the function, not the parquet) — it won't error at
   `_build_v3_model` construction level, but `_canonical_v059` will immediately
   fire because `_v3_model_symbols` will be `("BCHUSDT","LDOUSDT","TRXUSDT")` and
   the expected tuple is hard-coded as `("CRVUSDT","AAVEUSDT","GRTUSDT","ADAUSDT")`.
   The brief correctly says "the QE must sweep all 24 hard-coded occurrences" — this
   sweep IS required before the runner will pass pre-flight. It is correctly scoped
   in the brief; the "5 concrete changes" count refers to logical changes, not total
   line-edit count. NOT a gate concern — the brief disclosed it.

C. The `_verify_label_leakage_gap()` function currently prints
   "cross-cell gap 88 per 4-sym universe CRV/AAVE/GRT/ADA" — after the revert to
   3 symbols, REQUIRED_GAP will become 66 and `len(V3_MODELS)` will return 3, so
   the assertion `required_gap == REQUIRED_GAP` will pass only if both the constant
   and the `V3_MODELS` tuple are updated consistently. The brief specifies this
   (Section 3.5 change 2). CONFIRMED, not a concern.

D. `label_mode="triple_barrier"` is already set in `_build_v3_model` common_kwargs
   (lgbm.py:1907) and guarded by the iter-v3/111 correction check. The /111
   correction is confirmed preserved in the current codebase. PASS.

**Summary:** Section 3.5 is accurate, honest, and complete. The "LOW-RISK" claim
is substantiated by code inspection. The implementation scope is well-specified —
the 5 logical changes plus the 24-reference sweep constitute the full Phase 6 work.
Phase 6 can proceed on this spec.

---

## Cadence Check

- Cycle-6 EXPLORATION #3 of 10 (iter-v3/120 is the mandatory cycle-6 CONFIRMATION).
- Wall-clock declared ≤ 2h; ENSEMBLE_SIZE=3, n_trials=35, 1 pooled model × 3 seeds
  = 105 total Optuna trials (vs per-symbol baseline 315). Estimate 1.0–1.3h.
- Cadence declared consistent with prior cycle-6 runs (/110: 1.08h, /111: 1.09h).
- PASS.

---

## Single-Axis Discipline Check

ONE axis changed: model architecture (per-symbol → pooled). The universe revert
(BCH/LDO/TRX, REQUIRED_GAP 66) is a mandatory mechanical revert of the CLOSED
/110/111 CRV/AAVE/GRT/ADA universe — it is not a new varied axis; it restores the
/059-canonical comparison base. ITERATION_LABEL, feature stack, labels, risk gates,
ensemble seeds all unchanged. PASS.

---

## Status

OVERALL: PASS. Phase 6 may proceed.
