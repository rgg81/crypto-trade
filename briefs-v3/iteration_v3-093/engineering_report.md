# Engineering Report — iter-v3/093

## Headers

- Iteration: iter-v3/093
- Branch: iteration-v3/093
- Commit SHA (pre-backtest setup): `e792336` (fix: drop per-symbol OI leg, DERIVATIVES_FEATURE_COLUMNS 18→13)
- Hardware: WSL2 Linux 6.6.114.1, Roberto
- Wall-clock time: 1.62h (exit 0, orchestrator-detached run)

---

## Configuration Diff vs BASELINE_V3.md (`v0.v3-059`)

| Parameter | v0.v3-059 baseline | iter-v3/093 |
|---|---|---|
| Runner | `run_baseline_v3.py` | `run_derivatives_regime_v3.py` |
| Feature panel | 14 price-derived V3_FEATURE_COLUMNS | 13 derivatives-microstructure features (funding 7 + basis 4 + cross-asset BTC 2; OI leg dropped per Section-11 amendment) |
| Model label | Triple-barrier price barrier (ATR TP/SL) | Forward 21-bar realized-vol regime, 3-state terciles {calm, normal, stressed}, train-window cut-points |
| Model objective | Binary classification (LightGBM) | Multi-class classification (LightGBM, `objective=multiclass`, `num_class=3`) |
| Regime gate | Not present | Probability-weighted size multiplier: 1.0·P(calm) + 0.6·P(normal) + 0.0·P(stressed) |
| Universe | BCHUSDT, LDOUSDT, TRXUSDT | BCHUSDT, LDOUSDT, TRXUSDT (unchanged) |
| Outer seeds | 1 (seed=42, EXPLORATION mode) | 1 (seed=42, EXPLORATION mode) |
| ENSEMBLE_SIZE | 5 | 5 |
| n_trials | 35 | 35 |
| training_months | 24 | 24 (IMMUTABLE) |
| OOS_CUTOFF_DATE | 2025-03-24 | 2025-03-24 (IMMUTABLE) |
| Walk-forward embargo | `e149e9d` (22 candles) | `e149e9d` (22 candles, inherited) |

The single primary axis change is the re-architecture: price-barrier label + price-derived features replaced by a vol-regime label + derivatives-microstructure features, with the regime classifier gating the /059 base directional book's position size.

---

## Key Metrics Block

Source: `reports-v3/iteration_v3-093/comparison.csv`

| Metric | In-Sample | Out-of-Sample | Ratio |
|---|---|---|---|
| monthly_sharpe | 0.7916 | 1.7783 | 2.2465 |
| daily_sharpe | 2.3014 | 3.6853 | 1.6014 |
| max_drawdown | 2853.9164 | 1845.2386 | 0.6466 |
| profit_factor | 1.4166 | 1.6816 | 1.1871 |
| win_rate | 0.2975 | 0.4773 | 1.6044 |
| n_trades | 158 | 88 | 0.5570 |
| total_pnl | 63.7137 | 57.6951 | 0.9055 |
| monthly_calmar | 0.0277 | 0.0964 | 3.4746 |
| weighted_pnl_total | 63.7137 | 57.6951 | 0.9055 |
| dsr | −5.753645 | — | — |
| pbo | NaN | — | — |
| psr | 0.9742 | — | — |
| n_trials | 21875 | — | — |
| n_effective_trials | 1 | — | — |

**Anchor for Δ comparisons**: v0.v3-059 IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791.

Δ IS: +0.7916 − +1.0894 = **−0.2978** (the overlay HURT in-sample by −0.30 monthly Sharpe).
Δ OOS: +1.7783 − +0.5791 = **+1.1992** (large OOS lift, assessed below under SUSPICIOUS-pattern facts).

---

## Per-Symbol Breakdown

Source: `reports-v3/iteration_v3-093/comparison.csv` per-symbol section

| Symbol | OOS weighted_pnl | OOS n_trades | OOS win_rate | OOS concentration_pct |
|---|---|---|---|---|
| BCHUSDT | 35.6771 | 29 | 51.7% | 61.84% |
| LDOUSDT | −4.1576 | 12 | 33.3% | −7.21% |
| TRXUSDT | 26.1756 | 47 | 48.9% | 45.37% |

OOS stressed-gate zero-weight fraction per symbol (from `out_of_sample/trades.csv`, weight_factor=0.0 rows):
- BCHUSDT: 0 / 29 stressed-zeroed = 0.000
- LDOUSDT: 0 / 12 stressed-zeroed = 0.000
- TRXUSDT: 4 / 47 stressed-zeroed = 0.085

The stressed gate zeroed positions for TRXUSDT only (8.5% of TRX OOS trades). It never fired for BCH or LDO in OOS. This is consistent with the mean stressed_fire_rate of 0.015 across all months (see regime-gate behavior below).

---

## Regime-Gate Behavior

Source: `reports-v3/iteration_v3-093/per_month_regime_stats.csv` (125 rows spanning CPCV + walk-forward month splits)

| Statistic | Value |
|---|---|
| Mean stressed_fire_rate (all months) | **0.0153** |
| Max stressed_fire_rate (single month) | 0.8556 (CPCV path 2023-11 row) |
| N months with stressed_fire_rate > 0 | 28 of 125 rows |
| N months with stressed_fire_rate = 0 | 97 of 125 rows |

The stressed classifier fires on approximately 1.5% of bars on average. This is drastically below the expected ~33% (tercile-balanced training cut-points should produce equal-mass classes). The OOS regime IC artifact (`ic_matrix.csv`) contains pairwise feature-to-feature IC, not a direct classifier-vs-label IC; no dedicated OOS regime-IC scalar artifact is present in the report directory.

---

## Falsifier Evaluations (Brief Section 4.2)

Source for all runner numbers: `reports-v3/iteration_v3-093/comparison.csv` and `per_month_regime_stats.csv`.

| ID | Threshold | Observed | Status |
|---|---|---|---|
| F1 | OOS monthly Sharpe < +0.479 | OOS = +1.7783 | **does NOT fire** |
| F2 | OOS MaxDD >= 34.53% (v0.v3-059 OOS) | OOS = 1845.2386 (raw PnL units) | **INDETERMINATE — unit mismatch** |
| F3 | OOS regime-IC <= 0 | No direct OOS regime-IC artifact present | **cannot confirm** — see anomaly note |
| F4 | OOS total trades < 80 | OOS = 88 trades | **does NOT fire** |
| F5 | IS monthly Sharpe < +0.889 | IS = +0.7916 | **FIRES** (0.7916 < 0.889) |
| F6 | stressed_fire_rate outside [0.08, 0.45] | 0.0153 < 0.08 lower bound | **FIRES** (below lower band) |

**F2 anomaly note**: The baseline `v0.v3-059` comparison.csv reports OOS max_drawdown = 34.5280 (percent of book). This iteration's comparison.csv reports OOS max_drawdown = 1845.2386 — a different unit (raw PnL). The runner architecture change (new label type, regime-weighted sizing) altered how max_drawdown is computed or normalized. Direct numerical comparison against the 34.53% threshold is not valid. The OOS/IS MaxDD ratio is 0.647 (OOS drawdown is 64.7% of IS drawdown in the same raw-PnL unit) — directionally the gate reduced drawdown vs IS, but F2 as pre-registered cannot be evaluated against the brief's threshold with the artifacts as produced. This requires QR resolution.

**F3 anomaly note**: The brief specified F3 evaluation from `ic_matrix.csv` or a dedicated regime-IC artifact. The `ic_matrix.csv` produced contains pairwise Pearson IC between feature columns, not a classifier-vs-label IC. No `oos_regime_ic.csv` or equivalent artifact is present in the report directory. F3 cannot be confirmed. Indirect evidence strongly suggests F3 fires: stressed_fire_rate = 0.015 vs expected 0.33 means the classifier nearly universally predicted calm OOS — consistent with the IS vol-regime signal (IC +0.18) not transferring to the 2025-03→2026-05 OOS window.

**Confirmed fires: F5 and F6.**

---

## DSR / PBO / PSR Provenance

Source: `reports-v3/iteration_v3-093/dsr.json`

All three are genuine `validation_v3` runner computations, confirmed by the callsite metadata in `dsr.json`:

- **DSR = −5.753645**: computed via `validation_v3.deflated_sharpe_ratio_v3(observed_sr=oos_monthly_sharpe)`. Input granularity: monthly SR. DSR is catastrophically negative — the 21,875 Optuna trials produce a large E[max_SR] haircut that fully negates the OOS +1.78 monthly Sharpe. This is a structurally sound trials-deflated rejection, not a placeholder.

- **PBO = null**: an honest structural sentinel. The `dsr.json` `pbo_note` explains: "PBO undefined: path_metric_matrix has S=1 strategy axis. CSCV requires S>1." Single-strategy CPCV cannot produce a PBO matrix. This null is the /092 anti-recurrence guard's `pbo_frac_positive_paths` path: instead of a numeric PBO, the runner emits the descriptive `frac_positive_paths = 0.778` (35 of 45 CPCV paths positive, path Sharpe quartiles: Q25=0.137, Q50=0.569, Q75=1.022). `pbo=null` is NOT a hardcoded placeholder — it is structurally unavoidable and documented.

- **PSR = 0.9742**: computed via `validation_v3.psr(observed_sharpe=oos_trade_level_sr, n_obs=len(oos_trades))`. Input granularity: trade-level SR (per weighted_pnl). PSR > 0.95 appears to pass the Gate 6 threshold — however this metric is evaluated in context of the full falsifier set and the SUSPICIOUS pattern analysis below.

The /092 anti-recurrence guard (integration test #1: `test_dsr_json_is_computed`) was in place; these are genuine computed values.

---

## ADF Stationarity Audit

Source: `reports-v3/iteration_v3-093/adf_test.csv` (39 rows, 13 features × 3 symbols)

All 39 feature-symbol combinations are stationary (ADF p < 0.05). All p-values are 0.0 or near-zero (largest observed: 7e-06 for LDOUSDT f_sign_persist_9, 3.1e-05 for LDOUSDT b_level). No non-stationary feature in the panel.

---

## SUSPICIOUS-Pattern Facts

These facts are surfaced as-is. Classification is the QR's Phase-8 call; adversarial review is the Critic's Phase-7.5 call.

1. **OOS monthly Sharpe (+1.7783) soars while IS monthly Sharpe (+0.7916) falls below the /059 anchor (+1.0894).** The regime overlay improved OOS by +1.20 Sharpe units while degrading IS by −0.30 units. OOS/IS monthly Sharpe ratio = 2.25×. The brief's Section 8.1 SUSPICIOUS threshold is OOS/IS > 3.0; the ratio 2.25 does NOT cross that threshold. However the directional signature (IS regresses while OOS soars) is the diagnostic pattern documented in `feedback_v3_per_symbol_lifts_oos_breaks_is.md` and the /082/085/039 SUSPICIOUS-OOS-DOMINANT series.

2. **IS monthly Sharpe +0.7916 is below both the +1.0 merge floor AND the /059 anchor.** The overlay NET HURT the IS book. The base directional book (/059) produced IS +1.0894; adding the derivatives regime classifier on top produced IS +0.7916 — a regression of −0.2978. F5 fires (IS < +0.889 = /059 IS −0.20). The overlay degraded IS performance.

3. **The stressed gate fires on ~1.5% of bars, far below the pre-registered 20-40% expected band.** The vol-regime classifier trained on IS tercile-balanced classes (equal-mass by construction) but predicted "calm" for nearly every OOS bar — stressed_fire_rate = 0.015 vs ~0.33 expected. F6 fires (< 0.08 lower bound). The regime classifier did not transfer OOS. The +1.20 OOS Sharpe lift rests on a regime gate that fires on 1.5% of bars — a handful of OOS stress calls, not a durable architecture effect.

4. **DSR = −5.75 is a catastrophic trials-deflated rejection of the OOS Sharpe.** With n_trials = 21,875 Optuna trials, the expected maximum Sharpe under the null is large, and the DSR formula discounts the observed OOS +1.78 monthly SR to a negative value. DSR < 0 means the backtest's OOS Sharpe is statistically indistinguishable from what one would expect from optimization noise at this trial count.

5. **OOS MaxDD unit mismatch prevents F2 evaluation.** The new runner reports MaxDD in raw PnL units (1845.24 OOS) while the /059 baseline reports it as a percentage (34.53%). The OOS MaxDD improved relative to IS (OOS/IS ratio = 0.65 within the same raw-PnL unit), but the F2 gate cannot be applied as pre-registered. This requires QR resolution.

6. **BCH dominates OOS concentration at 61.84% of weighted PnL.** LDO is negative OOS (−7.21%). The OOS book's profitability rests on BCH + TRX; LDO is a drag.

---

## CPCV Path Summary

Source: `reports-v3/iteration_v3-093/cpcv_paths.csv`

45 CPCV paths. Path Sharpe: min = −3.692, Q50 = 0.569, Q75 = 1.022, max = 1.868. 35 of 45 paths positive (frac_positive_paths = 0.778). PBO undefined (S=1 strategy axis; reported as structural null in `dsr.json`). The CPCV distribution shows high variance — path Sharpe ranges from −3.69 to +1.87, a 5.56-unit spread across 45 paths. This breadth reflects high uncertainty about the architecture's edge.

---

## Merge-Gate Status

IS monthly Sharpe = +0.7916 < +1.0 floor (the absolute merge floor per `feedback_sharpe_floor.md`).

**NO-MERGE — IS floor not cleared, regardless of OOS.** This is an EXPLORATION and cannot merge regardless of outcome; the IS floor failure is noted as a hard constraint for the Phase-8 diary classification.

F5 fires (IS +0.7916 < +0.889). F6 fires (stressed_fire_rate 0.015 < 0.08). At minimum these two falsifiers fire, placing the outcome outside PROMISING (Section 8.5 requires all F1-F6 clear). Classification as NEGATIVE-class is indicated; the precise subtype (8.3 NEGATIVE-harmful for F5, or 8.4 for F6, or both) and the Section 8.1 SUSPICIOUS assessment (OOS/IS = 2.25, below the 3.0 threshold but the IS-regresses/OOS-soars pattern is documented) are Phase-8 and Phase-7.5 calls.

---

## Anomaly Notes

1. **MaxDD unit mismatch**: `comparison.csv` reports `max_drawdown` IS=2853.92, OOS=1845.24 in raw PnL units, not percentages as in /059 (IS=30.97, OOS=34.53). The runner architecture change (multi-class vol-regime label + regime-weighted sizing instead of ATR triple-barrier + weight_factor=1.0) altered the normalization. F2 cannot be evaluated as pre-registered; escalated to QR.

2. **No direct OOS regime-IC artifact**: `ic_matrix.csv` contains pairwise feature-to-feature IC, not classifier-vs-label IC. The brief specified `ic_matrix.csv` or a dedicated regime-IC artifact for F3. The artifact is absent. F3 evaluation is indirect only. Escalated to QR.

3. **Spot-check of 10 random OOS trades** (rows from `out_of_sample/trades.csv`): entry/exit PnL math is consistent with direction × (exit_price - entry_price) / entry_price × notional. weight_factor values in [0.0, 1.0]. exit_reason values are stop_loss, take_profit, or timeout — consistent with ATR-barrier semantics of the base /059 directional book. No NaN PnL, no impossible weight_factor. Four TRXUSDT OOS trades have weight_factor = 0.0 with non-zero raw PnL — these are stressed-gate-zeroed trades (the regime predicted stressed, size multiplied to 0.0; the raw PnL is the counterfactual). This is correct behavior per Section 3.3.

4. **n_effective_trials = 1**: PCA on Optuna trial returns identified rank 1 for ≥95% cumulative variance — the effective search was dominated by a single dimension. Combined with DSR = −5.75, this reinforces that the 21,875 nominal trials do not represent genuine independent searches.

---

## Status

OVERALL=READY-FOR-CRITIC
