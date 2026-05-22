# Phase 7.5 Critic Review — iter-v3/112 — FINAL (single round — no clarifications requested)

OVERALL: EXPLORATION-NEGATIVE — the pooled-full architecture is OOS-net-negative (−0.7228) and IS-non-viable (−1.1236); 2 of 3 pre-registered Section 4 falsifiers fire and the two aggregate Section 8 PASS criteria both fail. The implementation is clean — the NEGATIVE is a genuine, attributable property of the pooled architecture, not an artifact.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-6 EXPLORATION slot #3 of 10; iter-v3/120 is the mandatory cycle-6 CONFIRMATION)

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
The pooled training path is the novel surface and it is clean. Three independent leakage vectors were traced at source. (a) Walk-forward embargo: the pooled model calls the same `walk_forward.generate_monthly_splits` (`lgbm.py:269`) which sets `train_end_ms = test_start_ms − embargo_ms` with `embargo = compute_embargo_candles(10080, 480) = 22` candles — the `e149e9d` fix is inherited unchanged; `_train_for_month` then selects training rows by `train_start_ms ≤ open_time < train_end_ms`, purely temporal. (b) Cross-symbol label contamination: `label_trades` partitions by symbol (`labeling.py:308-310`) and every row's forward TP/SL/timeout scan walks only that row's own `sym_idx` array — a BCH row's forward scan cannot reach an LDO or TRX candle even though they are interleaved in the same pooled `master`. (c) ATR barrier σ: `_load_atr_for_master` loads each symbol's own `natr_21_raw` from that symbol's own parquet, so triple-barrier widths are symbol-correct on the pooled panel. Features are the /059-canonical 14-feature stack, unchanged. No look-ahead found.

### Check 2 — Embargo Width: PASS
Required gap = `(timeout_candles + 1) × n_symbols = (21+1) × 3 = 66`. The `REQUIRED_GAP` constant is `(21 + 1) * 3 = 66` (`validation_v3.py:76`, reverted from /110-111's 88). `_verify_label_leakage_gap()` independently recomputes `(21+1) × len(V3_MODELS)` with `len(V3_MODELS)=3`; run.log line 26 confirms PASS. The pooled-panel inner CV is also correct: `cv_gap = embargo_candles × n_symbols` where `n_symbols` is detected dynamically from the actual training rows (`lgbm.py:496-497`) — this correctly handles early walk-forward months where the pooled panel has only 2 symbols. Symmetric, dynamically-correct, no boundary contamination introduced by the pooled architecture.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)
`dsr.json`: DSR=0.0, PBO=0.1203, PSR=0.0004, n_trials=315, n_eff=21. PBO=0.1203 clears its <0.4 threshold (frac_positive_paths=0.644). DSR=0.0 and PSR=0.0004 fail their >0.95 thresholds — the expected mechanical consequence of an IS Sharpe of −1.12, and per `feedback_v3_dsr_mode_artifact.md` EXPLORATION-mode DSR/PSR at the 3-seed/35-trial budget are structural regime artifacts, not edge-significance evidence. Per the EXPLORATION protocol, Check 3-edge axis FAILs (DSR/PSR) do NOT trigger the verdict; the PBO axis passes. Flagged for record; not a verdict input.

### Check 4 — IC Correlation: PASS
`ic_matrix.csv` shows `vwap_dev_20 ↔ regime_momentum_signed_5d` |IC| = 0.764, above the 0.70 threshold — but iter-v3/112 adds zero new feature families. The 14-feature `V3_FEATURE_COLUMNS` stack is /059-canonical and verified UNCHANGED. Check 4 tests newly-added families; there are none. The |IC|=0.764 pair is a known baseline-inherited artifact: `regime_momentum_signed_5d` is a Category-2 composed feature which mechanically correlates with its primitives, and per `feedback_v3_engineered_feature_pivot.md` the strict |IC| gate is inapplicable to composed features. Present and accepted since /028. No new redundancy introduced.

### Check 5 — ADF Stationarity: PASS
`adf_test.csv` present with the required schema (2198 rows = 3 symbols × 14 features × [31, 63] months). run.log line 49 reports `1803/2198 (82.0%) cells stationary (p<0.05)`. v3's ADF is a per-(symbol, feature, retraining-month) panel; the first month per symbol shows empty `adf_statistic`/`p_value` and `stationary=False` — the documented "insufficient history for ADF" case, expected, no integrity concern. The features are the /059-canonical stack; no price-derived feature added or modified.

### Check 6 — Pareto Dominance: PASS
Not applicable to an EXPLORATION run under the unified ensemble architecture. Per BASELINE_V3.md, `pareto_front.csv` is no longer produced — the unified architecture yields ONE deterministic trade roster. iter-v3/112 ran `--exploration` (ENSEMBLE_SIZE=3, seeds 191664963/1662057957/1405681631, all outer=42 lineage). No chosen-seed dominance question; the 10-seed pre-MERGE Pareto validation is a CONFIRMATION concern (iter-v3/120).

### Check 7 — Reproducibility: PASS
Four properties verified. (a) Commit SHA: engineering report stamps code-pre-backtest SHA `e38aebdea5aab7dfeb18bedf05d552b3ab5b4ab1`. (b) Explicit `feature_columns`: `_build_v3_model` passes an explicit 14-element list, never `None`. (c) Ensemble seeds literal in `ensemble_summary.json`. (d) PnL spot-check: three random `out_of_sample/trades.csv` rows recomputed independently — Trade 1 (BCH LONG) net −3.8479, weighted −1.3468 ✓; Trade 6 (LDO LONG) net −4.9796, weighted −2.7388 ✓; Trade 11 (BCH SHORT) net −2.8364, weighted −1.3331 ✓. ATR 2:1 barrier geometry holds. No sign errors, no off-by-one.

### Check 8 — Hypothesis-Implementation Alignment: PASS
The headline check, verified at source — the POOLED architecture genuinely ran and the implementation matches the brief's hypothesis with no scope creep. (1) **Pooled-collapse logic confirmed at source:** `_run_single_seed` computes `_is_pooled = len(_labels) > 1 and len(set(_labels)) == 1` (`run_baseline_v3.py:2549`) — detecting all three `V3_MODELS` entries share the `"v3-pooled"` sentinel label — and when pooled builds exactly ONE `_build_v3_model` with `symbol=("BCHUSDT","LDOUSDT","TRXUSDT")` (`:2562-2575`), calling `run_backtest` ONCE; `_build_v3_model` accepts the tuple and sets `BacktestConfig(symbols=symbols_tuple)` so `build_master` concatenates all three panels into one time-sorted pooled `master`. run.log line 62 `MODEL v3-pooled [POOLED: BCHUSDT, LDOUSDT, TRXUSDT]` and line 20937 `v3-pooled [POOLED 3 syms]: 211 trades` confirm a SINGLE pooled LightGbmStrategy, not three per-symbol models. (2) `V3_MODELS` reverted to BCH/LDO/TRX. (3) `REQUIRED_GAP` = 66. (4) `label_mode="triple_barrier"` PRESERVED — set in `_build_v3_model` common_kwargs (`:1939`), enforced by the `_canonical_v059` accretion guard, run.log line 21 confirms `label_mode (iter-v3/111 correction): 'triple_barrier' PASS`; the /111 correction did NOT regress to `trend_scanning`. (5) No scope creep: the only `src/` changes (pooled-collapse logic, universe revert, probe-symbol sweep, `REQUIRED_GAP` constant) are all enumerated in brief Section 3.5. Every code change maps to a brief sentence.

## Verdict Reasoning

The verdict follows mechanically from the pre-registered Section 8 criteria, applied against the /060-lineage EXPLORATION-mode anchor (IS +0.8325 / OOS +0.1403):

- **C1** IS Δ ≥ +0.10 (IS ≥ +0.93): observed IS = **−1.1236** → **FAIL** (Δ = −1.9561).
- **C2** OOS Δ ≥ +0.20 (OOS ≥ +0.34): observed OOS = **−0.7228** → **FAIL** (Δ = −0.8631).
- **Falsifier #1** OOS < −0.10: observed −0.7228 → **FIRES.**
- **Falsifier #3** aggregate IS < +0.40: observed −1.1236 → **FIRES.**

Per Section 8, ANY fired Section 4 falsifier classifies the iteration EXPLORATION-NEGATIVE. Two fire. The pooled-full architecture is closed for cycle 6.

The methodology is sound and the result is attributable. Per-symbol OOS attribution on the stable `net_pnl_pct` metric: BCHUSDT −42.8003 (29 trades, 20.7% WR — the dominant loss driver, well below the 33.3% 2:1-barrier breakeven), TRXUSDT +12.1696 (24 trades, 45.8% WR), LDOUSDT +0.7623 (11 trades, 36.4% WR). The EDA's central mechanism — that pooling rescues the sample-starved LDO — has weak partial support: LDO's OOS `net_pnl_pct` is positive (+0.7623). But the architecture's failure mode is exactly the one the brief pre-registered as the most-plausible OOS failure (Section 7, mode 1): the pooled model's dilution of the sample-rich symbols dominated — BCH (95.76% of /059 IS PnL, the symbol the architecture most needed not to harm) inverted to a −42.80 OOS loss at a 20.7% win rate. The pre-registration is honest and the diagnosis is clean: a PROMISING-mechanism-partially-confirmed-but-net-negative outcome — the Phase-8 diary should record that the LDO-rescue mechanism showed weak transfer (informing a possible partial-pooling axis) while the full pooled architecture is NEGATIVE and non-advancing.

## Clarifications Requested from QR — NONE

Every check is unambiguous. The pooled architecture is verified to have genuinely run at source (Check 8), the look-ahead and embargo surfaces specific to the pooled panel are verified clean (Checks 1, 2), and the EXPLORATION-NEGATIVE verdict follows mechanically from the pre-registered Section 8 falsifiers.

**OVERALL: EXPLORATION-NEGATIVE** — pooled-full model architecture is OOS-net-negative and IS-non-viable; Section 4 falsifiers #1 and #3 fire; Section 8 criteria C1 and C2 fail. Non-advancing; NO-MERGE; BASELINE_V3.md unchanged (canonical `v0.v3-059`). The implementation is clean (Check 8 PASS verified at source), so the NEGATIVE is a genuine, attributable property of the pooled architecture. The QR's Section 7 pre-registered the realized failure mode correctly.

## Recommendations to QR

These are process-level items for the next cycle-6 EXPLORATION (iter-v3/113), not a salvage list for /112 — the verdict is final.

1. The brief's Section 8 anticipated this outcome with an `EXPLORATION-PROMISING-PARTIAL / mechanism-confirmed` category gated on falsifier #2 (LDO rescue transfers) holding while aggregate criteria fail. LDO OOS `net_pnl_pct` = +0.7623 is positive but the EDA's claimed mechanism magnitude is not directly observable as a delta vs the per-symbol BCH/LDO/TRX EXPLORATION-mode LDO from the /112 reports alone. If a partial-pooling axis is pursued at iter-v3/113, the brief must pre-commit a runnable per-symbol EXPLORATION-mode LDO reference so falsifier #2 can be evaluated against a measured baseline, not an inferred one.

2. The pooled architecture diluted BCH — the 95.76%-of-IS-PnL symbol — into a −42.80 OOS loss. The BASELINE_V3.md cycle-1 fragility flag ("an axis that improves LDO and/or TRX but reduces BCH IS contribution will likely collapse the headline IS Sharpe") was correctly cited in brief Section 4 and confirmed by the result. Any iter-v3/113 partial-pooling design (pool only LDO; keep BCH/TRX per-symbol) directly addresses this — it isolates the LDO sample-rescue without exposing BCH to cross-symbol dilution. This is a natural next axis and the EDA's per-symbol-conditional finding already supports it.

3. The EDA's aggregate horse race returned NO-GO (T5: pooled AUC lift −0.0008) and the brief honestly proceeded under THE PRIME DIRECTIVE "sharpened-GO". The realized OOS Δ (−0.8631 vs anchor) landed below the brief's own 80% predicted interval lower bound (point estimate +0.10, interval [−0.30, +0.55]) — an interval miss. For iter-v3/113, when the EDA returns an aggregate NO-GO and only a per-symbol-conditional GO, the predicted-effect interval should weight the aggregate NO-GO more heavily (a per-symbol rescue inside an aggregate AUC wash has historically not transferred net-positive through the production Optuna + 7-gate pipeline — cf. the /111 thin-AUC-margin inversion).
