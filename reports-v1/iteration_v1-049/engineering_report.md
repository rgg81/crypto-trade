# iter-v1/049 — Engineering Report

**Iteration**: iter-v1/049
**Type**: EXPLORATION (cycle-6 EXP-4)
**Axis family**: `feature-family` (NON-KLINE-CLASS — top-trader long/short ratio z-score)
**Feature added**: `long_short_zscore_30` (rolling 30-bar z-score of `sum_toptrader_long_short_ratio`)
**Anchor**: BASELINE_V1 `v0.v1-baseline-corrected` (`f8bc12c`); IS daily Sharpe +0.4767 / OOS daily Sharpe +1.1913
**Verdict**: **NEGATIVE-CLEAN** (sign-flipped IS/OOS with extreme IS MaxDD = single-seed lottery, no edge)

---

## Headline

| Metric | IS | OOS | Notes |
|---|---:|---:|---|
| Daily Sharpe | **-0.1717** | **+0.7322** | Sign-flip (ratio -4.27); structurally inconsistent with edge |
| MaxDD | **124.08%** | 40.36% | IS MaxDD > 100% = feature actively HARMS in-sample training |
| Total trades | 776 | 265 | IS rate fine; OOS rate fine |
| Win rate | 38.9% | 42.3% | Below 50/50 IS; OK OOS but underpowered |
| Profit factor | 0.9674 | 1.1560 | IS < 1.0 (losing); OOS marginally > 1.0 |
| DSR | 0.0 | 0.0 | Both zero — feature did NOT produce significant edge |
| PSR (monthly vs 0) | 0.357 | 0.748 | PSR_OOS > 0.50 but Sharpe sign-flip dominates |
| Total net PnL | -28.27% | +39.79% | IS loses, OOS wins — opposite signs |

**Anchor delta**: IS Δ daily Sharpe = -0.6484 (-0.1717 - +0.4767); OOS Δ daily Sharpe = -0.4591 (+0.7322 - +1.1913). **Both negative**. The OOS positive number is BELOW anchor; it is not an edge.

---

## Per-Symbol Headline (IS / OOS)

| Symbol | IS trades | IS pnl% | OOS trades | OOS pnl% | OOS WR |
|---|---:|---:|---:|---:|---:|
| BTCUSDT | 167 | **-102.69** | 55 | +45.51 | 45.5 |
| ETHUSDT | 186 | **-130.87** | 65 | -43.80 | 35.4 |
| LINKUSDT | 158 | +121.66 | 56 | +72.88 | 48.2 |
| LTCUSDT | 135 | +112.62 | 40 | -29.55 | 37.5 |
| DOTUSDT | 130 | +17.39 | 49 | +38.66 | 44.9 |

- **IS structure**: BTC + ETH catastrophic (-233% combined); LINK + LTC carry partial offset; DOT roughly flat. Universe-level IS PnL = -28.27%.
- **OOS structure**: BTC + LINK + DOT positive; ETH + LTC negative — different per-symbol structure than IS. The OOS positive headline is not a re-emergence of IS edge — it is a different attribution pattern.
- **Pattern**: positioning-sentiment z-score appears to ACTIVELY HARM the BTC + ETH pooled training (they share a model in v1 architecture); the LINK / LTC / DOT specialist heads partially mask the BTC+ETH loss IS but flip on OOS.

---

## Per-Symbol Long/Short Importance

**Feature importance CSV files were NOT produced by this iteration's runner** (`feature_importance_*.csv` absent under `reports-v1/iteration_v1-049/`). The `_write_feature_importance` defect class — known from iter-v3/015 / iter-v3/017 — was not patched into the iter-v1/049 runner. Per-symbol long/short attribution cannot be quantified from artifacts.

**Implication**: F1 (top-15 importance at portfolio-aggregated level) cannot be evaluated directly; the Sharpe-Δ falsifier carries the verdict alone. The fact that BTC + ETH are catastrophic IS argues the feature was selected but provided MIS-DIRECTING signal — not INERT — in those pooled heads.

---

## F-Axis Verdict (vs pre-registered falsifiers)

| Falsifier | Pre-registered threshold | Observed | Verdict |
|---|---|---:|---|
| F1 — Portfolio top-15 importance + IS Sharpe Δ ≥ +0.05 | both required | feature_importance CSVs absent; IS Δ = **-0.6484** | **FAIL** (Δ Sharpe direction wrong) |
| F2 — Per-symbol importance ≥3/5 top-20 | required | not measurable (importance absent) | INDETERMINATE |
| F3 — IS MaxDD ≤ baseline 50% absolute increase | < 75% absolute | **124.08%** | **FAIL** (more than 2× baseline) |
| F4 — ADF stationarity per symbol | p < 0.05 all 5 | PASS (pre-launch EDA) | PASS |
| F5' — IC orthogonality | max \|IC\| < 0.30 IDEAL, < 0.60 HARD | max \|IC\| = 0.2505 (pre-launch EDA PASS) | PASS |

**F-axis result**: **F1 + F3 BOTH FAIL**. F4 + F5' passed at pre-launch EDA but the in-Optuna model behavior contradicts what the orthogonality screen suggested — non-kline data class does NOT guarantee productive signal contribution. The feature is empirically orthogonal (|IC| 0.25) but the LightGBM model integrated it in a way that destabilized BTC + ETH IS training.

**Single-seed lottery context**: at `--seeds 1`, the IS / OOS sign-flip is the canonical "frozen-baseline + bad random seed" failure mode documented in `feedback_v3_single_seed_frozen_baseline.md` and `feedback_v3_engineered_features_dont_stack.md`. Multi-seed validation would dissolve into a mean closer to zero on both sides. At EXPLORATION budget single-seed, this counts as **NEGATIVE-no-effect (signal-undetectable above noise floor)** NOT as a TRUE positive OOS signal.

---

## Cycle-6 Context

- /046 PROMISING-DIVERGENCE (methodology axis)
- /047 NEG-CLEAN-PRE-EDA (skew_zscore_21; algebraic sister of stat_skew_20)
- /048 NEG-CLEAN-PRE-EDA (trade_count_zscore_30; volume-cluster collision)
- /049 **NEGATIVE-CLEAN** (long_short_zscore_30; passed EDA but failed in-Optuna)

This is the **LAST cycle-6 pooled-stack iteration**. Three consecutive feature-family attempts (/047 ABORT, /048 ABORT, /049 NEGATIVE-CLEAN) have exhausted the pooled-stack `feature-family` axis under v1's BTC+ETH-pooled / LINK / LTC / DOT model topology. Per axis rotation discipline + cycle-6 axis priority shift codified in `feedback_v1_kline_feature_space_dense.md`, the next iteration (/050) MUST pivot to **per-symbol architecture** (one specialist head per symbol) rather than continue adding features to the pooled stack — the pooled-stack scope is empirically saturated for non-kline single-feature adds at single-seed EXPLORATION budget.

---

## Artifacts

- Brief: `briefs-v1/iteration_v1-049/research_brief.md`
- IS reports: `reports-v1/iteration_v1-049/in_sample/`
- OOS reports: `reports-v1/iteration_v1-049/out_of_sample/`
- comparison.csv: `reports-v1/iteration_v1-049/comparison.csv`
- basin_diagnostics: `reports-v1/iteration_v1-049/basin_diagnostics/basin_diagnostics.json`
- EDA: `analysis/iteration_v1-049/eda.py` + outputs
- Source: `src/crypto_trade/features_v1/positioning_v1.py` (or equivalent) — to be REVERTED at closeout if NEGATIVE-CLEAN sticks per QR decision; see diary for revert directive.
