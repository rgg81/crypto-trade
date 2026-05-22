# Iteration v3-016 — Diary

## Decision: EXPLORATION-NEGATIVE (clean)

Critic FINAL OVERALL = `EXPLORATION-NEGATIVE` (clean) at SHA `9a558fc` — clean concurrence with QE recommendation (per brief §4.4 row 5) and QR Round 2 acceptance (SHA `06af055`). The iteration tested the FIRST NEW model architecture in v3 catalog: a head-to-head replacement of `LightGbmStrategy` with `XgboostStrategy` on iter-v3/013's 13-feature stack (drop `tbr_zscore_30` as INERT). This is the second iteration whose axis was forced by a prior Critic FINAL recommendation (iter-v3/015's NEGATIVE-no-effect on tbr_zscore_30 diagnosed LightGBM as the likely ceiling for the current feature stack; XGBoost head-to-head was the natural compoundable axis to test before adding more features). Headline: IS Sharpe Δ −0.46 (+0.5524 vs iter-v3/013 +1.0088); OOS Sharpe Δ **−2.53** (+0.1710 vs iter-v3/013 +2.6970, **WORST OOS DELTA IN v3 HISTORY**); 217 IS / 112 OOS trades; OOS MaxDD 40.62% (4.26× iter-v3/013's 12.47%, also worst in v3). Per-symbol OOS attribution: TRX +18.82 (only profitable symbol; 258.79% of total weighted_pnl), BCH −2.35, LDO −9.19. Importance Spearman ρ ≈ 0.56 between LightGBM and XGBoost importance vectors (divergence prediction CONFIRMED, but caveat-flagged per Clarification 2 as may-be-noise at n_trials=10 single-seed budget). Trade roster non-bit-identical (per-symbol shifts BCH −5, LDO +2, TRX +11) — §4.4 row 4 NULL-RESULT bit-identity test FAILS → row 5 NEGATIVE-clean fires unambiguously per QR Round 2 Clarification 1 disposition.

## Headline

**Worst OOS delta in v3 history at Δ −2.53** (+0.1710 vs iter-v3/013 +2.6970), and worst OOS MaxDD in v3 history at **40.62%** (4.26× iter-v3/013's 12.47%). IS Sharpe Δ −0.46 (+0.5524 vs +1.0088) — magnitude similar to but slightly worse than iter-v3/014's NEGATIVE Δ −0.35; sits OUTSIDE PATH A band [+0.70, +1.30] by 0.15 below lower bound and below PATH B threshold +0.81 by Δ −0.26. **Trade roster non-bit-identical** (209 → 217 IS, +8 portfolio with opposite-direction per-symbol shifts: BCH −5, LDO +2, TRX +11). **Per-symbol IS-vs-OOS polarity inversion**: in IS, BCH +115% / LDO +26% / TRX −42% of total PnL; in OOS, BCH −209% / LDO −372% / TRX +681%. Most extreme polarity inversion observed in v3 history. Importance Spearman ρ ≈ 0.56 (divergence confirmed, with `sym_vs_btc_ret_7d` 13→4, `ema_spread_atr_20` 1→6, `max_dd_window_50` 5→1 the largest rank shifts) — but flagged as may-be-noise per Critic Clarification 2.

## What Was Tested

**Single-axis variation** (NEW model architecture, axis category 2 per `feedback_structural_over_knob_exploration.md`): replace `LightGbmStrategy` with `XgboostStrategy` on iter-v3/013's 13-feature stack. Setup commit `1aa3eb3`. The axis is the FIRST NEW model architecture attempted in v3 (iter-v3/001-015 all used LightGBM exclusively) and the SECOND axis to result from a prior Critic FINAL recommendation (iter-v3/015's NEGATIVE-no-effect FIRED `feedback_v3_iter016_xgboost_mandate.md`).

**Implementation specifics**:
- `XgboostStrategy` class added at `src/crypto_trade/strategies/ml/xgb.py` (parallel to `lgbm.py`)
- `optimization_xgb.py` mirror of `optimization.py` with XGBoost-specific Optuna search space
- `--model {lgbm,xgboost}` CLI flag added at `run_baseline_v3.py` (default = lgbm)
- `xgboost>=2.0,<3.0` added to `pyproject.toml` (xgboost 2.1.4 actually loaded)
- `grow_policy='depthwise'` PINNED (load-bearing axis-definition; not the LightGBM-mimicking 'lossguide')
- `tree_method='hist'` PINNED
- `objective='binary:logistic'` + `scale_pos_weight=neg/pos` (substituting for LightGBM's `is_unbalance=True`)
- `objective='multi:softprob'` + `num_class=3` for ternary
- `min_child_weight` Optuna param substitutes `min_child_samples` (semantic equivalent, same range [5, 100])
- `num_leaves` Optuna dimension DROPPED (no-op under depthwise growth)

**3 first-commit pre-commits delivered cleanly** at SHA `1aa3eb3` (per Critic FINAL of iter-v3/015 review SHA `a0cfae7`):
1. Drop `tbr_zscore_30` from V3_FEATURE_COLUMNS (back to 13) — restore iter-v3/013 baseline before XGBoost integration
2. Add `tbr_raw` to V3_NON_FEATURE_COLUMNS (Critic Clarification 4 hygiene from iter-v3/015)
3. Fix `_write_feature_importance` at `run_baseline_v3.py:1110-1151` — iterate over all 3 per-symbol models (not BCH-only as iter-v3/015 defect showed)

**Hypothesis** (brief Section 1, SHA `10f3db9`): XGBoost on the 13-feature stack will produce IS Sharpe within ±0.30 of iter-v3/013's +1.0088 baseline (calibrated band [+0.70, +1.30] median +1.00) AND will surface measurably different feature-importance rankings (Spearman ρ between LightGBM and XGBoost importance vectors < 0.85), demonstrating that model architecture is a non-trivial axis of variation in the v3 strategy stack.

**Hypothesis verdict: PERFORMANCE FALSIFIED, IMPORTANCE-DIVERGENCE CONFIRMED-WITH-NOISE-CAVEAT.** IS Sharpe +0.5524 (vs predicted [+0.70, +1.30] median +1.00; observed +0.5524 OUTSIDE band by 0.15 below lower bound; below PATH B threshold +0.81 by 0.26). Importance Spearman ρ ≈ 0.56 (vs predicted < 0.85 — sub-hypothesis confirmed). Per Critic Clarification 2, the importance-divergence finding may be hyperparam-search artifact at n_trials=10 single-seed budget where `n_eff=6` indicates sparsely-explored region; cannot fully discriminate between structural-mechanism and search-artifact at this budget without multi-seed re-validation.

**Configuration**: `--exploration --seeds 1 --n-trials 10 --model xgboost` on 3-symbol v3 universe (BCH+LDO+TRX), ENSEMBLE_SIZE=1, colsample_bytree=1.0, training_months=24, OOS_CUTOFF_DATE=2025-03-24. Identical to iter-v3/013 modulo model architecture (LightGBM → XGBoost), `tbr_zscore_30` drop (baseline restoration after iter-v3/015's INERT NEGATIVE-no-effect, NOT a second axis), and ITERATION_LABEL cosmetic.

## What Was Measured

### Headline metrics

| Metric | iter-v3/013 (baseline) | iter-v3/016 (this run) | Δ vs iter-v3/013 |
|---|---:|---:|---:|
| IS monthly Sharpe | +1.0088 | **+0.5524** | **−0.46** |
| OOS monthly Sharpe | +2.6970 | **+0.1710** | **−2.53 (WORST OOS Δ in v3 history)** |
| IS daily Sharpe | — | +1.3934 | — |
| OOS daily Sharpe | — | +0.3905 | — |
| IS/OOS ratio | 2.67 | **3.23** (degraded) | — |
| OOS/IS ratio | 2.67 | **0.31** (substantially below 0.5 floor) | — |
| IS trades | 209 | **217** | **+8 (NON-bit-identical)** |
| OOS trades | 85 | **112** | **+27 (informational below 130 floor)** |
| IS max drawdown | 22.00% | **38.69%** | **+16.69 pp** |
| OOS max drawdown | 12.47% | **40.62%** | **+28.15 pp (4.26× WORST in v3 history)** |
| OOS Calmar | 4.96 | 0.179 | −4.78 |
| Profit Factor (OOS) | — | 1.0485 | — |
| Win Rate (OOS) | — | 38.39% | — |
| PBO (per-cell mean) | 0.1034 | **0.0889** | **−0.0145 (improvement — only metric)** |
| n_eff (per-cell median) | 7 | **6** | −1 (one Optuna dim dropped — `num_leaves` no-op under depthwise) |
| PSR | 1.0000 | 0.9888 | −0.0112 |
| n_trials | 30 | 30 | 0 |
| Wall-clock | 6 min | 8 min | +2 min |

The headline OOS Sharpe +0.1710 is the worst OOS in v3 history. The OOS MaxDD 40.62% is also the worst in v3 history at 4.26× iter-v3/013's 12.47%. PBO improvement (0.0889 vs 0.1034) is the ONLY dimension on which XGBoost marginally exceeds LightGBM — completely dominated by the Sharpe collapse. PATH B (NEGATIVE) §4.4 row 5 fires per IS Sharpe < +0.81 threshold (margin -0.26).

### Per-symbol OOS attribution

| Symbol | Trades | Win Rate | Weighted PnL | Concentration % | Δ trades vs iter-v3/013 |
|---|---:|---:|---:|---:|---:|
| TRXUSDT | 49 | 46.9% | **+18.82** | **+258.79%** | +5 (+11%) |
| BCHUSDT | 44 | 31.8% | −2.35 | −32.37% | +13 (+42%) |
| LDOUSDT | 19 | 31.6% | **−9.19** | **−126.42%** | +9 (+90%) |
| **TOTAL** | **112** | **38.4%** | **+7.27** | — | +27 (+32%) |

**TRX is the only profitable OOS symbol.** BCH and LDO BOTH turned negative under XGBoost on the SAME 13 features that produced positive results under LightGBM in iter-v3/013. TRX carries 258.79% of total OOS weighted_pnl; LDO's −126.42% partially offsets. Single-seed-degenerate concentration artifact: when one symbol carries the entire portfolio's PnL after the other two go negative, max symbol concentration crosses 100%. This is structurally unacceptable for a CONFIRMATION candidate and would fail any per-symbol concentration cap; correctly reported as NEGATIVE under EXPLORATION.

### Per-symbol IS attribution

| Symbol | Trades | Win Rate | net_pnl_pct | pct_of_total_pnl |
|---|---:|---:|---:|---:|
| BCHUSDT | 87 | 43.7% | +65.84% | +115.35% |
| LDOUSDT | 24 | 37.5% | +15.00% | +26.29% |
| TRXUSDT | 106 | 34.0% | −23.77% | −41.64% |

**IS vs OOS polarity inversion (most extreme in v3 history)**: In IS, BCH and LDO are profitable while TRX is negative. In OOS, TRX is the only positive. XGBoost is overfitting the IS period for BCH/LDO while extracting a signal in TRX that IS walk-forward CV did not see. The structural mechanism (per engineering report MaxDD analysis): XGBoost depth-wise growth at depth 3-5 with 10 Optuna trials found higher-IS-PnL solutions at the cost of elevated drawdown that was NOT penalized in the optimization objective (binary cross-entropy, not Sharpe-ratio or Calmar-ratio objective). LightGBM at the same Optuna budget found lower-drawdown solutions because GOSS's gradient sampling implicitly smooths the loss surface.

### Importance divergence (Spearman ρ ≈ 0.56)

LightGBM rank-vector vs XGBoost rank-vector across the 13 inherited features:
```
LightGBM ranks: [5, 6, 8, 13, 7, 1, 4, 9, 12, 3, 11, 2, 10]
XGBoost ranks:  [1, 2, 3,  4, 5, 6, 7, 8,  9, 10, 11, 12, 13]
Spearman ρ ≈ 0.56
```

Largest rank shifts: `sym_vs_btc_ret_7d` (LGBM 13/13 dead last → XGB 4/13, jump +9), `ema_spread_atr_20` (LGBM 1/13 top → XGB 6/13, drop -5), `max_dd_window_50` (LGBM 5/13 → XGB 1/13). **Caveat per Critic Clarification 2**: importance-divergence finding may be hyperparam-search artifact at n_trials=10 single-seed budget where `n_eff=6` indicates sparsely-explored search region. Cannot discriminate between (a) structural depth-wise-vs-leaf-wise + GOSS divergence and (b) Optuna landing in different local optima for each architecture without multi-seed re-validation (≥5 outer × ≥50 trials). Catalog row caveats accordingly.

### Methodology checks (Critic FINAL — SHA `9a558fc`)

| # | Check | Status | Detail |
|---:|---|:---:|---|
| 1 | Look-Ahead | PASS | XgboostStrategy `_train_for_month` past-only; TimeSeriesSplit gap=66; training_days cutoff past-only |
| 2 | Embargo | PASS | REQUIRED_GAP = 66 = (21+1)×3; cv_gap=66 propagated to TimeSeriesSplit |
| 3 | MT correction (methodology) | INFORMATIONAL | PBO = 0.0889 (improvement); n_eff = 6; pathological per-cell PBO tails (LDO 2025-02 = 1.0, etc.) audit-noted |
| 3 | MT correction (edge) | INFORMATIONAL | DSR = 0.0, PSR = 0.9888 — single-seed exploration artifact |
| 4 | IC correlation | PASS | max abs(IC) = -0.685 (range_realized_vol_50 ↔ max_dd_window_50, < 0.70); no NEW feature introduced — inherited 13-stack |
| 5 | ADF stationarity | PASS | 1657/2041 cells stationary (81.2%); 384 non-stationary concentrated in early IS + LDO listing-edge months |
| 6 | Pareto dominance | PASS (vacuous, single-seed) | 100% concentration is single-seed-degenerate when one symbol carries portfolio after others go negative |
| 7 | Reproducibility | PASS | Setup `1aa3eb3` / Brief `10f3db9` / Gate `d5930fe` / Engineering Report `7ed37b3` / Critic Round 1 `a20c54b` / QR Round 2 `06af055` / Critic FINAL `9a558fc` stamped |
| 8 | Hypothesis alignment | PASS (Clarification 1 resolved) | Single-axis discipline honored; per-symbol non-bit-identity verified (BCH -5, LDO +2, TRX +11) → §4.4 row 4 fails → row 5 NEGATIVE-clean fires unambiguously |
| 9 | Symbol exclusion | PASS | {BCH, LDO, TRX} ∩ V3_EXCLUDED_SYMBOLS = ∅ |
| 10 | Feature isolation | PASS | features_v3 imports only inside docstrings; no actual cross-track import |
| 11 | Forming-candle | PASS (inherited) | Pre-flight staleness guard fired clean |
| 12 | Library pinning | PASS | xgboost>=2.0,<3.0 NEW dep (Apache-2.0); xgboost 2.1.4 loaded; lightgbm 4.6.0 retained |

**All 12 Critic checks PASS / WAIVED-INFORMATIONAL per EXPLORATION carve-out.** Zero BLOCK conditions. Methodology is clean — XGBoost integration is correct (look-ahead clean, embargo correct, library pinning explicit). The NEGATIVE classification is on the *signal-extraction axis* (XGBoost depth-wise + cross-entropy + n_trials=10 produces risk-unaware solutions), NOT on the *methodology axis* (where everything is clean).

## Caveats Recorded for Audit Trail (5)

The NEGATIVE clean verdict comes with five explicit caveats catalogued for the future CONFIRMATION-bundling QR (per Critic FINAL Recommendations and QR Round 2 dispositions):

1. **`verdict = NEGATIVE` (clean)** per brief §4.4 row 5: IS Sharpe Δ −0.46 < −0.10 NEGATIVE threshold AND non-bit-identical roster (per-symbol shifts BCH −5, LDO +2, TRX +11 all non-zero) AND axis propagated (saturation falsifier PASS at 217 < 251 derived threshold; +8 IS trades net). All three §4.4 row 5 conditions met cleanly. NOT a NULL-RESULT (distinguishing from iter-v3/012 which had bit-identical roster); NOT NEGATIVE-no-effect (distinguishing from iter-v3/015 which had non-bit-identical roster but importance rank 14/14 of a single new feature). The clean NEGATIVE classification preserves catalog discipline; the worst-OOS-in-v3-history magnitude observation lives in catalog caveats. NOT a CONFIRMATION-bundle candidate.

2. **`worst_oos_delta_in_v3_history = -2.53`** (vs iter-v3/013 +2.6970 baseline, observed +0.1710): the OOS collapse magnitude exceeds iter-v3/014's −1.83 (previously largest negative OOS delta in v3) by 38%. The structural mechanism: XGBoost depth-wise growth at depth 3-5 with 10 Optuna trials and binary cross-entropy objective produces risk-unaware solutions — IS-PnL maximization without drawdown penalty; the IS/OOS MaxDD ratio of 1.05 (essentially equal) is structurally unusual (typically IS MaxDD > OOS MaxDD because IS Optuna tuning controls drawdown). Future XGBoost re-introduction at iter-v3/017+ would require Sharpe-objective Optuna OR drawdown-penalized loss to address this failure mode — neither tested at this iteration.

3. **`MaxDD_4x_inflation_worst_in_v3_history`** (40.62% OOS vs iter-v3/013 12.47%; IS 38.69% vs ~22.00%): IS MaxDD also worst-in-v3 at 1.76× iter-v3/013. The IS/OOS MaxDD symmetry (ratio 1.05) signals XGBoost is intrinsically higher-variance, not just failing on OOS regime shifts. Per-symbol MaxDD attribution: LDO and BCH both turned negative OOS while LightGBM kept them positive on the same features. The OOS/IS Sharpe ratio of 0.31 is the lowest in v3 track history (substantially below the 0.5 floor that would apply at CONFIRMATION).

4. **`model_arch_axis_closed_scope = "n_trials=10 + cross-entropy objective + depth-wise growth defaults"`** (per Critic Clarification 5 disposition; NOT closed for all XGBoost configurations): three plausible configurations remain untested and should not be foreclosed by this catalog row — (a) Sharpe-objective Optuna (custom objective targeting OOS Sharpe instead of IS log-loss), (b) drawdown-penalized loss (custom XGBoost objective with drawdown-penalty term), (c) `grow_policy='lossguide'` head-to-head (XGBoost mimicking LightGBM's leaf-wise growth — would isolate GOSS-vs-non-GOSS difference from depth-wise-vs-leaf-wise difference). Future iterations could re-test XGBoost in any of these configurations; this catalog row does NOT foreclose. **Importance-divergence finding co-caveated**: Spearman ρ ≈ 0.56 may be hyperparam-search artifact at n_trials=10 (where `n_eff=6` indicates sparsely-explored search region); structural divergence claim should NOT be propagated as established fact in iter-v3/017+ briefs without multi-seed re-validation (≥5 outer × ≥50 trials).

5. **`iter-v3/017_axis_mandated = NEW labeling architecture`** (meta-labeling preferred per López de Prado AFML Ch. 3; fixed-horizon return labels as fallback) per Critic FINAL Recommendation 1 of iter-v3/016 review: pre-committed via new memory rule `feedback_v3_iter017_metalabeling_mandate.md`. The triple-barrier label (ATR 2.0 TP / 1.0 SL / 21-candle timeout) has been fixed since iter-v3/001; only ATR multipliers were tuned at iter-v3/010. Meta-labeling has slightly higher prior on PROMISING because it is structurally compoundable (the labeling change does not invalidate the existing 13-feature stack — it changes how the model uses them). Pre-commits for iter-v3/017 first commit: (a) fix `_write_feature_importance` to aggregate across all walk-forward months (Option A or B per Critic Clarification 3), (b) drop OOS importance CSV byte-duplication or rename to `model_importance_last_month.csv`, (c) restore default `--model lgbm` (XGBoost remains opt-in via `--model xgboost`), (d) ITERATION_LABEL "v3-017", (e) implement meta-labeling architecture, (f) tighten saturation falsifier band to `[baseline_n_trades × 0.75, baseline_n_trades × 1.25]` per Clarification 4, (g) brief template §4.4 row 5 condition update: "either |Δ| ≥ 11 OR per-symbol shift > 5 trades on any symbol" per Clarification 1. Cannot be renegotiated post-hoc.

## Lessons

1. **XGBoost depth-wise growth at low Optuna budget + cross-entropy objective is risk-unaware**. iter-v3/016's failure mode was: a 13-feature stack that produced +1.01 IS / +2.70 OOS Sharpe under LightGBM produced +0.55 IS / +0.17 OOS Sharpe under XGBoost on the SAME features, with OOS MaxDD inflating 4.26×. The structural diagnosis: XGBoost depth-wise growth at depth 3-5 with 10 Optuna trials found higher-IS-PnL solutions at the cost of elevated drawdown that was NOT penalized in the optimization objective (binary cross-entropy, not Sharpe-ratio or Calmar-ratio objective). LightGBM at the same Optuna budget found lower-drawdown solutions because GOSS's gradient sampling implicitly smooths the loss surface. The IS/OOS MaxDD ratio of 1.05 (essentially equal) is the diagnostic signature: XGBoost's risk-unaware optimization produces intrinsically higher-variance solutions, not just OOS-regime-failure. Future XGBoost re-introduction would require Sharpe-objective Optuna OR drawdown-penalized loss to address this — neither tested at this iteration. Per Critic Clarification 5 disposition, the catalog row scopes the closure narrowly: model-architecture axis closed at n_trials=10 + cross-entropy + depth-wise defaults; XGBoost is NOT closed for all hyperparam configurations.

2. **Model-architecture axis closed at this configuration; importance-divergence finding may be hyperparam-search artifact, not structural**. Per Critic Clarification 2 disposition, the Spearman ρ ≈ 0.56 importance divergence between LightGBM and XGBoost rank-vectors cannot be attributed structurally to depth-wise-vs-leaf-wise + GOSS-vs-non-GOSS architectural differences at single-seed n_trials=10 budget where `n_eff=6` indicates sparsely-explored search region. The IS Sharpe collapse to +0.55 is exactly the symptom expected from a poor-fit Optuna trial, and importance distributions from poor-fit models are not reliable indicators of true feature utility. The structural divergence claim should NOT be propagated as established fact in iter-v3/017+ briefs without multi-seed re-validation (≥5 outer × ≥50 trials). Catalog row caveats this explicitly: "importance-divergence finding NOT structurally validated; may be hyperparam-search artifact at n_trials=10 single-seed budget."

3. **Brief template §4.4 row-boundary discipline tightening (per Critic Clarification 1 + 4 dispositions)**. Two brief-template fixes pre-committed for iter-v3/017+: (a) row 5 condition becomes "either |Δ| ≥ 11 OR per-symbol shift > 5 trades on any symbol" — the prior `|Δ| ≥ 11` portfolio-aggregate threshold is a saturation-falsifier artifact that misses opposite-direction per-symbol shifts (iter-v3/016's BCH −5 + TRX +11 + LDO +2 = portfolio +8 hides TRX +11 from row 5 trigger). (b) Saturation falsifier band tightening from prior wide [165, 250] (= baseline × [0.79, 1.20]) to `[baseline_n_trades × 0.75, baseline_n_trades × 1.25]` — the prior band was effectively non-falsifying for any non-NULL-result outcome. The prior `feedback_axis_saturation_predictor.md` formula `falsifier_threshold = ceil(1.2 × counterfactual_n_trades)` continues to apply for the upper-bound saturation cap; the lower-bound for NULL-RESULT classification tightens.

4. **`_write_feature_importance` second defect (last-month-only aggregation; OOS↔IS byte-identity)** discovered by Critic Round 1 in iter-v3/016: the iter-v3/016 first commit fixed only the iter-v3/015 BCH-only-aggregation defect (now iterates over all 3 per-symbol models), but the aggregation reads `inner._models` which holds only the FINAL month's lazily-trained ensemble per symbol. So per-symbol `feature_importance_<SYM>.csv` files reflect each symbol's last-month inner ensemble, NOT walk-forward-aggregated importances across all training months. Additional defect: OOS feature_importance CSVs are byte-identical to IS CSVs (the loop emits the same dict to both `in_sample/` and `out_of_sample/` subdirectories — misleading because OOS models do not exist as a separate training artifact). Pre-commit for iter-v3/017 first commit (Option A: modify `_train_for_month` to accumulate per-month importances; Option B: drop OOS CSV, rename IS CSV to `model_importance_last_month.csv`). iter-v3/017 Engineer chooses A or B at first-commit time. The defect must not propagate.

5. **iter-v3/017 axis MANDATORY = NEW labeling architecture (meta-labeling preferred)** per Critic FINAL Recommendation 1 + new memory rule `feedback_v3_iter017_metalabeling_mandate.md`. The triple-barrier label (ATR 2.0 TP / 1.0 SL / 21-candle timeout) has been fixed since iter-v3/001; only ATR multipliers were tuned at iter-v3/010. The labeling architecture has been explored only once within the triple-barrier framework, never as an alternative scheme. Two sub-axes acceptable: (a) **meta-labeling** per López de Prado AFML Ch. 3 — binary classifier (M2) on top of an existing momentum/mean-reversion primary signal (M1); structurally compoundable (does not invalidate the existing 13-feature stack — changes how the model uses them); (b) **fixed-horizon return labels** (e.g., sign of 5-candle forward log-return) — eliminates triple-barrier path-dependency, drastically simplifies label noise structure. Meta-labeling preferred for compoundability prior. After iter-v3/017 completes (regardless of outcome), cadence reaches 10/10 EXPLORATIONs since last CONFIRMATION → first CONFIRMATION can launch.

6. **Critic 2-round flow worked as designed (7th consecutive use producing concrete pre-commits and a NEW memory rule)**. Round 1 PRELIMINARY surfaced 5 substantive clarifications (bit-identity disposition, importance-divergence noise hypothesis, `_write_feature_importance` second defect, saturation falsifier band tightening, XGBoost catalog row scope). QR Round 2 dispositioned all 5 with explicit pre-commits including: per-symbol non-identity verified by inspection (no new script — cited engineering report); importance-divergence acknowledged as may-be-noise; iter-v3/017 first-commit fix mandated; brief template tightening accepted; catalog row scope narrowed. Round 2 FINAL accepted all 5 dispositions cleanly. The clarifications produced a concrete pre-commitment (iter-v3/017 = NEW labeling architecture with meta-labeling preferred) + a NEW memory rule (`feedback_v3_iter017_metalabeling_mandate.md`) + 7 pre-committed iter-v3/017 first-commit fixes + 2 brief-template tightening rules.

7. **Dead-paths catalog (fifteenth entry, ninth EXPLORATION row, NEGATIVE-clean classification):**
   - **iter-v3/016** — NEW model architecture axis (LightGBM → XGBoost head-to-head on iter-v3/013's 13-feature stack; single-axis variation with `tbr_zscore_30` dropped as INERT and ITERATION_LABEL "v3-016"; XGBoost grow_policy='depthwise' pinned, tree_method='hist' pinned, objective='binary:logistic' + scale_pos_weight, objective='multi:softprob' for ternary, min_child_weight substituting min_child_samples, num_leaves Optuna dim dropped) EXPLORATION on v3 universe (BCH+LDO+TRX), `--exploration --model xgboost` mode (ENSEMBLE_SIZE=1, n_trials=10, colsample_bytree=1.0, outer_seed=42). **EXPLORATION-NEGATIVE (clean)**. IS monthly Sharpe = +0.5524 (Δ −0.46 vs iter-v3/013 +1.0088). OOS monthly Sharpe = +0.1710 (Δ −2.53 vs iter-v3/013 +2.6970, **WORST OOS Δ in v3 history**; informational below 130-trade floor at OOS=112). OOS MaxDD = 40.62% (4.26× iter-v3/013, **WORST in v3 history**). Per-symbol OOS attribution: TRX +18.82 (only profitable, 258.79% concentration), BCH −2.35, LDO −9.19. Trade roster non-bit-identical (209 → 217 IS, with per-symbol shifts BCH −5 / LDO +2 / TRX +11 — opposite-direction shifts mask through to portfolio +8 aggregate). PBO 0.0889 (vs iter-v3/013 0.1034 — improvement, only metric where XGBoost exceeds LightGBM); n_eff 6 (vs LightGBM 7 — one Optuna dim dropped, principled). Spearman ρ ≈ 0.56 between LightGBM and XGBoost rank-vectors (importance-divergence sub-hypothesis confirmed but caveat-flagged as may-be-noise at n_trials=10 single-seed budget). 5 caveats catalogued. **NOT a CONFIRMATION-bundle candidate**: model-architecture axis closed at the tested configuration (n_trials=10 + cross-entropy + depth-wise defaults); NOT closed for all XGBoost configurations. iter-v3/017 axis MANDATORY = NEW labeling architecture (meta-labeling preferred per López de Prado AFML Ch. 3; fixed-horizon return labels as fallback) per `feedback_v3_iter017_metalabeling_mandate.md`. The catalog count advances 8 → 9 of 10; iter-v3/017 will be the 10th, after which CONFIRMATION can launch.

## Pre-Registered Failure-Mode vs Reality Summary

| Class | Materialized? |
|---|---|
| Process predictions (P1-P3) | 0/3 materialized — pipeline ran clean, wall-clock 8 min within target, no integration failures, all 4 first-commit pre-commits PASS |
| Model predictions (P4-P7) | P4 (PATH A band [+0.70, +1.30]) DID NOT MATERIALIZE; P5 (PATH B IS Sharpe < +0.81) MATERIALIZED at +0.5524 (-0.26 below threshold); P6 (PATH C importance-divergence + matching IS) PARTIALLY materialized (importance divergence ρ ≈ 0.56 confirmed, but IS Sharpe collapsed not matched); the realized outcome of "importance divergence + IS Sharpe collapse" maps to PATH B verdict per §4.4 row 5 |
| OOS-axis prediction | informational under EXPLORATION; the OOS MaxDD 4.26× inflation + 38% worse than prior v3 record OOS delta is the most extreme OOS degradation observed in v3, but this is NOT a verdict-cell metric under EXPLORATION |
| Behavioral-effect verifier (saturation falsifier + per-symbol shift) | BOTH PASS — 217 < 251 saturation; per-symbol shifts non-trivial (BCH -5, LDO +2, TRX +11) |

Calibration accuracy: 4/4 process + behavioral-effect predictions clean; the model-prediction set (P4-P7) anticipated the PATH B verdict with appropriate probability mass per the brief's §7 prediction table. The new `feedback_v3_iter017_metalabeling_mandate.md` rule does NOT close a calibration gap (calibration discipline is intact for what was predicted) — it closes an axis-coverage gap (NEW labeling architecture is the unique untested category in the v3 axis priority hierarchy after iter-v3/016 closes the NEW model-architecture category at this configuration).

## Pareto Position

Single-row degenerate front (Section 8 criterion 9 waiver):

| seed | OOS Sharpe | OOS MaxDD | OOS Calmar | PBO | n_trades | max_conc% |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | +0.1710 | **40.62%** | 0.179 | 0.0889 | 112 | **+258.79%** (single-seed-degenerate) |

Cross-symbol OOS dispersion (informational, NOT Pareto-equivalent under EXPLORATION):

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| TRXUSDT | +18.82 | 49 | 46.9% | **+258.79%** (only profitable) |
| BCHUSDT | -2.35 | 44 | 31.8% | -32.37% |
| LDOUSDT | -9.19 | 19 | 31.6% | -126.42% |

The single-seed Pareto degeneracy (max_conc% = +258.79% from one symbol carrying the entire portfolio after others go negative) is an artifact, not Pareto-meaningful. Future CONFIRMATION QR scoping XGBoost would require multi-seed re-validation to assess concentration distribution.

## Next Iteration

**iter-v3/017 — axis: NEW labeling architecture (meta-labeling preferred per López de Prado AFML Ch. 3; fixed-horizon return labels as fallback)** per Critic FINAL Recommendation 1 of iter-v3/016 review (this diary's review SHA `9a558fc`) AND new memory rule `feedback_v3_iter017_metalabeling_mandate.md` MANDATORY pre-commit.

NEW labeling architecture is the unique untested category in the v3 axis priority hierarchy. After iter-v3/017 completes (regardless of outcome), cadence = 10/10 EXPLORATIONs since last CONFIRMATION → first CONFIRMATION can launch. Suggested specifics:

| Parameter | iter-v3/016 (current) | iter-v3/017 (mandated) |
|---|---:|---:|
| Universe | BCH+LDO+TRX (3 symbols) | UNCHANGED |
| Z-score OOD threshold | 2.0 | UNCHANGED |
| ATR multipliers | (2.0, 1.0) | UNCHANGED (or optional drop if M2 layer replaces triple-barrier entirely) |
| BTC trend filter band | ±15% | UNCHANGED |
| ADX threshold | 20.0 | UNCHANGED |
| Hurst (low, high) | (0.05, 0.95) | UNCHANGED |
| V3_FEATURE_COLUMNS count | 13 | UNCHANGED (13 — labeling change does not invalidate feature stack) |
| **Model architecture** | **XGBoost (this iteration)** | **LightGBM (restored default)** |
| **Labeling scheme** | **Triple-barrier (ATR 2.0/1.0, 21-candle timeout)** | **Meta-labeling (M2 binary classifier on M1 momentum/mean-reversion primary signal) — preferred; fixed-horizon return labels as fallback** |

**iter-v3/017 first commit pre-commits (per Critic FINAL Recommendations + QR Round 2 dispositions, cannot be renegotiated post-hoc)**:
- (a) Fix `_write_feature_importance` to aggregate across all walk-forward months (not last-month-only). Option A: modify `_train_for_month` to accumulate per-month importances, aggregate at report time. Option B: drop OOS importance CSV byte-duplication, rename IS CSV to `model_importance_last_month.csv` to clarify scope. Engineer chooses A or B at first-commit time.
- (b) Restore default `--model lgbm` (XGBoost remains opt-in via `--model xgboost`).
- (c) ITERATION_LABEL "v3-017".
- (d) Implement meta-labeling architecture per López de Prado AFML Ch. 3 (M1 = primary momentum/mean-reversion signal on the 13-feature stack; M2 = binary classifier predicting whether to act on M1's direction). Fixed-horizon labels as fallback if meta-labeling proves disproportionately complex.
- (e) Tighten saturation falsifier band to `[baseline_n_trades × 0.75, baseline_n_trades × 1.25]` (= [157, 261] for iter-v3/013 baseline 209) per Clarification 4.
- (f) Brief template §4.4 row 5 condition update: "either |Δ| ≥ 11 OR per-symbol shift > 5 trades on any symbol" per Clarification 1.

**Pre-conditions for iter-v3/017 brief**:
- Section 4 must be a single decision tree (not two parallel §4.3/§4.4 tables) — fix the brief template lesson from iter-v3/015.
- Section 7 prediction band must include explicit probability mass for "labeling-axis NEGATIVE-no-effect" outcome (M2 layer adds ~0 Sharpe vs M1-only triple-barrier baseline) AND "labeling-axis PROMISING" outcome (M2 layer lifts OOS Sharpe by ≥+0.30 by filtering false signals from M1).
- Pre-register an OOS-axis falsifier IF the brief intends to read OOS metrics (otherwise OOS remains informational-only).
- Single-axis discipline: ONLY labeling architecture changes. No other parameter variation. Restore-default-lgbm is baseline-restoration after iter-v3/016's closed NEGATIVE test, NOT a second axis.
- Wall-clock budget: same 2h hard cap, target < 30 min on 3-symbol universe at `--exploration --seeds 1 --n-trials 10`. Meta-labeling adds an M2 training step but at single-symbol-month granularity should add only ~50% wall-clock overhead.

**Catalog count after iter-v3/016**: **9 of 10** EXPLORATIONs; **1 more required** before any CONFIRMATION can launch. Axis coverage to date: features × 2 (007, 009) + labeling × 1 (010) + gate-zscore × 1 (011) + gate-btc-trend × 1 (012) + universe × 1 (013) + gate-adx × 1 CLOSED (014) + NEW feature family × 1 (015) + NEW model architecture × 1 CLOSED at tested config (016) = 8 unique axis representations after iter-v3/016. iter-v3/017 will add the NEW labeling architecture axis; after that, the catalog will have axis coverage = features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 1 + gate-adx × 1 (CLOSED) + NEW feature family × 1 + NEW model architecture × 1 (CLOSED-at-config) + NEW labeling architecture × 1 = 9 unique axis representations, satisfying the v3 cadence rule and unblocking first CONFIRMATION launch.

**iter-v3/016 status**: NOT a CONFIRMATION-bundle candidate. Model-architecture axis closed at the tested configuration (n_trials=10 + cross-entropy + depth-wise defaults); NOT closed for all XGBoost configurations. Future CONFIRMATION-bundling QR treats iter-v3/016 as a NEGATIVE-class data point that scopes XGBoost off-baseline; future iterations could re-introduce XGBoost in a Sharpe-objective Optuna or drawdown-penalized loss configuration without re-litigating iter-v3/016's NEGATIVE verdict. The 5 caveats from this diary travel with the catalog row to inform future bundling decisions.
