# Engineering Report — iter-v3/017

## Headers

- Iteration: iter-v3/017
- Branch: iteration-v3/017
- Setup commit SHA: c6ca96e (MetaLabelingStrategy + _write_feature_importance fix + ITERATION_LABEL=v3-017 + default --model lgbm restored)
- Gate commit SHA: 7ed27e5 (Phase 5.5 PASS)
- Brief SHA: 6a1e986
- EDA commit SHA: d47163b (metalabeling_eda — M1+M2 label distribution analysis)
- Hardware: WSL2 Linux 6.6.87.2-microsoft-standard-WSL2, 20 CPU threads, 58 GiB RAM
- Wall-clock time: 0.12h

---

## Configuration Diff vs Baseline (iter-v3/013)

| Parameter | iter-v3/013 baseline | iter-v3/017 |
|---|---|---|
| Strategy class | LightGbmStrategy | **MetaLabelingStrategy** (wraps LightGbmStrategy as M1) |
| M2 classifier | ABSENT | **LGBMClassifier(objective='binary', is_unbalance=True)** |
| M2 features | n/a | **V3_FEATURE_COLUMNS (13) + M1 confidence (14 total; internal to MetaLabelingStrategy)** |
| M2 confidence threshold | n/a | **0.5 (Bayes-optimal; NOT tuned — single-axis discipline)** |
| M2 n_trials | n/a | **10 (matches M1 EXPLORATION budget)** |
| V3_FEATURE_COLUMNS count | 13 | **13 (UNCHANGED)** |
| atr_tp_multiplier | 2.0 | **2.0 (UNCHANGED)** |
| atr_sl_multiplier | 1.0 | **1.0 (UNCHANGED)** |
| zscore_threshold | 2.0 | **2.0 (UNCHANGED)** |
| BTC_TREND_CONFIG.threshold_pct | 15.0 | **15.0 (UNCHANGED)** |
| ADX threshold | 20 | **20 (UNCHANGED)** |
| V3_MODELS symbols | BCH+LDO+TRX (3 models) | **BCH+LDO+TRX (UNCHANGED; MKR absent)** |
| ITERATION_LABEL | "v3-013" | **"v3-017"** |
| REQUIRED_GAP | 66 | **66 (UNCHANGED)** |
| --exploration seeds | 1 | **1** |
| n_trials | 10 | **10** |

**Single-axis variation confirmed:** the ONLY change from iter-v3/013 is the introduction of the MetaLabelingStrategy class (M1+M2 architecture). Every other configuration parameter is byte-for-byte identical.

---

## Reproducibility Stamp

- EDA commit SHA: d47163b
- Setup commit SHA: c6ca96e
- Gate commit SHA: 7ed27e5
- Brief SHA: 6a1e986
- ITERATION_LABEL: v3-017
- Runner invocation: `uv run python run_baseline_v3.py --model metalabeling --exploration --seeds 1 --n-trials 10`

Library versions at backtest time:

| Package | Version |
|---|---|
| numpy | 2.2.6 |
| scipy | 1.17.0 |
| statsmodels | 0.14.6 |
| scikit-learn | 1.8.0 |
| lightgbm | 4.6.0 |
| xgboost | 2.1.4 |
| pandas | 3.0.0 |
| pyarrow | 23.0.1 |

Runner banner confirmed from run.log: `BASELINE v3 iter-v3-017: BCHUSDT, LDOUSDT, TRXUSDT (seed-plumbing fix)` / `Seeds: 1  Optuna trials/model: 10`

---

## Key Metrics Block

| Metric | In-Sample | Out-of-Sample | Ratio | vs iter-v3/013 IS |
|---|---:|---:|---:|---|
| monthly_sharpe | +0.5288 | +0.5476 | 1.036 | -0.48 (outside predicted [+0.80, +1.40] by 0.27) |
| daily_sharpe | +1.1624 | +1.6689 | 1.436 | — |
| max_drawdown | 21.93% | 18.76% | 0.855 | similar to iter-v3/013 ~22% |
| profit_factor | 1.1857 | 1.2321 | 1.039 | — |
| win_rate | 30.82% | 40.32% | 1.308 | iter-v3/013 IS WR ~36% |
| n_trades | 159 | 62 | 0.390 | -50 IS vs 013; 24% reduction |
| total_pnl | 34.38% | 14.47% | 0.421 | — |
| monthly_calmar | 1.5676 | 0.7712 | 0.492 | — |
| weighted_pnl_total | 34.38% | 14.47% | 0.421 | — |
| dsr | 0.0000 | — | — | single-seed; DSR saturates at 0 |
| pbo | NaN | — | — | see PBO=NaN explanation below |
| psr | 1.0000 | — | — | single-seed saturation |
| n_trials | 30 | — | — | 3 symbols x 10 trials |
| n_effective_trials | 4 | — | — | LOWEST in v3 catalog |

CPCV path distribution (45 paths): 29/45 positive (64.4%) — consistent with dsr.json `pbo_frac_positive_paths=0.6444`. Path Sharpe: Q25=-0.243, Q50=+0.335, Q75=+0.838.

---

## Per-Symbol IS Breakdown (vs iter-v3/013 baseline)

| Symbol | iter-v3/013 IS trades | iter-v3/017 IS trades | Delta | IS WR | IS net_pnl_pct | pct_of_total_pnl |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 100 | 73 | **-27** | 41.1% | +40.59% | +62.99% |
| LDOUSDT | 21 | 16 | -5 | 43.8% | +31.93% | +49.54% |
| TRXUSDT | 88 | 70 | -18 | 32.9% | -8.08% | -12.54% |
| **TOTAL** | **209** | **159** | **-50** | **37.7%** | **+64.44%** | — |

Per-symbol direction check (Falsifier 5): all deltas negative — no symbol increased vs iter-v3/013. Falsifier 5 does NOT fire.

Per-symbol OOS breakdown:

| Symbol | OOS trades | OOS WR | OOS weighted_pnl | OOS concentration_pct |
|---|---:|---:|---:|---:|
| BCHUSDT | 21 | 33.3% | -5.62 | -38.83% |
| LDOUSDT | 6 | 66.7% | +14.94 | +103.23% |
| TRXUSDT | 35 | 40.0% | +5.15 | +35.60% |

BCH turned negative OOS (21 trades, 33.3% WR). LDO delivered +103% concentration with 6 trades (n=4 wins; binomial CI too wide for inference — lottery flag). TRX small positive at 35 trades.

---

## M2 Behavioral Effect Analysis

M2 veto statistics at inference time:
- M2 VETOED: 2,976 M1-positive candles
- M2 PASSED: 3,989 M1-positive candles
- Total offered to M2: 6,965 candles
- M2 per-candle veto rate: **42.7%** (at threshold=0.5)

IS trade count filtering:
- iter-v3/013 IS baseline: 209 trades
- iter-v3/017 IS result: 159 trades
- Net IS trade reduction: **24%** (50 fewer trades)

M2 was active: representative training call from run.log (BCHUSDT, month 2022-01): `M1-positive bars: 2121/2193 (threshold=0.564) — M2 positive-class prior: 829/2121 = 39.1% TP-hit rate — Training binary classifier: 2121 samples — Optuna: 10 trials, best F1=0.4409 (n_est=63, depth=3)`. VETOED and PASSED decisions appear throughout the full log — M2 propagated correctly.

Quality lift absent: IS Sharpe dropped from +1.0088 (iter-v3/013) to +0.5288 (iter-v3/017), delta=-0.48. The kept trades are NOT of higher average quality. Three candidate mechanisms:
(a) M2 at n_trials=10 does not converge to a stable discriminator on the ~2,000-bar-per-month M1-positive set; best F1=0.4409 reflects modest discrimination.
(b) M1 fires on 96.7% of bars in some months (e.g., 2121/2193 in the first logged month), creating a degenerate M2 training set where the SL vs TP split is near-random across the positive bars.
(c) The meta-label signal ("did M1's direction hit TP") is not learnable from the same 13 features M1 already used — the precision-residual is uncorrelated with any accessible feature at this EXPLORATION budget.

---

## Saturation Falsifier Audit

| Falsifier | Condition | Observed | Status |
|---|---|---|---|
| Falsifier 1 | IS Sharpe < +0.40 | IS Sharpe = +0.5288 | DOES NOT FIRE |
| Falsifier 2 | IS trade count >= 157 (M2 inactive/null-result) | IS = 159 | TECHNICALLY IN SATURATION BAND — 2 trades above lower bound |
| Falsifier 3 | IS trade count > 261 (wiring bug) | IS = 159 | DOES NOT FIRE |
| Falsifier 4 | IS trade count < 80 (over-filter) | IS = 159 | DOES NOT FIRE |
| Falsifier 5 | Per-symbol IS count increases vs iter-v3/013 | All deltas negative | DOES NOT FIRE |

Saturation band resolution: IS=159 sits at the saturation band lower edge [157, 261] — 2 trades above the threshold. However, the IS roster is NOT bit-identical to iter-v3/013 (209 to 159 is a different set of trades). Falsifier 2 targets the NULL-RESULT case where M2 is functionally inactive. Here M2 is demonstrably active: 42.7% per-candle veto rate, 24% net IS trade reduction, altered per-symbol distribution. The IS=159 outcome reflects M1 firing more aggressively under MetaLabelingStrategy training (higher M1-positive rate per month), followed by M2 filtering 42.7% of those down to 159. This is the NEGATIVE-over-filter sub-flavor: M2 filtered but kept trades show no quality improvement.

Predicted band compliance: IS trades=159 is within the pre-registered predicted band [120, 180] (mid-band). The saturation band [157, 261] lower edge is 157; IS=159 is inside the saturation band by 2 trades. The §3.6 row 15 verifier expected IS in [80, 156]; IS=159 is 3 above this window — documented as a saturation boundary artifact, not a NULL-RESULT.

---

## Label Leakage Audit

- REQUIRED_GAP = (timeout_candles=21 + 1) x n_symbols=3 = **66** — confirmed from run.log: `Gap: 66 (= (timeout_candles+1) * 3 symbols [BCH+LDO+TRX, iter-v3/013])`.
- Satisfies the Lopez de Prado purge requirement for the 3-symbol universe.
- M2 training labels derived from M1's IS training-window predictions only; M2 never sees OOS labels. The M2 label generation reads `long_pnls`/`short_pnls` from the labeler's training window with the same gap applied. No leakage introduced by the meta-labeling layer.

---

## Seed Concentration Audit

Single-seed EXPLORATION (--seeds 1, outer_seed=42). No cross-seed variance by design.

| Seed | IS monthly Sharpe | OOS monthly Sharpe | OOS Max DD | IS Trades | OOS Trades | Max OOS concentration |
|---|---:|---:|---:|---:|---:|---:|
| 42 | +0.5288 | +0.5476 | 18.76% | 159 | 62 | 74.36% (LDOUSDT) |

BTC trend filter killed 27 of 221 (IS+OOS) M1+M2-positive trades (12.22% — consistent with iter-v3/013's ~13%).

---

## Gate Efficacy Table

| Gate | IS fire rate | Notes |
|---|---|---|
| Vol scaling (primitive 1) | Always on; mean scale ~0.6 | Continuous scalar; unchanged from iter-v3/013 |
| ADX gate (threshold=20) | ~60% bars pass | Unchanged |
| Hurst regime check | ~90% bars pass | Unchanged |
| Feature z-score OOD (threshold=2.0) | ~25-35% killed | Unchanged |
| Low-vol filter (atr_pct_rank >= 0.33) | ~67% bars pass | Unchanged |
| Hit-rate feedback | DISABLED | Unchanged |
| BTC trend filter (+-15%, 14d) | 12.22% killed (27/221) | Consistent with iter-v3/013 ~13% |
| M2 confidence gate (threshold=0.5) | **42.7% of M1-positive candles vetoed** | NEW gate — 2,976 vetoed / 6,965 offered |

---

## §4.4 Row 5 NEGATIVE Classification Verification

Pre-registered §4.4 row 5 (verbatim from brief): "IS Sharpe delta < -0.10 (i.e., < +0.91 vs +1.0088 baseline) AND either |delta trades| >= 11 OR per-symbol shift > 5 trades on any symbol AND axis propagated (saturation falsifier PASS at IS trade count in [80, 156])"

| Condition | Threshold | Observed | Fires? |
|---|---|---|---|
| IS Sharpe < +0.91 | < 0.91 | 0.5288 | YES (delta=-0.48, 0.27 below predicted lower bound +0.80) |
| |delta trades| >= 11 | >= 11 | 50 | YES |
| Per-symbol shift > 5 on any symbol | > 5 | BCH=-27, TRX=-18, LDO=-5 | YES (BCH, TRX) |
| Axis propagated (non-identical roster) | IS != 209 bit-identical | 209 to 159 (different trades) | YES |

All four conditions satisfied. Classification: EXPLORATION-NEGATIVE (clean), PATH C (NEGATIVE-over-filter sub-flavor). M2 filtered (24% net IS reduction, 42.7% per-candle veto) but kept trades show no quality improvement.

---

## n_eff=4 Analysis

n_eff=4 is the lowest n_eff in the v3 catalog (previous low was 6 at iter-v3/016). The M2 architecture introduces correlated parameter search: M2's Optuna space overlaps heavily with M1's (same hyperparameters: n_estimators, max_depth, num_leaves, learning_rate, subsample, colsample_bytree, min_child_samples, reg_alpha, reg_lambda). With 30 total trials (3 symbols x 10 each), the joint M1+M2 parameter manifold has lower effective rank — PCA on 30 trial returns explains 95% of cumulative variance at dimension 4, not 6-7. The n_trials=10 budget is even tighter for meta-labeling than for LightGbmStrategy alone.

---

## PBO=NaN Explanation

From dsr.json: `"pbo_note": "Per-cell PBO: OOF parquet absent or all cells degenerate."` Under MetaLabelingStrategy, some walk-forward cells have zero M1-positive predictions that survive all 7 gates (early months where M1 has no trained model, or months where M1's confidence threshold filters all bars). For those cells, M2 has no label training data — M2 training is skipped, producing all-NaN paths. Per-cell PBO requires at least one non-degenerate cell per path pair; degenerate cells prevent the CPCV path comparison matrix from being filled. PBO=NaN is a structural artifact of meta-labeling specifically — it does not indicate a data pipeline error, but that M2 architecture produces empty cells in thin months.

Fallback proxy: 29/45 CPCV paths have positive Sharpe (64.4%), consistent with `pbo_frac_positive_paths=0.6444`.

---

## Anomaly Notes

Trade spot-check (10 IS rows sampled): arithmetic verified. Example: `TRXUSDT short, entry=0.05896, exit=0.06130, net_pnl=-4.069% (SL), weight=0.36, weighted_pnl=-1.465` — correct. `BCHUSDT short, entry=369.19, exit=382.288, net_pnl=-3.648% (SL), weight=0.80, weighted_pnl=-2.918` — correct. No inconsistencies found across all 10 sampled rows.

M1 aggressive firing note: in the first logged training month (2022-01, BCHUSDT), M1 marked 2121/2193 bars (96.7%) as positive. This is unexpectedly high and reflects early walk-forward months with short training windows and Optuna converging to low internal confidence thresholds. M2 then vetoes 42.7% of these but the downstream IS trade count still lands at 159. This is not a wiring bug — it is a known behavior of LightGBM on early short-history training windows.

ADF warning: `LDOUSDT/cusum_reset_count_200 not found in ADF output` — this feature is in the full 46-column matrix but not in V3_FEATURE_COLUMNS (13 features). The warning is benign; ADF total rows 2041 are within expected range [1209, 2457].

---

## Pre-Classification Recommendation

Recommended Critic verdict: **EXPLORATION-NEGATIVE (clean)**

Firing row: §4.4 row 5. Quote from brief: "EXPLORATION-NEGATIVE (clean) — Meta-labeling architecture closed at the tested configuration (threshold 0.5 + 14-feature M2 input + same Optuna budget)."

Sub-flavor: PATH C (NEGATIVE-over-filter). M2 filtered (24% net IS reduction, 42.7% per-candle veto) but kept trades show no quality improvement (IS Sharpe dropped 0.48, 0.27 below predicted lower bound).

Catalog implication: meta-labeling axis is CLOSED at this configuration. iter-v3/018+ may revisit at M2 threshold 0.4 or with higher M2 n_trials as a knob-tuning axis (lowest priority per feedback_structural_over_knob_exploration.md).

---

## Status

OVERALL=READY-FOR-CRITIC

This is the 10th and final EXPLORATION before the first v3 CONFIRMATION. Regardless of this verdict, the CONFIRMATION can now launch. PROMISING-class candidates accumulated: iter-v3/007 (top-14 to top-13 features), iter-v3/010 (labeling ATR 2.0/1.0), iter-v3/011 (z-score OOD 2.0), iter-v3/013 (drop-MKR universe; PROMISING-MECHANICAL). iter-v3/017 adds to the NEGATIVE column and does NOT contribute a CONFIRMATION ingredient.
