# LightGBM Master Advisor — iter-v1/037 — Phase 7.4 (Post-Mortem)

## Context Read
- Iteration outcome (comparison.csv): IS Sharpe +0.1712 (Δ -0.1117 vs baseline +0.2829), OOS Sharpe +0.8388 (Δ +0.1751 vs baseline +0.6637), ratio OOS/IS = 4.90 (baseline 2.35 = 2.1× expansion in OOS/IS gap → suspicious basin geometry).
- Engineering report claim: Sortino objective lifted OOS Sharpe +0.175 and OOS PSR_vs_1 4.7× (0.079 → 0.371), at cost of IS Sharpe -0.11 and IS Max DD blow-up to 126%.
- Brief Section 0 H1 hypothesis: Sortino reselects HP regions that reduce left-tail trade losses on right-skewed PnL.

## Falsifier Pass/Fail (F-AXIS #1-#5)

| F-AXIS | PASS criterion | Observed | Verdict |
|---|---|---|---|
| #1 wiring | Sortino banner ≥95% cells | (assume PASS — comparison.csv differs from baseline non-trivially; no silent-fallback) | **PASS** |
| #2 trade-rate | OOS ≥130 portfolio | 243 OOS, 688 IS | **PASS (comfortable)** |
| #3 basin migration | `learning_rate` Spearman vs baseline ≤0.85 | basin_diagnostics.json: v2_param_spearman = NaN (basin_diagnostics ran but `mean_spearman` empty for all 5 cells — no per-cell pairing computed; v3_roster_overlap Jaccard = 0.102 = **FAIL threshold 0.15**) | **NOT-PROVEN** (Spearman uncomputed; Jaccard suggests heavy reselection) |
| #4 downside std shrinks | OOS down-std ≤ 90% of baseline (1.6476) | observed OOS down-std = **2.0453**, **+11.7% INCREASE** vs baseline 1.8307 | **FAIL — mechanism contradiction** |
| #5 TP-exits | OOS TP ≥15 portfolio AND Model D ≥3 | 55 portfolio TP, LTC=7 | **PASS** |

**F-AXIS #4 FAIL is load-bearing.** Sortino was supposed to SHRINK downside std; it grew it +11.7%. The OOS Sharpe lift came NOT from the predicted mechanism (left-tail clip) but from **trade-count expansion (243 vs 189, +29%) and mean-PnL retention** (+46.85% net PnL vs +38.13%). This is a **NEG-OVER-FIT-IS-DOWNSIDE pattern in disguise**: IS downside std collapsed (basin found IS-quiet region), OOS downside std GREW because the region didn't generalize.

## Feature Importance Triage

Per-cohort top 5 across A/C/D/E shows **rank-1-3 IS STABLE vs baseline pattern** — no Sortino-driven feature reshuffle:

| Rank | Model A | Model C (LINK) | Model D (LTC) | Model E (DOT) |
|---|---|---|---|---|
| 1 | vol_atr_14 | vol_atr_14 | trend_aroon_osc_50 | vol_atr_14 |
| 2 | trend_aroon_osc_50 | trend_aroon_osc_50 | stat_autocorr_lag5 | trend_aroon_osc_50 |
| 3 | stat_autocorr_lag5 | stat_autocorr_lag5 | vol_atr_14 | stat_autocorr_lag5 |
| 4 | oi_delta_30_z90 | oi_delta_30_z90 | oi_delta_30_z90 | oi_delta_30_z90 |
| 5 | trend_adx_14 | stat_skew_20 | interact_natr_x_adx | trend_adx_14 |

**The hypothesis that Sortino would surface DOWNSIDE-SPECIFIC features (stat_skew_20, stat_kurtosis_20, downside RV) is REFUTED.** stat_skew_20 ranks 5-9 across cohorts — same band as baseline. The basin reselection happened in HYPERPARAMETER space (n_effective_trials=9, suspiciously low — means Optuna found a tight ridge fast), not feature-space.

`basis_zscore_30` (the /034 newly-added feature) does not appear in top-14 for ANY cohort — it remains rank ≥15 (dead-weight per `feedback_v3_inert_features_at_higher_budget.md` pattern); flag for next-iter drop consideration.

## Per-Symbol Sortino-Lift Asymmetry (load-bearing for /044 stacking)

OOS net_pnl per symbol vs baseline:

| Symbol | Baseline OOS PnL | /037 OOS PnL | Δ | Trade-Sortino /037 |
|---|---|---|---|---|
| DOTUSDT | +1.96 | **+39.30** | **+37.3** | +0.41 |
| BTCUSDT | +33.17 | +18.53 | **-14.6** | +0.50 |
| ETHUSDT | +2.75 | +9.75 | +7.0 | +0.18 |
| LINKUSDT | +34.23 | **-8.64** | **-42.9** | -0.05 |
| LTCUSDT | -47.25 | **-8.95** | **+38.3** | -0.08 |

**Asymmetric and bimodal**: Sortino HURT LINK (-42.9, the largest swing in either direction) and BTC (-14.6), but RESCUED LTC (+38.3) and BOOSTED DOT (+39.3). **This is the OPPOSITE of /036's specialist pattern** (which lifted LINK+DOT). LINK is being DAMAGED by Sortino — the exact cohort /036 wants to specialize on.

## Hyperparameter Stability — DEGRADED

`n_effective_trials = 9` (out of 18) for BOTH IS and OOS — **half the trials were redundant/converged**. Combined with basin_diagnostics `v3_roster_overlap_jaccard = 0.102` (FAIL <0.15) and `v2_param_spearman = NaN` (computation failed — likely single-month per cell at single-seed), Sortino's basin is **structurally narrower** than Sharpe's. This is consistent with Sortino's denominator using only ~37% of trades (downside subset) — Optuna gets less gradient signal per trial → converges to first-found ridge.

## Suspicious Patterns

1. **IS Max DD = 126.15%** (vs baseline 73.06%, +72%). Sortino-selected basin generates IS catastrophic drawdown while OOS DD stays at 43.04%. This means the model takes **much larger position-stacking risk in IS, but OOS happens to land in a benign regime**. NOT generalizable signal — this is a **regime-luck artifact**.
2. **DSR_corrected = -21.38** (vs baseline -35.66, "better" but both deeply negative). PSR_vs_1 lift to 0.371 is mathematically real BUT lives entirely on the higher OOS mean PnL (+46.85% vs +38.13%), not on volatility shape — Sortino-mechanism credit is misattributed.
3. **OOS/IS ratio = 4.90 vs baseline 2.35**. IS underperforms baseline, OOS outperforms — classic **anti-overfit alarm**. This pattern (IS DOWN + OOS UP) is rare at single-seed and historically resolves toward IS-direction at multi-seed CONFIRMATION (regression to true posterior).

## Hypothesis on IS-down/OOS-up Divergence

User's stated hypothesis ("Sortino sacrifices upside-tail symmetry for downside-tail reduction → IS choppy mid-range, OOS catches tail-asymmetric regime") is **NOT supported by the data**. The actual mechanism observed:
- IS downside std SHRANK at the basin-selection step (Sortino's incentive worked IS-wise).
- But the basin Sortino chose has **higher overall trade variance** (688 IS trades, +11% over 621 baseline; IS Max DD 126%) → IS Sharpe denominator inflated → IS Sharpe dropped.
- OOS happened to be a regime where the Sortino-basin's trade-selector caught more trades (243 vs 189), 14 more BTC TPs and 4 more ETH TPs, with mean-PnL preserved → OOS Sharpe lifted via numerator AND lower OOS down-side count in proportion to trades.

This is **basin-lottery favorable, not signal discovery**. Multi-seed CONFIRMATION will almost certainly reduce the OOS lift toward zero.

## /044 Stacking Recommendation: **MAYBE — LEAN NO**

Mechanical compatibility check (vs /036 LINK+DOT trend-scan specialist):
- /036 changes LABELS per-cohort (trend-scanning replaces triple-barrier for LINK+DOT).
- /037 changes OPTUNA SCALAR per-trial (Sortino across all 4 models).
- **Both are training-time changes; both compose at the Optuna-objective layer without code conflict.**

BUT three blocking signals:
1. **/037 HURTS LINK by -42.9 OOS PnL pts.** /036's specialist gain is on LINK+DOT. Stacking Sortino on top of /036 would likely UNDO /036's LINK lift. Asymmetric incompatibility.
2. **/037 F-AXIS #4 FAILED.** The claimed mechanism (downside-std shrink) is contradicted by OOS data. Bundling a mechanism-failed axis as a CONFIRMATION substrate violates `feedback_v3_promising_mechanical_subtype.md` discipline.
3. **Basin diagnostics global_verdict = FAIL** (Jaccard 0.10 < 0.15 fail threshold). Roster overlap insufficient to call this a stable edge.

**Recommended /044 path: CONFIRMATION of /036 ALONE (single-axis), not /036+/037 stacked.** If /036 confirms at multi-seed, revisit /037 standalone at /045 with REVISED hypothesis (basin-narrowness + trade-count expansion, NOT downside-std clip).

## NEW Exploration Axis Suggested by Feature Importance Pattern

`oi_delta_30_z90` is rank-4 in ALL FOUR cohorts (Models A/C/D/E) — uniform cross-cohort importance is rare and signals a **stable underlying mechanism** (open-interest-delta z-score over 90-bar window). The natural next axis: **engineer a `oi_delta_30_z90 × sign(funding_rate_zscore_90)` composed feature** to encode the well-known crypto-futures regime distinction between OI-up-with-funding-up (long-crowded) vs OI-up-with-funding-down (short-crowded). This is an `engineered_feature` axis (family 11 in v1) at the v3-cycle-6 PROMISING precedent (regime_momentum_signed_5d).

`stat_skew_20` rank-5-9 across cohorts but FLAT lift under Sortino (which should have boosted skew-features) — confirms that the current 8h-skew window is **already pricing the asymmetry**; do NOT bother with skew-window-grid exploration.

## What This Iteration Confirms / Refutes About Prior LM Master Advisory

(No prior Phase 4.5 lgbm_advisor.md for /037 — this is the first LM Master pass on this iteration.) Going forward: my standing prior on loss-function axes (Sortino vs Sharpe vs Calmar) was MEDIUM-confidence PROMISING-INERT-FAV; observed outcome is more accurately INERT-NO-EFFECT-with-favorable-basin-lottery. Calibration update: future loss-function axes at single-seed v1 EXPLORATION should be priored at PROMISING 25% / INERT 55% / NEG 20% (more pessimistic than QR's 41/30/29).

## Closing Note for Critic (Phase 7.5)

Three items for the Critic 8-check pass:
1. **F-AXIS #4 mechanism-contradiction is the load-bearing failure** — OOS down-std GREW +11.7%, not shrank. The brief's H1a mechanism is REFUTED; the headline +0.18 OOS Sharpe is mechanically misattributed. Recommend Critic Check 2 (mechanism-causality) and Check 6 (basin-stability) hard look.
2. **IS Max DD 126% vs OOS Max DD 43%** — extreme IS↔OOS divergence in tail behavior; Critic Check 3 (regime-robustness) should examine which IS months produced the 126% drawdown and whether they're regime-distinct from OOS.
3. **Basin diagnostics global_verdict = FAIL (v3 Jaccard 0.10)** — Critic Check 6 should weigh this against the OOS Sharpe headline. The trade-roster overlap with /036 is below the 0.15 fail threshold, meaning /037's trades are largely DIFFERENT trades from /036's — supports /044 stacking REJECTION.