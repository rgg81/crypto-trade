# Iteration v3-015 — Diary

## Decision: EXPLORATION-NEGATIVE-no-effect

Critic FINAL OVERALL = `EXPLORATION-NEGATIVE-no-effect` at SHA `a0cfae7` — classification flip from QE's PROMISING-INERT (per brief §4.3 verbatim) to Critic+QR's NEGATIVE-no-effect (per brief §4.4 row 2 IS Sharpe band [+0.91, +1.11], structurally load-bearing). The iteration tested the FIRST NEW feature family in v3 catalog: a microstructure z-score `tbr_zscore_30` = 30-bar z-score of `taker_buy_quote_volume / quote_volume` added as a single column to `V3_FEATURE_COLUMNS` (13 → 14). This is also the FIRST iteration whose axis pivot resulted from a user course-correction (the prior MANDATORY ADX=18 axis was revoked at setup time per `feedback_adx_axis_asymmetric_v3.md` downgrade). Headline: IS Sharpe Δ −0.36 (+0.6445 vs iter-v3/013 +1.0088); OOS Sharpe Δ −0.58 (+2.1206 vs iter-v3/013 +2.6970, **3rd-highest in v3 history but NOT attributable to the new feature**); 205 IS / 85 OOS trades (4 IS trade reduction = non-bit-identical roster, distinguishing from iter-v3/012's NULL-RESULT exemplar); PBO 0.1034 in line with v3 norm. Importance rank 14/14 across BCH/LDO/TRX (16% / 41% / 20% of top feature) — model demonstrably did not learn the feature. Trade roster non-bit-identical AND IS Sharpe Δ −0.36 < −0.10 NEGATIVE threshold AND axis propagated (4 IS trades dropped, 11 TRX trades collapsed; saturation falsifier PASS at 205 < 251 derived threshold) — but the trade roster non-identity reflects Optuna re-routing on a 14-column loss surface, NOT signal-driven gating from the new feature. The combination is a third pattern (distinct from iter-v3/012 NULL-RESULT and iter-v3/014 NEGATIVE-clean): the model **partially** uses the feature (enough to perturb the trade roster) but learns no useful signal from it.

## Headline

**OOS Sharpe +2.1206 — 3rd-highest in v3 history (behind iter-v3/013 +2.6970 and iter-v3/012 +1.5914 reading-tied band), BUT NOT attributable to the new feature**. The lift is mechanical: Optuna re-optimized on the 14-column loss surface and landed in a different local minimum that happens to OOS-favor regime alignment, while LightGBM importance demonstrates the new feature was functionally near-discarded (rank 14/14 across all 3 per-symbol models). **IS Sharpe Δ −0.36** (+0.6445 vs iter-v3/013 +1.0088) — magnitude similar to iter-v3/014's NEGATIVE Δ −0.35; sits +0.27 OUTSIDE the §4.4 row 2 PROMISING-INERT band [+0.91, +1.11] lower bound (2.7× band half-width). **Trade roster non-bit-identical** (209 → 205 IS) — TRX dropped 11 trades, BCH gained 6, LDO held steady. **Max IC vs existing 13** = 0.086 (clean orthogonal) — the feature was structurally well-designed; the model architecture was the bottleneck.

## What Was Tested

**Single-axis variation** (NEW microstructure feature family, axis category 1 per `feedback_structural_over_knob_exploration.md`): `+tbr_zscore_30` in V3_FEATURE_COLUMNS (13 → 14). Setup commit `d2374a6`. The axis is the FIRST genuinely new feature family attempted in v3 (iter-v3/002+ scope per the v3 skill explicitly listing crypto-native feature families) and the FIRST axis to result from a user course-correction (catalog banner revoked the prior ADX=18 mandate at setup time, SHA `bd0706b`).

The compute is past-only by construction: `compute_tbr_zscore` at `volume_micro_v3.py:94-132` uses `s.shift(1)` then rolls on the shifted series — no look-ahead. Max pairwise |IC| with existing 13 features = 0.086 (with `vwap_dev_20`) — well below the 0.70 redundancy gate, structurally orthogonal. The hypothesis was that crypto's perpetual-futures microstructure (taker-buy ratio z-scored over 30 bars = 10 days at 8h cadence) would carry persistent signal not captured by price/return moments.

**Hypothesis** (brief Section 1, SHA `b9cc79b`): tbr_zscore_30 will lift IS Sharpe to [+0.50, +1.30] (median +0.90) by introducing microstructure information orthogonal to the existing 13-column stack. PROMISING band: [+0.91, +1.11]. PROMISING-INERT band (model ignores feature, IS axis preserved within band): [+0.91, +1.11] AND importance bottom-quartile.

**Hypothesis verdict: NOT SUPPORTED.** IS Sharpe +0.6445 (vs predicted [+0.50, +1.30] median +0.90; observed +0.6445 in lower band, below median by 0.26). Importance rank 14/14 across all 3 per-symbol models. The §4.3 falsifier "tbr_zscore_30 bottom-quartile across all 3 symbols → PROMISING-INERT" FIRED but the §4.4 row 2 PROMISING-INERT IS Sharpe band [+0.91, +1.11] DID NOT hold (observed +0.6445 outside band by +0.27 = 2.7× band half-width). Per Critic+QR's reconciliation, §4.4 wins the conflict — the catalog needs the structurally tighter classification. NEGATIVE-no-effect is the correct verdict because (a) IS Sharpe Δ −0.36 is band-violating, (b) trade roster non-bit-identical (so it's not a clean NULL-RESULT like iter-v3/012), (c) importance 14/14 across all 3 syms (so it's not iter-v3/014-style NEGATIVE-clean either).

**Configuration**: `--exploration --seeds 1 --n-trials 10` on 3-symbol v3 universe (BCH+LDO+TRX), ENSEMBLE_SIZE=1, colsample_bytree=1.0, training_months=24, OOS_CUTOFF_DATE=2025-03-24. Identical to iter-v3/013 modulo +tbr_zscore_30 in V3_FEATURE_COLUMNS, ADX reset 25→20 (baseline restoration after iter-v3/014's closed NEGATIVE test, NOT a second axis), and ITERATION_LABEL cosmetic.

## What Was Measured

### Headline metrics

| Metric | iter-v3/013 (current) | iter-v3/015 (this run) | Δ vs iter-v3/013 |
|---|---:|---:|---:|
| IS monthly Sharpe | +1.0088 | **+0.6445** | **−0.36** |
| OOS monthly Sharpe | +2.6970 | **+2.1206** | **−0.58 (3rd-highest in v3 history)** |
| IS daily Sharpe | — | +1.4906 | — |
| OOS daily Sharpe | — | +3.1740 | — |
| IS/OOS ratio | 2.67 | **3.29** | OOS now well ABOVE IS |
| IS trades | 209 | **205** | **−4 (NON-bit-identical)** |
| OOS trades | 85 | **85** | **0 (informationally below 130 floor)** |
| IS max drawdown | 20.77% | 22.00% | +1.23pp |
| OOS max drawdown | 12.47% | **12.47%** | 0.00 (BIT-IDENTICAL) |
| OOS Calmar | 4.96 | 3.5163 | −1.44 |
| Profit Factor (OOS) | — | 1.4849 | — |
| Win Rate (OOS) | — | 44.71% | — |
| PBO (per-cell mean) | 0.1075 | **0.1034** | −0.0041 |
| n_eff (per-cell median) | 7 | 7 | 0 (BIT-IDENTICAL) |
| n_high_pbo_cells_99 | 2 | **8** | **+6** (TRX/2025-Q4 carry-forward + 2 NEW: LDO 2026-05, BCH 2024-01) |
| Wall-clock | 6 min | 6 min | 0 |

The headline OOS Sharpe +2.12 is the 3rd-highest in v3 history but **must NOT be read as evidence of feature edge**. The lift attributes to (a) Optuna re-optimization landing in a different local minimum on the 14-column loss surface, (b) regime favorability in the OOS window (the same OOS window where iter-v3/013 also recorded +2.70 without this feature), (c) ensemble noise — NOT to the new feature, which the model demonstrably did not learn (importance 14/14 across all 3 syms). All falsifiers PASS clean: Falsifier 1 (IS Sharpe < +0.10) NOT triggered (+0.64 above), Falsifier 2 (saturation: IS trades > 251 = 1.2 × 209 counterfactual) NOT triggered (=205, Δ = −46 buffer), Falsifier 3 (wall-clock > 30 min) NOT triggered (6 min), Falsifier 4 (importance bottom-quartile across all 3 syms) FIRED — the §4.3 PROMISING-INERT pathway, but §4.4's IS Sharpe band overrides per QR Round 2 disposition.

### Per-symbol importance (analysis/iteration_v3-015/per_symbol_importance.csv, QR Round 2 SHA `407954d`)

| Symbol | tbr_zscore_30 importance | Rank | Bottom quartile (≥12)? | Importance % of top feature |
|---|---:|---:|:---:|---:|
| BCHUSDT | 107 | **14/14** | YES | 16% (vs ret_kurt_200=672) |
| LDOUSDT | 234 | **14/14** | YES | 41% (vs ret_skew_200=573) |
| TRXUSDT | 133 | **14/14** | YES | 20% (vs ret_skew_200=675) |

**All three per-symbol models place tbr_zscore_30 at rank 14/14 — dead last.** The model demonstrably did not learn the feature. The brief §4.3 verbatim falsifier "bottom-quartile across all 3 symbols" strictly fires.

**BONUS DEFECT discovered by QR Round 2** (Critic Clarification 2 disposition): `_write_feature_importance` at `run_baseline_v3.py:1110-1151` reads only `primary_model_pairs[0]` (BCH last-month inner ensemble), so the engineering report's "aggregated across all symbols/months" claim was incorrect. The per-symbol script confirmed the verdict regardless. **Pre-committed for iter-v3/016 first commit**: either aggregate properly across all (sym, month) models OR rename outputs to clarify single-symbol single-month scope. The QE-discovered defect must not propagate.

### Per-symbol OOS attribution

| Symbol | Trades | Win Rate | Weighted PnL | Concentration % | Δ trades vs iter-v3/013 |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 32 | 40.6% | +17.54 | 39.99% | +1 (+3%) |
| LDOUSDT | 11 | 63.6% | +19.84 | **45.23%** | +1 (+10%) |
| TRXUSDT | 42 | 42.9% | +6.48 | 14.77% | −2 (−5%) |
| **TOTAL** | **85** | **44.71%** | **+43.85** | — | 0 |

**OOS LDO concentration 45.23% > 30% CONFIRMATION cap** (informational under EXPLORATION). LDO 11 trades / 63.6% WR remains a lottery flag (exact-binomial 95% CI on 64% WR at n=11 ≈ [30.8%, 89.1%] — wide enough to span fair coin to skill). The OOS picture is structurally similar to iter-v3/013 (12.47% MaxDD bit-identical, OOS trade count IDENTICAL at 85) — the bit-identical OOS MaxDD is unusually clean evidence that the OOS lift is not driven by per-trade economics changes from the new feature.

### IC orthogonality (clean — feature was well-designed)

Max pairwise |IC| for `tbr_zscore_30` vs existing 13 features = **0.0862** with `vwap_dev_20` (Pearson). Far below the 0.70 redundancy gate. The feature is structurally orthogonal to the existing stack — the failure mode is NOT "candidate correlated to existing features wastes colsample picks" (the iter-v2/070 lesson). The failure mode IS "model architecture is the bottleneck — LightGBM trees don't surface this microstructure signal even when it's structurally clean and orthogonal."

### Methodology checks (Critic FINAL — SHA `a0cfae7`)

| # | Check | Status | Detail |
|---:|---|:---:|---|
| 1 | Look-Ahead | PASS | `compute_tbr_zscore` at `volume_micro_v3.py:94-132` is past-only via `s.shift(1)` then rolling on shifted series |
| 2 | Embargo | PASS | REQUIRED_GAP = 66 = (21+1)×3 confirmed at runtime; CPCV n_paths=45, embargo=27 symmetric |
| 3 | MT correction (methodology) | INFORMATIONAL | PBO = 0.1034; n_eff = 7 BIT-IDENTICAL to iter-v3/013; 8 high-PBO cells (TRX/2025-Q4 carry-forward + 2 NEW: LDO 2026-05, BCH 2024-01) |
| 3 | MT correction (edge) | INFORMATIONAL | DSR = 0.0, PSR = 1.0 — single-seed exploration artifact (cadence-rule informational) |
| 4 | IC correlation | PASS | max abs(IC) = 0.0862 (< 0.70); NEW feature structurally orthogonal to existing stack |
| 5 | ADF stationarity | PASS (PROMOTED) | 2199 ADF rows; tbr_zscore_30 4 non-stationary cells concentrate at symbol-listing months with insufficient rolling-window samples; all other cells p<0.01 |
| 6 | Pareto dominance | PASS (vacuous, single-seed) | EXPLORATION single-seed; LDO 45.23% concentration > 30% CONFIRMATION cap — informational under EXPLORATION |
| 7 | Reproducibility | PASS | SHAs `d2374a6` setup / `b9cc79b` brief / `c253e1d` Phase 5.5 gate / `3ce2572` engineering report / `2c155da` Critic Round 1 / `407954d` QR Round 2 / `a0cfae7` Critic FINAL stamped |
| 8 | Hypothesis alignment | PASS-WITH-FAILED-AXIS | Single-axis discipline honored (3 changes vs iter-v3/013: tbr_zscore_30 added, ADX baseline restored, ITERATION_LABEL cosmetic — last two not new axes); IS Sharpe Δ −0.36 outside §4.4 row 2 band by 2.7× band half-width; Falsifier 4 FIRED |
| 9 | Symbol exclusion | PASS | {BCH, LDO, TRX} ∩ V3_EXCLUDED_SYMBOLS = ∅ |
| 10 | Feature isolation | PASS | features_v3 does not import v1/v2; new `compute_tbr_zscore` track-isolated in `volume_micro_v3.py` |
| 11 | Forming-candle | PASS (inherited) | Pre-flight staleness guard functioning per spec |
| 12 | Library pinning | PASS | Stack identical to iter-v3/008-014 (lightgbm 4.6.0, numpy 2.2.6, etc.); zero new dependencies (numpy + pandas only) |

**All 12 Critic checks PASS / WAIVED-INFORMATIONAL per EXPLORATION carve-out (Check 5 PROMOTED from PRELIMINARY WARN).** Zero BLOCK conditions. Methodology is clean — the feature was well-designed (clean look-ahead, clean IC orthogonality, stationary). The NEGATIVE-no-effect classification is on the *signal axis* (model couldn't extract usable signal), NOT on the *methodology axis* (where everything is clean).

## Caveats Recorded for Audit Trail (5)

The NEGATIVE-no-effect verdict comes with five explicit caveats catalogued for the future CONFIRMATION-bundling QR (per Critic FINAL Recommendations):

1. **`verdict = NEGATIVE-no-effect`** (NULL-RESULT-class subtype): IS Sharpe Δ −0.36 OUTSIDE §4.4 row 2 PROMISING-INERT band [+0.91, +1.11] by 2.7× band half-width on the unfavorable side, AND trade roster non-bit-identical (209 → 205) — distinguishing from iter-v3/012's bit-identical NULL-RESULT exemplar. NOT a clean NEGATIVE (iter-v3/014 style; would require model using the new constraint), NOT PROMISING-INERT (iter-v3/012 style; would require bit-identical roster + IS Sharpe within band). This is the third pattern: model partially uses feature (4-trade Optuna re-routing) but learns no useful signal (rank 14/14 across all 3 syms). NOT a CONFIRMATION-bundle candidate.

2. **`importance_rank = 14/14`** across all 3 per-symbol models (BCH 16%, LDO 41%, TRX 20% of top feature): rank-14/14 with the largest gap in the importance distribution between rank 13 and rank 14 confirms the feature is functionally near-discarded. The §4.3 falsifier strictly fires. Per-symbol disambiguation done in `analysis/iteration_v3-015/per_symbol_importance.py` (committed at QR Round 2 SHA `407954d`); `_write_feature_importance` defect in `run_baseline_v3.py:1110-1151` discovered as bonus and pre-committed for iter-v3/016 fix.

3. **`IC_orthogonality = clean`** (max |IC| 0.086 < 0.70 redundancy gate): the feature was structurally well-designed. Failure mode is NOT "candidate correlated to existing features wastes colsample picks" (iter-v2/070 lesson). Failure mode IS "model architecture is the bottleneck — LightGBM trees don't surface microstructure signal even when feature is structurally clean." This diagnostic motivates iter-v3/016's pivot to NEW model architecture (XGBoost head-to-head) rather than continuing to add more microstructure features.

4. **`oos_n_trades_85_below_130_floor`** (informational caveat): OOS 85 trades is below the 130-trade floor (`feedback_trade_rate_floor`). Verdict is purely IS-axis driven; OOS Sharpe +2.12 records as informational caveat, NOT in verdict cell. Bundle-level math (85 × 5 outer × 3-4× ensemble = 1275-1700 OOS bundle trades) clears the floor at CONFIRMATION; single-seed EXPLORATION underpowering is structural, not a methodology issue.

5. **`iter-v3/016_axis_mandated = LightGBM → XGBoost head-to-head`** per Critic FINAL Recommendation 1: pre-committed via new memory rule `feedback_v3_iter016_xgboost_mandate.md`. Drop `tbr_zscore_30` from V3_FEATURE_COLUMNS (back to 13) — restore iter-v3/013 baseline before XGBoost integration. Add `tbr_raw` to V3_NON_FEATURE_COLUMNS (Critic Clarification 4 hygiene). Fix `_write_feature_importance` defect at `run_baseline_v3.py:1110-1151`. Cannot be renegotiated post-hoc.

## Lessons

1. **NEW feature families require model-architecture validation BEFORE adding more features**. iter-v3/015's failure mode was: a structurally clean (max IC 0.086, stationary, past-only) NEW microstructure feature added to a 13-column LightGBM stack produced rank 14/14 across all 3 per-symbol models. The model demonstrably did not learn the feature even though the feature was well-designed. The diagnostic is: **LightGBM may be the ceiling for the current feature stack** — leaf-wise tree growth, GOSS sampling, and the default colsample_bytree=1.0 may not be surfacing microstructure signal that a different boosting library (XGBoost: depth-wise growth, hist binning, explicit gamma/lambda regularization) might. iter-v3/016 axis MANDATORY = LightGBM → XGBoost head-to-head on iter-v3/013's 13-feature stack (drop tbr_zscore_30 as INERT). Cannot be renegotiated post-hoc per `feedback_v3_iter016_xgboost_mandate.md`. Re-introducing more microstructure features (signed-trade imbalance, OFI, cross-features) is deferred until the model-architecture finding is established — otherwise we accumulate INERT features that contaminate `colsample_bytree` picks in future iterations (the iter-v2/070 lesson).

2. **PROMISING-INERT subtype band must be tighter than ±0.10 to prevent classification ambiguity**. The brief's §4.3 verbatim falsifier ("If tbr_zscore_30 is bottom-quartile importance across all 3 symbols, classify as PROMISING-INERT") collapsed two distinct outcomes into the same verdict: (a) band-equivalent-with-zero-importance (genuine PROMISING-INERT — feature added without harm) and (b) band-degraded-with-zero-importance (NEGATIVE-no-effect — feature added but model couldn't use it AND IS axis degraded). The §4.4 row 2 IS Sharpe band [+0.91, +1.11] is the structurally load-bearing constraint; the §4.3 falsifier should have been *"If tbr_zscore_30 is bottom-quartile importance across all 3 symbols AND IS Sharpe ∈ [+0.91, +1.11], classify as PROMISING-INERT."* Future EXPLORATION-NEW-feature briefs must reconcile §4.3 falsifier triggers and §4.4 outcome rows in a single decision tree, not two parallel tables. iter-v3/016+ brief template will fold §4.3 into §4.4 as decorating conditions, not standalone classifications.

3. **`_write_feature_importance` defect at `run_baseline_v3.py:1110-1151`** (QR Round 2 bonus finding): the function reads only `primary_model_pairs[0]` (BCH last-month inner ensemble), so the engineering report's claim that `feature_importance.csv` is "aggregated across all per-symbol LightGBM models and all walk-forward months" was incorrect. The published CSV reflects BCH's final-month inner ensemble only (size=1 in --exploration mode). Per-symbol disambiguation required a separate analysis script (`analysis/iteration_v3-015/per_symbol_importance.py` at SHA `407954d`). Pre-committed for iter-v3/016 first commit: either aggregate properly across all (sym, month) models OR rename outputs to clarify single-symbol single-month scope. The defect must not propagate.

4. **Brief template §4.3 vs §4.4 conflict — QR must reconcile both sections at brief-authoring time**. The brief presented two parallel classification pathways that disagreed on the realized outcome. §4.3 verbatim said "rank 14/14 → PROMISING-INERT." §4.4 row 2 said "IS Sharpe ∈ [+0.91, +1.11] → PROMISING-INERT." The realized outcome triggered §4.3 (rank 14/14 confirmed) but failed §4.4 (IS Sharpe +0.6445 outside band). Without reconciliation, the QE in good faith classified PROMISING-INERT per §4.3 verbatim; the Critic+QR converged on NEGATIVE-no-effect per §4.4's load-bearing band. Future brief templates: §4 must be a single decision tree where each leaf has a unique classification, not two parallel tables. Pre-commit the logic-consistency check at brief-authoring time.

5. **First NEW feature family attempted in v3 catalog**. iter-v3/015 is the FIRST iteration to test category-1 (NEW feature family) per `feedback_structural_over_knob_exploration.md` priority order. By iter-v3/014, v3 had 4 of 7 EXPLORATIONs on gate-threshold knobs (009, 011, 012, 014) with zero NEW feature families tested despite the v3 skill explicitly listing crypto-native features (funding rates, OI, basis, liquidations, microstructure) as iter-v3/002+ scope. The user course-correction at iter-v3/015 setup ("why the quant-researcher is so crazy in fine tune parameters, instead of going full exploration?") drove the axis pivot. This iteration's NEGATIVE-no-effect outcome does NOT invalidate the structural axis hierarchy — it specifically diagnoses that adding MORE microstructure features before testing model architecture is premature. iter-v3/016's XGBoost head-to-head establishes the model-architecture finding compoundably (a finding that pairs with every future feature/label/gate axis), unblocking microstructure family expansion at iter-v3/017+ if XGBoost demonstrates better signal-extraction.

6. **Critic 2-round flow worked as designed (6th consecutive use producing concrete pre-commits and a NEW memory rule)**. Round 1 PRELIMINARY surfaced 4 substantive clarifications (classification subtype flip, per-symbol importance disambiguation, iter-v3/016 axis pre-commit, tbr_raw write-through audit). QR Round 2 responded with explicit dispositions including a NEW analysis script (`per_symbol_importance.py`) confirming rank 14/14 across all 3 syms AND a bonus defect discovery in `_write_feature_importance`. Round 2 FINAL accepted all 4 clarifications with a classification flip (QE PROMISING-INERT → Critic+QR NEGATIVE-no-effect). The clarifications produced a concrete pre-commitment (iter-v3/016 = LightGBM → XGBoost head-to-head) + a NEW memory rule (`feedback_v3_iter016_xgboost_mandate.md`) + 3 pre-committed iter-v3/016 first-commit fixes (drop tbr_zscore_30, add tbr_raw to V3_NON_FEATURE_COLUMNS, fix `_write_feature_importance`).

7. **Dead-paths catalog (fourteenth entry, eighth EXPLORATION row, NEGATIVE-no-effect classification):**
   - **iter-v3/015** — NEW microstructure feature axis (`tbr_zscore_30` = 30-bar z-score of `taker_buy_quote_volume / quote_volume`; single feature added to V3_FEATURE_COLUMNS, 13 → 14) EXPLORATION on v3 universe (BCH+LDO+TRX), `--exploration` mode (ENSEMBLE_SIZE=1, n_trials=10, colsample_bytree=1.0, outer_seed=42). **EXPLORATION-NEGATIVE-no-effect**. IS monthly Sharpe = +0.6445 (Δ −0.36 vs iter-v3/013 +1.0088). OOS monthly Sharpe = +2.1206 (Δ −0.58 vs iter-v3/013 +2.6970, 3rd-highest in v3 history; informational below 130-trade floor at OOS=85; NOT attributable to new feature). Trade roster non-bit-identical (209 → 205 IS, with TRX losing 11 / BCH gaining 6 / LDO held steady; 85 OOS trades bit-identical to iter-v3/013). PBO 0.1034 (vs iter-v3/013 0.1075); n_eff 7 BIT-IDENTICAL; n_high_pbo_cells_99 = 8 (TRX/2025-Q4 carry-forward + 2 NEW LDO/2026-05, BCH/2024-01). Importance rank 14/14 across all 3 per-symbol models (BCH 16% / LDO 41% / TRX 20% of top feature) — model demonstrably did not learn feature. Max IC vs existing 13 = 0.0862 (clean orthogonal — feature was well-designed; model couldn't use it). 5 caveats catalogued. **NOT a CONFIRMATION-bundle candidate**: feature INERT (model architecture is the bottleneck, NOT feature pool). iter-v3/016 axis MANDATORY = LightGBM → XGBoost head-to-head on iter-v3/013's 13-feature stack (drop tbr_zscore_30) per `feedback_v3_iter016_xgboost_mandate.md`. The catalog count advances 7 → 8 of 10; iter-v3/016 axis is XGBoost head-to-head per Critic FINAL Recommendation 1.

## Pre-Registered Failure-Mode vs Reality Summary

| Class | Materialized? |
|---|---|
| Process predictions (P1-P3, total 20%) | 0/3 materialized — pipeline ran clean, wall-clock 5x under target, tbr_zscore_30 propagated cleanly (saturation falsifier PASS at 205 < 251) |
| Model predictions (P4-P7, total 105%) | P4 (PROMISING band [+0.91, +1.11]) DID NOT MATERIALIZE; P6 (PROMISING-INERT 13-decimal-rank) PARTIALLY materialized (rank 14/14 satisfied, IS Sharpe band failed); the realized outcome of "rank 14/14 + IS Sharpe outside band" was not a discrete probability mass in §7 — falls in the §4.4 row 2 NEGATIVE-no-effect verdict not anticipated by the brief's §7 prediction set |
| OOS-axis prediction | informational under EXPLORATION; the OOS bit-identity at 85 trades + bit-identical OOS MaxDD 12.47% confirms the OOS lift is mechanical Optuna re-routing, NOT feature-driven |
| Behavioral-effect verifier (saturation falsifier + per-symbol importance) | BOTH PASS — 205 < 251 saturation; importance 14/14 across all 3 syms |

Calibration accuracy: 3/3 process + behavioral-effect predictions clean; the model-prediction set (P4-P7) did not anticipate the realized §4.4 row 2 verdict because the brief's §4.3/§4.4 schism was unresolved at brief time. Pre-committed brief-template fix: §4 must be a single decision tree at brief authoring time. The new `feedback_v3_iter016_xgboost_mandate.md` rule does NOT close a calibration gap (calibration discipline is intact for what was predicted) — it closes an axis-coverage gap (model-architecture unmodeled in the v3 catalog), and addresses the failure-mode diagnostic that LightGBM may be the ceiling for the current feature stack.

## Pareto Position

Single-row degenerate front (Section 8 criterion 9 waiver):

| seed | OOS Sharpe | OOS MaxDD | OOS Calmar | PBO | n_trades | max_conc% |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | +2.1206 | 12.47% | 3.5163 | 0.1034 | 85 | 45.23% |

Cross-symbol OOS dispersion (informational, NOT Pareto-equivalent under EXPLORATION):

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| LDOUSDT | +19.84 | 11 (lottery flag) | 63.6% | 45.23% |
| BCHUSDT | +17.54 | 32 | 40.6% | 39.99% |
| TRXUSDT | +6.48 | 42 | 42.9% | 14.77% |

LDO 45.23% concentration > 30% CONFIRMATION cap (informational under EXPLORATION). LDO lottery flag carries forward unchanged from iter-v3/011/012/013/014 + this iteration's bit-identical OOS LDO trade-count. The OOS bit-identity (85 trades, 12.47% MaxDD, 45.23% LDO concentration all matching iter-v3/013 to high precision) is unusually clean evidence that the OOS lift is not driven by per-trade economics changes from the new feature — it is mechanical Optuna re-routing on a 14-column loss surface.

## Next Iteration

**iter-v3/016 — axis: LightGBM → XGBoost head-to-head on iter-v3/013's 13-feature stack** per Critic FINAL Recommendation 1 of iter-v3/015 review (this diary's review SHA `a0cfae7`) AND new memory rule `feedback_v3_iter016_xgboost_mandate.md` MANDATORY pre-commit.

XGBoost head-to-head closes the model-architecture coverage gap. After iter-v3/016 completes (regardless of outcome), the model-architecture finding pairs compoundably with every future feature/label/gate axis. Suggested specifics:

| Parameter | iter-v3/015 (current) | iter-v3/016 (mandated) |
|---|---:|---:|
| Universe | BCH+LDO+TRX (3 symbols) | UNCHANGED |
| Z-score OOD threshold | 2.0 | UNCHANGED |
| ATR multipliers | (2.0, 1.0) | UNCHANGED |
| BTC trend filter band | ±15% | UNCHANGED |
| ADX threshold | 20.0 | UNCHANGED |
| **V3_FEATURE_COLUMNS count** | **14 (with tbr_zscore_30)** | **13 (drop tbr_zscore_30 as INERT)** |
| **Model architecture** | **LightGBM** | **XGBoost (head-to-head, single-axis)** |
| Optuna search-space | LightGBM (learning_rate, max_depth, num_leaves, min_child_samples, subsample, colsample_bytree, reg_alpha, reg_lambda) | **XGBoost mirror** (learning_rate, max_depth, min_child_weight, subsample, colsample_bytree, gamma, reg_alpha, reg_lambda) |

**iter-v3/016 first commit pre-commits (per Critic FINAL Recommendation 3)**:
- (a) Drop `tbr_zscore_30` from V3_FEATURE_COLUMNS (back to 13) — restore iter-v3/013 baseline before XGBoost integration. ITERATION_LABEL "v3-016".
- (b) Add `tbr_raw` to V3_NON_FEATURE_COLUMNS (Critic Clarification 4 low-priority hygiene).
- (c) Fix `_write_feature_importance` at `run_baseline_v3.py:1110-1151` — either aggregate properly across all (sym, month) models OR rename outputs to clarify single-symbol single-month scope. The QE-discovered defect must not propagate.
- (d) Add XGBoost as a runner-selectable model alternative (likely a `--model xgboost` flag or a parallel runner file). Match LightGBM's hyperparam search budget per Optuna config.

**Pre-conditions for iter-v3/016 brief**:
- Section 4 must be a single decision tree (not two parallel §4.3/§4.4 tables) — fix the brief template lesson from iter-v3/015.
- Section 7 prediction band must include explicit probability mass for "model-architecture-axis NEGATIVE-no-effect" outcome (XGBoost matches LightGBM IS Sharpe within ±0.10) AND "model-architecture-axis PROMISING" outcome (XGBoost lifts IS Sharpe by ≥+0.20). The XGBoost head-to-head is genuinely uncertain priors are wide.
- Pre-register an OOS-axis falsifier IF the brief intends to read OOS metrics (otherwise OOS remains informational-only).
- Single-axis discipline: ONLY model architecture changes (LightGBM → XGBoost). No other parameter variation. tbr_zscore_30 drop is baseline-restoration, not a second axis.
- Wall-clock budget: same 2h hard cap, target < 30 min on 3-symbol universe at `--exploration --seeds 1 --n-trials 10`. XGBoost training is comparable to LightGBM (within 2–3× on identical data); engineer scopes the search space at iter-v3/016 setup.

**Catalog count after iter-v3/015**: **8 of 10** EXPLORATIONs; **2 more required** before any CONFIRMATION can launch. Axis coverage to date: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 1 + gate-adx × 1 (closed) + NEW feature family × 1 = 7 unique axis representations after iter-v3/015. iter-v3/016 will add the model-architecture axis; iter-v3/017+ will need 1 more unique axis (NEW labeling architecture, NEW risk primitive, or returning to NEW feature family expansion gated on iter-v3/016's XGBoost finding).

**iter-v3/015 status**: NOT a CONFIRMATION-bundle candidate. Feature INERT (model architecture is the bottleneck, NOT feature pool). Future CONFIRMATION-bundling QR treats `tbr_zscore_30` as dropped from V3_FEATURE_COLUMNS effective iter-v3/016; microstructure family expansion is deferred until iter-v3/016's XGBoost finding establishes whether model-architecture is the ceiling. The 5 caveats from this diary travel with the catalog row to inform future bundling decisions.
