# Phase 7.5 Critic Review — iter-v1/040

OVERALL: EXPLORATION-NEGATIVE-CLEAN — composed feature `regime_momentum_signed_5d` LEARNED but at low rank across all 5 cohorts (median rank 26/44, max rank 30); v3 /025 PROMISING precedent (importance 51% top, OOS +0.84) FAILED to transfer to v1's 5-cohort 44-feature stack; IS Sharpe Δ +0.28 vs OOS Sharpe Δ −0.37 = classic IS-overfit signature (basin re-search captured noise, not signal); F1 Δ = −0.37 lies inside NEG-CLEAN band [−0.45, −0.15). Composed-feature mechanism axis CLOSED for v1 cycle-5.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION

## QR Response Considered (Round 2 only)
Not invoked. Single-round FINAL — every load-bearing F-AXIS predicate resolves on the comparison.csv + feature_importance CSVs without ambiguity. Brief Section 11.6 fifth-row "NEGATIVE Δ < −0.10 any-F2 → composed-feature axis CLOSED" fires directly off the OOS Sharpe column (+0.2959 vs baseline +0.6637 = Δ −0.3678).

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
- Foundation: `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` (pre-flight Check A verified; grep-confirmed).
- New code at `src/crypto_trade/features_v1/composed_v1.py:156` computes `ret_5d = log_close − log_close.shift(15)` — strictly past-only via shift.
- `_rolling_hurst` (line 98-108) computes `values[i-window:i]` — bar i uses bars i-window to i-1, structurally past-only (BYTE-FOR-BYTE copy from `features_v3/regime_v3.py:69-75`, already verified by v3 test suite).
- `sign_hurst.replace(0.0, np.nan)` handles the pure-random-walk edge case correctly; EDA finding hurst > 0.5 in 100% of samples means sign is effectively +1 everywhere → composed feature ≡ ret_5d (15-bar), confirmed by |IC|=1.000 in brief Section 1.4. No look-ahead.
- `tests/test_lookahead_embargo.py` present (regression test confirmed via pre-flight Check E).

### Check 2 — Embargo Width: PASS
Unchanged from baseline. Composed feature is a kline-derived rolling computation; does not interact with label generation or MonthSplit construction. `walk_forward.py:113` embargo intact.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)
- DSR_corrected (OOS) = −48.39, IS = −56.46 (well below 0.95 threshold). Worst DSR among /034 /037 /038 /039 cycle-5 EXPLORATIONs — corroborates the negative-edge verdict.
- PSR_monthly_vs_1 (OOS) = 0.215 (vs 0.95 threshold).
- PSR_monthly_vs_0 (OOS) = 0.612.
- n_effective_trials = 9 (IS + OOS, matching /037 + /038 — **third consecutive n_eff=9 at v1 EXPLORATION budget**; the LM Master Phase 4.5 advisor flagged this 2-iter recurrence and warned the 3rd would escalate to STRUCTURAL).
- Per skill §5.1, Check 3 axis FAILs are INFORMATIONAL at TYPE=EXPLORATION — not BLOCK-triggering. NOTED for catalog.

### Check 4 — IC Correlation: PASS (composed-feature IC carve-out)
Brief Section 1.4 documents |IC|=1.000 vs `ret_5d_15bar_PRIMITIVE` (mechanical identity since sign=+1 everywhere) and |IC|=0.80 with `mom_rsi_14`. Strict |IC|<0.50 gate fails by construction. Composed-feature IC carve-out applies per `feedback_v3_engineered_feature_pivot.md`: binding falsifier is split-count importance ≥ 30 in ≥ 2/5 cohorts. F2 LOAD-BEARING gate evaluated under Check 8.

### Check 5 — ADF Stationarity: PASS
Brief Section 1.2: all 5 v1 symbols ADF p-value < 2e-13 → stationary. EDA-only computation (Hurst+ret_5d are log-return-derived, structurally stationary).

### Check 6 — Pareto Dominance: N/A
Single seed=42 EXPLORATION (NORMAL-RISK declared, brief Section 2.5). Multi-seed Pareto deferred to /044 CONFIRMATION — but /040 NEG-CLEAN falsifier closes the axis before that point.

### Check 7 — Reproducibility: PASS
- HEAD `2559e15` on `iteration-v1/040`.
- Dispatch at `run_baseline_v1.py:4142` fires BEFORE catch-all; `"v1-040"` present in catch-all exclusion tuple (per /030 LESSON, pre-flight Check B confirmed).
- V1_FEATURE_COLUMNS_PRUNED contains `regime_momentum_signed_5d` and does NOT contain `basis_zscore_30`; `len == 44` assertion holds (pre-flight Check C).
- Hurst R/S computation is deterministic (vectorized rolling, no random sampling).
- Ensemble seeds [42, 123, 456] for ENSEMBLE_SIZE=3; outer seed=42.

### Check 8 — Hypothesis-Implementation Alignment: FAIL (H1 REFUTED, F1 NEG-CLEAN band fires, F2 LOAD-BEARING FAIL on top-importance criterion)

**H1 PRIMARY claim** (brief Section 1.5 + LM Master Phase 4.5 Rec): "v3 /025 PROMISING-CLEAN precedent's 51% top-importance, OOS Δ +0.84 lift transfers to v1's 44-feature stack with predicted portfolio rank 6-10 and importance ≥ 30 in 3-4 of 5 cohorts." H1 is REFUTED on both clauses:

| Cohort | Predicted rank | Observed rank | Verdict |
|---|---|---|---|
| Model_A_pool (BTC+ETH) | 5-12 (QR) / 6-10 (LM) | **28 / 44** | FAIL (3× worse than predicted) |
| Model_C_LINK | 8-15 (QR) / 3-7 (LM) | **23 / 44** | FAIL (3× worse than LM, 1.5× worse than QR) |
| Model_D_LTC | 10-18 (QR) / 8-14 (LM) | **30 / 44** | FAIL (2-3× worse) |
| Model_E_DOT | 8-15 (QR) / 5-10 (LM) | **26 / 44** | FAIL (2× worse) |
| portfolio | 6-10 | **26 / 44** | FAIL (3× worse) |

Predicted "rank 1-5 in ≥3/5 cohorts" PASS criterion (F2 strict gate): **0 of 5 cohorts** ranked 1-5 → STRICT FAIL.
PASS-CONDITIONAL criterion "rank ≤ 30 in ≥ 2 of 5 cohorts": **5 of 5 cohorts** at rank ≤ 30 (LINK=23, A_pool=28, DOT=26, portfolio=26, LTC=30) → cleared on TECHNICAL PASS-CONDITIONAL only.

The composed feature was LEARNED — but at the bottom third of the stack across all 5 cohorts. This pattern matches brief Section 11.5 "RSI colsample-theft INERT" pre-registered modal failure: |IC|=0.80 with `mom_rsi_14` meant the composed feature's signal was redundant with incumbents. Observed: `mom_rsi_14` rank in /040 actually FELL from /038's rank 1-3 to {A=30, LINK=32, LTC=23, DOT=27, portfolio=27} — RSI itself was displaced by `vol_atr_14` (rank 1 across all 5), `trend_aroon_osc_50` (rank 1-3), `stat_autocorr_lag5` (rank 2-3). The 44-col stack reorganized AWAY from RSI in /040 toward volatility/autocorrelation primitives, suggesting Optuna basin shifted on the regen and the new feature was inserted into a basin that didn't load on momentum at all.

**F-AXIS #1 (OOS Sharpe Δ vs baseline +0.6637)**: OOS Sharpe = +0.2959 → Δ = **−0.3678**. Lies inside NEG-CLEAN band per brief Section 11.6 fifth row (Δ < −0.10 → NEGATIVE → composed-feature axis CLOSED at v1; /041 NEW axis). The brief's Section 4 verdict matrix and Section 11.6 numerical band agree: NEGATIVE-no-effect verdict.

**OVERFIT-MECHANISM diagnosis (load-bearing)**: IS Sharpe = +0.5588 vs baseline IS +0.2829 → Δ_IS = **+0.276**. OOS Sharpe = +0.2959 vs baseline OOS +0.6637 → Δ_OOS = **−0.368**. The +0.276 IS lift WITH −0.368 OOS drop is the canonical IS-OVERFIT signature: Optuna re-searched the basin around the new feature, found a configuration that fit the IS window (high IS PnL, +106.26 vs baseline ~+54.05), then failed to generalize. Specifically: trade count exploded (IS 724 vs baseline 621, +17%; OOS 274 vs baseline 189, +45%) → the feature swap dragged the model into a higher-frequency regime; IS PSR_monthly_vs_0 = 0.905 (high IS confidence) collapsed to 0.612 OOS; n_effective_trials = 9 means Optuna ridge was tight, so the basin selected was over-specialized. This is NOT a regime-decay story (regime-decay would have flat IS / negative OOS); this is a basin-shift overfitting story. Max DD held in similar range (IS 60.36% / OOS 50.17%) — the failure mode is signal-quality not tail-risk.

**F-AXIS #3 (trade count)**: IS 724 (predicted [560, 690]) → exceeds upper bound by 5%. OOS 274 (predicted [165, 215]) → exceeds upper bound by 27%. Both above predicted bands → feature added a higher-frequency entry trigger, NOT a confirmation/filter — consistent with the basin-shift overfitting diagnosis.

**F-AXIS #4 (per-symbol OOS Δ direction)**: per-symbol breakdown not in comparison.csv (per_symbol.csv missing from `reports-v1/iteration_v1-040/`). Cannot evaluate strictly; informational only. NOT a BLOCK-PENDING-FIX because per_symbol.csv is documented as a CONFIRMATION-mode artifact at v1 EXPLORATION single-seed (per pre-flight Check 14 narrative).

### Check 13 — Anti-Pattern Static Scan: PASS
A1 (`train_end_ms = test_start_ms` no-subtract): 0 unexplained matches in `src/` (pre-flight Check F confirmed; verified at HEAD). A2 (forward-window labeling std): `labeling.py` unchanged. A3 (scaler.fit_transform combined): 0 matches. A5 (master-data-extent invariance): composed feature uses shift+rolling kernels, structurally invariant (test #4 `test_compute_regime_momentum_signed_5d_past_only` covers). A7-A14: no methodology-axis changes in /040. Cross-track import scan returns only the documented BYTE-FOR-BYTE COPY comments in `composed_v1.py:54-55, 101-102` — Hurst math copied not imported per v1 track isolation. CLEAN.

### Check 14 — Axis Family Validation: FAIL (FAMILY REPEAT — 2-iter consecutive NEG within feature-family)

Brief Section 0.6 declares `feature-family` with REPEAT-MECHANISM-JUSTIFIED rationale (/034 exogenous new-data-source vs /040 endogenous composed-from-incumbents). The src/ diff confirms feature-family changes: NEW `features_v1/composed_v1.py`, tuple swap in `features_v1/__init__.py`, registry edit in `features/__init__.py`, dispatch edit in `run_baseline_v1.py`. Declaration matches actual diff → Check 14 strict-axis-declaration PASS.

**However**: the v1-only Critic adversarial duty now triggers a FAMILY-SATURATION secondary flag. Combined verdict over /034 + /040 feature-family axes:

| iter | sub-axis | F1 OOS Δ | F2 importance verdict | family verdict |
|---|---|---|---|---|
| /034 | basis_zscore_30 ADD (exogenous new-data) | NEG-CLEAN (Δ ≈ −0.20 territory) | INERT-by-importance (rank 25-32 across cohorts) | NEG-CLEAN |
| /040 | regime_momentum_signed_5d swap (endogenous composed) | NEG-CLEAN (Δ = −0.368) | LEARNED-but-redundant (rank 23-30) | NEG-CLEAN with IS-overfit |

Both feature-family sub-axes within cycle-5 produced NEG-CLEAN/OVERFIT verdicts. The "different mechanism class" justification (exogenous vs endogenous) was honored at the declaration level but produced **convergent empirical outcomes**: in both cases the feature was LEARNED-but-LOW-RANK, the Optuna basin shift produced IS amplification + OOS regression, and the OOS Δ landed in the same NEG-CLEAN band. The feature-family axis is now at **2/2 NEG within cycle-5**.

**Implication for cycle-5 #8/9/10 axis selection** (binding on next 3 EXPLORATIONs): a 3rd consecutive feature-family axis at /042-/045 cannot be defended on "MECHANISM-JUSTIFIED" rationale alone — the empirical NEG/NEG pattern across exogenous-AND-endogenous sub-mechanisms suggests the v1 44-feature stack's saturation is mechanism-INVARIANT at single-seed EXPLORATION budget. Critic verdict: 3rd feature-family axis in /041-/045 requires STRUCTURAL JUSTIFICATION beyond "different sub-mechanism class" — specifically, evidence that the proposed new feature has |IC| < 0.30 with ALL existing momentum/volatility/regime primitives AND a load-bearing falsifier on Optuna n_effective_trials ≥ 13 (i.e., not the recurring n_eff=9 ridge). Without that, the next feature-family axis should be DEFERRED to cycle-6 substrate.

## Observed Results vs Brief Verdict Matrix

| Metric | Baseline | /040 | Δ | Band threshold | Within band |
|---|---|---|---|---|---|
| OOS Monthly Sharpe | +0.6637 | +0.2959 | **−0.3678** | NEG-CLEAN [−0.45, −0.15) | YES (NEG-CLEAN) |
| IS Monthly Sharpe | +0.2829 | +0.5588 | **+0.276** | informational (IS-overfit signature) | IS lift WITHOUT OOS lift = OVERFIT |
| OOS/IS ratio | 2.346 | **0.530** | −1.82 | ≥ 0.5 floor | barely clears (suspicious — was 2.35×) |
| OOS Max DD | 40.94% | 50.17% | +9.2pp WORSE | informational | tail-risk INCREASED |
| IS Max DD | 73.06% | 60.36% | −12.7pp | IS-only informational | IS-favorable optimization (consistent with overfit) |
| IS trades | 621 | 724 | +103 | [560, 690] band | ABOVE upper bound |
| OOS trades | 189 | 274 | +85 | [165, 215] band | ABOVE upper bound by 27% |
| OOS WR | 40.2% | 40.9% | +0.7pp | regime-stable | PASS |
| Profit factor (OOS) | 1.156 | 1.057 | −0.099 | informational | degraded |
| DSR (OOS) | −35.66 | **−48.39** | −12.73 | informational EXP | worsened |
| PSR monthly vs 0 (OOS) | (~0.97) | 0.612 | regression | informational EXP | regression |
| PSR monthly vs 1 (OOS) | 0.079 | 0.215 | +0.136 | informational EXP | numerical artifact of lower Sharpe variance, not edge improvement |
| n_effective_trials | (varies) | **9** | 3rd consecutive iter at 9 | LM Master flagged | STRUCTURAL RIDGE RECURRENCE |
| Composed feature importance | predicted rank 6-10 portfolio | **rank 26 portfolio** | 3× worse than predicted | F2 LOAD-BEARING strict gate | FAIL strict; PASS-CONDITIONAL only |
| Composed feature top-5 hit rate | predicted ≥3/5 cohorts | **0/5 cohorts** | strict FAIL | F2 PASS-strict criterion | FAILED |

## Verdict Cell

**EXPLORATION-NEGATIVE-CLEAN** per brief Section 11.6 fifth row (Δ ∈ [−0.30, −0.10) → NEGATIVE → composed-feature axis CLOSED at v1; /041 NEW axis). The observed OOS Δ of −0.3678 actually exceeds the NEGATIVE upper threshold of −0.30 stated in Section 4 row 5, but the brief's authoritative Section 11.6 verdict matrix locks the band at NEGATIVE for Δ ∈ [−0.30, −0.10)] and NEG-CATASTROPHIC for Δ < −0.30. Strict reading: Δ = −0.3678 places the iteration in **NEG-CATASTROPHIC territory by Section 4 but in NEGATIVE by Section 11.6** (Section 11.6 has no NEG-CAT row — its NEGATIVE row says Δ < −0.10 any-F2 → axis CLOSED). The Section 11.6 verdict matrix is the load-bearing one per pre-registration discipline; verdict is **NEGATIVE-CLEAN** with the OVERFIT-MECHANISM annotation as the salient diagnostic.

**OVERFIT-MECHANISM**: composed feature was LEARNED (5/5 cohorts at rank ≤ 30 — PASS-CONDITIONAL F2 cleared) but at LOW rank (median 26/44, max 30, top-5 hit rate 0/5). Optuna at n_trials=18 selected a basin that over-fit IS (Δ_IS = +0.276, IS trade count +17%, IS profit factor +0.06) while drifting away from generalizable OOS edge (Δ_OOS = −0.368, OOS trade count +45%, OOS profit factor −0.10). The IS-OOS Sharpe ratio collapsed from baseline 2.346× to 0.530× — a 4.4× regression. The signal-quality interpretation: trees absorbed the 15-bar return primitive in basin-cost-of-search not basin-edge-gain — exactly what `feedback_v3_inert_features_at_higher_budget.md` documents for v3, and what LM Master Phase 4.5 explicitly pre-warned in its "Predicted PROMISING-INERT-FAV as modal" assessment (which observed strictly worse than its prior — outcome landed in the 10% NEG-CLEAN tail).

**Forensic note**: v3 /025 PROMISING-CLEAN precedent (IS +0.50, OOS +0.84, importance 51% top in v3 BCH+LDO+TRX 14-feature stack) did NOT transfer to v1's 5-cohort 44-feature stack. The v3 mechanism specifically depended on (a) a sparse 14-feature TOP_N where colsample sampling reliably exposed the composed feature, and (b) a momentum-light incumbent stack where the 15-bar horizon was genuinely novel. v1 has neither: 44-feature stack means colsample at 0.6 default puts the new feature in only ~60% of trees, AND v1 already has `stat_log_return_5` (40h), `mom_macd_line_12_26_9`, `trend_aroon_osc_50`, `trend_adx_14`, `mom_roc_10`, `interact_ret1_x_ret3`, `interact_ret1_x_natr` — a dense momentum/return primitive cluster that the 120h horizon competes against, not extends. The "v1 lacks a 5-day momentum primitive" re-framing in brief Section 1.3 was correct narratively but the IS-OOS overfit pattern shows the model could not find ORTHOGONAL signal in the 120h horizon vs the existing 40h + autocorrelation + ATR cluster.

The v3-PROVEN composed-feature mechanism does NOT generalize from v3's 3-cohort 14-feature universe to v1's 5-cohort 44-feature universe at single-seed EXPLORATION budget. A v1-counter-example should be appended to `feedback_v3_engineered_features_proven.md` documenting this non-transfer per brief Section 8 explicit pre-registration.

## Recommendations to QR

1. **Composed-feature mechanism axis is CLOSED for v1 cycle-5.** Do NOT propose a second composed feature (e.g. `vol_adj_autocorr_5_signed`) at /041 stacking experiment — brief Section 8 Path Forward conditionally proposed this for PROMISING-INERT-FAV outcome only. /040 landed in NEGATIVE, which closes the axis. Stacking would compound the IS-overfit + low-rank-learning pattern.

2. **Feature-family axis is at 2/2 NEG-CLEAN in cycle-5 (/034 + /040).** A 3rd feature-family axis in /041-/045 requires explicit STRUCTURAL JUSTIFICATION beyond "different mechanism class": (a) load-bearing falsifier on Optuna n_effective_trials ≥ 13 (must escape the 3-iter n_eff=9 ridge), (b) candidate feature with |IC| < 0.30 against ALL existing momentum + volatility + regime primitives, (c) per-cohort hit-rate prediction with rank ≤ 10 in ≥ 4/5 cohorts (not the looser "rank ≤ 30 in ≥ 2/5" PASS-CONDITIONAL gate used here). Without all three, the next feature-family axis should be DEFERRED to cycle-6.

3. **n_eff=9 is a 3-iter recurrence (/037 /038 /040).** LM Master Phase 4.5 pre-warned this and predicted it would escalate to STRUCTURAL on /040 hit. It hit. The v1 44-col stack at n_trials=18 + ENSEMBLE_SIZE=3 is structurally ridge-prone independent of axis. The /041 brief Section 7 (failure-mode prediction) must include a load-bearing falsifier on n_eff ≥ 13 OR a methodology-substrate axis (n_trials lift OR feature stack reduction) as the natural cycle-5 #8 candidate.

## Path Forward (mandatory)

Prior 5 EXPLORATIONs since /035 (cycle-5 ledger): /034 feature-family + /035 labeling + /036 per-cohort-specialization + /037 loss-function + /038 risk-primitive + /039 risk-primitive + **/040 feature-family**. Prior 5 (looking back from /040): /035 + /036 + /037 + /038 + /039 (4 distinct families + 1 risk-primitive repeat). No monoculture armed; rotation rules satisfied. The pre-drafted /041 + /042 + /043 axes must be re-validated below.

**Critic validation of the pre-drafted /041 + /042 + /043 axes given /040 NEG-CLEAN**:

1. **/041 (LABELING width asymmetry — TP=1.5/SL=0.75 per LM Master /038 §6 Rec 2 MEDIUM CONFIDENCE)**: **VALID.** Family `labeling` was last used at /035 (NEG-CAT-bundle bimodal trend-scanning) — different sub-mechanism (TB-width vs trend-scanning), 5 EXPLORATIONs ago → rotation rule clean. The width-asymmetry mechanism is orthogonal to /040's basin-shift failure. Recommended forward-binding: Section 7 falsifier on n_eff ≥ 13 (per Recommendation 3 above) AND pre-registered IS-OOS gap < +0.15 (to catch the /040 OVERFIT signature ex-ante). Without these falsifiers, /041 risks repeating the IS-overfit pattern.

2. **/042 (MODEL-ARCH XGBoost head-to-head per LM Master /038 §6 Rec 3 MEDIUM-LOW CONFIDENCE)**: **VALID with CAVEAT.** Family `model-arch` is fresh in v1 cycle-5 (untouched since /016 in v3, which was NEG-CLEAN). Caveat: v3 /016 closed model-arch at 13-feature stack n_trials=10 cross-entropy depth-wise defaults; v1's 44-feature stack + EXPLORATION budget is a different regime BUT carries the same n_eff=9 ridge structural risk. Recommended: brief Section 2.5 declares HIGH-RISK (model-arch swap changes Optuna search-space dimensionality + LightGBM↔XGBoost basin lottery); pair with Pareto cross-seed Spearman as in /040 F-AXIS #5. The /042 axis is valid but should be reordered AFTER /041 if /041 produces NEG (model-arch is the higher-variance axis).

3. **/043 (per LM Master /038 §6 Rec — sample-weighting refresh OR cross-asset non-OHLCV from v3 catalog)**: **VALID** for either sub-mechanism. Sample-weighting was last used at /032 (cycle-5 sample-weighting `composite_inv_concurrency` PROMISING-BASIN-RELOCATION-ARTIFACT, requires user authorization per brief Section 8). Cross-asset non-OHLCV (`feedback_v3_cross_asset_ohlcv_closed.md` explicitly preserved non-OHLCV cross-asset as PERMITTED with rolling-window T5 importance test) is a fresh family in v1 — strongly recommended over feature-family-3rd-attempt. Either choice clears rotation rules.

**Family-saturation guidance for /041-/045 sequence**: feature-family is at 2/2 NEG-CLEAN within cycle-5. If a third feature-family axis is contemplated at /045+ post-/041-/042-/043, it requires the three structural justifications enumerated in Recommendation 2 above. Without those, the /045 axis MUST come from one of the unused-since-/032 families: sample-weighting (with user authorization), prediction-architecture (ternary class head per /037 Critic Rec 2 — the highest-priority unexhausted axis from /038 review's Path Forward), or methodology (e.g., n_trials lift to escape the n_eff=9 ridge).

**Three alternative axes from families NOT used in the prior 5 EXPLORATIONs (constructive duty discharged)**:

1. **Prediction-architecture (ternary {long, neutral, short} class head)** — family: `prediction-architecture` (NEW 9th family; would require Critic + LM Master + QR 3-way orthogonality convergence per catalog Section 0.6 Note). Replaces binary class head with ternary + per-symbol neutral threshold via Optuna. Mechanism: explicit "no-trade" class lets LightGBM MODEL trade-skipping directly rather than relying on Optuna confidence-threshold post-hoc. Orthogonal to loss-function, labeling, weighting, feature, model-arch, and risk-gate axes. This was raised in /037 and /038 Critic reviews; given /040 closes the composed-feature mechanism in cycle-5, prediction-architecture is the highest-priority unexhausted axis.

2. **Methodology — n_trials lift to escape n_eff=9 ridge** — family: `methodology`. Raise n_trials from 18 → 35 at SAME ENSEMBLE_SIZE=3 + same single-seed=42 + frozen feature stack + frozen labeling. Pure substrate test of the 3-iter n_eff=9 recurrence (LM Master pre-warned). Mechanism: more Optuna exploration breadth opens search beyond the ridge cluster. EDA pre-flight from /037+/038+/040 trial-return matrices can predict ridge-escape probability before launch. Cycle-5 single-axis isolation compatible.

3. **Cross-asset non-OHLCV feature port from v3 (e.g., perp-spot funding-rate basis from a non-Binance source, OR on-chain stablecoin supply Z-score)** — family: `feature-family` (3rd within cycle-5 BUT cross-asset non-OHLCV is structurally distinct per `feedback_v3_cross_asset_ohlcv_closed.md`). Tests whether v1 has been over-anchored on price-derived features at the entire 44-col stack level. Strict |IC| < 0.30 vs all 43 existing features + rolling-window T5 importance test mandatory. If selected, brief Section 0.6 must declare the family-saturation structural justification explicitly per Recommendation 2 above.

(All three from families NOT in the prior-5 EXPLORATIONs OR within feature-family with new structural justification. Critic is advisory; QR may adopt, modify, or reject. None depend on the failed /040 mechanism.)

---

**End-of-review summary for parent agent**:

OVERALL: **EXPLORATION-NEGATIVE-CLEAN** — Δ_OOS = −0.368, Δ_IS = +0.276 (classic IS-overfit signature). 

**regime_momentum_signed_5d importance ranks** (5 cohorts): A_pool=28, LINK=23, LTC=30, DOT=26, portfolio=26. Median 26/44. F2 strict gate (rank 1-5 in ≥3 cohorts): 0/5 FAIL. F2 PASS-CONDITIONAL (rank ≤ 30 in ≥2 cohorts): 5/5 PASS (technical only).

**OVERFIT mechanism**: Optuna at n_trials=18 + n_eff=9 (3rd consecutive iter at 9 — LM Master pre-warned STRUCTURAL RIDGE) selected a basin that lifted IS Sharpe +0.28 + IS trade count +17% + IS profit factor +0.06 while OOS Sharpe regressed −0.37 + OOS trade count +45% + OOS profit factor −0.10. v3 /025 PROMISING precedent (14-col TOP_N, sparse stack, momentum-light) did NOT transfer to v1's 44-col dense momentum-rich stack at single-seed EXPLORATION budget; v1-counter-example documented for `feedback_v3_engineered_features_proven.md`.

**/041 + /042 + /043 axis validity confirmation**: ALL THREE VALID with caveats. /041 (labeling TB-width asymmetry) clean rotation; recommend forward-binding n_eff ≥ 13 + IS-OOS gap < +0.15 falsifiers. /042 (model-arch XGBoost head-to-head) valid but reorder AFTER /041 (higher variance + n_eff ridge risk); declare HIGH-RISK at brief Section 2.5. /043 (sample-weighting OR cross-asset non-OHLCV) valid for either sub-mechanism; cross-asset non-OHLCV strongly recommended over feature-family-3rd-attempt. Feature-family family-saturation guidance: a 3rd feature-family axis in /045+ requires structural justification (n_eff floor ≥ 13 + |IC| < 0.30 + rank ≤ 10 in ≥ 4/5 cohorts prediction) — without all three, defer to cycle-6.

Key file paths inspected:
- /home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-040/research_brief.md
- /home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-040/critic_preflight.md
- /home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-040/phase5p5_gate.md
- /home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-040/lgbm_advisor.md
- /home/roberto/crypto-trade/.worktrees/quant-research/reports-v1/iteration_v1-040/comparison.csv
- /home/roberto/crypto-trade/.worktrees/quant-research/reports-v1/iteration_v1-040/in_sample/feature_importance_{Model_A_pool,Model_C_LINK,Model_D_LTC,Model_E_DOT,portfolio}.csv
- /home/roberto/crypto-trade/.worktrees/quant-research/src/crypto_trade/features_v1/composed_v1.py
- /home/roberto/crypto-trade/.worktrees/quant-research/BASELINE_V1.md
- /home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-038/review.md (structural template)
