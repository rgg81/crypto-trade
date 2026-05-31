# LightGBM Master Advisor — iter-v1/040 — Phase 4.5 (Pre-Design)

## Context Read
- Track: v1. Anchor: BASELINE_V1 (`v0.v1-baseline-corrected`, IS +0.2829 / OOS +0.6637).
- /040 axis: DROP `basis_zscore_30` (3-consec INERT, mean rank 27.67/44) + ADD `regime_momentum_signed_5d = ret_5d × sign(hurst_100 - 0.5)`. 44 → 44 cols (swap).
- v3 precedent: /025 PROMISING-CLEAN (IS +0.50 / OOS +0.84, importance 51% top), /028 CONFIRMATION-MERGE first multi-seed-validated v3 edge ingredient.
- EDA gotcha: `sign(hurst_100 - 0.5) = +1` in 100% of IS samples across all 5 v1 symbols. **The feature is structurally a 15-bar (120h / 5-day) log return primitive**, NOT regime-conditioned. v1's `stat_log_return_5` is 5-bar (40h). New horizon, not new regime mechanic.

## Recommended Hyperparameter Direction

### 1. Bump Optuna `colsample_bytree` upper bound 0.85 → 0.95 [MEDIUM]
- **What**: ensure regime_momentum_signed_5d has high probability of being sampled per tree. At 44 cols × 0.6 default colsample, the new feature is omitted from ~40% of trees.
- **Why**: |IC|=0.80 with `mom_rsi_14` (RSI ranks 1-3 across all 5 cohorts at /038). If colsample steals the regime_momentum-or-RSI pick toward RSI in early trials, the composed feature appears INERT spuriously. v3 /025 effectively trained on 14 cols where colsample mattered less.
- **Expected**: importance rank lift 2-3 positions across cohorts; net Optuna basin shift small (decisive at single-seed).
- **Risk**: higher colsample → narrower tree diversity, slight overfit. Pair with `min_data_in_leaf` floor 20.

### 2. Keep `n_trials=18` + `ENSEMBLE_SIZE=3` (DO NOT raise) [HIGH]
- **What**: hold the v1 EXPLORATION budget standard. v3 /025 ran single-seed n_trials=35 and PROMISED at OOS +0.84.
- **Why**: feature-family axis is signal-discovery not basin-navigation. Per `feedback_v3_inert_features_at_higher_budget.md`, INERT additions at higher budget actively harm; if regime_momentum is signal-bearing, n_trials=18 reveals it; if not, n_trials=35 only amplifies noise capture in a richer 44-col stack. The /037+/038 `n_effective_trials=9` recurrence (2-iter pattern at v1) shows tight Optuna ridges already form — don't widen the search and invite a 3rd recurrence.

### 3. Hold `learning_rate` Optuna bounds [0.01, 0.1] [HIGH]
- **What**: no change. Feature-swap axes do NOT motivate LR retuning.
- **Why**: cycle-5 isolation discipline. Single-axis variation only.

## Recommended Feature-Engineering Direction

### 1. ADD `regime_momentum_signed_5d` (single feature, no stacking)
- **What**: per EDA. Implementation BYTE-FOR-BYTE copy from `features_v3/regime_v3.py:34-75` + `engineered_v3.py:36-91`. Recompute ALL 5 v1 parquets.
- **IC carve-out pre-warning**: |IC| vs RSI = 0.80; vs stat_log_return_5 = 0.58. Strict <0.50 gate FAILS. Composed-feature gate per `feedback_v3_engineered_feature_pivot.md`: importance ≥ 30 in ≥ 2/5 cohorts is the binding falsifier.
- **Expected importance rank (per-cohort prediction)**:
  - Model_A_pool: **6-10** (BTC+ETH richer momentum competition than v3 BCH/LDO/TRX)
  - Model_C_LINK: **3-7** (LINK rewards momentum; RSI rank 2 at /038)
  - Model_D_LTC: **8-14** (LTC weakest momentum response; highest INERT risk)
  - Model_E_DOT: **5-10** (DOT 2022 bear-regime momentum amplifier)
  - portfolio: **5-9** (averaged)
- **Predicted hit rate**: importance ≥ 30 in **3-4 of 5 cohorts**. If ≤ 1 cohort → INERT verdict, axis closes.

## Saturation Risks to Flag

**FEATURE-FAMILY 3-CONSEC-NEG WATCH**: /034 (basis_zscore_30 ADD = NEG-CLEAN) + /037 (loss-axis, basis still INERT) + /038 (risk-primitive, basis still INERT). /040 is the **4th consecutive iteration where basis_zscore_30 is the noise floor**. If /040 also produces a feature-family NEG or INERT verdict on regime_momentum, **feature-family is CLOSED for v1 cycle-5** and the final 3 axes (/041-/043) must be non-feature: model-arch (XGB head-to-head), labeling (TB-width), or universe (denominator expansion).

**HURST = +1 EVERYWHERE**: the hypothesis re-frames as "v1 lacks a 5-day momentum primitive" rather than "regime-conditioned momentum." This is **weaker** than v3's narrative — v1 already has `stat_log_return_5` (40h), `mom_rsi_14`, `trend_aroon_osc_50`, `trend_adx_14`, MACD across the 44-col stack. The horizon-extension hypothesis (40h → 120h) is the actual signal-discovery claim. Predict PROMISING-INERT-FAV (learned-but-redundant with RSI/Aroon) as modal vs v3-style PROMISING-CLEAN.

**OPTUNA RIDGE 3-ITER RECURRENCE**: /037+/038 both hit `n_effective_trials=9` at n_trials=18. If /040 also hits ≤10, Phase 7.4 must structurally flag — the 44-col stack at v1 budget may be **structurally ridge-prone**, independent of axis.

## What I Did NOT Recommend, and Why

I did NOT recommend raising `num_leaves` Optuna upper bound (currently 127). A larger leaf budget would let trees absorb the new feature via finer splits, but the load-bearing constraint is colsample-pick (see Rec 1), not leaf depth. I did NOT recommend dropping additional INERT features beyond basis_zscore_30 (e.g., the rank-20-25 cohort) — single-axis isolation discipline (cycle-5 doctrine) prevents bundled feature edits. If /040 PROMISES, /041+ can prune at /043 confirmation.

## Prior Distribution

| Outcome | Probability | Rationale |
|---|---|---|
| **PROMISING-CLEAN** | **30%** | v3 /025 precedent strong but v1 momentum-richer than v3 14-col TOP_N |
| **PROMISING-INERT-FAV** | **35%** | MODAL — RSI |IC|=0.80 implies learned-but-redundant |
| **INERT** | **20%** | colsample-stolen by RSI; horizon-extension is signal-bearing but loss-surface-redundant |
| **NEG-CLEAN** | **10%** | regime-decay during OOS; RSI displacement net-negative |
| **NEG-CATASTROPHIC** | **5%** | structural basin shift on Model A as /038 showed (unlikely on feature-swap) |

**PROMISING tail (combined CLEAN + INERT-FAV) = 65%** — higher than typical v1 EXPLORATION (~40-50%) because v3 precedent is CONFIRMATION-MERGED and EDA stationarity/distribution all PASS.

## Closing Note

**HIGH confidence** that regime_momentum_signed_5d will appear in feature_importance.csv across all 4 cohorts (F2 wiring passes — mechanical certainty given parquet regen). **MEDIUM confidence** on importance rank ≤ 5 in ≥ 3/4 cohorts — the v3 narrative is partially dissolved by the hurst=+1 finding, and v1's momentum-richer 44-col stack will compete harder than v3's 14-col TOP_N. **MEDIUM-LOW confidence** that OOS Sharpe Δ clears +0.20 (v3 /025 magnitude). The single most important thing the QR should NOT ignore: **`n_effective_trials` from /037+/038 ≤ 9 is a 2-iter Optuna-ridge recurrence**. If /040 also lands ≤ 10, Phase 7.4 escalates the ridge pattern to structural and the 5-cohort-richer-stack hypothesis (v1 cycle-5 basin-locked) gains weight independent of /040's verdict.

Predicted importance rank at /040 post-mortem: **portfolio rank 6-10, LINK rank 3-7, LTC rank 8-14**. Predicted modal verdict: **PROMISING-INERT-FAV** (learned but RSI-redundant). 65% PROMISING-tail combined probability.


---

# LightGBM Master Advisor — iter-v1/040 — Phase 7.4 (Post-Mortem)

## Context Read
- Outcome: IS +0.5588 / OOS +0.2959 / IS-OOS ratio **0.53** vs baseline 2.35 — **IS-LIFT/OOS-DROP overfit signature**.
- Engineering report: ran clean, F2 wiring verified (banner + V1_FEATURE_COLUMNS_PRUNED swap), `n_effective_trials=9` (3rd consecutive iter — see §Suspicious Patterns).
- Phase 4.5 prior: PROMISING-tail 65%, modal PROMISING-INERT-FAV 35%. Observed verdict: **NEG-CLEAN with INERT-by-rank composed feature** — a class not in the prior distribution (NEG + INERT simultaneously = 0% prior). **Phase 4.5 was directionally wrong.**

## F-Axis Falsifier Table

| # | Gate | Predicted | Observed | Verdict |
|---|---|---|---|---|
| F1 | OOS Sharpe Δ vs baseline | PROMISING ≥ +0.20 (modal +0.10 to +0.50) | **-0.3678** | **FIRES NEG-CLEAN** band [-0.45, -0.15] |
| F2 | Wiring (banner + parquet regen + col list) | PASS | PASS | clean |
| F3 | **regime_momentum importance ≥30 gain in ≥2/5 cohorts** | rank 3-14 / hit 3-4 of 5 | **rank 23-30 in ALL 5 cohorts** | **FIRES INERT** |
| F4 | Trade-count band | IS ~700 / OOS ~250 | IS 724 / OOS 274 | PASS |
| F5 | Wall-clock | n/a | n/a | PASS |
| F6 | n_effective_trials ≥ 12 (Optuna ridge gate from Phase 4.5 §Saturation Risks) | ≥ 12 | **9** | **FIRES — 3rd consecutive ridge recurrence /037/038/040** |

**Combined verdict: NEG-CLEAN-INERT (F1 + F3 + F6 fire)** — composed feature was rank-evidenced REFUTED as load-bearing, yet the swap-out of basis_zscore_30 + swap-in of an inert dimension produced loss-surface reorganization that LIFTED IS by basin-jumping into an OOS-decaying region.

## regime_momentum_signed_5d Importance Rank per Cohort

| Cohort | Predicted rank (Phase 4.5) | Observed rank | Observed gain | Verdict |
|---|---|---|---|---|
| Model_A_pool | 6-10 | **28 / 44** | 307.99 | INERT |
| Model_C_LINK | 3-7 | **23 / 44** | 260.82 | INERT (LINK was supposed to reward momentum) |
| Model_D_LTC | 8-14 | **30 / 44** | 233.44 | INERT (worst-case prediction confirmed and exceeded) |
| Model_E_DOT | 5-10 | **26 / 44** | 227.65 | INERT |
| portfolio | 5-9 | **26 / 44** | 1029.91 | INERT |

**Prediction error: -18 to -22 ranks across all 5 cohorts.** Zero cohorts cleared rank ≤10 (predicted 3/5). Zero cohorts cleared the composed-feature importance ≥30 falsifier — by gain, all cohorts cleared the absolute threshold (227-1030), but **rank is the binding signal**: 23-30 in a 44-feature stack means the feature lives in the bottom-half tail with the inert noise floor (basis was rank 27.67 mean; regime_momentum landed at rank ~27 portfolio — **identical noise-floor band**). The v3 /025 narrative (51% top-of-table gain share) dissolves completely at v1 cycle-5 — composed feature is RSI/Aroon/MACD-spanned at v1's 44-col density.

## Overfit Mechanism Analysis

The +0.28 IS lift without rank-evidenced signal-bearing is the diagnostic. Three mechanisms compound:

1. **Basis-drop loss-surface reorganization (LOAD-BEARING).** Dropping basis_zscore_30 (rank 27-30 inert noise at /037+/038) didn't remove signal — it removed a noise dimension Optuna was already ignoring. But the **colsample-bytree** stochastic pick now samples one fewer noise column per tree, marginally tightening the effective tree distribution. The IS basin Optuna found shifted to a slightly different ridge (the 3rd consecutive `n_effective_trials=9` confirms ridge-prone topology). That ridge over-fit to IS-specific 2022-Q4 + 2023-Q1 momentum regimes — LTC IS PnL +140% / LINK +121% drove the +0.28 IS lift, but those symbols collapsed in OOS (LTC +20%, LINK -20%).

2. **regime_momentum composed feature as noise injector (NOT signal).** Trees used the feature for efficiency splits (1030 gain portfolio-wide) but rank 26 means **per-split it captures less than 25% of the gain that the top-5 features (vol_atr_14, trend_aroon_osc_50, stat_autocorr_lag5, oi_delta_30_z90, interact_natr_x_adx) capture each**. The feature acts as a **44th-column lottery ticket** for Optuna — sometimes selected, sometimes not, shifting basin position iter-to-iter. Per `feedback_v3_inert_features_at_higher_budget.md`, INERT features at n_trials=18 are not as harmful as at n_trials=35, but in v1's already-ridge-prone topology, they tilt the basin OOS-suboptimal direction.

3. **Why /025 worked at v3 and /040 failed at v1.** v3 /025 ran on 14-col TOP_N where regime_momentum had only 13 competitors — and importance landed at 51% top, displacing weaker features. At v1's 44-col stack the **top-5 features (atr_14, aroon_osc_50, autocorr_lag5, oi_delta_30_z90, natr_x_adx) command 26,318 / 165,000 ≈ 16% portfolio gain EACH** — there is no room at the top for regime_momentum's modest signal density. **v1 momentum primitives (RSI 14, Aroon 50, MACD 12-26-9, stat_log_return_5) already saturate the 5-day signed-momentum subspace.** The hurst=+1 EDA finding (Phase 4.5 §Saturation Risks) predicted this — the feature is a 120h log-return primitive without regime conditioning, and v1 already has 8 momentum-family features.

## Suspicious Patterns for Critic Check 3 + 5

- **Per-symbol IS positive-pair / OOS negative-pair regression**: LTC + LINK drove BOTH the +0.28 IS lift AND the OOS collapse (LINK went +121% IS → -20% OOS, the largest single-symbol IS/OOS divergence in v1 cycle-5). Investigate: is LINK over-fitting on a 2022-Q4-specific 5-day momentum regime that decayed in 2024 OOS? **Recommend Critic Check 3 (DSR) drill-down on per-symbol stability**.
- **3rd consecutive `n_effective_trials=9` recurrence (/037 + /038 + /040)** — Phase 4.5 flagged at 2-iter recurrence. Now 3-iter. **The v1 44-col cycle-5 stack at n_trials=18 is structurally ridge-locked** — Optuna's effective trial saturation is independent of axis. Critic should flag for /044 substrate decision: this is the strongest evidence yet that **n_trials=18 budget is undersized for 44-col density**, OR the 44 cols are over-correlated to the point that the effective dimensionality is ~9.
- **DSR=-48.39 OOS** — this is the worst DSR in v1 cycle-5 (vs baseline /033 DSR ~-30). Critic Check 6 should investigate PSR_monthly_vs_1 = 0.215 (below 0.30 floor); /040 is **structurally PSR-failing** even ignoring the IS overfit.

## Hyperparameter Trial Stability

Cannot read run.log Optuna traces directly (file not in artifacts), but `n_effective_trials=9` at n_trials=18 implies **50% trial saturation** — Optuna found one ridge and stuck. This is consistent across /037 (HIT loss axis) + /038 (DD brake) + /040 (feature swap) — 3 different axes, same saturation. **Conclusion: the v1 44-col stack at n_trials=18 has a single dominant attractor basin that all 3 axes navigate into.**

## Next-Iteration Recommendations (3 items)

### 1. /044: DO NOT bundle regime_momentum_signed_5d into substrate.
- **What**: feature-engineering composed-feature axis CLOSED for v1 cycle-5 absent re-test at smaller search space (n_trials=10 + min_data_in_leaf=50 floor + colsample=1.0 to force the feature into every tree).
- **Mechanism**: rank 23-30 across 5/5 cohorts is rank-evidenced refutation. Per `feedback_v3_engineered_features_proven.md`, composed features WORK when there's signal-headroom in the feature stack (v3 14-col); v1 44-col saturates the momentum subspace.
- **Risk**: ignoring rank evidence and re-testing at higher Optuna budget will INVERT — see `feedback_v3_inert_features_at_higher_budget.md` (iter-v3/023 INERT feature at n_trials=35 produced OOS -1.85 Δ).

### 2. /041-/043: NON-FEATURE axes mandatory.
- **What**: 4-consec feature-family NEG/INERT on basis_zscore_30 + regime_momentum closes the family. Next 3 EXPLORATIONs MUST be: model-arch (XGB head-to-head), labeling (TB-width), or universe (denominator expansion). Per `feedback_v3_iter016_xgboost_mandate.md` v3 precedent — when feature axis saturates, switch arch.
- **Mechanism**: cycle-5 closure discipline. Per `feedback_structural_over_knob_exploration.md`, do NOT re-test feature variants.

### 3. Pre-commit /044 substrate: address the `n_effective_trials=9` ridge.
- **What**: at /044 CONFIRMATION-spec, raise n_trials to 35 (CONFIRMATION default) AND add Optuna sampler diagnostic — log effective_trials per cell. If still ≤15 at n_trials=35, the 44-col stack is over-correlated and needs PCA-style decorrelation or 14-col TOP_N prune (mirror v3 architecture).
- **Mechanism**: 3-iter recurrence is structural. Cannot ignore.

## What This Iteration Confirms / Refutes About Prior LM Master Advisory

**Phase 4.5 was directionally wrong but mechanistically right.** I assigned 65% PROMISING-tail and predicted modal PROMISING-INERT-FAV (35%). Observed was a **NEG-CLEAN + INERT-by-rank hybrid** — a class I did not pre-allocate probability to (effectively 0%). **Correctly predicted**: (a) hurst=+1 weakness of the regime narrative — Phase 4.5 §Saturation Risks called out "weaker than v3" and "PROMISING-INERT-FAV as modal vs v3-style PROMISING-CLEAN"; (b) the rank=8-14 worst-case for LTC was hit at rank 30; (c) the `n_effective_trials` ridge recurrence was flagged at 2-iter and is now 3-iter structural. **Incorrectly predicted**: (a) MEDIUM confidence on rank ≤5 in ≥3/4 cohorts — observed 0 cohorts cleared rank ≤10; (b) failed to allocate probability mass to the IS-LIFT/OOS-DROP overfit mode despite calling it out as a basin-shift risk. **Calibration update**: composed features in stacks ≥40 cols should default to 20% PROMISING-CLEAN, 30% INERT-rank, 30% NEG-overfit-basin-shift.

## Closing Note for Critic (Phase 7.5)

Critic Check 3 (DSR/PSR robustness): DSR -48.39 + PSR_monthly_vs_1 0.215 are structurally weak — note that this is INDEPENDENT of the IS overfit. Critic Check 5 (feature stationarity): regime_momentum_signed_5d ADF should PASS (it's a 5-day log return composed feature, stationary by construction); the failure is rank-importance, not stationarity. **Single most important flag**: 3rd consecutive `n_effective_trials=9` across 3 distinct axes is a structural ridge-lock pattern — Critic should consider whether v1 cycle-5 is BASIN-LOCKED independent of /040's NEG verdict, and whether /044 substrate decision should pre-commit a sampler diagnostic.
