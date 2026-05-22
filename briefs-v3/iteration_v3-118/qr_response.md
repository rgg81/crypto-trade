# iter-v3/118 — QR Round-2 Response

**To**: Critic
**From**: QR
**Re**: PRELIMINARY review at `briefs-v3/iteration_v3-118/review_preliminary.md` (orchestrator-authored Round 1)
**Round-2 evidence-introduction constraint**: this response cites ONLY committed artifacts — `analysis/iteration_v3-118/*` (EDA tables T1–T9 + synthesis), `briefs-v3/iteration_v3-118/engineering_report.md`, `reports-v3/iteration_v3-118/{in_sample,out_of_sample}/*`, `briefs-v3/iteration_v3-118/research_brief.md`, `briefs-v3/exploration_catalog.md`, prior diaries (`diary-v3/iteration_v3-{115,116,117}.md`), the cycle-6 axis menu (`project_v3_cycle6_axis_menu.md`), and existing memory rules. No new data, no new EDA, no new analysis script.

## Round-2 Position

I STAND BY THE VERDICT. The Critic's PRELIMINARY classification — `EXPLORATION-NEGATIVE catastrophic` via Section-8 Criterion 1a (IS Sharpe Δ = −0.4543 << −0.20 vs /060) — is mechanically correct and substantively supported by the 3 corroborating diagnostics in the Critic's prose (per-symbol role-reversal vs EDA T9, importance-benchmark fail vs /025, multivariate-interaction-cancellation pattern from `feedback_v3_inert_features_at_higher_budget.md`). All 8 of the Critic's PRELIMINARY per-check statuses are correct and I do not contest any. The 4 clarifications below are substantive answers, not requests for reconsideration.

---

## Clarification 1 — Axis-Closure Scope (specific C3 vs broader "value × vol-regime-sign" lineage)

**Recommendation: CLOSE the broader "value × vol-regime-sign" Category-2 composed lineage at /118**, NOT only the specific C3 = ema_spread_atr_20 × sign(rv_50 − rolling_median_200) composite. The Critic's broader-closure lean is correct.

The EDA's T2–T9 chain proved C3 was the BEST candidate in the EDA's 6-candidate screen on the production-relevant criterion (T9 POOLED multivariate-lift +0.0081 vs the closest competitor C4's +0.0010 — an 8× edge in the controlling metric per `feedback_v3_engineered_features_proven.md`/`feedback_v3_engineered_feature_pivot.md`), AND the only candidate clearing the multivariate-importance gain ≥ 30% bar on all 3 symbols at the EDA's depth-4 (14+1) LightGBM screen (T5 ranks 8–10 with gain 38–63%). The production runner — at /060's hyperparameter envelope plus C3 — INVERTED both predictions: portfolio rank dropped from EDA's predicted 8–10 to 6/15 (a partial pass on rank, fail on the 30%-share gain threshold at 7.1%), and the per-symbol distribution flipped from EDA's TRX-led-positive / BCH-LDO-negative to TRX-collapsed / BCH-positive / LDO-catastrophic. The EDA's depth-4 single-tree screen and the production walk-forward depth-3-5 Optuna search occupy structurally different points in the bias-variance frontier (`feedback_v3_lr_pf_methodology.md`'s "trees can use derived features for EFFICIENCY without that allocation reflecting NEW signal" concern, applied in inverse direction here: trees CAN allocate to a feature in a screen yet fail to convert that allocation to OOF AUC lift at production scale).

The variants the Critic flagged as potentially LIVE within the narrow lineage — rolling-median-100, expanding-median, alternate vol estimators (Parkinson, Garman-Klass, Rogers-Satchell), alternate value primitives (RSI-spread, MACD-histogram-spread, etc.) — would all parametrize the same `value × sign(vol-classifier)` algebraic form against the same production loss surface that just produced the inversion. The argument for re-trying within the narrow lineage would require a NEW mechanism to dissolve the inversion, and the Critic's third diagnostic (single-seed lottery + multivariate-interaction-cancellation at n_trials=35) names the inversion as a STRUCTURAL property of the single-seed + 15-dim-Optuna combination, not a property of the specific median window or value primitive. Retrying within the narrow lineage at single-seed EXPLORATION budget would be expected to produce another instance of the inversion against a different per-symbol carrier — i.e., information-theoretic ZERO marginal value.

**Closed at /118 catalog level**: the entire `value × sign(vol-regime-classifier)` Category-2 composite family, at single-seed EXPLORATION budget on the BCH/LDO/TRX universe.
**Still LIVE within the broader engineered-feature axis**: composite families on STRUCTURALLY DIFFERENT regime classifiers (e.g., realized-skew sign, MACD-histogram sign, ATR-percentile-rank sign, autocorrelation sign at different lags) AND composite families on STRUCTURALLY DIFFERENT value primitives that are themselves orthogonal to the EMA-spread family (e.g., volume-based primitives, microstructure primitives, cross-asset primitives). The /025 PROMISING precedent — `regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5)` — used hurst as the regime classifier, NOT vol. The vol-regime branch is now closed; the hurst-regime branch has the /025 precedent; OTHER regime classifiers remain unexplored.

**Catalog wording**: "value × vol-regime-sign Category-2 lineage CLOSED at /118 EXPLORATION-NEGATIVE-catastrophic on the BCH/LDO/TRX cohort at single-seed n_trials=35. The narrower vol-classifier specifics (median window, vol estimator) are subsumed by the broader closure; reopening requires either (a) multi-seed CONFIRMATION-budget validation OR (b) a different regime-classifier family."

---

## Clarification 2 — Mode 3 Inversion Mechanism (single-seed lottery vs intrinsic property)

**Read: the inversion is PRIMARILY a single-seed-lottery + multivariate-interaction-cancellation artifact AND PARTIALLY an intrinsic property of C3's information geometry against the /060 stack. The two channels are entangled. I do NOT expect the inversion to dissolve cleanly at 10-seed multi-seed — I expect it to ATTENUATE but not invert back to the EDA T9 prediction.**

The Critic's third PRELIMINARY diagnostic correctly identifies the central mechanism: with C3 added simultaneously to all 3 symbols at n_trials=35 single-seed, Optuna's 15-dim search lands on a TRX-favorable hyperparameter point that maximizes C3's allocation to TRX (rank 1/15, importance 205.0) at the cost of TRX's incumbent 14-feature edge — and this is `feedback_v3_inert_features_at_higher_budget.md`'s mechanism observed in reverse direction (not "INERT feature actively HARMS at higher budget" but "WEAK-multivariate-lift feature actively REDIRECTS attention at higher-than-screen-budget"). The EDA's T9 multivariate-lift screen was at depth 4 single-tree LightGBM — a structurally different optimizer than the production walk-forward Optuna at depth 3-5 ensembled over 3 seeds × 105 walk-forward training-month rebuilds.

The intrinsic-property component: C3's `sign(rv_50 − rolling_median_200)` is a SLOW (~67-day) regime indicator whose state-transitions are sparse — within the 21-bar triple-barrier horizon, the regime classifier rarely flips. Combined with `ema_spread_atr_20`'s mean-reverting value primitive at ~6-day timescale, the C3 product is dominated by the value-primitive variance during the long stretches where the regime sign is stable. This means C3 carries information that is LARGELY ALREADY ENCODED in `ema_spread_atr_20` + `range_realized_vol_50` independently when the model sits at depth ≥ 2 — exactly the iter-v3/053 hurst_drift_50_200 mechanism (`feedback_v3_lr_pf_methodology.md`: "trees can use derived features for EFFICIENCY without that allocation reflecting NEW signal"). The EDA's R²=0.196 is a marginal redundancy measure that misses the conditional-on-tree-structure efficiency channel.

**Multi-seed expectations**: at the 10-seed unified ensemble (CONFIRMATION envelope), each seed lands in a different Optuna attractor. Approximately:
- Some seeds land in TRX-led attractors → TRX dominates C3 importance, BCH/LDO get little C3 weight, IS edge similar to /118
- Some seeds land in BCH-led attractors → BCH dominates C3 importance, TRX gets little C3 weight, IS edge similar to inverted /118
- Some seeds land in LDO-led attractors → LDO dominates C3 importance, BCH/TRX get little C3 weight, IS edge similar to a different per-symbol pattern
- The 10-seed MEAN attenuates the cross-symbol asymmetry but does NOT recover the EDA T9 POOLED +0.0081 lift because the multivariate-interaction-cancellation channel is seed-invariant: each seed individually produces C3-OFFSETS-EDGE-IN-ONE-SYMBOL behavior, the mean is small, and the variance across seeds is high.

Net expectation at 10-seed: IS Sharpe Δ vs /060 stays NEGATIVE-but-smaller-magnitude (modal: Δ ∈ [−0.20, −0.05]; less catastrophic than /118's −0.4543 but still NEGATIVE), with a wider per-seed dispersion that fails Gate 10 Pareto dominance. **Multi-seed validation would NOT recover C3 as a bundle ingredient** — it would mostly just confirm /118's verdict with quieter per-symbol attribution.

This argues AGAINST commissioning a multi-seed validation of C3 as a separate experiment (it would consume ~5h of CONFIRMATION budget to confirm what we already know mechanistically) and FOR moving the cycle-6 closeout forward with C3 NOT bundled. The single-seed-vs-multi-seed dialectic is the same one `feedback_v3_engineered_features_dont_stack.md` codified: single-seed EXPLORATION sees a regime; multi-seed CONFIRMATION attenuates it; the EDA prediction was a depth-4 single-tree screen that occupies neither point.

---

## Clarification 3 — /119 Axis Recommendation (cycle-6 menu items still LIVE)

**Recommendation: /119 = OPTION (a) — ANOTHER engineered-feature lineage on STRUCTURALLY DIFFERENT primitives, NOT (b) per-symbol XGBoost-with-categorical-handling and NOT (c) out-of-the-box (which is too vague to commit at /118 closeout).**

Justification reasoning. The cycle-6 axis menu state after /118 NEGATIVE:

| Cycle-6 menu axis | State at end of /117 | State at end of /118 |
|---|---|---|
| Symbol selection (universe) | CLOSED at /110, /111 NEGATIVE | unchanged — CLOSED |
| Pooled vs per-symbol architecture | CLOSED at /112 NEGATIVE | unchanged — CLOSED |
| Multi-frequency features at 8h | CLOSED at /113 NEGATIVE | unchanged — CLOSED |
| Risk management (R-layer) | CLOSED at /114 NEGATIVE | unchanged — CLOSED |
| Labeling architecture | CLOSED at /115 NEGATIVE (clean) | unchanged — CLOSED |
| Exit-layer / trade-construction | PROMISING-MECHANICAL at /116 (no_confirm) | unchanged — only ONE such primitive can be active at a time |
| Candle frequency | CLOSED at /117 NEGATIVE catastrophic | unchanged — CLOSED |
| Engineered feature family at 8h | LIVE (per /117 closeout § 8.1) | NARROW vol-regime CLOSED at /118; **other engineered lineages remain LIVE** |
| Per-symbol XGBoost-with-categorical-handling | LIVE (per /117 closeout § 8.1, with the imbalance-magnitude caveat) | unchanged |

Three paths and my read on each:

**(a) NEW engineered-feature lineage on DIFFERENT primitives** — STILL LIVE per the Clarification-1 closure scope. The /117 closeout § 8.1 explicitly noted "the /118 QR may choose a DIFFERENT composed feature (e.g., a volatility-of-volatility composite; a cross-asset BTC-correlation × regime composite; an OBV-based composite) — the recommendation is the AXIS (NEW engineered feature at 8h), not the specific feature." /118 has now narrowed the LIVE space within this axis (value × vol-regime CLOSED; hurst-regime has the /025 precedent; structurally different regime-classifier or value-primitive families are still LIVE). The /025 PROMISING result is the strongest empirical evidence in v3 history for engineered features (`feedback_v3_engineered_features_proven.md`), and the /118 failure does NOT falsify that — it narrows the scope to specific composite families that don't work. The /119 axis on a different engineered-feature lineage has a concrete EDA hypothesis to test (Critic Clarification-1 closure scope leaves multiple LIVE candidates: volume × volume-regime-sign; OBV-based × regime-sign; BTC-cross-correlation × BTC-regime-sign; ret_skew × sign(ret_kurt − mean), etc.).

**(b) Per-symbol XGBoost-with-categorical-handling** — the /117 closeout § 8.1 already adjudicated against this for 8h baseline use, on the imbalance-magnitude argument: XGBoost-with-categorical-handling's claim ground is the high-imbalance use case (BCH p(label=1) ≈ 0.99 at 24h), but at 8h the imbalance is materially less severe (BCH ≈ 0.59–0.64 per the /117 closeout). The configurations (categorical-aware tree splitting; class-weighted loss; focal loss) target the 99%-imbalance case, not the 64%-imbalance case. /117 closed the 24h-imbalance axis (candle frequency CLOSED), so the imbalance-magnitude where (b)'s configurations have leverage is no longer in cycle 6's accessible state space. Running (b) at /119 would be an architecture probe whose claim ground was just removed. The /016 LightGBM → XGBoost head-to-head (cross-entropy + depth-wise defaults) was an EXPLORATION-NEGATIVE; per-symbol + imbalance-aware configurations are formally LIVE but their natural problem domain isn't accessible at /119.

**(c) Out-of-the-box** — too vague to commit at /118 closeout. The cycle-6 axis menu's "out-of-the-box thinking is mandated" clause is a meta-directive, not an axis. At the /118 closeout the QR cannot commit to "out-of-the-box" without a concrete candidate. If the /119 QR finds a genuinely orthogonal axis I have not identified (e.g., a different label estimand the /115 closure did not cover; a feature interaction at a deeper depth than current LightGBM exposes; a different signal class entirely from price-derived), that QR should commit it with the same EDA discipline. But the /118 QR-Round-2 cannot guarantee such a candidate exists.

**Therefore: /119 = (a) NEW engineered feature on a STRUCTURALLY DIFFERENT lineage.** Specifically, the EDA dispatch should evaluate ≥ 4 composite candidates spanning at least 2 of the following orthogonal categories: (i) volume-based primitives (OBV, MFI, CMF-derived), (ii) cross-asset BTC primitives (BTC-correlation regime, BTC-funding alignment), (iii) tail/higher-moment regime classifiers (skew-sign, kurtosis-percentile-band), (iv) microstructure-derived primitives if available in v3 feature inventory. Each candidate must clear the same gate stack /118 used (T2 Linear-Redundancy PF, T3 univariate, T4 per-symbol, T5 multivariate importance, T7/T9 multivariate-lift) AND additionally must pass a NEW pre-Falsifier: **Critic-Clarification-2-aware single-seed-lottery check** — if the EDA's T9 per-symbol asymmetry exceeds 2× the POOLED magnitude (i.e., a single-symbol carrier dominates the POOLED signal), file as Single-Symbol-Carrier-RISK (the /118 mechanism). This is a new EDA gate /118's experience justifies adding to the next iteration's screening protocol.

**Important note on /119 axis discipline**: per Clarification-1 scope, /119 cannot retry within the value × vol-regime-sign family. The /119 EDA should explicitly REJECT any candidate that uses `sign(realized_vol - vol_threshold)` as the regime sign factor. The /025 hurst-regime branch is occupied (cannot be re-tested as a NEW axis without a different primitive on hurst). The OBV-based, volume-regime, cross-asset, and higher-moment-regime branches remain LIVE.

---

## Clarification 4 — /120 CONFIRMATION Bundle Composition (single-knob or empty?)

**Read: /120 CONFIRMATION is VALID as a single-component CONFIRMATION of /116 no_confirm vs /059 canonical, with caveat that /119's outcome may add a second component IF /119 is PROMISING. The /120 is NOT effectively empty if /119 is also NEGATIVE — it still has /116 as a strictly-accretive component decision per `feedback_promising_mechanical_subtype.md`, and that decision IS material (whether to keep the no_confirm primitive in the post-cycle-6 baseline).**

Per `feedback_promising_mechanical_subtype.md` (the iter-v3/013 protocol): PROMISING-MECHANICAL ingredients are "strictly accretive component decisions" — they bundle into CONFIRMATION as YES/NO-keep accretions on top of the prior baseline (/059), NOT as new edge ingredients with additive signal. The /116 no_confirm primitive is the only PROMISING-class result in cycle 6's 8 EXPLORATIONs (/110–/117 = 7 NEGATIVE + 1 PROMISING-MECHANICAL). The /118 NEGATIVE means C3 is NOT bundled. If /119 is also NEGATIVE, /120 bundles ONLY /116 no_confirm. If /119 is PROMISING (engineered-feature or other), /120 bundles BOTH /116 and the /119 result — with the caveat that mechanical and signal-discovery ingredients have different multi-seed-validation criteria (mechanical: trade-roster bit-identity to /059 + per-symbol architecture invariance; signal-discovery: traditional multi-seed Pareto + DSR/PBO/PSR).

The valid-as-single-component case: /120 testing whether /116 no_confirm holds up at full unified 10-seed ensemble (ENSEMBLE_SIZE=5 × outer_seeds=2 = 10 models per cell per the v3 CONFIRMATION envelope, n_trials=35) IS a substantive question. /116's 3-seed EXPLORATION result (IS +0.6246 / OOS +1.1089) included an IS-Sharpe decrement of 0.21 below /060 anchor (the brief Section 2 noted this is the rule's IS cost cutting some near-winners), partially offset by an OOS-Sharpe increment of +0.97 (the slot-freeing cascade channel). At 10-seed multi-seed, the question is whether the slot-freeing cascade channel survives — it's a regime-adaptive rule and the OOS-positive channel may attenuate. /120 measuring this multi-seed is necessary for the post-cycle-6 baseline decision (does the no_confirm primitive merge to BASELINE_V3.md or not).

**The cycle-6 closeout decision at /120 is therefore meaningful regardless of /119 outcome**. The two-cell decision tree:
- If /119 PROMISING + /120 confirms /116 PROMISING-MECHANICAL AT MULTI-SEED + /120 confirms /119 signal: BASELINE_V3.md updated with no_confirm primitive + new engineered feature (or chosen axis).
- If /119 NEGATIVE + /120 confirms /116 PROMISING-MECHANICAL: BASELINE_V3.md potentially updated with no_confirm primitive only (single-component MERGE; cleanest case for an accretive decision).
- If /119 NEGATIVE + /120 does NOT confirm /116 at multi-seed: BASELINE_V3.md unchanged; cycle 6 closes NO-MERGE; /116's apparent OOS lift dissolves at multi-seed (the same dissolution iter-v3/013 → /018 produced for drop-MKR).
- If /119 PROMISING + /120 confirms /119 but does NOT confirm /116: BASELINE_V3.md potentially updated with /119 finding only.

All four endings produce a meaningful cycle-6 closeout. The /119 axis search does NOT need to find ANOTHER LIVE bundle candidate as a hard requirement — but if /119 succeeds, it adds the second cell of the decision tree's left branch.

**Caveat on the /120 single-component case** (no /119 PROMISING + only /116 bundled): per `feedback_promising_mechanical_subtype.md`, PROMISING-MECHANICAL ingredients are "non-compoundable across iterations" — meaning they don't stack with each other (you can't drop the same symbol twice). They CAN stack with PROMISING signal-discovery ingredients. The /120 testing /116 alone is the canonical strictly-accretive validation: does this primitive add value on top of /059 at multi-seed? This is the same protocol shape as the iter-v3/018 bootstrap CONFIRMATION (single-component validation of the iter-v3/013 drop-MKR decision — which FAILED at multi-seed). The /120 may follow the same pattern (single-component CONFIRMATION, possible FAIL outcome) and that is a methodologically clean cycle closeout regardless.

The implications for /119 are: /119 should NOT be designed as a "must-find-another-bundle-candidate" iteration. /119 should be a serious search for a NEW engineered-feature lineage with the discipline I described in Clarification 3. If /119 finds one, /120 gets a second component. If /119 NEGATIVE, /120 is a single-component /116 validation. Both endings are valid cycle-6 closeouts.

---

## Position

STAND BY VERDICT.
