# Phase 5.5 Gate — iter-v3/116

OVERALL: PASS

## Iteration Type
TYPE: EXPLORATION
Runner flags: `--exploration --n-trials 35`
ENSEMBLE_SIZE: 3 (first 3 seeds of unified 10-seed lineage)
Wall-clock cap: ≤ 2h
Axis: single (early-exit-on-no-confirmation exit primitive)
Cycle position: cycle-6 EXPLORATION slot #7 of 10 (iter-v3/120 is mandatory CONFIRMATION)

## Cadence Check
- Cadence constraint: 10 EXPLORATIONs before CONFIRMATION (iter-v3/120)
- Cycle-6 EXPLORATIONs filed to date: /110 (slot #1), /111 (slot #2), /112 (slot #3),
  /113 (slot #4), /114 (slot #5), /115 (slot #6) — all NEGATIVE; catalog entries confirmed
- iter-v3/116 is slot #7 of 10: cadence COMPLIANT, 3 slots remain (/117, /118, /119)
- Wall-clock estimate: ~0.70–0.80h based on /113–/115 precedents — UNDER the 2h EXPLORATION cap
- EXPLORATION-mode flags and ENSEMBLE_SIZE=3: CORRECT

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE = 2025-03-24 and training_months = 24 stated explicitly as IMMUTABLE in runner (lines 84–85, confirmed by brief); IS window 24 months ending 2025-03-23; OOS window from 2025-03-24 onward. Confirmed unchanged from /059 canonical.

- Section 0.5 (Iteration Type Declaration): PASS — TYPE=EXPLORATION, `--exploration --n-trials 35`, ENSEMBLE_SIZE=3 (first 3 seeds of unified 10-seed lineage: 191664963, 1662057957, 1405681631), cycle-6 slot #7, anchor iter-v3/060 (IS +0.8325 / OOS +0.1403), canonical baseline v0.v3-059. All required fields present.

- Section 1 (Hypothesis): PASS — One sentence, specific, honest. States the modal outcome is EXPLORATION-NEGATIVE/INERT with explicit mechanism (g2 FAIL: rule cuts below-average winners, not losers). Names the single axis (early-exit-on-no-confirmation), the two scalar parameters (trigger_atr=0.50, k_candles=4), the unchanged estimand (triple-barrier), and the unchanged barrier geometry (2.0/1.0 ATR). The PRIME DIRECTIVE rationale and residual-uncertainty criterion for proceeding despite NO-GO EDA are clearly stated.

- Section 2 (IS-Only Numerical Evidence): PASS — Ten result tables (T1–T10) produced by five committed analysis scripts (commit `52444c9`) in `analysis/iteration_v3-116/`. EDA commit `52444c9` predates the brief commit `5d4cc6d` — temporal fence verified. All scripts assert `close_time < OOS_CUTOFF_MS = 1742774400000`; no OOS-window file read. Three distinct structural axes mapped (A: regime-conditioned barrier — NO-GO at shuffle placebo T3a, 5/6 fail; B: scaled-entry — formal NO-GO, 0/81 cells positive; C: early-exit-on-no-confirmation — the chosen axis). Specific numerical tables provided: T7 grid (chosen cell all-3-positive IS lift), T8 mechanism gate (g2 FAIL confirmed, all 48 cells `cuts_losers=False`), T9 out-of-fold robustness (g3 partial fail on LDO). Evidence is numerical, committed, IS-only, and reproducible. Category-matching absent.

- Section 3 (Proposed Changes): PASS — Enumerated configuration diff vs /059 with every knob explicitly stated. Single substantive axis: new optional exit primitive via three new BacktestConfig fields (default-False). Label mode, barrier multipliers, feature stack, universe, seeds, gates all explicitly confirmed /059-identical. /115 revert for `label_mode` and ATR multipliers explicitly listed in the table. ITERATION_LABEL update specified.

- Section 3.5 (8-Change Feasibility Scope): PASS — see dedicated verification below.

- Section 4 (Expected OOS Impact): PASS — Four pre-registered outcome modes with explicit probability assignments (~55%/~25%/~15%/~5%). Numerical bands anchored on /060 EXPLORATION-mode reference (IS +0.8325 / OOS +0.1403). Explicit falsifiers: IS monthly Sharpe < +0.7325 (Δ < −0.10) fires NEGATIVE; OOS/IS > 3.0 fires SUSPICIOUS; both deltas inside ±0.05 AND no_confirm count < 30 fires INERT. Confidence interval and falsifier present and specific.

- Section 5 (Risk Mitigation): PASS — Five risks enumerated with explicit mitigations. Risk 4 (the /115 carry-over revert) explicitly named with accretion guard mechanism. Risk 5 (Order dataclass extension) addressed via byte-identity integration test. Behavioral-inertia floor (< 30 no_confirm exits) specified as a production-detectable condition. Pre-flight log requirement stated.

- Section 6 (Risk Management Design): PASS — Confirms 7-gate RiskV2 stack UNCHANGED from /059. All nine RiskV2Config knobs enumerated explicitly (zscore_threshold, adx_threshold, adx_threshold_per_symbol, BTC_TREND_CONFIG.threshold_pct, block_long_for, block_short_for, enable_per_symbol_drawdown_brake, enable_ldo_realvol_gate, regime_gate_symbols, enable_regime_gate). Orthogonality of the new exit primitive relative to the gate layer established (gates decide entry; primitive decides when to close an open trade). Stateful-deadlock failure mode (/054) explicitly addressed and correctly excluded (no persistent strategy state updated by the primitive).

- Section 7 (Pre-Registered Failure-Mode Prediction): PASS — Four failure modes, each with: named failure signature, diagnostic metric pattern, and probability estimate. Modal outcome (Mode 1, ~55%) is honest given the g2 FAIL and g3 LDO instability. The IS-collapse/OOS-spike pattern (Mode 3, ~15%) correctly named as the /065/073/114 regime-exposure class. Predictions are forward-looking and verifiable against Phase 8 diary.

- Section 8 (Pre-Registered MERGE/NO-MERGE Criteria): PASS — Five-class taxonomy with explicit first-match-wins evaluation order. Numerical thresholds locked: NEGATIVE fires at IS < +0.7325 OR OOS < −0.10 OR OOS/IS < 0; SUSPICIOUS at OOS/IS > 3.0; INERT at both deltas inside ±0.05 AND no_confirm count < 30; NULL-RESULT at rule fires AND both deltas inside ±0.20 AND ratio ∈ [0.0, 3.0]; PROMISING requires IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 AND frac_positive_paths ≥ 0.50 AND ratio ∈ [0.0, 3.0] AND no_confirm rate ∈ [5%, 25%] AND g2 mechanism holds on ≥ 2/3 symbols. Pre-registration eliminates post-hoc rationalization. PROMISING criterion (f) correctly embeds the g2 mechanism gate.

- Section 9 (Library Stack Declaration): PASS — Full library table with versions. Confirms no new library introduced. Early-exit primitive declared as pure Python in backtest.py. mlfinlab, pypbo, fracdiff correctly deferred to CONFIRMATION (iter-v3/120). No unavailable library claimed.

- Section 10 (QR Audit Trail): PASS — Dispatch's recommended axis (Axis A regime-conditioned barrier) vs chosen axis (Axis C early-exit) documented with explicit pivot rationale backed by the shuffle-placebo NO-GO. All 8 dead-path adjacencies addressed individually with structural distinction for each: /107 (complement mechanism), /065 (opposite direction — narrows not widens), /042 (barrier knob not this), /073 (static per-symbol vs dynamic per-trade state; global not per-symbol-tuned), /074+/114 (entry prevention vs post-entry closure), /079 (size scalar vs path change), /108 (M2 model vs deterministic rule), /115+/072+/105 (label estimand explicitly reverted — CLOSED). ADX axis closure honored. /115 cosmetic-cleanup task explicitly assigned to QE in Section 3.5.

## Section 3.5 — 8-Change Scope Verification

All 8 changes are feasible against the current codebase state:

1. **BacktestConfig 3 new fields** (PASS): Current `BacktestConfig` in `src/crypto_trade/backtest_models.py` (lines 42–77) does NOT contain `enable_no_confirm_exit`, `no_confirm_trigger_atr`, or `no_confirm_k_candles`. The three fields with default-False/0.50/4 defaults are genuinely new additions. Default-False preserves byte-identity with all prior runs.

2. **Order 2 new fields** (PASS): Current `Order` (lines 80–91) does NOT contain `no_confirm_arm_time` or `no_confirm_threshold_price`. Extension with defaults `(0, 0.0)` is binary-compatible — the fields are never read when the flag is False. The frozen dataclass extension is correct.

3. **"no_confirm" exit_reason docstring** (PASS): `TradeResult.exit_reason` (line 103) currently documents `"stop_loss" | "take_profit" | "timeout" | "end_of_data"`. Adding `"no_confirm"` is a docstring update only; the string-typed field accepts any value. Reporting layer groups naturally.

4. **atr_distance from Signal.sl_pct at create_order** (PASS): `Signal` already carries `sl_pct` (line 33). The derivation `atr_distance = entry_price * sl_pct / 100.0` at order creation is correct for the v3 `sl_mult=1.0` canonical. No new `Signal` field required.

5. **create_order populate new Order fields** (PASS): The brief's pseudocode for `create_order` is mechanically correct. The `interval_ms` derivation `timeout_minutes // 21 * 60_000` gives 8h (28,800,000 ms) for the v3 10080-minute timeout. Conditional on `enable_no_confirm_exit and signal.sl_pct is not None`.

6. **Order-loop mutable confirmed dict** (PASS): The placement ordering (TP/SL check → no_confirm check → timeout check) is correct per the brief. The mutable side dict keyed by `id(Order)` is the standard pattern for annotating frozen dataclasses. Scope: one walk-forward symbol-month loop; cleared on order resolution. Live-engine restart behavior (re-initializes to False, conservative early exit) explicitly noted and acceptable.

7. **Runner setup** (PASS — critical /115 revert confirmed): The runner currently contains (a) `ITERATION_LABEL = "v3-115"` (line 131), (b) `MODEL_SPECS` with `"v3-113-BCH/LDO/TRX"` prefix (lines 197–199), (c) accretion guard asserting `label_mode = "fixed_horizon"` (lines 1094, 1118, 1125, 1191, 1196, 1201), (d) `label_mode="fixed_horizon"` in `_build_v3_model` (line 1991), (e) `atr_tp_multiplier=100.0` / `atr_sl_multiplier=100.0` (lines 1970–1971), (f) stale banner-print `V3_FEATURE_COLUMNS=22` (line 2889). The brief's Change 7 explicitly mandates: update ITERATION_LABEL to `"v3-116"`, fix MODEL_SPECS prefix to `"v3-116-"`, revert accretion guard from `fixed_horizon` to `triple_barrier`, revert `label_mode` to `triple_barrier` in model builder, revert ATR multipliers from 100.0/100.0 to 2.0/1.0, fix banner-print to `V3_FEATURE_COLUMNS=14`, extend accretion guard with three new /116 knobs. The revert is explicit and complete.

8. **Adversarial integration test** (PASS): `tests/test_no_confirm_exit.py` (new file) asserting three paths: confirmed trade proceeds to TP/SL/timeout; non-confirmed trade exits at `"no_confirm"` with candle K close price; `enable_no_confirm_exit=False` produces byte-identical `TradeResult` to control run on synthetic OHLCV. Data-extent-independent (synthetic OHLCV). This is the smoke test required for any new module per the Engineer protocol.

## /115 Revert Verification

CONFIRMED. The brief is explicit and specific on the /115 revert at Section 3.5 Change 7(e):
- `label_mode = "fixed_horizon"` guard entry MUST REVERT to `"triple_barrier"` in the accretion guard
- `atr_tp_multiplier = atr_sl_multiplier = 100.0` MUST REVERT to `(2.0, 1.0)` in `_build_v3_model`
- Three new /116 knobs must be ADDED to the accretion guard
- Pre-flight assertion at Change 7(f): `assert label_mode == "triple_barrier"` explicit

Current runner state (confirmed by grep): `label_mode="fixed_horizon"` at lines 1094, 1191, 1991; `atr_tp_multiplier=100.0`/`atr_sl_multiplier=100.0` at lines 1970–1971. The revert is a genuine, non-trivial, required code change. If the QE fails to revert these, the backtest runs the /115 axis confounding the new exit primitive — the /110 stale-knob failure mode. The brief has anticipated this risk explicitly in Section 5 Risk 4 and the accretion guard Change 7(e).

## Provenance Discipline Verification

PASS. Both hand-chosen scalars are correctly declared per `feedback_v3_brief_parameter_provenance.md`:

- `trigger_atr = 0.50`: DECLARED hand-chosen (Section 0 explicit). Justification: round-number midpoint of the swept [0.25, 0.50, 0.75, 1.00] grid; chosen for the all-3-positive-IS-lift property of the `(0.50, 4)` cell in T7 (the only such cell in the 16-cell grid), NOT for being the per-symbol grid optimum (per-symbol optima from T9: BCH 0.50, LDO 1.00, TRX 0.50 — using per-symbol optima would be the closed /073 axis). Source: `T7_early_exit_grid.csv` (commit `52444c9`).

- `k_candles = 4`: DECLARED hand-chosen (Section 0 explicit). Justification: selected at the same T7 cell for the all-3-positive property and for being approximately the median holding time of the static triple-barrier book (T6_confirm_separates.csv) — the "fast-confirm or cut" window covering the first third of the 21-candle timeout. Source: `T7_early_exit_grid.csv` and `T6_confirm_separates.csv` (commit `52444c9`).

No parameter is laundered as a sweep optimum or an Optuna output. The EDA commit `52444c9` predates the brief commit `5d4cc6d` (ancestry-path confirmed). The OOS annex pattern used at /115 is correctly omitted (no OOS-window EDA produced; the temporal fence is commit ordering + IS-only assertion in every analysis script).

## Reasons

No BLOCK conditions. All 10 mandatory sections PASS. The gate file records one informational note:

- INFORMATIONAL: The brief's Section 3.5 Change 7 is unusually long (8 sub-items) for an EXPLORATION. This is appropriate — the /115 revert is substantial (accretion guard + model builder + ATR multipliers + label_mode) and the cosmetic cleanup is pre-committed Critic Rec 2 from /115. The scope is enumerated precisely. The QE should treat the revert as the first task in Phase 6 setup, before adding the new /116 fields, to avoid confounding.

- INFORMATIONAL: The mutable `confirmed` dict in Change 6 uses `id(Order)` as the key. The QE must ensure the dict is scoped correctly per symbol-month loop (not shared across symbols or walk-forward months) to prevent stale confirmation state leaking between loop iterations. The brief notes "cleared when the order resolves" — the QE should verify the dict is also cleared at the start of each walk-forward month.
