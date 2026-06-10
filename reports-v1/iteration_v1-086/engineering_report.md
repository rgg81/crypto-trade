# Engineering Report — iter-v1/086

## Headers

- Iteration: iter-v1/086
- Branch: iteration-v1/086
- Commit SHA (runner): 5da75fa8 (feat(iter-v1/086): TRBUSDT specialist runner + dispatch)
- HEAD at report time: 17b51b23429f8a1d4725303fd46597f9fc13f2e3
- Hardware: WSL2 (Linux 6.6.114 Microsoft), CPU multi-core
- Wall-clock time: ~6h (runner committed 2026-06-10 06:24 UTC+2; comparison.csv written 2026-06-10 12:25 UTC+2)
- Report generated: 2026-06-10

---

## Configuration Diff vs Baseline (BUNDLE-002 / v1-082)

| Parameter | BUNDLE-002 (v1-082) baseline | iter-v1/086 SPECIALIST |
|---|---|---|
| Symbols | BTC + ETH + DOT + LINK + AAVE (5-coin pool) | TRBUSDT only |
| feature_columns | 48 (V1_FEATURE_COLUMNS_PRUNED) | 48 (V1_FEATURE_COLUMNS_PRUNED, STOCK — NO new features) |
| specialist_mode | True (50-seed) | True (INTENDED 50-seed; actual: 1-seed=42, --seeds 1) |
| n_trials | 30 | 30 |
| ensemble_seeds | [42..91] (50 seeds, BUNDLE) | [42] (1 seed, --seeds 1) |
| ENSEMBLE_SIZE | 1 | 1 |
| max_depth | 5 FIXED | 5 FIXED |
| num_leaves | 31 FIXED | 31 FIXED |
| atr_tp / atr_sl | 2.9 / 1.45 | 2.9 / 1.45 (Model A ETH cell) |
| R1 | OFF (CATALOG-CLOSED) | OFF |
| R2 | OFF | OFF |
| R3 | ON-SHARED cutoff=0.70 | ON-SHARED cutoff=0.70 |
| R5 | ON vt_target_vol=0.3 | ON vt_target_vol=0.3 |
| training_months | 24 | 24 |
| OOS_CUTOFF_DATE | 2025-03-24 | 2025-03-24 (UNCHANGED) |
| new features | none (STOCK 48) | ZERO (explicit one-variable discipline; hash prefix b81176f8) |

**Seeds note**: The runner header advertised `V1_SPECIALIST_SEED_COUNT=50` (the module constant), but was invoked with `--seeds 1`, which the baseline runner maps to `ensemble_seeds=[42]`. The actual backtest used a single outer seed (seed=42). This is confirmed by `basin_diagnostics/v1_cross_seed_variance.csv`: `n_outer_seeds=1, std_sharpe=0.0` (trivially zero — no variance with one seed). The `cross_seed_sharpe_std=0.000` reported by the basin diagnostic is therefore a degenerate artifact of the single-seed dispatch and is NOT evidence of inter-seed agreement or robustness.

---

## Key Metrics Block

| Metric | In-Sample | Out-of-Sample | Ratio |
|---|---|---|---|
| Monthly Sharpe | **-0.3044** | **-0.5967** | 1.9602 |
| Sortino | -0.2662 | -1.2719 | 4.7771 |
| Max Drawdown | 72.95% | 34.47% | 0.4725 |
| Win Rate | 35.7% | 35.6% | 0.9968 |
| Profit Factor | 0.9045 | 0.8555 | 0.9459 |
| Total Trades | 157 | 90 | 0.5732 |
| Calmar Ratio | 0.346 | 0.465 | 1.344 |
| Total Net PnL (%) | -25.24 | -16.03 | 0.635 |
| DSR (corrected) | -59.58 | -38.09 | 0.639 |
| PSR (monthly vs 0) | 0.3545 | 0.3027 | 0.854 |
| PSR (monthly vs 1.0) | 0.0351 | 0.1028 | 2.930 |
| N_eff trials | 1 | 1 | 1.000 |
| R5 fire rate | 0.0000 | 0.0000 | — |
| Vol ceiling fire rate | 0.0000 | 0.0000 | — |

**Baseline comparison (BUNDLE-002 / v1-082)**: IS monthly Sharpe +0.7157, OOS monthly Sharpe +1.0043. This SPECIALIST is deeply below baseline on both windows; it does not qualify for bundle consideration.

---

## THE LOAD-BEARING FINDING: Probe→Full Degradation

### What the probe predicted vs what the full run delivered

The GATE-2 PRIMARY probe (`analysis/iteration_v1-086/probe_TRBUSDT.py`) scored:
- Probe config: seed=42, **n_trials=10**, max_depth=5 FIXED, num_leaves=31 FIXED, same 48-col V1_FEATURE_COLUMNS_PRUNED stack, same atr_tp=2.9/atr_sl=1.45 label, IS-only walk-forward Sharpe.
- **Probe IS monthly Sharpe: +0.4930** → GATE-2 PRIMARY PASS (threshold ≥+0.30).

The full SPECIALIST backtest used:
- Same config in every respect EXCEPT: **n_trials=30** (probe was n_trials=10), single outer seed (seed=42).
- **Full IS monthly Sharpe: -0.3044**.
- **Probe→full degradation: Δ -0.7974**.

### Why seed count is NOT the variable

The runner dispatched `--seeds 1` (ensemble_seeds=[42]), so the full run and the probe used the same single seed (seed=42). The `v1_cross_seed_variance.csv` confirms `n_outer_seeds=1, std_sharpe=0.000` — the zero cross-seed variance is a trivial consequence of running exactly one seed, not evidence of seed agreement or robustness. Seed count cannot explain the -0.7974 degradation.

### Attribution: n_trials=30 overfits a noisy loss surface

With seed held constant at 42, the ONLY difference is `n_trials: 10 → 30`. The deeper Optuna search (30 trials vs 10) explores more of the hyperparameter space. On a structurally weak signal where the IS walk-forward Sharpe surface is noisy, a 3x deeper search finds parameter configurations that exploit IS noise more aggressively — producing higher apparent IS Sharpe on the held-out probe fold but worse walk-forward IS Sharpe in aggregate. This is the overfitting mechanism: n_trials=10 is below the noise-exploitation threshold; n_trials=30 crosses it.

This mirrors the mechanism documented in feedback_v3_inert_features_at_higher_budget.md (iter-v3/023: adding an INERT feature to V3_FEATURE_COLUMNS at n_trials=35 produced OOS Sharpe -1.07 vs +0.78 at n_trials=10, Δ -1.85 — a larger-scale version of the same effect).

### Cross-iteration pattern

| Iteration | Symbol | Probe IS Sharpe (n_trials=10) | Full IS Sharpe (n_trials=30) | Probe→Full Δ |
|---|---|---|---|---|
| v1-085 / UNI | UNIUSDT | -0.243 (GATE-2 REJECT) | -0.7005 | -0.458 |
| v1-086 / TRB | TRBUSDT | **+0.493** (GATE-2 PASS) | **-0.3044** | **-0.797** |

In both cases, the n_trials=30 full run degraded relative to the n_trials=10 probe by approximately 0.5–0.8 Sharpe points. For UNI/085 the probe was already negative (REJECT), so the probe filter worked correctly. For TRB/086 the probe was positive at +0.493 — above the +0.30 threshold — but the full run collapsed to -0.30. The probe at n_trials=10 is a **systematically optimistic predictor** of n_trials=30 performance for this symbol class, with an apparent optimism bias of ~0.5–0.8 Sharpe points.

### Methodological implication for GATE-2 reform

The current GATE-2 PRIMARY design (n_trials=10 probe, threshold ≥+0.30) passed TRB at +0.493 but the n_trials=30 specialist is -0.30. To prevent this class of false pass, one of two reforms is needed:
1. **Probe at n_trials=30** (matching the full specialist budget) — eliminates the probe/full discrepancy at the cost of 3x longer probe time.
2. **Raise the probe threshold to account for the ~0.5–0.8 bias** — e.g., require probe IS Sharpe ≥+0.80 to provide adequate margin for the expected degradation at n_trials=30.

This finding is documented here for the QR's Phase 8 diary and methodology reform decision.

---

## IS Start Date / Data Integrity Verification

- First IS trade open_time: `1662595199999` → **2022-09-07 23:59:59 UTC** (no `start_time` trim; earliest available TRB kline data used).
- IS date range spans 2022-09 through 2025-03 (29 monthly PnL rows in `in_sample/monthly_pnl.csv`; 3 months have 0 trades due to training-window warm-up).
- IS years: 4.55 (confirmed in `probe_TRBUSDT_results.csv`; no truncation).
- **Embargo intact**: last IS trade close_time = 2025-03-26 15:59:59 UTC; first OOS trade open_time = 2025-03-27 15:59:59 UTC; gap = 24h (one 8h-candle boundary). `OOS_CUTOFF_MS = 1742774400000` (2025-03-24 00:00 UTC) is unchanged.

---

## Feature Column Verification

- `V1_FEATURE_COLUMNS_PRUNED` count: **48 columns** (global, unchanged; no V1_ITER086 local additions).
- Pre-registered hash prefix: `b81176f893826500` — confirmed matching at runner launch (run.log line 1: `[iter-v1/086] features-base-hash: b81176f893826500...`).
- All 48 columns present in TRBUSDT parquet (`probe_TRBUSDT_results.csv`: `feature_col_coverage=48/48`).
- `dot_vs_btc_ret_ratio_30` and `eth_vs_btc_ret_ratio_30`: ALL-NaN for TRBUSDT (symbol-conditional; expected; confirmed in run.log and feature_importance_portfolio.csv ranks 47/48 with mean_gain=0.0).
- **ZERO new features** — one-variable discipline explicitly maintained.

---

## Feature Importance (Top 10 / Bottom 5, mean_gain)

| Rank | Feature | Mean Gain |
|---|---|---|
| 1 | vol_atr_14 | 4601.6 |
| 2 | btc_funding_spread_30_90 | 4054.5 |
| 3 | stat_autocorr_lag5 | 3683.1 |
| 4 | trend_aroon_osc_50 | 3503.4 |
| 5 | mom_macd_line_12_26_9 | 3262.9 |
| 6 | interact_natr_x_adx | 3040.8 |
| 7 | funding_rate_zscore_30 | 2818.3 |
| 8 | funding_rate_zscore_90 | 2708.2 |
| 9 | trend_adx_14 | 2486.7 |
| 10 | oi_delta_30_z90 | 2443.1 |
| ... | ... | ... |
| 44 | stat_log_return_1 | 60.5 |
| 45 | mr_rsi_extreme_14 | 3.8 |
| 46 | cal_hour_norm | 2.5 |
| 47 | dot_vs_btc_ret_ratio_30 | 0.0 (ALL-NaN; symbol-conditional OK) |
| 48 | eth_vs_btc_ret_ratio_30 | 0.0 (ALL-NaN; symbol-conditional OK) |

The top features are dominated by vol/ATR (rank 1), cross-asset BTC funding spread (rank 2), and momentum/trend features (ranks 3–10). Despite positive importance rankings, the model failed to convert feature signal into positive IS Sharpe at n_trials=30.

---

## Trade Execution Verification

Spot-checked 5 random OOS trades for entry/exit/PnL math:

| Trade | Dir | Entry | Exit | WF | pnl_pct (reported) | pnl_pct (calc) | Diff |
|---|---|---|---|---|---|---|---|
| 1 | -1 | 31.31 | 27.797446 | 0.33 | +11.2186 | +11.2186 | 3.3e-5 |
| 2 | -1 | 27.056 | 23.437675 | 0.33 | +13.3735 | +13.3735 | 3.4e-5 |
| 3 | +1 | 23.932 | 21.945128 | 0.33 | -8.3022 | -8.3022 | 4.4e-5 |
| 4 | +1 | 21.741 | 19.687396 | 0.33 | -9.4458 | -9.4458 | 3.4e-5 |
| 5 | +1 | 22.430 | 22.946 | 0.33 | +2.3005 | +2.3005 | 1.0e-5 |

All diffs are floating-point rounding only (< 1e-4). `weight_factor` range OOS: 0.33–0.33 (vol-targeting active, clipped below max). All `weight_factor > 0` verified. Trade math is correct.

IS: 157 trades confirmed across 29 monthly bins (2022-09 through 2025-03).
OOS: 90 trades confirmed across 16 monthly bins (2025-03 through 2026-06).

---

## Basin / Seed Diagnostics

| Dimension | Value | Threshold | Verdict |
|---|---|---|---|
| V1 cross_seed_sharpe_std | 0.000 | PASS < 0.3 | PASS (degenerate: n_outer_seeds=1) |
| V2 per_cell_spearman_rho | NaN | 0.5 | BORDERLINE (single-symbol; degenerate) |
| V3 OOS_trade_roster_Jaccard | NaN | 0.4 | SKIPPED |
| **GLOBAL** | — | — | **BORDERLINE** |

The V1 PASS verdict is a degenerate artifact: `std_sharpe=0.0` because `n_outer_seeds=1` (single-seed run). There is no meaningful inter-seed spread information. The GLOBAL=BORDERLINE label is appropriate for a single-seed specialist.

`specialist_dispersion_mean` (IS) = **48.84** — this is the mean across-seed signed-weight standard deviation computed at every candle. At 50 seeds (the intended roster) this would reflect genuine ensemble spread; at 1 seed it measures the intra-model prediction variance across IS candles and is not interpretable as a basin metric.

---

## Risk Gate Efficacy

All risk gates showed zero fire rates in both IS and OOS:

| Gate | IS fire rate | OOS fire rate |
|---|---|---|
| R5 vol kill-switch | 0.0000 | 0.0000 |
| R5 binary kill | 0.0000 | 0.0000 |
| Vol ceiling | 0.0000 | 0.0000 |

Gates did not activate — the losses came from directional misses, not volatility events triggering protection.

---

## Verdict

**SPECIALIST-NEGATIVE — subtype: NEGATIVE-PROBE-INCONSISTENT**

- IS Sharpe -0.3044, OOS Sharpe -0.5967: fails absolute Sharpe floors (IS ≥+1.0, OOS ≥+1.0).
- Both windows negative: no edge at n_trials=30 with the STOCK 48-col stack on TRBUSDT.
- **No merge**; BUNDLE-002 (tag v0.v1-082, IS +0.716 / OOS +1.004) remains the v1 baseline.
- **F5 diversification-conditionality is MOOT**: TRB is negative standalone; no bundle seat possible.
- Cross-seed variance is a degenerate single-seed artifact; the SPECIALIST-NEGATIVE verdict does not depend on basin analysis.

The load-bearing methodological finding is the **probe→full degradation at n_trials=30**: probe (n_trials=10) predicted +0.493 (PASS); full (n_trials=30, same seed) delivered -0.304 (Δ -0.797). This is the primary GATE-2 failure mode for this symbol. QR should consider GATE-2 reform (probe at n_trials=30 OR raise threshold to ≥+0.80) before the next diversification-cohort SPECIALIST mine.

---

## Status

OVERALL=READY-FOR-CRITIC
