# Engineering Report — iter-v3/085

## Headers

- Iteration: iter-v3/085 — cycle-3 EXPLORATION #4
- Branch: iteration-v3/085
- Pre-flight commit SHA (setup): ae38f1e
- Phase 5.5 gate SHA: 0a67b71
- Report commit SHA: d1f8b36
- Hardware: WSL2 Linux 6.6.114.1-microsoft-standard-WSL2
- Wall-clock time: 0.71h (within the 2h EXPLORATION HARD CAP)

---

## Implementation Summary

Single-axis change from the /059-canonical 14-feature baseline: one new Category-2 composed feature
`funding_regime_momentum_5d = regime_momentum_signed_5d × sign(funding_z_30)` appended to
`V3_FEATURE_COLUMNS_TOP_N` (14 → 15 features). No labeling change, no symbol change, no
risk-gate change, no model-architecture change. The feature is computed in
`src/crypto_trade/features_v3/engineered_v3.py`; `V3_FEATURE_COLUMNS_TOP_N` count assertion
updated 14 → 15 in `run_baseline_v3.py`; `ITERATION_LABEL = "v3-085"`.

Run mode: `--exploration --n-trials 35` (EXPLORATION-mode 3-seed ensemble, 35 Optuna trials per model).
n_trials = 35 × 3 seeds × 3 symbols = 315 (matches comparison.csv). Universe: BCHUSDT / LDOUSDT / TRXUSDT (unchanged).

---

## Run Integrity

| Check | Result |
|---|---|
| Exit code | 0 (clean) |
| "Optimization failed" count | 0 |
| "Traceback / magic bytes / end of stream" count | 0 |
| n_trials | 315 (35 × 3 seeds × 3 symbols — PASS) |
| REQUIRED_GAP | 66 = (21+1)×3 — PASS |
| PER_CELL_GAP | 22 (= REQUIRED_GAP / n_symbols = 66/3) |
| Feature count | 15 confirmed in runner log ("15 feature columns, 53 walk-forward splits" for BCH) |
| Ensemble mode | EXPLORATION (3 seeds: 191664963, 1662057957, 1405681631) |
| V3_FEATURE_COLUMNS | 15 — PASS (pre-flight assertion logged) |
| Config-accretion pre-flight | All 11 /059-canonical knobs verified — PASS |
| BCH ATR multipliers | (2.0, 1.0) DEFAULT — PASS |
| ADX threshold | 20.0 global — PASS |
| per_symbol ADX overrides | {} empty — PASS |
| vol_scale_floor overrides | {} empty — PASS |
| trial_oof_returns.parquet | present and readable |
| Zero-trade months IS | None (minimum 1 trade every active month — PASS) |

All pre-flight checks PASS. The run is clean.

---

## Configuration Diff vs /059-Canonical Baseline

One change only:

```
V3_FEATURE_COLUMNS_TOP_N: 14 → 15
  Added: funding_regime_momentum_5d  (= regime_momentum_signed_5d × sign(funding_z_30))
```

All 11 RiskV3-config knobs unchanged vs /059 canonical. ITERATION_LABEL updated to "v3-085".

---

## Headline Metrics vs /084 EXPLORATION-MODE-REFERENCE

/084 is the architecture-matched anchor (3-seed EXPLORATION-mode): IS +0.8325 / OOS +0.3322.
/059 CONFIRMATION baseline (10-seed) is reserved for iter-v3/092 and is NOT the comparison anchor here.

| Metric | IS | OOS | Ratio |
|---|---:|---:|---:|
| Monthly Sharpe | 0.9743 | 0.2854 | 0.293 |
| Daily Sharpe | 2.0420 | 0.8768 | 0.429 |
| Max Drawdown | 19.30% | 44.04% | 2.281 |
| Profit Factor | 1.366 | 1.127 | 0.825 |
| Win Rate | 32.74% | 38.24% | 1.168 |
| n_trades | 168 | 102 | 0.607 |
| Total PnL | 60.52 | 15.11 | 0.250 |
| Monthly Calmar | 3.135 | 0.343 | 0.109 |

**Delta vs /084 anchor:**

| | IS monthly Sharpe | OOS monthly Sharpe |
|---|---:|---:|
| /085 | +0.9743 | +0.2854 |
| /084 anchor | +0.8325 | +0.3322 |
| **Delta** | **+0.1418** | **−0.0468** |

IS delta +0.1418 exceeds the +0.10 IS falsifier threshold (PROMISING IS leg passes).
OOS delta −0.0468 is within [−0.20, +0.20] (not NEGATIVE OOS).
OOS/IS ratio = 0.293 (< 3.0, SUSPICIOUS sub-mode (a) does not fire).
IS delta > 0 so the OOS-DOMINANT sub-mode (b) does not fire.

---

## CPCV / DSR / PBO / PSR

| Metric | Value | Note |
|---|---|---|
| PBO (per-cell mean) | 0.0921 | EXPLORATION artifact; per-cell gap = 22 |
| frac_positive_paths | 0.644 | PASS (threshold 0.55) |
| path_sharpe_q25 | −0.243 | |
| path_sharpe_q50 | +0.335 | |
| path_sharpe_q75 | +0.838 | |
| PSR | 1.000 | EXPLORATION artifact |
| DSR | 0.000 | EXPLORATION artifact (n_trials=315; E[max_SR] >> observed SR) |
| DSR_relative_B4 | 0.8239 | |
| n_eff | 19 | |
| n_trials | 315 | |
| min_trl_months | 18.67 | |

DSR=0.0 and PSR=1.0 are structural artifacts of EXPLORATION mode (n_trials=315,
E[max_SR] greatly exceeds observed annualized SR per the `feedback_v3_dsr_mode_artifact.md`
rule). These are informational only; CONFIRMATION-mode DSR is the merge gate.

---

## Feature Importance — `funding_regime_momentum_5d` (THE CORE SECTION)

### Per-Symbol Importance Rank and Absolute Share (Last IS Month, 3-Seed Mean)

| Symbol | Rank / 15 | Absolute Importance | Importance Share |
|---|---:|---:|---:|
| BCHUSDT | **13 / 15** | 59.33 | 4.10% |
| LDOUSDT | **14 / 15** | 78.33 | 3.43% |
| TRXUSDT | **15 / 15** | 55.33 | 2.89% |
| Portfolio (all 3) | **15 / 15** | 193.0 | 3.42% |

The `conditional_orthogonality.csv` portfolio importance share (PART_A_runner) = 0.0347 (3.47%),
consistent with the per-symbol breakdown above. Note: the EDA T3 back-fill column is absent from
`conditional_orthogonality.csv` for `funding_regime_momentum_5d` (marked `PART_A_runner_only`);
the per-symbol CSVs above are the authoritative source.

### Binding Gate Evaluation (brief Section 3.2 / Section 8.1)

Gate: importance rank **≤ 10/15** AND absolute importance **≥ 30** for **≥ 1 symbol**.

| Symbol | Rank ≤ 10? | Abs. importance ≥ 30? | Both conditions met? |
|---|---|---|---|
| BCHUSDT | FAIL (rank 13) | PASS (59.33) | NO |
| LDOUSDT | FAIL (rank 14) | PASS (78.33) | NO |
| TRXUSDT | FAIL (rank 15) | PASS (55.33) | NO |

**The binding gate FAILS on all three symbols.** The absolute-importance leg passes everywhere
(all three symbols show importance > 30), but the rank leg fails on all three symbols. No symbol
clears rank ≤ 10/15. The PROMISING gate (Section 8.1 of the brief) requires all five conditions;
the binding importance gate is one of them. Because the rank condition fails on all three symbols,
the PROMISING gate as a whole does not clear.

The INERT alternative clause (Section 8.4): "rank ≥ 14/15 on ≥ 2 of 3 symbols." LDO (rank 14)
and TRX (rank 15) both satisfy rank ≥ 14; BCH does not (rank 13). Two of three symbols meet the
INERT rank clause.

Context: `regime_momentum_signed_5d` (the primitive constituent of the new feature) itself ranks
13/15 on BCH, 15/15 on LDO, 12/15 on TRX in the portfolio CSV — both the composed feature and
its primitive cluster at the bottom of the importance distribution. The composed feature did not
surface as a learned split axis despite having absolute importance > 30 everywhere (the trees
allocated a non-trivial number of splits to it but it placed last in the ranked list).

The IS lift of +0.1418 vs the /084 anchor is real but, given the rank-15 position of
`funding_regime_momentum_5d` on TRX and rank 14 on LDO, the IS improvement cannot be attributed
to the new feature by the brief's own pre-registered attribution criterion. The +0.1418 IS gain is
more likely an Optuna search-space perturbation that happened to produce a favorable hyperparameter
draw at 3-seed EXPLORATION resolution — the mechanism the brief pre-registered as the
PROMISING-INERT failure mode (Section 7).

---

## IC Analysis — `funding_regime_momentum_5d`

Source: `ic_matrix.csv` (pooled across all symbols, Pearson IC between feature time-series).

| IC pair | Value |
|---|---:|
| vs `regime_momentum_signed_5d` (its primitive) | **+0.0065** |
| vs `range_realized_vol_50` (max |IC| among 14 anchors) | **+0.0840** |
| vs `ema_spread_atr_20` | +0.0533 |
| vs `ret_autocorr_lag1_50` | +0.0516 |
| vs `vwap_dev_20` | +0.0440 |

Max |IC| vs the 14-anchor stack: **0.0840** (well below the 0.50 strict target and the 0.70 hard gate).
The new feature is near-orthogonal to its own primitive (|IC| = 0.0065), confirming the sign-switch
mechanism genuinely restructures the feature rather than merely rescaling it. IC orthogonality is
not in question; the feature is genuinely novel in IC terms. The binding gate failure is on model
importance rank, not on collinearity.

These IC values match the EDA T2 tables from `analysis/iteration_v3-085/funding_regime_engineered_feature.py`
(brief Section 2.2), which reported per-symbol max |IC| up to 0.1936. The pooled IC matrix shows
the max at 0.0840 (pooled across all three symbols' combined time-series). No inconsistency.

---

## Per-Symbol IS / OOS Breakdown

### In-Sample (168 trades)

| Symbol | Trades | Win Rate | Net PnL% | % of IS PnL |
|---|---:|---:|---:|---:|
| BCHUSDT | 84 | 42.9% | +52.31 | 95.3% |
| TRXUSDT | 74 | 35.1% | +7.21 | 13.1% |
| LDOUSDT | 10 | 40.0% | −4.62 | −8.4% |

BCH continues to dominate IS PnL at 95.3% concentration (matching BASELINE_V3.md pattern).
IS spans 37 active months (2022-02 through 2025-03 with gap at 2025-01), minimum 1 trade/month.

### Out-of-Sample (102 trades)

| Symbol | Trades | Win Rate | Net PnL% | % of OOS PnL |
|---|---:|---:|---:|---:|
| TRXUSDT | 53 | 43.4% | +13.48 | 318.2% |
| LDOUSDT | 15 | 40.0% | +8.93 | 210.8% |
| BCHUSDT | 34 | 32.4% | −18.17 | −428.9% |

OOS concentration is inverted vs IS: BCH is a significant OOS drag (−428.9% of OOS PnL),
TRX and LDO contribute positively. BCH OOS win rate 32.4% vs IS 42.9% — a meaningful
IS/OOS win-rate gap for the dominant IS symbol. OOS spans 14 months (2025-04 through 2026-05).

---

## ADF Stationarity — `funding_regime_momentum_5d`

The new feature is stationary (p < 0.05) from the first month where enough history exists
to compute the ADF test (BCH: stationary from 2020-03 onward; TRX: stationary throughout
with ADF statistics in the range −8 to −14 with p ≈ 0). The feature is consistently
I(0) — stationarity is not a concern. All BCHUSDT and TRXUSDT months with sufficient
history return `stationary=True`; LDO's shorter history shows the same pattern from
its first eligible month. The composed feature inherits stationarity from its two components:
`regime_momentum_signed_5d` (a short return times a sign) and `sign(funding_z_30)` (a
bounded sign function of a stationary z-score).

---

## Monthly PnL Zero-Trade Check

IS: no zero-trade months in the 37 active IS months — verified from `in_sample/monthly_pnl.csv`.
OOS: no zero-trade months in the 14 active OOS months — verified from `out_of_sample/monthly_pnl.csv`.

---

## Gate Efficacy

Risk-gate stack is the unchanged /059-canonical 7-primitive stack. No gate changes in /085.
Gate fire rates are not recomputed for this feature-only EXPLORATION (no gate inputs change
except a marginal OOD-z-score vector perturbation from the 15th feature). Gate efficacy
is carried forward from the /084 reference and is the QR/Critic's interpretive domain.

---

## Trade Spot-Check

Verified 5 random rows from `in_sample/trades.csv` and 5 from `out_of_sample/trades.csv`:
entry/exit/PnL math consistent; exit_reason values from {stop_loss, take_profit, timeout};
weight_factor values in (0, 1]; no NaN PnL; no degenerate rows. No anomalies found.

---

## Anomaly Notes

- The IS lift (+0.1418 vs /084) is present but the new feature ranks bottom-2 (rank 13-15/15)
  across all three symbols. The IS improvement is not traceable to the new feature by the
  brief's binding attribution gate.
- BCH IS win rate (42.9%) and OOS win rate (32.4%) show a material gap — consistent with
  the v3 BCH fragility pattern documented across prior iterations.
- `conditional_orthogonality.csv` shows `funding_regime_momentum_5d` with empty EDA correlation
  fields (marked `PART_A_runner_only`). This is because the runner uses the last-month importance
  as PART_A; the EDA T3 back-fill path did not match the feature name in the CSV cross-join.
  The per-symbol importance CSVs are the authoritative source and are complete.

---

## Status

OVERALL=READY-FOR-CRITIC
