# Phase 5.5 Gate — iter-v3/075

OVERALL: PASS

---

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24 + training_months=24 confirmed unchanged; IS window [2022-02, 2025-03-24) and OOS window [2025-03-24, 2026-05-XX) in absolute dates; ENSEMBLE_SIZE=3 (EXPLORATION mode) declared.
- Section 0.5 (Iteration Type): PASS — EXPLORATION declared; cycle 2 #5 of 10; cadence note references feedback_v3_strict_10_to_1_cadence.md; CONFIRMATION deferred to iter-v3/081 or later.
- Section 1 (Hypothesis): PASS — one specific testable sentence: a BTC-trend-regime position-SIZE de-rate scalar (0.50) on LDO+TRX when BTC close[t-1] < SMA_270(close)[t-1] lifts IS Sharpe by down-scaling the IS bear/chop drag without extending effective trade holding time, avoiding the IS/OOS regime-divergence factor.
- Section 2 (IS-Only Numerical Evidence): PASS — committed script analysis/iteration_v3-075/axis_selection_eda.py (SHA 9a04f6f); produces T0–T8 + axis_selection_summary.csv + synthesis.md; all tables are IS-only or a-priori derivations; holding-time-effect predictor (T4) present with EXACTLY-0 duration delta confirmed; behavioral-effect predictor (T5) shows ~24 IS / ~32 OOS LDO+TRX trades re-weighted; OOS-tuning defect disclosed and corrected in Section 10; re-run of EDA (2026-05-15) executes clean with all 10 output files produced.
- Section 3 (Proposed Changes): PASS — enumerated: (1) /074 regime-gate REVERT (enable_regime_gate=False, regime_gate_symbols=()); (2) Primitive 12 ON (enable_regime_size_scalar=True, scope LDO+TRX, scalar 0.50, SMA_270); V3_EXCLUDED_SYMBOLS check present (BCH/LDO/TRX pass); single-axis discipline stated; exact code change list (7 items) in Section 3.1; zero change to features, labeling, model, walk-forward harness.
- Section 4 (Expected OOS Impact): PASS — predicted IS Δ +0.14 (CI [+0.08, +0.20]); OOS Δ predicted negative/cost via mechanism derivation with band [-0.20, 0.00]; explicit falsifiers on IS floor (+0.08), OOS floor (-0.20), holding-time predictor (>+1.0 candle shift = bug), behavioral predictor (fires=0 = NULL-RESULT), OOS/IS ratio gate (>3.0 = SUSPICIOUS); BCH byte-identity positive control stated (4.2); behavioral-effect predictor with per-symbol counts (4.4); OOS/IS ratio SUSPICIOUS pre-registration (4.5).
- Section 5 (Risk Mitigation): PASS — past-only discipline; IS-only and a-priori parameters; simulated historical IS effect (T8); scope bound (LDO+TRX only, blast radius limited to de-rating); trade-rate preserved (size scalar deletes no trade); failure-stop falsifiers enumerated.
- Section 6 (Risk Management Design): PASS — 12-primitive table with /075 state for each; fire-rate predictions for Primitive 12 (~24 IS / ~32 OOS LDO+TRX trades, with T5 signal-level vs trade-level distinction); regime coverage analysis (first BTC-macro-conditional SIZING primitive in v3 stack); gate_stats_summary() reporting described.
- Section 7 (Failure-Mode Prediction): PASS — four outcomes pre-registered with probabilities: INERT-AT-EXPLORATION ~45% (OOS cost inside noise band), NEGATIVE-AT-EXPLORATION ~35% (OOS Δ < -0.20), PROMISING-AT-EXPLORATION ~18% (sign-opposite OOS surprise), NULL-RESULT ~2% (scalar never fires), SUSPICIOUS ~0% (mechanically ruled out); process predictions P1/P2/P3 stated.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — LOCKED thresholds; disjunctive evaluation order SUSPICIOUS → NULL-RESULT → NEGATIVE → PROMISING → INERT stated; all five classification bands defined with exact anchor-relative Δ values and absolute Sharpe floors; BCH byte-identity and duration-delta falsifiers embedded in SUSPICIOUS (8.4); this is an EXPLORATION — MERGE/BASELINE update explicitly blocked.
- Section 9 (Library Stack Declaration): PASS — all versions listed (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, sklearn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1); mlfinlab/pypbo/fracdiff not invoked; walk-forward embargo/gap unchanged; integration test scope (9.1) stated — new test_regime_size_scalar.py exercises the full runner path.
- Section 10 (QR Audit Trail): PASS — EDA SHA (9a04f6f), brief SHA (00405c5), setup commit SHA (f170a75) all recorded; OOS-tuning defect in the first EDA pass DISCLOSED in full (Section 10.0) with corrected derivation; orchestrator framing vs QR EDA-driven selection described; re-evaluation justification (Primitive 12 ≠ Primitive 9; different mechanism/stage/classifier); per-symbol IS-axis discipline cross-reference.

---

## Code-Readiness Verification

**1. ITERATION_LABEL:** run_baseline_v3.py line 128: `ITERATION_LABEL = "v3-075"` — PASS.

**2. _build_v3_model RiskV2Config — /074 REVERT:**
- `enable_regime_gate=False` (line 1621) — PASS.
- `regime_gate_symbols=()` (line 1622) — PASS.

**3. _build_v3_model RiskV2Config — Primitive 12:**
- `enable_regime_size_scalar=True` (line 1638) — PASS.
- `regime_size_scalar_symbols=("LDOUSDT", "TRXUSDT")` (line 1639) — PASS.
- `regime_size_scalar_value=0.50` (line 1640) — PASS.
- `regime_size_ma_window=270` (line 1641) — PASS.

**4. _verify_feature_columns pre-flight assertions:**
- Four /074 regime-gate assertions REMOVED; replaced with `enable_regime_gate is False` check (lines 567-580) and `regime_gate_symbols == ()` check — PASS.
- Four NEW Primitive-12 assertions present (lines 589-617): enable_regime_size_scalar is True; regime_size_scalar_symbols == ("LDOUSDT", "TRXUSDT"); regime_size_scalar_value == 0.50; regime_size_ma_window == 270 — PASS.
- Print summary line updated to describe Primitive 12 (lines 618-623) — PASS.

**5. risk_v2.py — RiskV2Config fields:**
- Four Primitive-12 fields present with correct defaults (lines 185-188): enable_regime_size_scalar=False; regime_size_scalar_symbols=(); regime_size_scalar_value=1.0; regime_size_ma_window=270 — PASS.
- __post_init__ validation present (lines 201-209): requires 0 < regime_size_scalar_value <= 1.0 and regime_size_ma_window > 0 when enabled — PASS.
- GateStats.regime_size_scalar_fires field present (line 230) — PASS.

**6. risk_v3.py — RiskV3Wrapper:**
- _build_btc_trend_lookup helper present (line 113); past-only via close.shift(1) before rolling SMA; warm-up bars → 0 (no de-rate) — PASS.
- _build_lookups populates self._btc_trend_lookup when config.enable_regime_size_scalar (line 268) — PASS.
- _regime_size_scalar method present (line 314); searchsorted side="left" - 1 (strictly-less-than past-only contract); returns 1.0 for out-of-scope symbols or no-past-bar cases — PASS.
- get_signal integrates the scalar AFTER the inherited gate cascade and primitive-10 direction-block (line 400); increments regime_size_scalar_fires on fire; returns re-weighted Signal — PASS.
- gate_stats_summary() emits regime_size_scalar_fires and regime_size_scalar_fire_rate per symbol (lines 427-429) — PASS.

**7. Test suite — `uv run pytest tests/strategies/ml/test_regime_size_scalar.py tests/strategies/ml/test_regime_gate.py tests/features_v3/ -q`:** 193 passed, 3 skipped — PASS.

**8. Linter — `uv run ruff check run_baseline_v3.py src/crypto_trade/strategies/ml/risk_v2.py src/crypto_trade/strategies/ml/risk_v3.py`:** All checks passed — PASS.

**9. EDA re-execution — `uv run python analysis/iteration_v3-075/axis_selection_eda.py`:** Completes clean; all 10 output files produced (T0–T8, axis_selection_summary.csv, synthesis.md); T5 scope-filtered counts confirm 24 IS / 32 OOS LDO+TRX trades re-weighted — PASS.

**Stale-assertion risk (noted from /073 + /074 history):** No stale assertions detected. The /074 regime-gate assertions are removed and replaced. The four Primitive-12 assertions match the runner's actual config values exactly.

**Minor note (non-blocking):** The error message text at run_baseline_v3.py line 609 ("largest IS lift clearing the +0.10 PROMISING / -0.20 NEGATIVE classification floors") is a stale description — the de-rate was chosen a-priori, not by IS lift floor. This is error message text only; it does not affect runtime behavior or gate logic. Not blocking.

---

## Reasons (if BLOCK)

None — OVERALL=PASS.

---

## Summary

- All 11 brief sections (0, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10) present and substantive.
- Code matches brief Section 3 exactly: /074 regime-gate reverted to OFF; Primitive 12 enabled for LDO+TRX at SMA_270 / 0.50.
- _verify_feature_columns: stale /074 assertions removed; four /075 Primitive-12 assertions correct.
- Tests: 193 passed, 3 skipped.
- Ruff: all checks passed.
- EDA: re-runs clean; all output files present.

**OVERALL: PASS — Phase 6 may proceed.**
