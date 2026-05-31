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
