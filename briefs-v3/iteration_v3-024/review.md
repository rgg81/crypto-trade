# Phase 7.5 Critic Review — iter-v3/024

OVERALL: **EXPLORATION-NEGATIVE (clean)** — BTC cross-asset funding produces same INERT-OVERFIT pattern as iter-v3/023. Funding family ENTIRELY closed in v3 (per-symbol + cross-asset BTC both rank 14/14).

## Per-Check Status

All 12 methodology checks PASS or PASS-EXPLORATION (informational). Single-axis discipline preserved (atomic funding-source switch). New `compute_btc_funding_rate_zscore` past-only verified by adversarial test.

## §4.4 Classification

| Condition | Threshold | Observed | Triggered |
|---|---|---|---|
| OOS Sharpe Δ < -0.10 | < -0.10 | -1.20 | YES (severe) |
| Importance rank 14/14 | bottom | 14/14 portfolio | YES |
| OOS MaxDD breach | concerning | 49.97% | YES |
| IS lift attributable to feature | rank ≤7 | 14/14 | NO — IS lift is lottery |

PATH C fires unambiguously. Verdict: NEGATIVE clean.

## Generalized Finding

3 of 3 funding-derived axes tested:
- iter-v3/019: per-symbol funding (n=10) — rank 14/14, lottery-positive OOS +0.78
- iter-v3/023: per-symbol funding (n=35) — rank 14/14, overfit-negative OOS -1.07
- iter-v3/024: BTC cross-asset funding (n=35) — rank 14/14, overfit-negative OOS -0.82

The funding family is genuinely uninformative for v3's per-symbol LightGBM at the 13-feature stack. Permanently CLOSED.

## INERT-OVERFIT Generalization

Per `feedback_v3_inert_features_at_higher_budget.md`: 2 consecutive iterations confirm the pattern — adding rank-14/14 features at n_trials=35 causes OOS collapse via Optuna's larger search space finding IS-overfit trajectories that don't generalize. The OOS MaxDD breaching 50% in BOTH iter-v3/023 and iter-v3/024 (a v3-historic threshold) indicates the overfit is deep, not noise.

## Recommendations to QR

**iter-v3/025 axis MANDATORY = genuine feature engineering** (per user directive 2026-05-08). Off-the-shelf feature additions have produced 3 consecutive INERT outcomes at the 13-feature stack baseline. The next axis must be a COMPOSED feature built from existing primitives — testing whether the model has been missing INTERACTIONS the trees can't express at depth 3-5 from raw feature inputs.

Pre-commit candidates (single-axis = ONE engineered feature):
1. **Regime-conditional momentum**: `ret_5d × sign(hurst_100 - 0.5)` — flips momentum sign by trend regime
2. **Vol-adjusted return persistence**: `ret_autocorr_lag1_50 / range_realized_vol_50` — autocorrelation normalized by realized vol
3. **ADX-direction interaction**: `adx × sign(ret_14d)` — directional trend strength
4. **Cross-asset divergence**: `(sym_ret_7d - btc_ret_14d) / vwap_dev_20`
5. **Multi-timeframe regime drift**: `hurst_diff_100_50` (already in feature set — NOT a new candidate)
6. **Fractional differentiation** (López de Prado AFML Ch. 5 — explicitly listed in v3 skill, never implemented)

**Critic strong prior**: iter-v3/025 = candidate #1 (regime-conditional momentum) OR candidate #6 (fractional differentiation). #1 is the simplest, most interpretable, and tests the "signal exists but model can't compose" hypothesis directly. #6 is the v3 skill's own mandate from iter-v3/001 that was never delivered. QR's call.

## Catalog Row

`| iter-v3/024 | 2026-05-08 | btc_funding_rate_zscore_30 cross-asset (DROP per-sym + ADD BTC broadcast; same V3_FEATURE_COLUMNS=14) | +0.60 (vs anchor +0.3788) — IS lift is lottery on INERT 14th feature | -0.8170 (Δ -1.20, 3rd worst single-seed; OOS MaxDD 49.97% 2nd 50% breach) | EXPLORATION-NEGATIVE (clean) | NO — BTC funding rank 14/14 same pattern as iter-v3/019+023; INERT-OVERFIT confirmed across funding family; entire funding family permanently CLOSED; iter-v3/025 = genuine feature engineering (composed feature) per user directive |`
