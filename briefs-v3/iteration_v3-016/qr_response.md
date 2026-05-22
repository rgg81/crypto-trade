# Phase 7.5 QR Round 2 Response — iter-v3/016

OVERALL: ACCEPT Critic Round 1 PRELIMINARY headline classification (`EXPLORATION-NEGATIVE` clean). All 5 clarifications dispositioned below. Stand by methodology PASS, stand by NEGATIVE verdict, request OVERALL = `EXPLORATION-NEGATIVE` (clean).

Critic Round 1 PRELIMINARY SHA `a20c54b`; engineering report SHA `7ed37b3`; brief SHA `10f3db9`; Phase 5.5 gate SHA `d5930fe`; setup commit SHA `1aa3eb3`; current HEAD `a20c54b`.

---

## Clarification 1 (LOAD-BEARING) — Bit-identity disposition for §4.4 row 4 vs row 5 boundary

**Position: TAKE RESOLUTION PATH (a). Per-symbol trade-roster non-bit-identity verified by inspection. §4.4 row 4 NULL-RESULT bit-identity test FAILS unambiguously → §4.4 row 5 NEGATIVE-clean fires.**

The Critic correctly identified that `|217 − 209| = 8 < 11` triggers the §4.4 row 4 NULL-RESULT bit-identity test (the saturation-falsifier-derived |Δ| ≥ 11 threshold for row 5 fires only when the trade count delta exceeds the saturation predictor's lower bound, which it does not in this iteration). The row 4 bit-identity test is therefore the one that must be exercised to disambiguate.

**Per-symbol verification (no new script required — the per-symbol counts are in the engineering report at SHA `7ed37b3`):**

| Symbol | iter-v3/013 IS trades | iter-v3/016 IS trades | Δ |
|---|---:|---:|---:|
| BCHUSDT | 92 | 87 | **−5** |
| LDOUSDT | 22 | 24 | **+2** |
| TRXUSDT | 95 | 106 | **+11** |
| **Portfolio** | **209** | **217** | **+8** |

**Per-symbol non-identity proof:** No single symbol's trade count matches between iterations. TRX shifted +11 trades (the largest absolute shift; same magnitude as the row 5 portfolio threshold). BCH shifted −5 trades. LDO shifted +2 trades. Trade roster CANNOT be bit-identical because per-symbol counts differ on every symbol. The portfolio-aggregate +8 dilution that masks the per-symbol shifts is a coincidence of opposite-direction symbol moves; per-symbol per-trade weighted_pnl 4-decimal verification is unnecessary because the trade-count constraint alone is sufficient to falsify bit-identity (a bit-identical roster requires count equality on every symbol).

**Conclusion:** §4.4 row 4 NULL-RESULT bit-identity test FAILS → row 5 NEGATIVE-clean fires unambiguously. The row 5 verdict was structurally correct but textually under-justified in the engineering report; this Round 2 response fills the missing per-symbol-count proof.

**Brief drafting weakness acknowledgement (per Critic resolution path b):** The brief's row 5 condition `|Δ| ≥ 11` is an artifact of the saturation-falsifier predictor (`ceil(0.05 × 209) = 11`), and is too coarse — it misses cases like iter-v3/016's where the portfolio-aggregate delta hides large per-symbol shifts in opposite directions. Pre-commit for iter-v3/017+ brief template: row 5 condition becomes `"either |Δ| ≥ 11 OR per-symbol shift > 5 trades on any symbol"`. This guards against future iterations where opposite-direction per-symbol shifts mask through to the portfolio aggregate as a bit-identity-passing delta.

---

## Clarification 2 (MEDIUM PRIORITY) — XGBoost importance-divergence: structural mechanism vs hyperparam-search noise

**Position: ACKNOWLEDGE Critic's noise hypothesis as a co-plausible alternative interpretation. Cannot fully discriminate between structural-mechanism and hyperparam-search-artifact at single-seed n_trials=10 budget. Catalog row caveats accordingly.**

The Critic's noise hypothesis is well-formed: at n_trials=10 single-seed with `n_eff=6` from PCA on the search space, the importance ranking is extracted from a sparsely-explored hyperparameter region where the optimum likely sits in a poor-fit local minimum. The IS Sharpe collapse to +0.55 (Δ −0.46) is exactly the symptom expected from a poor-fit Optuna trial, and importance distributions from poor-fit models are not reliable indicators of true feature utility. Furthermore, `max_dd_window_50` being depth-0 split for 2 of 3 per-symbol models is consistent with depth-wise tree growth's tendency to lock onto a single globally-discriminative feature, but is also consistent with Optuna's narrow trial budget settling there by chance — both interpretations fit the observation.

**Cannot discriminate at this budget.** A structurally-grounded claim ("XGBoost depth-wise growth surfaces signal across a broader feature set vs LightGBM's leaf-wise + GOSS") would require multi-seed XGBoost runs (e.g., 5 outer seeds × 50 trials each) where the importance-rank distribution stabilizes under Optuna budget convergence. At single-seed n_trials=10, the rank inversion (`sym_vs_btc_ret_7d` 13→4, `ema_spread_atr_20` 1→6, `max_dd_window_50` 5→1) could equally reflect either:
- (a) genuine architectural-bias divergence in feature utility under depth-wise growth, OR
- (b) hyperparam-search artifact from a sparsely-explored search region landing in different local optima for each architecture.

**Catalog row caveat (mandatory text):** "importance-divergence finding NOT structurally validated; may be hyperparam-search artifact at n_trials=10 single-seed budget. Future re-test would require multi-seed XGBoost (≥5 outer seeds × ≥50 trials) where importance rankings stabilize under Optuna convergence to discriminate structural-mechanism from search-artifact."

This caveat is load-bearing for any future QR who reads the iter-v3/016 catalog row and considers re-introducing XGBoost in a different configuration. The structural divergence claim should NOT be propagated as established fact in iter-v3/017+ briefs without multi-seed re-validation.

---

## Clarification 3 (MEDIUM PRIORITY) — `_write_feature_importance` second defect (last-month-only aggregation)

**Position: ACKNOWLEDGE the second defect. Pre-commit for iter-v3/017 first commit: fix or rename.**

The Critic correctly identified that the iter-v3/016 first commit (SHA `1aa3eb3`) fixed only the iter-v3/015 defect (per-symbol CSV emission was hardcoded to `primary_model_pairs[0]` = BCH-only). The fix iterates over all 3 per-symbol models, but the aggregation reads `inner._models` — which holds only the FINAL month's lazily-trained ensemble per symbol. So the per-symbol `feature_importance_<SYM>.csv` files reflect each symbol's last-month inner ensemble, NOT walk-forward-aggregated importances across all training months. This is a strictly less misleading version of the iter-v3/015 defect (the engineering report no longer claims aggregation is per-(sym, month) when it isn't), but the brief's intent was full month-aggregation.

**Additional defect:** OOS feature_importance CSVs are byte-identical to IS CSVs (the loop emits the same dict to both `in_sample/` and `out_of_sample/` subdirectories). This is misleading because OOS models do not exist as a separate training artifact — they are IS-trained models applied to OOS data; the dict is the same.

**Pre-commit for iter-v3/017 first commit (LOAD-BEARING — cannot be deferred):** Adopt one of the two resolution options below. Pre-committed via the new memory rule `feedback_v3_iter017_metalabeling_mandate.md` and the iter-v3/017 brief template. Cannot be renegotiated post-hoc.

- **Option A (preferred):** Modify `_train_for_month` to accumulate per-month importances during walk-forward training (store `feature_importances_` per-(sym, month) in a class-level dict). At report time, aggregate via `mean()` or `sum()` across all months per symbol, then aggregate across symbols for the portfolio CSV. Requires ~30 lines of code change in `lgbm.py` and `run_baseline_v3.py`.
- **Option B (fallback):** Drop the OOS importance CSV entirely (it's byte-identical to IS — misleading), rename the IS CSV from `feature_importance.csv` → `model_importance_last_month.csv` to clarify scope, and document in the engineering-report template that this is single-month not walk-forward-aggregated.

**Either option is acceptable.** Option A is preferred because it produces the structurally correct artifact; Option B is fast and removes the misleading dual-CSV pattern. Pre-commit deferred to iter-v3/017 Engineer to choose A or B at first-commit time.

---

## Clarification 4 (LOW PRIORITY) — Saturation falsifier band tightening to [iter_NNN_baseline ± 25%]

**Position: ACCEPT. iter-v3/017+ brief template tightens the saturation predictor to `[baseline ± 25%]` (not the prior wide [165, 250] = baseline × [0.79, 1.20] artifact).**

The Critic's observation is correct: the iter-v3/016 brief's prediction band [165, 250] median 200 (baseline × [0.79, 1.20]) was wider than necessary and effectively non-falsifying. Realized = 217 sat well within band; the falsifier did not fire even though the realized iteration was a clear NEGATIVE. A tighter [baseline ± 25%] band (= [iter-v3/013 baseline 209 × [0.75, 1.25]] = [157, 261]) would not have flipped the iter-v3/016 verdict (217 still within the tighter band) but is structurally more discriminating going forward — it tightens the band on the unfavorable side enough that a NULL-RESULT classification requires the trade roster to remain very close to baseline, while an axis-propagated outcome (whether PROMISING or NEGATIVE) requires the trade count to shift by ≥25% in either direction.

**Pre-commit (iter-v3/017+ brief template rule):** Saturation falsifier band derived as `[baseline_n_trades × 0.75, baseline_n_trades × 1.25]`, rounded to nearest integer. The prior `feedback_axis_saturation_predictor.md` formula `falsifier_threshold = ceil(1.2 × counterfactual_n_trades)` continues to apply for the upper-bound saturation cap, but the lower-bound for NULL-RESULT classification tightens from "no explicit lower bound" to `floor(0.75 × baseline_n_trades)`. Documented in the new memory rule `feedback_v3_iter017_metalabeling_mandate.md`.

---

## Clarification 5 (LOW PRIORITY) — XGBoost catalog row scope: closed for all configs vs scoped closure?

**Position: ACCEPT Critic's distinction. Catalog row scopes the closure narrowly: "model-architecture axis closed at n_trials=10 + cross-entropy objective + depth-wise growth defaults". XGBoost is NOT closed for all hyperparam configurations.**

The Critic's argument is structurally important: the iter-v3/016 result diagnoses a specific failure mode ("XGBoost depth-wise growth at depth 3-5 with cross-entropy objective and 10 Optuna trials produced higher-IS-PnL solutions at the cost of elevated drawdown that was not penalized in the optimization objective"). This is a finding about a *configuration*, not about XGBoost as an architecture writ large. Three plausible configurations remain untested and should not be foreclosed by the iter-v3/016 catalog row:

1. **Sharpe-objective Optuna** (custom Optuna objective targeting OOS Sharpe instead of IS log-loss). Could surface XGBoost configurations that produce lower-MaxDD solutions even under depth-wise growth.
2. **Drawdown-penalized loss** (custom XGBoost objective subtracting a drawdown-penalty term from the binary cross-entropy gradient). Could produce configurations with the IS-PnL upside but better OOS MaxDD discipline.
3. **`grow_policy='lossguide'` head-to-head** (XGBoost mimicking LightGBM's leaf-wise growth via lossguide policy). Would isolate the GOSS-vs-non-GOSS difference from the depth-wise-vs-leaf-wise difference; arguably a cleaner architectural ablation.

**Catalog row text update (vs the iter-v3/016 first draft):** "Model-architecture axis closed at the tested configuration: n_trials=10 + cross-entropy objective + depth-wise growth defaults. XGBoost is NOT closed for all hyperparam configurations; future iterations could re-test with Sharpe-objective Optuna, drawdown-penalized loss, or `grow_policy='lossguide'` head-to-head if the QR believes the architecture is compoundably valuable in a tested config."

This narrower closure preserves the option to re-introduce XGBoost in a structurally different configuration without re-litigating the iter-v3/016 NEGATIVE verdict. It does not affect the iter-v3/017 mandate (NEW labeling architecture, per Critic Pre-Commitment for iter-v3/017 Axis).

---

## Position Summary

**STAND BY VERDICT.** Request OVERALL = `EXPLORATION-NEGATIVE` (clean) per Critic Round 1 PRELIMINARY's strong prior. All 5 clarifications dispositioned with explicit pre-commits for iter-v3/017+ brief template (Clarifications 1, 4) and iter-v3/017 first commit (Clarification 3). Catalog row scoped narrowly per Clarification 5 to preserve future XGBoost re-introduction option in different configurations.

**iter-v3/017 axis mandated:** NEW labeling architecture (meta-labeling per López de Prado AFML Ch. 3 preferred, fixed-horizon return labels as fallback). Per Critic Pre-Commitment of iter-v3/016 review, this is the unique untested category in the v3 axis priority hierarchy after iter-v3/016 closes the NEW model-architecture category at n_trials=10 + cross-entropy + depth-wise defaults configuration. Pre-committed via new memory rule `feedback_v3_iter017_metalabeling_mandate.md`. Cannot be renegotiated post-hoc.

After iter-v3/017 completes, cadence = 10/10 EXPLORATIONs since last CONFIRMATION → first CONFIRMATION can launch.
