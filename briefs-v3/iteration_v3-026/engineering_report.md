# Engineering Report — iter-v3/026

## Status: READY-FOR-CRITIC

Wall-clock 0.24h (14 min). Setup `d450692`. **STRUCTURALLY SUSPICIOUS RESULT** — IS Sharpe collapsed to near-zero while OOS spiked to v3-historic high.

## Hypothesis-Implementation Alignment

ADD `vol_adj_autocorr` (V3_FEATURE_COLUMNS 14 → 15). KEEP `regime_momentum_signed_5d`. ITERATION_LABEL=v3-026. Single-axis discipline preserved (one new engineered feature).

## Reproducibility Stamps

Setup `d450692`, gate `03f9f75`, brief `685287d`, EDA `97302db`.

## Headline Metrics — STRUCTURAL ANOMALY

| Metric | Value | vs iter-v3/025 ref (+0.88/+1.22) | vs iter-v3/018 anchor (+0.38/+0.39) |
|--------|-------|-----------------------------------|--------------------------------------|
| IS monthly Sharpe | **+0.0493** | Δ -0.83 | Δ -0.33 |
| OOS monthly Sharpe | **+1.4501** | Δ +0.23 | Δ +1.06 (would be highest in v3) |
| IS daily Sharpe | +0.1227 | (collapsed) | — |
| OOS daily Sharpe | +3.3558 | (extreme lift) | — |
| IS/OOS daily ratio | **27.4×** | (statistically absurd) | — |
| IS MaxDD | **51.37%** | (worst IS MaxDD in v3 history) | — |
| OOS MaxDD | 19.47% | improved | — |
| IS Trades | 196 | similar | — |
| OOS Trades | 79 | < 130 floor | — |
| DSR | 0.0 | EXPLORATION artifact | — |
| PBO mean | 0.0914 | PASS | — |
| PSR | 1.0 | EXPLORATION saturation | — |

## Per-Symbol OOS

| Symbol | weighted_pnl | Trades | WR | concentration |
|--------|--------------|--------|-----|---------------|
| BCH | +37.29 | 29 | **48.3%** | **78.46%** (single-symbol carry returned) |
| LDO | +2.68 | 9 | 44.4% | 5.64% |
| TRX | +7.56 | 41 | 39.0% | 15.90% |

BCH carries 78% of portfolio — concentration gate FAILS hard. iter-v3/025's healthier balance (BCH 35% / LDO -6% / TRX 71%) reverted.

## Feature Importance

Portfolio:
- Top: range_realized_vol_50 (630)
- regime_momentum_signed_5d: rank 13/15 (300 = 48% of top) — preserved from iter-v3/025
- vol_adj_autocorr: rank 14/15 (283 = 45% of top) — meaningful contribution
- ret_autocorr_lag1_50 (primitive): rank 15/15 (265) — fell BELOW its derivative

The new engineered feature IS used by the model (importance 283 ≥ 30 threshold) — Falsifier 4 PASSES. The feature is NOT INERT.

## Structural Anomaly Diagnosis

**IS Sharpe 0.05 + OOS Sharpe 1.45 is not a normal result**. Possible mechanisms:

1. **IS Overfit Breakdown**: combining 2 engineered features expanded Optuna search space to a regime where IS-optimal hyperparams produce near-zero Sharpe but the resulting model happens to generalize OOS by accident.

2. **Regime Mismatch**: vol_adj_autocorr captures autocorrelation/vol ratio that has different IS vs OOS distributions. Model learns IS distribution (low or no signal) → OOS distribution shifts favorably.

3. **Single-seed Lottery (Stronger Variant)**: more extreme version of iter-v3/013 pattern. Lucky Optuna trajectory at seed=42 + 35 trials hit OOS-favorable hyperparams without IS support.

4. **BCH Single-symbol Carry**: BCH OOS WR 48.3% on 29 trades is the dominant contributor. If BCH 2025-Q1+ regime is favorable to vol_adj_autocorr's signal, the model exploits that without learning IS pattern.

The 27× IS/OOS daily Sharpe ratio is the strongest signature of mechanism 1+2 combined (IS overfit + OOS regime favorability).

## §4.4 Classification

| Condition | Threshold | Observed | Trigger |
|---|---|---|---|
| IS Sharpe Δ < -0.10 vs iter-v3/025 ref | < -0.10 | -0.83 | YES (PATH C) |
| IS Sharpe Δ < -0.10 vs anchor | < -0.10 | -0.33 | YES (PATH C) |
| OOS Sharpe Δ ≥ +0.10 vs reference | ≥ +0.10 | +0.23 | YES (would be PATH A on OOS axis) |
| Concentration ≤ 30% | ≤ 30% | 78% BCH | NO |
| New feature importance ≥ 30 | ≥ 30 | 283 | YES (feature USED) |

**MIXED PATTERN**: PATH C on IS axis, PATH A-direction on OOS axis. Single-seed lottery suspect at iter-v3/013 strength or worse.

## Verdict Recommendation: EXPLORATION-NEGATIVE-SUSPICIOUS-OOS

PATH C fires on IS axis (decisive at single-seed EXPLORATION where IS is the controlled axis). OOS lift is single-seed-untrustable — needs multi-seed CONFIRMATION before any trust. Per `feedback_v3_inert_features_at_higher_budget.md` analogue: IS Sharpe of 0.05 indicates Optuna found IS-overfit configuration; OOS bonanza at IS=0.05 is structurally suspect.

**Caveats**:
- IS Sharpe 0.05 is the lowest IS Sharpe in any post-bootstrap iteration → quasi-NEGATIVE-no-effect signature
- OOS +1.45 would be highest in v3 if multi-seed-validated — BUT iter-v3/013's +2.70 OOS at single-seed was falsified to +0.39 multi-seed (86% reduction)
- vol_adj_autocorr importance 283 ≥ 30 → feature is USED, NOT INERT (so not a PROMISING-INERT outcome)
- BCH 78% concentration fails gate 7 → BASELINE_V3.md outstanding constraint regression

## Recommendations

iter-v3/027 axis:
1. **DROP vol_adj_autocorr** from V3_FEATURE_COLUMNS (revert 15 → 14). The IS Sharpe collapse is decisive — the feature destabilizes IS even though it has importance.
2. **KEEP regime_momentum_signed_5d** (proven at iter-v3/025).
3. **Try DIFFERENT engineered feature** at the 14-feature stack:
   - cross_asset_divergence_norm = (sym_ret_7d - btc_ret_14d) / (vwap_dev_20 + 1e-6) — different mechanism (relative-strength)
   - hurst_drift_50_200 = hurst_50 - hurst_200 (requires adding hurst_50 and hurst_200 as primitives if not present)
   - fracdiff_d05_close (López de Prado AFML Ch. 5 — preserves memory while making stationary)

Critic should decide. Critic prior: cross_asset_divergence_norm (uses existing primitives, smallest implementation cost, structurally orthogonal to regime momentum's sign-flip mechanism).

Status: READY-FOR-CRITIC.
