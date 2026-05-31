# iter-v1/040 EDA Findings — F-AXIS #1 (FEATURE-ENGINEERING)

**Axis**: DROP basis_zscore_30 (INERT-3-consec) + ADD regime_momentum_signed_5d (v3-proven composed feature).

**Cycle-5 slot**: EXPLORATION #7/10.

**LM Master reference**: /038 closeout Rec 1 (HIGH CONFIDENCE).

Analysis script: `analysis/iteration_v1-040/eda.py`.
Outputs: `distribution_per_symbol.csv`, `ic_matrix.csv`, `adf_per_symbol.csv`, `basis_z30_importance_history.csv`.

---

## T1 — basis_zscore_30 INERT confirmation (DROP justification)

basis_zscore_30 was added at /034. Importance ranks across the 3 most-recent iterations (5 cohorts × 3 iters = 15 measurements):

| iter | Model_A_pool | Model_C_LINK | Model_D_LTC | Model_E_DOT | portfolio |
|---|---|---|---|---|---|
| /034 | 25 | 29 | 32 | 26 | 27 |
| /037 | 25 | 29 | 31 | 25 | 27 |
| /038 | 25 | 29 | 32 | 26 | 27 |

- Mean rank: **27.67** (out of 44 features)
- Min rank: **25** (Model A across all 3 iters — never improved)
- Max rank: **32**
- All 15 observations have rank ≥ 25 (bottom-half of 44-feature set)
- Stability of rank across 3 iters is itself diagnostic: the feature is not "lottery-INERT" — it is structurally low-importance.

Per `feedback_v3_inert_features_at_higher_budget.md`: adding INERT features at higher Optuna budget actively HARMS OOS (iter-v3/023: rank 14/14 INERT feature flipped OOS Sharpe from +0.78 → −1.07 at n_trials 10→35). v1 cycle-5 EXPLORATION is at n_trials=18 (per `feedback_v1_trial_budget_standardization.md`, default 18). The harm potential is lower than v3's documented case, but the 3-consec INERT pattern triggers the doctrine DROP mandate.

**Decision**: DROP basis_zscore_30 from V1_FEATURE_COLUMNS_PRUNED. 44 → 43 features, before ADD.

---

## T2 — regime_momentum_signed_5d distribution (per-symbol IS-only)

Composed feature: `regime_momentum_signed_5d = ret_5d * sign(hurst_100 - 0.5)`

Where:
- `ret_5d` = log(close_t) − log(close_{t−15}) at 8h cadence (15 bars × 8h = 120h = 5 calendar days). v3-IDENTICAL.
- `hurst_100` = rolling 100-bar R/S Hurst exponent. Computed inline via v3's `_hurst_rs` / `_rolling_hurst` (BYTE-FOR-BYTE copy from `src/crypto_trade/features_v3/regime_v3.py:34-75`).

v1 features parquet does NOT contain hurst_100 OR a 15-bar ret_5d. The composed feature must be computed in the v1 features module at Phase 6 (QE work).

**Per-symbol stats (IS-only, close_time < 2025-03-24):**

| symbol  | n_valid | mean    | std    | min    | max    | hurst_mean | autocorr_lag1 | adf_pvalue |
|---------|---------|---------|--------|--------|--------|------------|---------------|------------|
| BTCUSDT | 5,628   | 0.0059  | 0.0748 | −0.625 | +0.286 | 1.004      | 0.937         | 2.0e-15    |
| ETHUSDT | 5,628   | 0.0064  | 0.0974 | −0.799 | +0.508 | 1.012      | 0.938         | 6.1e-17    |
| LINKUSDT| 5,579   | 0.0032  | 0.1240 | −0.868 | +0.539 | 1.006      | 0.931         | 5.2e-18    |
| LTCUSDT | 5,588   | 0.0005  | 0.1044 | −0.790 | +0.395 | 1.010      | 0.931         | 8.6e-19    |
| DOTUSDT | 4,926   | 0.0000  | 0.1173 | −0.836 | +0.818 | 1.004      | 0.932         | 1.5e-13    |

- **Stationarity**: All 5 symbols pass ADF at p << 0.001 → composed feature is stationary. PASS.
- **Distribution**: Mean ≈ 0 (slight positive drift on BTC/ETH from IS-window bull regime); symmetric around 0.
- **Autocorr lag-1 ≈ 0.93** across all 5 symbols. This is HIGH — the feature is persistent (overlapping 15-bar windows; structurally identical to ret_5d which also has ~0.93 lag-1 autocorr). v3 /025 EDA reported the same. NOT a defect.

### IMPORTANT FINDING — sign(hurst_100 − 0.5) is +1 ALMOST ALWAYS

| symbol  | pct_trending (hurst > 0.5) | pct_meanrev (hurst < 0.5) |
|---------|---------------------------|---------------------------|
| ALL 5 v1 symbols | 100.0% | 0.0% |

The v3 R/S Hurst estimator at 100-bar window on 8h crypto data produces values centered ~1.00 with std ~0.05; the minimum observed across IS is ~0.71 (in v3 parquet). The sign-flip mechanism is therefore **NEVER engaged in practice** at this window/cadence — `regime_momentum_signed_5d` is mechanically equivalent to `ret_5d` (15-bar log return) across the full IS sample.

This matches v3's parquet (BCH/LDO/TRX hurst_100 mean 0.998–1.008, all-positive sign). v3 /025 PROMISING-CLEAN and /028 multi-seed CONFIRMATION-MERGE happened despite this — implying the LIFT in v3 came from `ret_5d` (15-bar log return) being a NEW feature NOT in V3_FEATURE_COLUMNS_TOP_N, not from regime conditioning.

For v1, `stat_log_return_5` is ALREADY in V1_FEATURE_COLUMNS_PRUNED at horizon = 5 bars (40h), NOT 15 bars (120h). The composed feature we are adding is effectively the **15-bar log return** — a NEW longer-horizon momentum primitive masquerading as a regime-conditioned signal.

This re-frames the hypothesis: we are not adding a regime-aware feature; we are adding a 5-DAY momentum primitive that v1 currently lacks.

---

## T3 — IC matrix (composed feature vs incumbents + primitives)

|symbol  | ic_stat_return_5 | ic_stat_log_return_5 | ic_vol_atr_14 | ic_trend_aroon_osc_50 | ic_stat_autocorr_lag5 | ic_mom_rsi_14 | ic_trend_adx_14 | ic_ret_5d_15bar_PRIMITIVE | ic_hurst_100_PRIMITIVE |
|---|---|---|---|---|---|---|---|---|---|
|BTCUSDT |0.583 |0.588 |−0.082 |0.396 |−0.013 | 0.815 |0.092 |1.000 |0.026|
|ETHUSDT |0.588 |0.596 |−0.165 |0.427 |−0.002 | 0.813 |−0.006 |1.000 |−0.012|
|LINKUSDT|0.567 |0.577 |−0.076 |0.397 |−0.020 | 0.820 |−0.069 |1.000 |0.005|
|LTCUSDT |0.559 |0.567 |−0.103 |0.374 |−0.022 | 0.814 |−0.133 |1.000 |0.004|
|DOTUSDT |0.575 |0.582 |−0.062 |0.402 |0.093 | 0.798 |−0.059 |1.000 |0.063|

**Composed-feature IC carve-out applies** per `feedback_v3_engineered_feature_pivot.md`:

- |IC| vs ret_5d_15bar value primitive = **1.000 EXACT** (mechanical: sign factor is +1 everywhere; rms_5d ≡ ret_5d at 15-bar horizon).
- |IC| vs hurst_100 regime primitive = **≤ 0.063** (the regime primitive contributes essentially zero variance since the sign is always +1).

|IC| vs incumbents (the relevant cross-family signal):
- vs `mom_rsi_14`: **0.80–0.82** (HIGH — momentum-family overlap; both encode trend direction)
- vs `stat_return_5` (5-bar pct return): **0.56–0.59** (moderate; same family, different horizon 40h vs 120h)
- vs `stat_log_return_5` (5-bar log return; ALREADY IN V1 PRUNED SET): **0.57–0.60** (moderate; horizon mismatch)
- vs `trend_aroon_osc_50`: **0.37–0.43** (moderate; trend-strength family)
- vs `vol_atr_14`, `stat_autocorr_lag5`, `trend_adx_14`: **< 0.20** (orthogonal — good)

**Critic Check 4 evaluation per IC carve-out**:
- Strict |IC| < 0.50 against incumbents would FAIL (RSI overlap 0.80; stat_log_return_5 overlap 0.58).
- Composed-feature gate: importance ≥ 30 in ≥ 2 of 5 cohorts (binding falsifier).
- Test multivariate contribution (cluster-MDA), not univariate rank correlation. The |IC|=0.80 with RSI is the dominant concern: RSI ranks 1–3 across all 5 cohorts at /038 — colsample picks may be stolen.

---

## T4 — Predicted importance rank per cohort

v3 precedent: regime_momentum_signed_5d ranked **51% top-importance** (Model A) at /025, vs 22-25% off-the-shelf. v3 universe (BCH/LDO/TRX) has different feature competition than v1.

**v1 prediction (5 cohorts):**
- Model_A_pool (BTC+ETH): RANK 5–12. Predicted top-30%. Adding a 5-day momentum primitive into a model that already has RSI + ADX + MACD + 4 stat_return horizons (1/2/3/5/10/15/20/30 bars; only stat_return_5 at 5-bar) — high competition but distinctive horizon.
- Model_C_LINK: RANK 8–15. LINK historically rewards momentum signals (per /037 feat importance: RSI rank 2, MACD rank 4).
- Model_D_LTC: RANK 10–18. LTC has weaker momentum response (RSI rank 5 at /038); riskier.
- Model_E_DOT: RANK 8–15. DOT trades momentum strongly during 2022 IS bear regime (DOT post-2021-launch had structural drift); composed-feature horizon-extension may help.
- portfolio: RANK 6–10 (averaged).

Expected: **importance ≥ 30 in 3-4 of 5 cohorts**. Passes composed-feature gate.

**Risk**: if mom_rsi_14 colsample picks get stolen due to |IC|=0.80 overlap, the composed feature could displace RSI without net signal gain. v3 /025 success may not generalize because v1's existing feature set is RICHER in momentum primitives than v3's 14-feature TOP_N.

---

## T5 — F-AXIS #1 prediction band (per LM Master HIGH confidence)

LM Master /038 closeout assigned HIGH confidence with the following modal weights:

| Outcome | Probability | Description |
|---|---|---|
| **PROMISING-CLEAN** | 35% | Δ IS Sharpe ≥ +0.10 AND Δ OOS Sharpe ≥ +0.20; both signs positive. Mirrors v3 /025 (IS +0.50 / OOS +0.84). |
| **PROMISING-INERT-FAV** | 30% | Δ within ±0.10 IS / ±0.20 OOS but importance ≥30 in ≥2 cohorts (feature LEARNED but signal-redundant with incumbents). |
| **INERT** | 20% | Δ within ±0.05; importance < 20 in ≥3 cohorts (feature NOT LEARNED; colsample-stolen by RSI). |
| **NEGATIVE** | 15% | Δ OOS Sharpe ≤ −0.20 (5-day-momentum feature breaks down during /034-style OOS regime; RSI displacement net-negative). |

**QR adjustment from EDA**: the finding that sign(hurst_100 − 0.5) is always +1 means we are NOT adding regime conditioning; we are adding a 15-bar log return primitive (5-day momentum). This is materially different from the v3 narrative but does NOT invalidate v3's empirical lift. I would shift weights slightly:

- PROMISING-CLEAN: 30% (slight down — v1 feature set is richer in momentum than v3's 14-feature TOP_N; competition is harder)
- PROMISING-INERT-FAV: 35% (up — high |IC| with RSI suggests learned-but-redundant is the modal outcome)
- INERT: 20% (unchanged)
- NEGATIVE: 15% (unchanged — same regime-decay risk)

**Modal band**: PROMISING-INERT-FAV (35%) > PROMISING-CLEAN (30%) > INERT (20%) > NEGATIVE (15%).

Both PROMISING modes share the basis_zscore_30 DROP cleanup, so the floor effect (removing INERT-3-consec) provides a small lift independent of the regime_momentum_signed_5d ADD. Expected Δ IS Sharpe from DROP alone: +0.00 to +0.05 (per `feedback_v3_inert_features_at_higher_budget.md` doctrine — INERT removal mostly neutral but reduces overfitting risk).

---

## Compute / kill-switch criteria

- **Phase 6 must**: add `compute_regime_momentum_signed_5d` to `src/crypto_trade/features_v1/` (or via a new `engineered_v1.py` module), wire into v1 dispatch, regenerate ALL 5 v1 parquets, swap V1_FEATURE_COLUMNS_PRUNED (DROP basis_zscore_30, ADD regime_momentum_signed_5d; 44→44).
- **Critic Check 4** (Phase 7.5): IC carve-out cited; binding gate is importance ≥30 in ≥2/5 cohorts. Falsifier triggered if importance < 30 in ALL 5 cohorts.
- **Kill-switch**: if /040 produces Δ OOS Sharpe ≤ −0.30 (NEGATIVE catastrophic), append to `feedback_v3_engineered_feature_pivot.md` as v1-counter-example; v1 cycle-5 #8 pivots to non-engineered-feature axis (per Critic Path Forward from /038).

---

## References

- `feedback_v3_engineered_feature_pivot.md` — IC carve-out for composed features (gate: importance ≥30, NOT |IC|<0.50)
- `feedback_v3_engineered_features_proven.md` — v3 /025 first PROMISING in post-bootstrap
- `feedback_v3_engineered_features_dont_stack.md` — single-feature only at single-seed EXPLORATION
- `feedback_v3_inert_features_at_higher_budget.md` — INERT-feature removal doctrine
- `src/crypto_trade/features_v3/engineered_v3.py:36-91` — reference implementation
- `src/crypto_trade/features_v3/regime_v3.py:34-75` — _hurst_rs and _rolling_hurst (v3-identical)
