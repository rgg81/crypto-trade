# Phase 5.5 Gate — iter-v3/080

**OVERALL: PASS**

Branch: `iteration-v3/080`
Gate timestamp: 2026-05-16
Gate SHA: (filled by commit)

---

## Per-Section Status

| Section | Status | Notes |
|---|---|---|
| Section 0 (Data Split) | PASS | OOS_CUTOFF_DATE = 2025-03-24, training_months = 24 confirmed unchanged. Re-anchoring to IS +0.8236 / OOS +0.2078 stated with decomposition (IS code-drift −0.0089 from /061 TRX vol_scale_floor + OOS data-extent +0.0675). V3_MODELS = BCH/LDO/TRX confirmed. /059 CONFIRMATION baseline untouched. |
| Section 0.5 (Iteration Type) | PASS | EXPLORATION cycle 2 #10/10. PASSIVE-DIAGNOSTIC type declared with justification. Run mode --exploration, 3-seed, n_trials=35, wall-clock estimate 1.0–1.3h within 2h cap. |
| Section 1 (Hypothesis) | PASS | Single diagnostic hypothesis sentence, precisely stating what changes (persist `confidence` scalar Signal→Order→TradeResult, emit `confidence_distribution.csv`), why (cycle-3 C_REF placement), and the key invariant (bit-identical roster). |
| Section 2 (IS-Only Evidence) | PASS | EDA committed SHA `0029155`. Five quantified tests: TEST A (instrumentation gap — 15 columns, `confidence` absent); TEST B (vol-adjusted barrier is holding-time-extension-family knob on closed axis — 3-iteration table); TEST C (conviction residual support — de-rated IS trades underperformed: −0.18% vs +0.32% mean net_pnl_pct, 27.3% vs 31.8% WR); TEST D (bit-identity proof — IS 159=159, 0/0 keys added/removed); TEST E (holding-time predictor — mechanical identity, 0.000 candle delta). AST self-audit `_grep_no_oos_tuning()` returns PASS. OOS quantities used only for count-only bit-identity proofs. |
| Section 3 (Proposed Changes) | PASS | Exactly two changes enumerated precisely. (1) Primary axis: `confidence` field threading Signal→Order→TradeResult with exact field names, constructor call sites, and `_write_trades_csv` column append specified. `confidence_distribution.csv` schema fully specified (symbol, is_month, conf_bin_lo, conf_bin_hi, n_trades, realized_optuna_conf_threshold). (2) Mandatory baseline-restore: revert lgbm.get_signal line 754 to `weight = 100`, remove conviction_derate import from runner. Single-axis discipline verified. |
| Section 4 (Expected OOS Impact) | PASS | Predicted Δ = 0.000 IS / 0.000 OOS (mechanical identity). Falsifier stated (any non-zero roster key/weight_factor delta beyond ≤+1 OOS data-extent trade → Phase-6 wiring defect). Behavioral-effect predictor (0 IS/OOS roster changes). Holding-time predictor (0.000 candle delta, added/removed sets DEGENERATE-EMPTY). OOS/IS SUSPICIOUS pre-registration: ratio gate > 3.0, OOS-DOMINANT sub-mode threshold defined — predicted ratio 0.2523 mechanically far below gate. |
| Section 5 (Risk Mitigation) | PASS | Two engineering risks identified: (1) Phase-6 wiring defect (mitigated by Section 4.2 falsifier + QE pre-flight + Critic Check 8); (2) look-ahead via new field (structurally impossible — `confidence` sourced from past-only `proba`-derived scalar already in scope). Restoring flat weight=100 noted as risk reduction. |
| Section 6 (Risk Management Design) | PASS | 7-primitive gate table at /060 config. Conviction-derate (primitive 13) explicitly REMOVED. Regime coverage identical to /060. Adversarial test suite enumerated: (a) passive-field behavioral non-effect; (b) static grep for non-forward-copy consumers; (c) weight=100 literal; (d) bit-identity on keys+weight_factor; (e) look-ahead-clean sourcing. |
| Section 7 (Failure-Mode Prediction) | PASS | NULL-RESULT ≈93% expected/intended. SUSPICIOUS mechanically ruled out (≈2% residual = Phase-6 wiring defect probability). INERT ≈5% (benign non-determinism). Bit-identity PROOF justifies sub-base-rate SUSPICIOUS weight per Critic /076 Rec #3 + /077 precedent. Reporting-completeness risk (per-IS-month threshold overlay degeneracy) acknowledged; `confidence` column on trades.csv is the load-bearing deliverable regardless. |
| Section 8 (MERGE/NO-MERGE Criteria) | PASS | Five-class disjunctive taxonomy LOCKED with numerical thresholds: PROMISING (IS≥+0.10, OOS≥+0.20, frac_positive_paths≥0.50), NEGATIVE (IS<−0.10 OR OOS<−0.20), INERT (both shifts in noise band, roster NOT bit-identical), SUSPICIOUS (ratio>3.0 OR OOS-DOMINANT: IS<0 AND OOS≥+0.20), NULL-RESULT (bit-identical roster, shifts ≈0). Evaluation order stated. EXPLORATION-level merge semantics clarified (EXPLORATION-MERGE = diagnostic infrastructure, not edge ingredient, not bundled into /081). |
| Section 9 (Library Stack) | PASS | 8 libraries pinned (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1). No new libraries. `confidence` implementation uses only stdlib csv + numpy (already in stack). |
| Section 10 (QR Audit Trail) | PASS | EDA SHA `0029155` precedes brief. Axis selection provenance documented (2 orchestrator candidates; QR chose candidate #1 via EDA TEST A/B/C). Per-parameter IS-only/a-priori disclosure table present (4 parameters, all a-priori). Setup commit SHA `dec440e` documented. |

---

## Code-Readiness Checks

### CR-1: ITERATION_LABEL

`run_baseline_v3.py` line 128: `ITERATION_LABEL = "v3-080"`. **PASS.**

### CR-2: V3_MODELS

`run_baseline_v3.py` lines 151–154: `V3_MODELS = (("A (BCHUSDT)", "BCHUSDT"), ("C (LDOUSDT)", "LDOUSDT"), ("D (TRXUSDT)", "TRXUSDT"))`. **PASS.**

### CR-3: /079 Conviction-Derate Revert Status (SPLIT — runner DONE, lgbm.py PHASE-6 SCOPE)

The setup commit `dec440e` reverted the **runner side**: removed the `conviction_derate` import from `run_baseline_v3.py` and removed the 3-point pre-flight assertion block. **Runner-side revert: DONE.**

The **`lgbm.py` call-site revert** (`lgbm.py:754`) is **Phase-6 scope** — not in the setup commit, explicitly stated so in the setup commit message and brief Section 10.3. The current `lgbm.py` line 754 still reads:

```python
weight = conviction_derate(confidence)
```

This is the expected pre-Phase-6 state. The `conviction_derate` helper (lines 114–137) remains defined as dead-code-pending-revert. The runner no longer imports it or asserts on it.

**The /079 revert is INCOMPLETE at gate time — this is by design per the QR/brief's Phase-6 scope declaration.** The QE MUST revert line 754 to `weight = 100` before running the backtest. This is the most load-bearing single Phase-6 change: an incomplete revert means the backtest runs with conviction-derate still active, producing a result that is NOT bit-identical to /060 and is misrepresented as NULL-RESULT. The Critic's Check 8 will catch this, but the QE must not ship it.

### CR-4: Bit-Identity Claim Verification — Is `confidence` Provably Pure Passive Metadata?

**The `confidence` field is NOT YET THREADED** — this is Phase-6 scope. Current state:

- `backtest_models.py`: `Signal`, `Order`, `TradeResult` do **not** have a `confidence` field. The current `Signal` dataclass (line 30) has 4 fields: `direction`, `weight`, `tp_pct`, `sl_pct`. No `confidence`.
- `backtest.py`: no `confidence` reference.
- `iteration_report.py` `_write_trades_csv` fields list (lines 98–114): 15 fields, no `"confidence"`.

The brief's Section 3.1 specifies the threading precisely:
1. `Signal` gains `confidence: float | None = None` (frozen dataclass, optional, default None — no existing call site changes).
2. `lgbm.get_signal` return statement gains `confidence=confidence` keyword argument.
3. `Order` gains `confidence: float | None = None`; `make_order`/order-construction copies `signal.confidence`.
4. `TradeResult` gains `confidence: float | None = None`; `make_result` copies `order.confidence`.
5. `_write_trades_csv` appends `"confidence"` to fields list; writes `f"{t.confidence:.6f}"` if non-None else `""`.
6. `_write_confidence_distribution(...)` emits `confidence_distribution.csv`.

**The bit-identity claim is structurally sound if and only if the Phase-6 implementation respects the `None`-default pattern on frozen dataclasses.** The key architectural fact: `Signal` is a frozen dataclass. Adding an optional field with `None` default means ALL existing `Signal(direction=..., weight=..., tp_pct=..., sl_pct=...)` call sites (non-lgbm strategies, tests, etc.) continue to produce objects with `confidence=None`, unchanged on every pre-existing field. Only `lgbm.get_signal` passes `confidence=confidence`. No decision path reads `Signal.confidence`, `Order.confidence`, or `TradeResult.confidence` — the brief Section 3.1 states this explicitly, and the QE's Phase-6 adversarial test (static grep, Section 6(b)) must verify it.

**The bit-identity claim is verifiable and the architecture is correct for a passive metadata field, provided:**
(a) The `confidence` field is added ONLY as an optional trailing field with `None` default.
(b) No existing constructor call site is modified except `lgbm.get_signal`.
(c) No module other than the forward-copy constructors and `_write_trades_csv` reads the attribute.
(d) The `conviction_derate` call at `lgbm.py:754` is reverted to `weight = 100` — this is the single behavioral change needed; without it the bit-identity claim fails immediately.

**ASSESSMENT: The bit-identity claim is provably correct architecture, contingent on clean Phase-6 implementation. No current code violates it; the threading simply does not exist yet.**

### CR-5: Phase-6 Scope — What the QE Must Implement

The setup commit `dec440e` did runner-scope-only work. The following are Phase-6 QE scope (explicitly stated in the setup commit message and brief Section 10.3):

1. **`lgbm.py:754`** — revert `weight = conviction_derate(confidence)` to `weight = 100`. Remove the iter-v3/079 comment block at lines 751–754. The `conviction_derate` helper (lines 114–137) may remain as dead code or be removed — Engineer's call.
2. **`lgbm.py:755`** — add `confidence=confidence` to the `Signal(...)` return (after `Signal` gains the field).
3. **`backtest_models.py`** — add `confidence: float | None = None` to `Signal` (after `sl_pct`), `Order` (after `timeout_time`), and `TradeResult` (after `timeout_time`).
4. **`backtest.py`** — thread `signal.confidence` into `Order` constructor and `order.confidence` into `TradeResult` constructor at `make_order`/`make_result` call sites.
5. **`iteration_report.py`** — append `"confidence"` to `_write_trades_csv` fields list; write the value.
6. **`iteration_report.py` or `run_baseline_v3.py`** — add `_write_confidence_distribution(...)` function emitting `confidence_distribution.csv` (schema: symbol, is_month, conf_bin_lo, conf_bin_hi, n_trades, realized_optuna_conf_threshold).
7. **Tests** — Phase-6 adversarial test suite per Section 6: (a) passive-field non-effect; (b) static grep for non-forward-copy consumers; (c) `weight = 100` literal in `lgbm.get_signal`; (d) bit-identity on keys+weight_factor vs /079 roster; (e) look-ahead-clean sourcing.

### CR-6: Pre-Flight Assertions

The conviction-derate 3-point pre-flight assertion is removed from the runner (setup commit `dec440e`). Remaining pre-flight checks (`_verify_track_isolation`, `_verify_feature_columns`, REQUIRED_GAP assertion, OOF parquet contamination guardrail) are unchanged and intact. **PASS.**

### CR-7: Ruff Check

`uv run ruff check run_baseline_v3.py src/crypto_trade/strategies/ml/` — **All checks passed.** PASS.

### CR-8: Tests

`uv run pytest tests/features_v3/ tests/strategies/ml/ -q` — **376 passed, 3 skipped.** PASS.

### CR-9: Branch Verification

`git branch --show-current` = `iteration-v3/080`. `git rev-parse --show-toplevel` = `/home/roberto/crypto-trade/.worktrees/quant-research`. **PASS.**

---

## Summary

**All 10 brief sections PASS.** All code-readiness checks PASS or are correctly identified as Phase-6 scope per the brief's explicit split.

**The /079 conviction-derate revert is the most load-bearing Phase-6 change.** `lgbm.py:754` must be changed from `weight = conviction_derate(confidence)` to `weight = 100`. This is documented in the setup commit and the brief — it is expected pre-Phase-6 state, not a gap.

**The bit-identity claim is architecturally sound.** The `confidence` field threading adds an optional `None`-default field to three frozen dataclasses; no existing call site changes behavior; no decision path reads the new field. The claim is contingent on clean Phase-6 implementation, which the brief's adversarial test suite (Section 6) is designed to verify.

---

## OVERALL: PASS

Phase 6 may proceed. The QE must implement the five `src/` changes and the adversarial test suite enumerated in CR-5 before running the backtest.
