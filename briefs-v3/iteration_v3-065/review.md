# Phase 7.5 Critic Review — iter-v3/065

OVERALL: EXPLORATION-PROMISING (SUSPICIOUS-OOS-DOMINANT subtype certified clean; /069 CONFIRMATION advancement candidate)

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle 1 #6 of 10; NON-FEATURE PIVOT; UNIVERSAL LABELING AXIS Path D — SL widened 1.0×ATR → 1.5×ATR universally; TP unchanged 2.0×ATR)

## Per-Check Status

### Foundation Audit (Boot Steps 9-11): PASS

- `walk_forward.py:113` `train_end_ms = test_start_ms - embargo_ms` (post-`5566a69` fix) INTACT. `compute_embargo_candles(10080, 480) = 22` → 22-candle embargo. CV gap reuses helper via `lgbm.py:453-457` (single source of truth).
- `labeling.py::label_trades()` lines 215, 220-223: SL widening 1.0× → 1.5× widens `sl_dist` only; `deadline = close_time_arr[idx] + timeout_ms` is bounded by unchanged 10080-min timeout. Wider SL does NOT extend forward-scan window.
- `lgbm.py:343-360`: `label_tp = self.atr_tp_multiplier`, `label_sl = self.atr_sl_multiplier or self.atr_tp_multiplier / 2.0` correctly threaded.
- `validation_v3.py:54`: `REQUIRED_GAP = 66` UNCHANGED.
- `run_baseline_v3.py:128`: `ITERATION_LABEL = "v3-065"` ✓.
- `run_baseline_v3.py:416-422`: pre-flight assertion bumped to (2.0, 1.5) ✓.
- `run_baseline_v3.py:504-512`: per-symbol fallback assertion for all 3 symbols bumped to (2.0, 1.5) ✓.
- `features_v3/__init__.py:222`: `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5)` ✓.
- `features_v3/__init__.py:133-204`: `V3_FEATURE_COLUMNS_TOP_N` = 14 features BIT-IDENTICAL to /060 anchor.

### Regression Test Confirmation: PASS

features_v3 suite 169 passed, 3 skipped; full suite 293 passed, 3 skipped, 4 pre-existing failures (none /065-induced).

### §11 Anti-Pattern Static Scan: PASS (13/13)

- A1 frozen-baseline: single-seed lineage; pattern not active.
- A2 lookahead shift: no negative shifts in changed paths.
- A3 deadline extension under SL change: `deadline` set from `timeout_ms`, not `sl_dist`. No interaction.
- A4 silent feature reorder: explicit `feature_columns=list(features_for_symbol(symbol))`.
- A5 Optuna n_jobs > 1: n_jobs=1 carried forward.
- A6 CV gap < REQUIRED_GAP: assertion enforces formula match.
- A7 single-seed advance to merge: brief Section 8.3 prohibits direct merge; routed to /069 CONFIRMATION.
- A8 per-symbol customization: V3_ATR_MULTIPLIERS_PER_SYMBOL = {} empty (UNIVERSAL change).
- A9-A10 feature stacking: zero feature changes.
- A11 ORACLE EDA on stateful primitive: labeling is stateless pre-computed transform.
- A12 methodology axis without integration test: brief Section 9 integration test documented.
- A13 post-hoc input traceback: not applicable.

### Check 1 — Look-Ahead Audit: PASS

Verified end-to-end:
- ATR at `regime_v3.py:30-31` uses `tr.ewm(alpha=1/period).mean()` over past-only `_true_range`.
- Labeling consumes `atr_values[idx]` (entry-time-known ATR).
- Wider SL multiplier widens price barrier `sl_dist = atr * 1.5`, not time horizon. Forward-scan deadline `close_time_arr[idx] + timeout_ms` UNCHANGED.
- Walk-forward embargo: 22 candles purged per fold boundary. Symmetric application.

### Check 2 — Embargo Width: PASS

`REQUIRED_GAP = (21+1) × 3 = 66` (López de Prado purge for 3-symbol pooled CV). `cv_gap = embargo_candles × n_symbols = 22 × 3 = 66`. Single source of truth via `compute_embargo_candles`.

### Check 3 — Multiple-Testing Correction: INFORMATIONAL (EXPLORATION-mode artifact)

dsr.json: dsr=0.0 (legacy), pbo=0.1068 (PASS <0.4), psr=1.0, **dsr_relative=0.9203**, frac_positive_paths_gate_pass=true (0.6444). n_trials=315, n_eff=19.

Per `feedback_v3_dsr_mode_artifact.md`: at EXPLORATION n_trials=315, DSR/PSR/DSR_relative are INFORMATIONAL ONLY. The DSR_relative=0.9203 jump from 0.0 (/060) to 0.92 (/065) reflects OOS Sharpe lift relative to architecture-invariant CPCV-Q75 benchmark of 0.8378. The EXPLORATION value cannot be cited as edge significance evidence; CONFIRMATION-mode at /069 will use n_trials=1050 and recalibrate E[max_SR]. PASS for EXPLORATION classification.

### Check 4 — IC Correlation: PASS

`ic_matrix.csv` (14×14) BYTE-IDENTICAL to /060 (labeling change does not alter feature covariance). Pre-existing carve-outs documented (`vwap_dev_20 × regime_momentum_signed_5d = 0.7642` Category 2 composed-feature carve-out). No /065-specific IC redundancy.

### Check 5 — ADF Stationarity: PASS

`adf_test.csv` end-of-training-window 2025-03 row per symbol shows all 14 features stationary (p < 0.05) across BCH/LDO/TRX.

### Check 6 — Gate 10-CPCV: PASS

`cpcv_frac_positive_paths = 0.6444` (PASS @ 0.55). Architecture-invariant.

### Check 7 — Reproducibility: PASS

Setup `6d1c7cf` → impl `176f46f` → pre-flight ATR assertion fix → phase5p5 gate `7bbbf75` → engineering report `ae7bf50`. `ENSEMBLE_SEEDS[0:3] = (191664963, 1662057957, 1405681631)` confirmed in `ensemble_summary.json`. Trade-math spot-check on 2 OOS trades matches to 0.002% rounding.

### Check 8 — Hypothesis-Implementation Alignment: WARN (anchor-value propagation; not BLOCK)

- Brief Section 1 hypothesis correctly matched to implementation: single-variable change `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5)`.
- Section 8.3 LOCKED criteria match observed: IS Δ = -0.16 < +0.10 AND OOS Δ = +0.91 ≥ +0.20 → SUSPICIOUS-OOS-DOMINANT. Classification CORRECT.
- **Anchor-value inconsistency (Critic /064 Rec #1 recurrence)**: Brief Section 2.1 row "n_trades_out_of_sample" correctly cites /060 OOS trades = 102 (`comparison.csv:7`). Brief Section 4.3 behavioral predictor row says ~94, and Engineering Report Section 2.1 propagates the wrong 94 anchor (Δ "-1" instead of correct Δ "-9"). Likely came from /059 multi-seed mean confused with /060. Gate C.7 threshold [60, 130] clears at 93 either way — verdict unchanged — but recurrence flag for Recommendation #1.
- TRX OOS WR discrepancy: `per_symbol.csv` shows 46.3% (19/41); `comparison.csv` shows 43.9%; Engineering Report Section 2.3 reports 43.9%. Source mismatch between trades.csv and per_symbol.csv. Not falsifier-affecting.

### Check 9 — Symbol Exclusion: PASS
### Check 10 — Feature Isolation: PASS
### Check 11 — Forming-Candle: PASS
### Check 12 — Library Version: PASS

### Check 13 — Universal labeling axis specific: PASS with cautions

- SL widening 1.0× → 1.5× changes label distribution (more long-TP, fewer long-SL); does NOT introduce label leakage (forward-scan deadline unchanged).
- CPCV invariance verified: `cpcv_path_sharpe_q75 = 0.8378` IDENTICAL to /060/063/064.
- DSR_relative=0.92 at single-seed EXPLORATION is methodologically valid as a within-EXPLORATION consistency signal but CANNOT be cited as edge significance per `feedback_v3_dsr_mode_artifact.md`.
- Behavioral-effect predictor (Section 4.3): trade-count Δ = +2 IS / -1 OOS, both |Δ|<5 (saturation-falsifier-threshold). Predictor was designed for feature axes; labeling-axis behavioral effect manifests as WR/PnL shifts (+11pp IS, +12pp OOS), not trade-count shifts. Process flag for Recommendation #3.

## Adversarial Findings

### Q1 — Is OOS Sharpe +1.05 magnitude consistent with mechanism or lottery?

Predicted band Section 4.1 was [+0.10, +0.40]; observed +1.05 is 2.6× the upper bound. BCH 39 trades / 59.0% WR = 23 wins, 16 losses (95% CI on WR [42.6%, 73.4%] — wide but distinctly above 50%). Per QE Section 13 #1, attributes to "favorable OOS window for BCH at new label configuration, not structural overfitting." Cross-symbol math: BCH +57.40 + LDO -19.82 + TRX +0.92 = +38.50 net (vs /060 +5.4). The lift is BCH-dominated but LDO improved + TRX flat (not collapsed). Classification SUSPICIOUS-OOS-DOMINANT correctly flags magnitude for /069 validation.

### Q2 — LDO improvement: real or small-sample fluctuation?

/060 LDO OOS: 11 trades, 2 wins, 18.2% WR. /065 LDO OOS: 13 trades, 4 wins, 30.8% WR. The improvement is 4 vs 2 wins out of 13 vs 11 trades. Statistical significance: marginal but directionally consistent with predicted label-noise reduction (EDA T1 predicted LDO long_tp_hit_rate 30.8% under Path D — observed 30.8% exact match). Engineering report Section 13 #2 disclaims breakthrough until /069 multi-seed validation. Adversarially: the EDA T1 prediction was strikingly accurate — supports mechanism over lottery.

### Q3 — BCH OOS concentration 149%

Less extreme than /064 (599%) and /063 (118%). LDO+TRX net OOS PnL = -18.90, BCH +57.40 = +38.50. Concentration 149% reflects BCH carrying the load with LDO/TRX near-zero. /060 BCH IS share = 176.68%; /065 BCH IS share dropped to 93.71% — both clear the 80% one-sided gate, but the IS rebalancing toward TRX+LDO at /065 is structurally informative (universal SL widening helped LDO and TRX participate more in IS PnL).

### Q4 — Brief-vs-implementation parity

V3_FEATURE_COLUMNS_TOP_N at /065 BIT-IDENTICAL to /060 anchor (14 features). DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5) is the SOLE substantive change.

### Q5 — Pre-flight ATR assertion fix

Verified bumped from (2.0, 1.0) to (2.0, 1.5) at run_baseline_v3.py:504 in the pre-flight fix commit. Original /065 launch FAILED on this assertion; fix re-enabled the backtest.

### Q6 — Anchor-value correctness

Section 2.1 anchor table is byte-correct vs /060 comparison.csv. Section 4.3 and Engineering Report Section 2.1 have propagated wrong /059-mean values (OOS trades cited 94 vs actual /060 102). Recurrence of /064 Rec #1 violation; non-verdict-affecting.

## Recommendations to QR

1. **Anchor-value correctness gate STRENGTHENING (Critic /064 Rec #1 carry-forward)**: At /065 the brief Section 2.1 was bit-correct but Section 4.3 and Engineering Report propagated a wrong anchor (OOS=94 vs actual /060=102). The /069 CONFIRMATION brief MUST cite anchor values bit-exactly from `reports-v3/iteration_v3-NNN/comparison.csv:LINE` references in EVERY band-prediction table AND the engineering report's "Headline Metrics" table — not just Section 2.1. Add a Phase 5.5 gate check that every numerical anchor reference appears verbatim in the cited comparison.csv row.

2. **TRX OOS WR source consistency**: `trades.csv` vs `per_symbol.csv` aggregation discrepancy (46.3% vs 43.9% at /065). Engineering reports must declare canonical source for each per-symbol metric and verify trades.csv groupby matches per_symbol.csv published values. Add a unit test asserting bit-identity between these two report files.

3. **Behavioral-effect predictor calibration extension for labeling axes** (per `feedback_v3_axis_saturation_predictor.md` amendment): The Section 4.3 trade-count Δ saturation falsifier was designed for feature axes. For labeling axes, predict per-symbol WR Δ (IS+OOS) with explicit counterfactual bands; saturation = WR Δ within ±2pp at all 3 symbols. The /065 observed WR Δ +11.4pp IS / +12.2pp OOS was not predicted — predict it next time.

4. **/069 CONFIRMATION bundle pre-registration**: SUSPICIOUS-OOS-DOMINANT means the axis is CLOSED-PENDING-CONFIRMATION per Section 8.3 — a /069 candidate but NOT a confirmed PROMISING component. The /069 brief must declare a STRICT MULTI-SEED PASS criterion specific to /065 ingredient: under unified 10-seed ensemble (ENSEMBLE_SIZE=10, full ENSEMBLE_SEEDS tuple), the (2.0, 1.5) universal SL multiplier must produce BOTH (a) IS Sharpe ≥ /059 anchor +1.0894 AND (b) OOS Sharpe ≥ /059 anchor +0.5791 (per `feedback_v3_strict_both_is_oos_baseline.md`). Pre-register FAIL action: if EITHER axis regresses vs /059, /065's universal SL widening is RETIRED to PARKED. Pre-register gate D.x recalibration for universal-axis bundles: per-symbol Δ bands replaced by absolute per-symbol collapse thresholds (WR<15% OOS OR wpnl < -40 OOS OR n_trades<3 OOS).
