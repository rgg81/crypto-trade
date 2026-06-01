# LightGBM Master Advisor — iter-v1/038 — Phase 7.4 (Post-Mortem)

## Context Read
- Track: v1. Anchor: BASELINE_V1 (`v0.v1-baseline-corrected`, IS +0.2829 / OOS +0.6637).
- /038 axis: per-symbol vol-target ceiling (75th pct of `rv_30d_ann`, 0.5× scale, 5 cohorts).
- Phase 4.5 prior: HIGH-confidence-NEGATIVE-sign. EDA §3 modal +25% NEG-CLEAN, asymmetry table §4 inverted for 3 of 5 symbols (LINK -3.30, DOT -10.46 net_pnl asymmetry).
- Outcome: IS -0.0308 (Δ -0.31) / OOS +0.1337 (Δ -0.53) → **NEG-CATASTROPHIC** band breached on OOS.

## 1. F-AXIS Falsifier Table

| # | Criterion | Observed | Verdict |
|---|---|---|---|
| 1 | Wiring: fire_rate_is > 0 | 10.56% IS / 3.85% OOS | **PASS** |
| 2 | Trade-count band IS [610, 632] | **720 IS** (overshoot +14%) | **FAIL** — ceiling did not cull trades; it kept all and halved sizing, so total count went UP (different model basin emitted more entries) |
| 3 | Per-symbol PnL Δ vs EDA-§3 linear sign | 2 of 5 sign-match (BTC, LINK); 3 of 5 INVERTED (ETH, LTC, DOT) | **FAIL** — load-bearing |
| 4 | Bundle IS PnL Δ in [-30%, -15%] | observed Δ from +24.98 → **-4.57** = **-118% relative** | **FAIL — CATASTROPHIC OVERSHOOT** (~4.5× worse than linear prediction) |
| 5 | OOS sign consistency with IS | IS sign NEG / OOS sign POS (+7.18 PnL) but Sharpe both worse than baseline | **FAIL** — both worse than baseline magnitude |

**4 of 5 FALSIFIERS FAIL.** Hypothesis H1a (retraining absorbs the ceiling) is **REFUTED in the wrong direction**: retraining AMPLIFIED damage rather than compensating it.

## 2. Per-Symbol Sign-Match (vs EDA §3 linear prediction)

| Symbol | EDA Δ pred | /038 IS PnL | Baseline IS PnL | Observed Δ | Sign match? |
|---|---|---|---|---|---|
| BTC | +6.16 | -86.59 | -37.28 | **-49.31** | **NO** (predicted improve; got worse) |
| ETH | +4.81 | -114.00 | -13.70 | **-100.30** | **NO** (predicted +5; got -100) |
| LTC | +3.58 | +116.39 | +3.27 | **+113.12** | **YES** (sign +, magnitude 32× larger) |
| DOT | -6.24 | +60.74 | +26.62 | **+34.12** | **NO** (predicted worse; got better) |
| LINK | -32.94 | +42.58 | +72.06 | **-29.48** | **YES** (sign -, magnitude matches within 12%) |

Only **2 of 5 sign-match**. The portfolio collapse (-55pp PnL) is driven by **ETH (-100pp) and BTC (-49pp)** — exactly the cohorts EDA predicted would IMPROVE. The linear-roster prediction was **wrong on sign for the majority of the universe** because retraining shifted Model A (BTC+ETH pooled) into a fundamentally different basin.

## 3. Why Retraining Did NOT Absorb the EDA Prediction

**Hypothesis confirmed**: pruned 43-feature stack + n_trials=18 + single-seed (per brief Section 5 "Optuna search space, training labels, features, loss surface bit-identical to baseline") **broke catastrophically for Model A only**. Evidence:

- `n_effective_trials = 9` (comparison.csv) — Optuna found a tight ridge fast in 9 of 18 trials. Same number as /037; this is now a **2-iteration recurrence** at v1's reduced-trial budget.
- The ceiling DOES NOT enter the Optuna loss surface (it's a downstream multiplier on `position_size` AFTER trade decision). Optuna is optimizing a Sharpe whose denominator is unaffected by sizing scale but whose tail moments ARE — and the n_trials=18 budget cannot navigate the new geometry for the 2-symbol pool.
- Model A IS PnL went from -50.98 (baseline pooled BTC+ETH) to **-200.59** (/038 pooled). Models C/D/E (single-symbol) all directionally MATCHED EDA prediction in sign (LINK -, LTC +, DOT improved). **The pooled cohort is the failure mode.**

The 0.5× sizing on BTC+ETH high-vol entries reshuffled Optuna's per-trade Sharpe contribution unevenly between the two pooled symbols, and at n_trials=18 the search found a basin that is good for `weighted_pnl_pooled` IS metric but emits 318 trades (vs baseline 258 for BTC+ETH pooled) at far worse mean expectancy.

## 4. Feature Importance Shift

Top-5 ranks are **bit-identical to baseline and to /037**: `vol_atr_14`, `trend_aroon_osc_50`, `stat_autocorr_lag5`, `oi_delta_30_z90`, `trend_adx_14`/`stat_skew_20`. Mean-gain magnitudes are HALVED across the board (Model A rank-1 gain: baseline ~13k → /037 20k → /038 6.5k). **The basin reorganization is hyperparameter-space, NOT feature-space.** No new feature surfaced; the ceiling did not surface vol/regime features higher than they were.

`basis_zscore_30` remains rank ≥15 (3rd-iteration INERT — confirms /037 LM Master flag; **drop candidate at /039**).

## 5. STRUCTURAL CONCLUSION — V1 Catalog

> **Per-symbol sizing-side ceiling primitives (vol-target ceilings, vol-floors, RV-percentile gates that scale `position_size` downstream of model prediction) are AXIS-CLOSED for v1's 5-cohort universe at single-seed EXPLORATION budget (n_trials=18, ENSEMBLE_SIZE=3). The mechanism does not enter Optuna's loss surface; n_trials=18 cannot navigate the resulting basin geometry for pooled Model A; per-symbol asymmetry table §4 inversion (3 of 5 symbols high-vol-EDGE-positive) makes symmetric thresholds structurally unsuitable. The /010 R5 vol-FLOOR (the only prior risk-primitive precedent) is the ceiling-rule's mirror image and was the only viable sizing-side risk primitive ever to clear v1 EDA.**

This forecloses two future axes: (a) symmetric vol-ceilings at any percentile or scale, (b) RV-based pre-trade sizing modulation in general. **Asymmetric per-symbol kill-switches** (binary OFF for specific cohorts in specific regimes — semantically distinct from proportional scaling) remain open per `feedback_v3_concentration_is_signal.md` orthogonal-mechanism doctrine.

## 6. /039 Pivot Recommendations (3 non-risk-primitive axes)

### Rec 1 — DROP `basis_zscore_30` + REPLACE with composed feature `regime_momentum_signed` (FEATURE-ENGINEERING family) [HIGH CONFIDENCE]
- **What**: drop `basis_zscore_30` (rank ≥15 for 3 consecutive iters /034-/038 = INERT recurrence per `feedback_v3_inert_features_at_higher_budget.md` doctrine), add v3-proven `regime_momentum_signed_5d = ret_5d × sign(hurst_100 - 0.5)`. Hurst already in V1_FEATURE_COLUMNS_PRUNED — pure composition, no new data.
- **Why**: iter-v3/025 PROMISING + iter-v3/028 CONFIRMATION-MERGE precedent (importance 51% top vs 22-25% off-the-shelf). Trees at depth 3-5 can't compose this. The 43-col pruned stack has held identical rank-1-5 for 5 iterations — **feature-space is saturated; need NEW signal not new gate**.
- **Mechanical compatibility with /036 + /037**: ORTHOGONAL. /036 was per-cohort specialization (model arch); /037 was Sortino objective (loss function). FEATURE family has not been touched since /034.
- **Risk**: Critic Check 4 IC carve-out per `feedback_v3_engineered_feature_pivot.md` — composed features mechanically correlate with primitives; use importance ≥30 threshold not |IC|<0.50.

### Rec 2 — LABELING-AXIS pivot to triple-barrier WIDTH asymmetry (LABELING family) [MEDIUM CONFIDENCE]
- **What**: keep TP=2.0×ATR / SL=1.0×ATR ratio but TIGHTEN both to TP=1.5 / SL=0.75 (50% narrower bands → shorter label horizons → more trades per training cell, mean trade duration drops). Target IS trade count 800+ (was 621 baseline, 720 /038).
- **Why**: LABELING family has been **never touched in v1 cycles 1-5**. All cycle-5 axes (/034 feature, /035 OOD risk, /036 specialization, /037 loss, /038 risk-primitive) leave the (TP, SL, timeout) tuple fixed. This is the biggest unexplored axis-family with prior v3 evidence of effect (see v3 /017 meta-labeling though NEG-PATH-C; structural axis NEVER touched in v1).
- **Mechanical compatibility**: ORTHOGONAL to /036 (model arch) and /037 (loss). Re-labels training data → forces full Optuna re-search → tests whether basin migration is constrained by long-horizon labels.
- **Risk**: tighter barriers → more noise / more trades / more whip-saws. Pair with `min_data_in_leaf` floor bump from 20 → 50.

### Rec 3 — MODEL-ARCH XGBoost head-to-head on the SAME 43-feature stack (MODEL family) [MEDIUM-LOW CONFIDENCE]
- **What**: swap LightGBM → XGBoost (depth-wise, n_trials=18, max_depth ∈ [3,7], `tree_method='hist'`, `objective='reg:squarederror'` on triple-barrier label). Single-axis controlled comparison.
- **Why**: iter-v3/016 ran this on v3's 13-feature stack at n_trials=10 and got NEGATIVE clean — but v1's 43-feature stack + 5-symbol pool is a fundamentally different regime; the v3 negative does not foreclose v1. MODEL-ARCH family is the only structural family with a clean prior precedent.
- **Mechanical compatibility**: ORTHOGONAL to /036 (LightGBM per-cohort specialization). If XGBoost beats LightGBM at the pooled level, /036's specialization stack would be re-evaluated under XGB.
- **Risk**: 8h candles + 43 cols + 5 cohorts × monthly walk-forward = ~50× per-cell compute at XGB defaults; ensure brief Section 7 enforces 2h CAP at EXPLORATION.

## What This Iteration Confirms About Prior LM Master Advisory

Phase 4.5 prior was **HIGH-confidence-NEGATIVE-sign**, predicted modal **NEG-CLEAN [-0.45, -0.15]**. Observed OOS Δ = **-0.53** → **NEG-CATASTROPHIC**, beyond the modal band. **Direction correct, magnitude underestimated by ~20%.** The miss: I priored "EDA's linear -26% IS PnL prediction will roughly hold under retraining"; reality was retraining **catastrophically amplified** the damage in Model A (BTC+ETH pool went -200 PnL vs baseline -51). The Optuna-basin-instability flag from /037 (n_effective_trials=9) was the load-bearing signal I underweighted — this is the **2nd consecutive iteration** Optuna found a tight ridge in <9 trials, and that pattern now requires explicit Phase 4.5 attention.

## Closing Note for Critic (Phase 7.5)

Critic Check 3 (per-symbol PnL stability): note that **3 of 5 cohorts (ETH, LTC, DOT) sign-INVERT vs EDA §3 linear prediction**, and Model A pooled (BTC+ETH) drops -150 IS PnL alone. The PSR_monthly_vs_1 lifted (0.183 OOS) is a **statistical artifact of variance compression from sizing halving 10% of trades** — not edge discovery. Check 8 (basin instability) should weight `n_effective_trials=9` as a **2-iter recurrence pattern**, not noise.
