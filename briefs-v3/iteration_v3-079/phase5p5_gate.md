# Phase 5.5 Gate — iter-v3/079

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` confirmed unchanged. IS window: earliest-available → 2025-03-24. OOS window: 2025-03-24 → present (~2026-05). Re-anchoring to IS +0.8236 / OOS +0.2078 stated with −0.0089/+0.0675 additive decomposition. `V3_MODELS = BCH/LDO/TRX` confirmed in `run_baseline_v3.py` lines 151–155.
- Section 0.5 (Iteration Type): PASS — EXPLORATION, cycle 2 #9 of 10. Single-axis discipline asserted. 2h wall-clock hard cap stated. EXPLORATION does not update BASELINE_V3.md.
- Section 1 (Hypothesis): PASS — ONE sentence: the M1 ensemble computes directional confidence that `get_signal` currently discards (emitting flat `weight=100`); replacing it with a monotone a-priori conviction-DERATE map (bounded [50,100], de-rate-only) lifts IS aggregate Sharpe by shrinking marginal-confidence trades, without IS/OOS regime tension because the map is holding-time-orthogonal, selection-orthogonal, and feature-orthogonal by construction.
- Section 2 (IS-Only Evidence): PASS — committed `analysis/iteration_v3-079/sizing_axis_eda.py` (SHA `0a54acd`, cleanup `b942dc7`, refinement `dc5b723`). PART A falsifies the inverse-vol cross-symbol candidate with numerical tables (T1–T5: IS monthly Sharpe collapse −0.5304). PART B provides T6 per-trade dispersion, T7 conviction-blindness of current sizing (pooled corr +0.094, TRX −0.141 wrong-sign), T8 holding-time degeneracy proof (0 trades added/removed). EDA confirmed IS-data-only; OOS roster read exactly once in T8 for trade-count only, no OOS metric selects any design parameter. EDA limitation (per-trade confidence not persisted) honestly disclosed (Section 2.6).
- Section 3 (Proposed Changes): PASS — Section 3.1 specifies the conviction-DERATE map formula, the three a-priori constants (C_FLOOR=0.50, C_REF=0.65, W_MIN_FRAC=0.50), the exact application point in `lgbm.py:get_signal` (after the existing confidence-threshold gate, before the `Signal(...)` return at line ~725), the `confidence` variable already in scope (lines 646–650), de-rate-only property, bounded [50,100], monotone non-decreasing. Section 3.2 delineates QR setup-commit scope (runner config) vs QE Phase-6 scope (`lgbm.py` map + wiring + adversarial test). Section 3.3 confirms single-axis discipline with V3_MODELS revert as baseline-restore.
- Section 4 (Expected OOS Impact): PASS — Central prediction IS Δ +0.05 to +0.20 (central +0.12) / OOS Δ −0.10 to +0.20 (central +0.05). Primary falsifier: IS Δ < +0.05. Behavioral-effect predictor: ≥25% IS trades de-rated, falsifier <15%. Holding-time predictor: exactly 0.000 candle delta. Added-vs-removed roster sub-channel: DEGENERATE (0 added / 0 removed). OOS/IS ratio SUSPICIOUS: >3.0. OOS-DOMINANT sub-mode: IS shift <0 AND OOS shift ≥+0.20.
- Section 5 (Risk Mitigation): PASS — Four R-properties: gross-exposure-neutral-or-lower (de-rate-only, W_MAX=100); bounded floor (W_MIN_FRAC=0.50, no trade dropped); composes multiplicatively with existing 7-primitive stack; IS-calibrated behavioral bound via Section 4.3 fire-rate band. Honest statement that per-trade-level simulation is Phase-6 scope (confidence not persisted in EDA artifacts).
- Section 6 (Risk Management Design): PASS — 7-primitive RiskV3 gate stack unchanged. Primitive 13 (conviction-derate) in table: type (per-trade weight scalar, de-rate only), scope (all 3 symbols, all directions), fire-rate prediction (≥25% IS trades de-rated, falsifier <15%), regime coverage (regime-neutral by construction). QE Phase-6 adversarial test items enumerated (monotonicity, boundary values, roster bit-identity, look-ahead-clean).
- Section 7 (Failure-Mode Prediction): PASS — Three failure modes with calibrated probabilities: INERT-AT-EXPLORATION ≈40% (modal honest outcome; confidence not proven informative), SUSPICIOUS-OOS-DOMINANT ≈45% (floored at cycle-2 base rate 4/8=50%, reduced only by partial structural closure of three of four regime-loading vectors), NULL-RESULT ≈10% (behavioral saturation, all trades ≥0.65 confidence). PROMISING ≈5%. The fourth regime-loading vector (conviction-correlation channel) explicitly disclosed and not dismissed.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — LOCKED disjunctive taxonomy evaluated in order SUSPICIOUS → NULL-RESULT → NEGATIVE → PROMISING → INERT. Section 8.1–8.5 each have locked numerical thresholds. Section 8.4 SUSPICIOUS criteria match Section 4.5 pre-registration. Section 8.5 NULL-RESULT correctly uses de-rated-count discriminator (not roster bit-identity) since key roster is bit-identical by construction. Section 8.6 Phase-6 BLOCK conditions enumerated (roster diff, non-monotone map, look-ahead wiring).
- Section 9 (Library Stack): PASS — No new libraries. Pure arithmetic (`clip`, `round`) on existing `proba` vector. Full pinned stack listed: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1.
- Section 10 (QR Audit Trail — v3 mandatory): PASS — Axis selection provenance documented. Candidate #1 (cross-symbol re-weighting) tested and FALSIFIED first. Candidate #2 (new labeling) rejected for duration-extension risk. Candidate #3 (conviction-weighted sizing) selected on EDA-backed structural grounds. Per-parameter IS-only / a-priori selection-function table in Section 10.2: all three numeric parameters confirmed data-free a-priori constants. EDA SHA, brief SHA, setup SHA, SHA-backfill commit SHA all recorded in Section 10.3.

## Code-Readiness Verification

### 1. Runner constants
- `ITERATION_LABEL = "v3-079"` — CONFIRMED at `run_baseline_v3.py` line 128.
- `V3_MODELS` reverted to BCH/LDO/TRX — CONFIRMED at lines 151–155. `/078`'s ADAUSDT removed; LDOUSDT restored. Comment at lines 138–150 documents the revert as a baseline-restore of the closed universe-revision axis.
- `OOS_CUTOFF_DATE = "2025-03-24"` — CONFIRMED line 81.
- `TRAINING_MONTHS = 24` — CONFIRMED line 83.

### 2. Setup commit `3dbbd4b` consistency
The QR setup commit modifies only `run_baseline_v3.py` and `tests/features_v3/test_fracdiff_d05_universal.py`. Specifically:
- All pre-flight assertion sites, smoke-loop symbol tuples, and comment/print strings referencing ADAUSDT were reverted to LDOUSDT.
- The test file was renamed `test_v3_models_at_iter_v3_079`, asserts the BCH/LDO/TRX universe, and updates `_V3_MODELS_ITER_052` accordingly.
- No `src/` model code was touched — the conviction-derate map is correctly left for Phase 6.
- `REQUIRED_GAP = 66 = (21+1) × 3` confirmed unchanged (3 symbols).
- With the conviction-derate flag absent (map not yet implemented), the runner is baseline-identical to the /060 anchor config — no RiskV2Config or conviction flag was added in the setup commit; the `lgbm.py` hardcoded `weight=100` at line 725 is untouched. The runner will therefore reproduce the /060-config baseline on the current code when run before Phase 6 implementation. This is correct workflow: the QE implements the map in Phase 6 and the backtest runs with the map enabled.

### 3. What Phase 6 must implement (exact QE scope)
The QE must implement all of the following in Phase 6, per brief Section 3.1/3.2/6/8.6:

**a. `conviction_derate(confidence)` helper function in `lgbm.py`:**
```
def conviction_derate(confidence: float,
                      c_floor: float = 0.50,
                      c_ref: float = 0.65,
                      w_min_frac: float = 0.50) -> int:
    return round(100 * float(np.clip(
        (confidence - c_floor) / (c_ref - c_floor),
        w_min_frac, 1.0
    )))
```
Exact constants: C_FLOOR=0.50, C_REF=0.65, W_MIN_FRAC=0.50. Returns int in [50, 100].

**b. Wire into `LightGbmStrategy.get_signal` at line ~725:** replace hardcoded `weight=100` with `weight=conviction_derate(confidence)`. The variable `confidence` is already in scope at that line (computed at lines 646–650 from the past-only `proba` vector). No other change to `get_signal`.

**c. Pre-flight assertion in `run_baseline_v3.py`:** assert `conviction_derate(0.50) == 50`, `conviction_derate(0.65) == 100`, `conviction_derate(1.00) == 100` (3-point sanity check). Assert the map is monotone at a representative grid. This fires before the backtest loop.

**d. Adversarial test** (new test file in `tests/strategies/ml/`):
- Assert the map is monotone non-decreasing on a dense confidence grid [0.50, 1.00].
- Assert `conviction_derate(c) == 100` for all `c ≥ 0.65`.
- Assert `conviction_derate(c) == 50` for all `c ≤ 0.50`.
- Assert the map returns an int (Signal.weight contract).
- Assert the `(symbol, open_time)` key roster from a controlled toy backtest is bit-identical whether `weight=100` hardcoded or `weight=conviction_derate(confidence)` — confirming a pure weight scalar adds/removes no trade (Section 8.6 BLOCK condition #1).
- Assert `confidence` is derived solely from the `proba` vector already computed (no future-bar read) — a structural inspection of the call path.

### 4. Lint and test results
- `uv run ruff check run_baseline_v3.py src/crypto_trade/strategies/ml/` — ALL CHECKS PASSED (confirmed).
- `uv run pytest tests/features_v3/ tests/strategies/ml/ -q` — **345 passed, 3 skipped** (confirmed; the conviction-derate map test is not yet written — it is Phase 6 scope, and the suite passes without it since `lgbm.py` still has `weight=100`).

## Reasons

No BLOCK reasons. All 10+0.5 sections PASS. Code-readiness is sound. Brief Section 3.1 is precisely specified — the QE has the formula, constants, application point (`lgbm.py` line ~725), variable already in scope (`confidence`), de-rate-only constraint, and the adversarial test specification.

## Status

OVERALL: PASS — proceed to Phase 6.
