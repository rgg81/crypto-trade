# Phase 7.5 Critic Review — iter-v3/068

OVERALL: MERGE (NEGATIVE certified clean — methodologically sound)

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle 1 #9 of 10; NON-FEATURE PIVOT continuation — LABELING TIMEOUT axis Path C: timeout 10080→20160 minutes / 21→42 candles)

## Disposition

NEGATIVE classification certified clean. The catastrophic LDO OOS (1/12 WR, -38.98 wpnl) and OOS MaxDD doubling (34.53%→62.76%) are attributable to legitimate axis-induced model degradation, NOT silent bugs. Section 8.4 disjunctive-OR + Section 8.5 NEGATIVE-EMBARGO-COUPLED sub-mode fired exactly as Section 7 calibrated (25% NEGATIVE tail).

## Foundation Audit (Boot Steps 9-11): PASS

- `walk_forward.py:113` lookahead fix INTACT (`train_end_ms = test_start_ms - embargo_ms`)
- `compute_embargo_candles(20160, 480) = 43` per formula
- `validation_v3.REQUIRED_GAP = (42+1)*3 = 129` (line 56)
- `lgbm.py:458-460` recomputes `cv_gap = compute_embargo_candles * n_symbols` → 43*3=129
- Embargo math: `embargo_ms (1,238,400,000) > timeout_ms (1,209,600,000)` by exactly 1 candle (480 min) — canonical López de Prado purge buffer. **No look-ahead.**
- `run_baseline_v3.py:128` ITERATION_LABEL="v3-068"; `:721-738` label_timeout=20160 runtime assertion ENFORCED; `:706-714` inference_threshold_floor==0.0 ENFORCED (reverts /067)
- V3_FEATURE_COLUMNS_TOP_N=14 unchanged

## §11 Anti-Pattern Static Scan: PASS

Track isolation clean; sacred constants intact; explicit feature_columns list (no auto-discovery); V3_EXCLUDED_SYMBOLS enforced; forming-candle filter active.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

Forward-scan walk at `labeling.py:240-280`: `deadline = close_time_arr[idx] + timeout_ms`; for-else terminator labels `-2` (timeout) when scan exceeds end-of-symbol data; numpy bounds-checked. embargo_ms strictly exceeds timeout_ms by 1 candle — canonical purge. Labels generated at rightmost training candle cannot reach into test month.

### Check 2 — Embargo Width: PASS

REQUIRED_GAP=129=(42+1)*3 verified at all 3 call sites (validation_v3.py, run_baseline_v3.py, lgbm.py). Single source of truth via compute_embargo_candles. Doubling cost ~3-5% training samples per WF cell (pre-disclosed at brief T6 Section 2.7). NEGATIVE-EMBARGO-COUPLED sub-mode anticipated.

### Check 3 — Multiple-Testing Correction: PARTIAL FAIL (informational at EXPLORATION)

- DSR=0.0 structural artifact (n_trials=315)
- **PBO=0.0747 PASS** (threshold <0.4; improved from /060's 0.1278)
- **PSR=0.0000 FAIL** (threshold >0.95; collapsed from /060's 0.9763)

PSR=0.0 is mathematically sound: with mean weighted_pnl=-0.1417 (negative), raw_sharpe_oos<0, z<0, Φ(z)→tiny → 0.0 at 4dp. Sign-flip in observed_sharpe IS the proximate cause. Per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION DSR/PSR are informational only.

### Check 4 — IC Correlation: PASS (no new features at /068)

Pre-existing max |IC| = 0.7642 (regime_momentum_signed_5d × vwap_dev_20) is inherited from BASELINE_V3.md, not /068. Established composed-feature carve-out.

### Check 5 — ADF Stationarity: PASS

adf_test.csv 2199 rows; 1803 stationary; False entries concentrated in early-2020 warm-up months (NaN p_value). All 14 features stationary at end-of-IS window.

### Check 6 — Pareto Dominance: N/A (single-seed EXPLORATION)

### Check 7 — Reproducibility: PASS

- Commit SHAs verified (setup `0e9eb30`, EDA `c16d53c`)
- ITERATION_LABEL="v3-068"
- ensemble_seeds explicit list; feature_columns explicit list
- Trade-math spot-checks (2 OOS rows): both match CSV to ±0.0006%
- Library versions per phase5p5 PASS

### Check 8 — Hypothesis-Implementation Alignment: PASS

- Brief Section 1 hypothesis correctly matched to implementation
- Single-axis discipline: only label_timeout_minutes changed (with /067 floor revert + REQUIRED_GAP recalculation)
- Section 7 pre-registered probabilities: NEGATIVE 25%, INERT 50%, PROMISING 15%, SUSPICIOUS-OOS 10%. NEGATIVE HIT (25% mass).
- Section 8.4 disjunctive-OR triggered (both gates): IS Δ -0.35 < -0.20 AND OOS Δ -0.48 < -0.30.

**Prediction-band miscalibration**: Section 2.5 T4 predicted IS Δ [-0.10, +0.10] / OOS Δ [-0.15, +0.15]. Observed -0.35/-0.48 are 2-3× the lower bound. Section 7 NEGATIVE expected-metrics text IS consistent with observed (matches the floor of the disjunctive-OR gate), but the MAGNITUDE was under-quantified. Process-level finding for future labeling-DURATION axes.

## Adversarial Questions Resolved

### Q1 — OOS MaxDD jump (34.53% → 62.76%): structural attribution

Trades remain barrier-bound (most close within 1-7 candles via TP/SL), NOT timeout-bound. MaxDD doubling is NOT mechanically explained by longer-held trades. Instead reflects Optuna re-converging under doubled embargo to a model that picks WORSE OOS trades (lower per-trade quality). 62.76% across 102 trades consistent with the 14-week LDO+TRX bleed period. Section 8.5 NEGATIVE-EMBARGO-COUPLED pre-registered sub-mode fits.

### Q2 — LDO 8.3% OOS WR catastrophe: axis-driven or methodology?

Pure axis-driven. Only row 12 is a TP (+11.17 pnl_pct); other 11 are stop_loss exits. Brief T3 predicted LDO=INSENSITIVE at first-order (zero LDO timeouts at K=21 in /060); /068 LDO effect comes from SECOND-ORDER Optuna re-convergence under doubled embargo. LDO has lowest absolute trade count (9 IS, 11 OOS at /060) — training-sample loss hits LDO hardest. With fewer training labels + larger noise floor, Optuna at n_trials=35 cannot distinguish signal from noise → degenerate model. Third consecutive cycle 1 LDO catastrophe (/060 18.2%, /064 7.1%, /068 8.3%).

### Q3 — PSR=0.0 sanity check

Mathematically sound: negative mean → negative raw_sharpe → z<0 → Φ(z)→tiny → 0.0 at 4dp rounding. /060 PSR=0.976 (OOS positive) vs /068 PSR=0.0 (OOS negative); sign-flip in observed_sharpe IS proximate cause.

### Q4 — Anchor-byte correctness (Critic /064-067 Rec #1 recurrence check)

CLEAN. All T0 anchor values byte-exact against `reports-v3/iteration_v3-060/comparison.csv`. No recurrence of /065 13× anchor error pattern at /066/067/068.

## Adversarial Findings (Non-Blocking)

1. **Prediction-band miscalibration**: T4 predicted bands under-quantified embargo-coupled cost by 2-3×. Future labeling-DURATION axes should pre-register full [-0.50, +0.50] envelope.

2. **IS trade count 184 vs predicted [134, 179]**: marginal +3% over. Second-order Optuna re-convergence per brief Section 2.5 T4.

3. **n_effective_trials drop 19→18**: within noise floor.

4. **Pre-existing IC violation**: vwap_dev_20 × regime_momentum_signed_5d = 0.7642 (inherited from /059 baseline; established carve-out, not introduced at /068).

## Recommendations to QR

1. **Pre-register magnitude bands wider for labeling-axis EXPLORATIONs** (per F1). T4 bands [-0.10,+0.10]/[-0.15,+0.15] were under-quantified by 2-3×. Future axes pre-register [-0.50, +0.50] envelope.

2. **Address inherited IC violation at /070 CONFIRMATION bundle composition**. vwap_dev_20 × regime_momentum_signed_5d = 0.7642 is a structurally inherited /059 baseline issue. Document or address explicitly in /070 bundle review.

3. **LDO weakness pattern across /060 (18.2%) / /064 (7.1%) / /068 (8.3%) WR demands LDO-targeted axis at /069 or post-/070**. Three consecutive cycle 1 OOS failures. Escalate to feature/model axis (NOT labeling-timeout/SL — those are closed). Candidates: LDO-only feature_columns variation, LDO-only ATR labeling override, or universe expansion to dilute concentration via denominator-expansion per `feedback_v3_concentration_is_signal.md`.
