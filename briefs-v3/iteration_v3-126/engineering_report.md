# Engineering Report — iter-v3/126

## Headers
- Iteration: iter-v3/126
- Branch: iteration-v3/126
- Commit SHA: 70a6b3c944559e3223b070c0a0597043fb0ef775
- Wall-clock time: 0.70h
- Hardware: WSL2 Linux 6.6.114

---

## Configuration Diff vs BASELINE_V3.md (/121)

| Parameter | /121 BASELINE | /126 |
|---|---|---|
| ITERATION_LABEL | v3-121 | v3-126 |
| V3_MODELS universe | BCH/LDO/TRX | BCH/LDO/TRX (REVERTED from /125 ATOM/RUNE/UNI) |
| V3_FEATURE_COLUMNS_TOP_N count | 14 | **15** (appended `d24_ret_autocorr_lag1_50`) |
| Feature pipeline | 8h-only | 8h + 24h causal merge_asof (offset_id=0, direction='backward') |
| Triple-barrier K | 21 | 21 (UNCHANGED) |
| enable_no_confirm_exit | True | True (UNCHANGED) |
| ENSEMBLE_SIZE | 10 (CONFIRMATION) | 3 (EXPLORATION) |
| n_trials | 35 | 35 |
| REQUIRED_GAP | 66 | 66 |

Single structural axis: V3_FEATURE_COLUMNS_TOP_N 14 → 15 via append `d24_ret_autocorr_lag1_50`.

---

## Key Metrics Block

| Metric | IS | OOS | Ratio |
|---|---:|---:|---:|
| monthly_sharpe | +0.0999 | −0.1124 | −1.1254 |
| daily_sharpe | +0.2285 | −0.2607 | −1.1409 |
| max_drawdown | 58.78% | 24.96% | 0.4246 |
| profit_factor | 1.0355 | 0.9638 | 0.9308 |
| win_rate | 27.87% | 38.04% | 1.3651 |
| n_trades | 183 | 92 | 0.5027 |
| total_pnl | +7.38 | −3.33 | −0.4519 |
| monthly_calmar | +0.1255 | −0.1335 | −1.0642 |
| dsr | 0.0 | — | — |
| pbo | 0.1189 | — | — |
| psr | 0.1016 | — | — |
| n_trials | 315 | — | — |
| n_effective_trials | 18 | — | — |

**vs /121 BASELINE (IS +1.3108 / OOS +0.9682):**
- IS Δ: −1.2109 (catastrophic IS collapse)
- OOS Δ: −1.0806 (catastrophic OOS collapse)
- OOS/IS Sharpe ratio: −1.127 (IS-OOS inversion — positive IS yields negative OOS)

CPCV: frac_positive_paths = 0.644 (45 paths; path_sharpe_q25 = −0.243, q50 = +0.335, q75 = +0.838). PBO = 0.1189 PASS; frac_pos PASS at 0.644 > 0.55. Both these statistics are structurally consistent with a degraded but not uniformly negative distribution — the IS collapse concentrates in the TRX per-symbol channel, not across all CPCV paths.

---

## Section 8 Falsifier Evaluation (first-match wins)

**Criterion 1 — NEGATIVE-catastrophic (PUBLIC anchor: /121 IS +1.3108 / OOS +0.9682):**
- IS threshold: IS < +0.91 (Δ < −0.40). Observed IS = +0.0999. TRIGGERED (Δ −1.21).
- OOS threshold: OOS < +0.67 (Δ < −0.30). Observed OOS = −0.1124. TRIGGERED (Δ −1.08).

**CLASSIFICATION: EXPLORATION-NEGATIVE-catastrophic. First-match fires at Criterion 1. Remaining criteria not evaluated.**

---

## Per-Symbol Attribution

### IS
| Symbol | Trades | WR | PnL | Concentration |
|---|---:|---:|---:|---:|
| BCHUSDT | 78 | 37.2% | +20.44 | +141.1% |
| LDOUSDT | 18 | 38.9% | +24.92 | +172.0% |
| TRXUSDT | 87 | 28.7% | −30.88 | −213.2% |

TRX IS: 87 of 183 trades (47.5%), WR 28.7%, net PnL −30.88. TRX IS dominance in trade count + catastrophic WR collapse (28.7% vs 37–39% for BCH/LDO) drives the IS Sharpe to near-zero. BCH and LDO IS are individually positive (+20.44 / +24.92) but TRX offsets both.

### OOS
| Symbol | Trades | WR | PnL | Concentration |
|---|---:|---:|---:|---:|
| TRXUSDT | 52 | 48.1% | +27.05 | +426.6% |
| BCHUSDT | 30 | 36.7% | −7.71 | −121.6% |
| LDOUSDT | 10 | 30.0% | −13.00 | −205.0% |

IS-OOS inversion at per-symbol level: TRX flips from IS loss source (−30.88, WR 28.7%) to OOS gain source (+27.05, WR 48.1%). BCH/LDO flip from IS gain sources to OOS loss sources. This is a clean IS-OOS regime-flip pattern: TRX's WR is 28.7% IS and 48.1% OOS (19.4pp reversal); BCH/LDO drop from ~38% IS to 30–37% OOS. The 15th feature does not stabilize edge direction — it alters trade selection into a regime-dependent allocation that inverts across the IS/OOS boundary.

**Behavioral-effect predictor (Section 4.4)**: IS trade count +21 vs /121 (183 vs 162 = +13.0%). Within the predicted 10–30% band. The feature was behaviorally active (not INERT), but the behavioral change was destructive — the new TRX entry-selection shift loaded the IS-negative TRX WR channel.

---

## Production Importance vs EDA Prediction

EDA (T5) predicted BCH rank 2/15, LDO rank 1/15, TRX rank 3/15.

**Production (last-month walk-forward aggregation):**
| Symbol | Production rank | Importance share |
|---|---:|---:|
| BCHUSDT | 8/15 | 5.8% |
| LDOUSDT | 11/15 | 6.0% |
| TRXUSDT | 4/15 | 7.4% |

Rank degradation: BCH 2→8 (6-rank drop), LDO 1→11 (10-rank drop), TRX 3→4 (marginal). The EDA T5 ran at depth-3 with no Optuna search-space interaction; the production walk-forward Optuna at n_trials=35 discovers depth-3-5 tree structures where the 14-feature incumbents absorb importance via branching interactions. LDO's rank-1→11 collapse is particularly severe: the feature that ranked first in a single-window EDA becomes mid-table in rolling walk-forward, confirming that EDA importance ranking is single-window-biased and does not generalize under Optuna's multi-trial exploration of depth-5 subspaces.

Shares near 1/15 parity (~6.7%) across all 3 symbols. The feature was learned but at near-uniform allocation — not the dominant signal the T5 table predicted.

---

## IC Matrix Check — New Feature

Production IC for `d24_ret_autocorr_lag1_50` vs all 14 incumbents (from `ic_matrix.csv`, pooled IS):

| Partner | Pooled IC |
|---|---:|
| btc_ret_14d | 0.127 |
| hurst_100 | 0.108 |
| ret_kurt_200 | 0.085 |
| range_realized_vol_50 | 0.080 |
| ret_autocorr_lag1_50 (8h sister) | 0.068 |

Max pooled IC = 0.127 (vs btc_ret_14d). EDA T4 pre-registered max |IC| = 0.160 (also btc_ret_14d). Production IC is LOWER than EDA IC (0.127 vs 0.160) — consistent with the feature being structurally orthogonal. The catastrophic performance is NOT attributable to IC-collinearity with incumbents; the IC matrix check is CLEAN.

**Conclusion**: the NEGATIVE-catastrophic outcome is not an IC contamination failure. It is a walk-forward distributional failure where a single-window-EDA-strong feature causes destructive trade-selection shifts in the production rolling walk-forward.

---

## ADF Stationarity Check

ADF stationarity for `d24_ret_autocorr_lag1_50` (from `adf_test.csv`, per-symbol per-month rolling): first available BCH row (2020-03): ADF statistic −0.916, p-value 0.783 — NON-STATIONARY at IS-start. The feature is non-stationary in early IS windows. Later IS months (warm-up complete) converge toward stationarity as the 50-bar window fills. This partial non-stationarity in early walk-forward training windows (2020–2021 for BCH/TRX) means early walk-forward folds had degraded signal quality, contributing to Optuna fitting noise in TRX's low-WR window distribution.

---

## EDA-vs-Production Walk-Forward Disagreement Pattern (Cycle-7 Recurring)

This is the 5th cycle-7 NEGATIVE following /122 (NEGATIVE-INERT), /123 (NEGATIVE-catastrophic), /124 (NEGATIVE-catastrophic), /125 (NEGATIVE-catastrophic).

The recurring mechanism: single-window EDA importance (T5) and AUC lift (T6) capture feature utility at a FIXED training window. The production walk-forward Optuna runs 35 trials per month across a ROLLING training window distribution (24 months ending at each test month). Key differences that explain the gap:

1. **T5 EDA uses depth-3 / 100 trees at fixed hyperparams.** Production Optuna searches depth 3–5 / 50–200 trees with colsample_bytree 0.6–0.9. At depth 4–5, incumbents form compound splits that consume the autocorrelation signal the 15th feature would otherwise capture in depth-3 trees.

2. **T6 AUC uses 5-fold walk-forward without the 7-gate RiskV2 stack.** The no_confirm gate (/116) selectively filters signal-weak trades. Adding `d24_ret_autocorr_lag1_50` shifts the entry-selection pattern into the TRX-WR-28.7% regime; the RiskV2 stack does not block TRX entry selection because TRX IS Hurst/ADX conditions are not uniformly gated.

3. **Rolling IS-start varies from 2020 to 2025.** Early IS windows (2020–2022) have a non-stationary 24h autocorrelation feature (50-bar warm-up partially complete). EDA T6's 5 static folds cover a LONGER fixed IS than the production roll's narrowest training windows; the production walk-forward's early folds see a noisy feature, anchoring TRX Optuna toward over-trading in the low-WR direction.

**Single-window EDA importance/AUC cannot be used as a sufficient predictor for rolling walk-forward performance. This is the same root cause as /122 (T5 ranks 14/14 → INERT in production) and /123 (EDA PASS → catastrophic production). The failure mode is structural to the EDA methodology under multi-frequency feature stacking.**

---

## Gate Efficacy Table

Gates bit-identical to /121 (no gate changes in /126 axis). Gate efficacy is not a variable in this iteration. TRX IS MaxDD = 58.78% hit (Section 6.1 CATASTROPHIC threshold IS MaxDD > 50% AND IS Sharpe < +0.50: BOTH conditions met). This would have triggered a stop-loss at IS level but did not prevent the OOS IS-inversion — the MaxDD is in a different direction (TRX IS PnL negative, OOS positive).

---

## Seed Concentration Audit

3-seed EXPLORATION (seeds: 191664963, 1662057957, 1405681631; all outer=42 lineage). Ensemble mode confirmed in `ensemble_summary.json`. Per-cell PBO = 0.1189 consistent with 3-seed mode per `feedback_v3_dsr_mode_artifact.md` artifact note — EXPLORATION-mode DSR/PSR INFORMATIONAL ONLY.

---

## Label Leakage Audit

REQUIRED_GAP = 66 = (21+1) × 3 symbols. Inherited from /121. Walk-forward embargo verified at prior iterations; no change in /126. Look-ahead audit on 24h merge_asof confirmed 0 violations (T2 table: 0/0/0 across BCH/LDO/TRX, 14130 joined rows). Causal fence intact.

---

## Anomaly Notes

IS monthly PnL table shows 37 months with data, 8 positive months. IS is predominantly negative with a few large positive months (2024-04: +22.79, 2024-10/11: +10.44/+10.46, 2025-02: +15.33). The IS Sharpe of +0.0999 reflects near-zero net PnL (+7.38 total) over a high-volatility IS trajectory — the feature did not provide consistent directional advantage, only occasional large wins offset by persistent small losses.

OOS 14 months: 6 positive, 8 negative. OOS PnL −3.33. The IS-OOS inversion at per-symbol level (TRX flips sign) explains the breakdown — no systematic feature edge present.

Production importance rank degradation (BCH 2→8, LDO 1→11 vs EDA) is ANOMALOUS in magnitude for a feature with max IC = 0.127. This pattern (rank-1 in EDA → rank-11 in production) has been observed in prior cycle-7 iterations and is now cataloged as the EDA-vs-production walk-forward disagreement pattern.

---

## Status

OVERALL=READY-FOR-CRITIC

**Classification**: EXPLORATION-NEGATIVE-catastrophic
- Section 8 Criterion 1 (first-match): IS Δ −1.21 AND OOS Δ −1.08 both TRIGGER
- IS MaxDD 58.78% (exceeds CATASTROPHIC threshold IS MaxDD > 50%)
- PSR 0.1016 catastrophic; DSR 0.0
- Axis-CLOSE recommendation per Section 8 Criterion 1: `d24_ret_autocorr_lag1_50` CLOSED; multi-frequency-stack axis class status to be determined by Critic interpretation
