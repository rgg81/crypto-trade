# Phase 7.5 Critic Review — iter-v3/067

OVERALL: EXPLORATION-MERGE (INERT-AT-EXPLORATION certified clean)

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle 1 #8 of 10; NON-FEATURE PIVOT CONTINUATION — ENSEMBLE PARAMETERS axis; Path D inference_threshold_floor=0.60)

## Foundation Audit (Boot Steps 9-11): PASS

- `walk_forward.py:113` lookahead fix INTACT: `train_end_ms = test_start_ms - embargo_ms`
- `lgbm.py:144` `inference_threshold_floor: float = 0.0` param added
- `lgbm.py:188` stored as `self._inference_threshold_floor`
- `lgbm.py:515-517` floor applied via `max(np.mean(self._confidence_thresholds), self._inference_threshold_floor)` at aggregation
- `run_baseline_v3.py:128` ITERATION_LABEL="v3-067"
- `run_baseline_v3.py:1424-1428` `inference_threshold_floor=0.60` passed to LightGbmStrategy only (XGBoost/metalabeling untouched)
- `run_baseline_v3.py:1475` vol_scale_ceiling NOT set in RiskV2Config — defaults to 1.0 (explicit revert of /066 0.8)
- `features_v3/__init__.py:222` DEFAULT_ATR_MULTIPLIERS=(2.0, 1.0) UNCHANGED
- V3_FEATURE_COLUMNS_TOP_N=14 BIT-IDENTICAL to /060 anchor
- Runtime assertion at `run_baseline_v3.py:691-732` enforces `_inference_threshold_floor == 0.60` AND `vol_scale_ceiling == 1.0`

## §11 Anti-Pattern Static Scan: CLEAN (13/13)

Track-isolation grep `from crypto_trade.features ` in `features_v3/` returns only same-file docstrings (no actual cross-track imports). V3_EXCLUDED_SYMBOLS audit enforced.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Inference-only change at `lgbm.py:515-517`. No historical-data scan, no feature pipeline modification. Walk-forward embargo unchanged.

### Check 2 — Embargo Width: PASS
Required gap = 22 candles per-symbol = 66 candles cross-symbol. Single-source-of-truth via `compute_embargo_candles()`. UNCHANGED from /060.

### Check 3 — Multiple-Testing Correction: PASS (informational at EXPLORATION)
DSR=0.0 (structural at n_trials=315), PBO=0.1278 (≪0.4), PSR=0.985 informational, frac_positive_paths=0.6444 ≥0.55 Gate-10-CPCV. Per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode DSR/PSR are informational only.

### Check 4 — IC Correlation: PASS
ic_matrix.csv (14×14). No NEW features. Highest pair `regime_momentum_signed_5d × vwap_dev_20 = 0.7642` is established composed-feature carve-out per `feedback_v3_engineered_feature_pivot.md`.

### Check 5 — ADF Stationarity: PASS
adf_test.csv: zero `False` rows in stationary column.

### Check 6 — Pareto Dominance: PASS (replaced by Gate 10-CPCV)
Single-outer-seed-lineage EXPLORATION (3-seed subset). frac_positive_paths=0.6444 ≥ 0.55. CPCV quantiles Q25=-0.243, Q50=+0.335, Q75=+0.838 IDENTICAL to /060.

### Check 7 — Reproducibility: PASS

- Setup `ae50dfd` + brief LOCK `65a9094` + pre-flight fix + EDA `aa5b0c8` all in git log.
- ENSEMBLE_SEEDS subset [191664963, 1662057957, 1405681631] verified in ensemble_summary.json.
- **BCH OOS bit-identity verified**: 37 BCH OOS trades byte-for-byte identical to /060 (open_time, close_time, prices, weight_factor, pnl_pct, weighted_pnl, exit_reason all match). Strongest possible reproducibility signal.
- LDO: 11 of 12 trades byte-identical to /060; 12th is end_of_data boundary artifact.
- TRX: 54 trades identical count; weight differences = vol_scale_ceiling revert (1.0 vs 0.8 at /066), NOT Path D.

### Check 8 — Hypothesis-Implementation Alignment: PASS

Brief Section 1 hypothesis predicted ~45% INERT-AT-EXPLORATION as most likely outcome. Section 7 4-mode table: INERT 45%, PROMISING 25%, NEGATIVE 25%, SUSPICIOUS-OOS 5%. Observed (IS Δ -0.026, OOS Δ +0.012; trade roster -1.89%/+0.98%) PRECISELY matches pre-registered ~45% INERT-AT-EXPLORATION mode. Hypothesis-faking absent: code change at lgbm.py:515-517 exactly implements brief Section 3 Sub-fix 1 Option 1 spec. Path D mechanism non-activation IS the registered mode firing.

### Check 9-12: PASS

### Check 13 — Path D Mechanism Non-Activation: PASS

Three lines of evidence converge to "floor structurally non-binding":

1. **BCH OOS bit-identity** (37 trades byte-for-byte match /060). Floor `max(mean, 0.60)` returns `mean` whenever `mean ≥ 0.60`. For BCH cells, every per-cell Optuna mean was ≥0.60 → floor a no-op → trade roster bit-identical. Implementation correct; axis exhausted at floor=0.60.

2. **LDO delta arithmetic-traceable**: -0.0770 wpnl delta = 0.77 weight × -0.10 fee = exactly -0.0770. The extra LDO trade (line 104) is `end_of_data` at open_time = close_time = 1778716799999 (OOS-final candle), pnl_pct=0.00 with only the entry-fee -0.10% loss. Optuna second-order TPE re-convergence under the (vacuous) floor produced one marginal LDO signal at the OOS-final candle. Data-boundary artifact, not structural regression.

3. **TRX trade count identical (54)**. Weight differences exclusively attributable to vol_scale_ceiling revert per /066 closeout — orthogonal to Path D mechanism.

Implementation at lgbm.py:515-517 is correct. Axis structurally exhausted at floor=0.60 because Optuna's per-cell means re-converged ≥0.60 in nearly all cells. Section 8.2 INERT-AT-EXPLORATION criteria all met.

### Anchor-Byte-Correctness (Critic /066 Rec #1 recurrence check): PASS

Brief Section 2.1 cites:
- BCH OOS +1.9078 → matches `reports-v3/iteration_v3-060/comparison.csv:18`
- LDO OOS -19.7208 → matches comparison.csv:19
- TRX OOS +23.3119 → matches comparison.csv:20
- IS Sharpe +0.8325 / OOS Sharpe +0.1403 / n_trades IS 159 / OOS 102 all match

The /065 brief's 13× anchor-error pattern is NOT present at /067. Phase 5.5 anchor-value gate fired and PASSED.

## Adversarial-Specific Questions

### Q1 — Path D non-activation: structural EDA failure or measurement artifact?

**STRUCTURAL EDA FAILURE**. BCH OOS bit-identity confirms floor returned `mean` (not `floor`) on every BCH cell — every per-cell Optuna mean was ≥0.60. EDA T2 used structural reasoning about Optuna's [0.50, 0.85] search range expecting means below 0.60 in many cells; actual TPE convergence produced means mostly ≥0.60. Methodology lesson: future Path-D-family axes require per-cell threshold persistence (not yet implemented in the runner). No measurement-side problem.

### Q2 — BCH OOS bit-identity vs LDO/TRX shifts: asymmetric binding?

**NOT asymmetric per-symbol binding**. BCH bit-identity confirms floor non-binding for all BCH cells. LDO +1 trade is data-boundary artifact (Optuna re-convergence stochasticity at OOS-end candle). TRX weight differences are vol_scale_ceiling revert (1.0 vs 0.8), not Path D. Shifts are Optuna noise / unrelated revert effects.

### Q3 — Trade-roster -3 IS / +1 OOS: floor binding or noise?

**Optuna re-convergence stochasticity, not floor binding**. The floor changes one variable, propagating through downstream rng-using code. ±3 IS trade drift is normal noise at 3-seed × 35-trial × 38-month-cell scale.

### Q4 — Anchor consistency at /067 (Critic /066 Rec #1 recurrence check)

**COMPLIANT at /067**. Brief Section 2.1 anchor values byte-match /060 comparison.csv. No recurrence of /065 13× anchor error.

## Final Verdict Rationale

iter-v3/067 is a clean **INERT-AT-EXPLORATION** classification:

- Implementation structurally correct
- Mechanism non-activation is the registered ~45% mode firing, not hypothesis-faking
- All Section 4.4 falsifier gates PASS. D.14 saturation falsifier fires by spec (informational). D.15 over-tightening NOT triggered
- BCH OOS bit-identity is the strongest possible reproducibility signal
- /070 CONFIRMATION bundle: /067 correctly EXCLUDED. Confidence-threshold-floor=0.60 family CLOSED.

## Recommendations to QR

1. **Path D family CLOSED at 0.60 — do NOT retest higher floor values without per-cell threshold logging.** Future ensemble-parameter EXPLORATIONs at this axis family must FIRST add threshold logging to the runner (one-line CSV append at `lgbm.py:517` writing `(sym, month, seed, threshold)` per cell) and run that as a methodology-axis EXPLORATION before attempting another floor value.

2. **/068 axis: respect Critic /066 Rec #2 (universal symmetric clip/cap STRUCTURALLY EXHAUSTED) AND Critic /067 (gate-modifier non-activation at single-seed local optimum)**. Cycle 1 has 2 INERT + 1 SUSPICIOUS-OOS-DOMINANT + 2 NEGATIVE on non-feature axes. Cycle-1-fresh axes remaining: universe expansion (4th symbol), labeling variant orthogonal to /065 SL widening (TP ratio or timeout horizon), per-symbol customization (with mandatory IS-preservation pre-falsifier per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`). QR EDA required before commit.

3. **/070 CONFIRMATION bundle composition — pre-register at /069 brief**: current bundle candidates are /065 SL widening (SUSPICIOUS-OOS-DOMINANT, first /070 advancement candidate) + /062 Path B4 (methodology axis, deferred spec). /067 does NOT contribute. Pre-register bundle composition in /069 brief Section 8 to prevent post-hoc rationalization at /070 (per `feedback_v3_iter064_process_lessons.md` Rule 1). If /068-/069 produce no additional PROMISING components, /070 bundle is the 2-component (/065 + /062 Path B4) set — not expanded post-hoc.
