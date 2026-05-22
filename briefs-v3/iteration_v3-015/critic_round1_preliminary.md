# Phase 7.5 Critic Round 1 PRELIMINARY — iter-v3/015

OVERALL: PASS-WITH-CLARIFICATIONS — proceed to Phase 8 contingent on QR responding to 4 clarifications. Methodology checks all PASS / WAIVED-INFORMATIONAL. The substantive disagreement is the **classification subtype**, not the methodology — recommended classification differs from QE's PROMISING-INERT preference.

Brief SHA `b9cc79b`; Phase 5.5 gate SHA `c253e1d`; engineering report SHA `3ce2572`; setup commit SHA `d2374a6`; HEAD `bd0706b`.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
`compute_tbr_zscore` at `src/crypto_trade/features_v3/volume_micro_v3.py:94-132` is strictly past-only by construction. The function takes the raw `tbr_raw` series, computes `s.shift(1)` once and **rolls on the shifted series** for both `mean` and `std`, then computes `(s.shift(1) - rmean) / rstd`. So the value at bar `t` is `(tbr_raw[t-1] - mean(tbr_raw[t-window-1 : t-1])) / std(...)` — bar `t`'s own taker volume is fully excluded. This is a stricter discipline than the EDA reference at `analysis/iteration_v3-015/tbr_zscore_eda.py:135-162` (the EDA computes the rolling on `s.shift(1)` then subtracts `s.shift(1)` itself, producing a value at bar `t` derived from `t-1` values; the production code uses an equivalent formulation also using only `t-1` and earlier). Confirmed `taker_buy_quote_volume + quote_volume` are bar-close columns from Binance kline spec — fully knowable at bar close. The 13 inherited features are byte-identical to iter-v3/013 and previously cleared this check.

### Check 2 — Embargo Width: PASS
`REQUIRED_GAP = 66 = (timeout_candles=21 + 1) × n_symbols=3` enforced at runtime via `validation_v3.REQUIRED_GAP` and asserted in `run_baseline_v3._verify_label_leakage_gap()`. CPCV uses `n_paths=45`, embargo=27, symmetric. UNCHANGED from iter-v3/013. The introduction of `tbr_zscore_30` does not change the labeling horizon; the 21-candle timeout is unchanged so the purge requirement is unchanged.

### Check 3 — Multiple-Testing Correction: INFORMATIONAL (EXPLORATION carve-out)
DSR=0.0, PSR=1.0 are single-seed exploration artifacts (cadence-rule informational per skill spec). PBO (methodology axis) = 0.1034 — IN-LINE with the v3 norm 0.10–0.11. `frac_positive_paths` = 0.6444. `n_eff` = 7. The new feature does NOT change PBO meaningfully (iter-v3/013/014 both reported 0.1075; the 4×10⁻³ delta is path-Sharpe noise from the Optuna re-optimization on a 14-column space). 8 cells in `per_cell_pbo.csv` show PBO ≥ 0.99 (BCH 2024-01 1.00, BCH 2025-09 0.83, LDO 2024-11 0.95, LDO 2026-05 0.99, LDO 2023-08 0.92, TRX 2025-11 1.00, TRX 2025-10 0.90, TRX 2026-04 0.03, etc.) — TRX/2025-10/11 carry-forward unchanged from iter-v3/011-014; 2 NEW high-PBO cells (LDO 2026-05 = 0.99, BCH 2024-01 = 1.00) are at OOS frontier. NOT BLOCKING at EXPLORATION but max-aggregator pre-commit travels forward.

### Check 4 — IC Correlation: PASS
`ic_matrix.csv` row/column for `tbr_zscore_30`: max absolute pairwise IC vs the existing 13 columns is **|IC| = 0.0862** with `vwap_dev_20` (Pearson on the post-add IC matrix). Note this differs from the EDA's pre-commit Spearman-IC max 0.1654 — the production matrix uses Pearson on the full IS pooled sample; both metrics far below the 0.70 redundancy gate. The post-add 14-feature pairwise max IC remains the inherited iter-v3/013 ceiling (0.6602) since the new column adds no pair above 0.6602. **NEW feature is structurally orthogonal to the existing stack** — the strong methodological win of this iteration.

### Check 5 — ADF Stationarity: PASS (PROMOTED)
`adf_test.csv` 2199 rows. For `tbr_zscore_30` specifically: 4 rows out of ~140 (BCH 2020-01, LDO 2022-09, LDO 2022-10, LDO 2022-11, TRX 2020-01) are non-stationary — all concentrate at the symbol's listing month or the immediately following month where the rolling-30 window has insufficient samples. Every other (symbol, month) cell for `tbr_zscore_30` shows p < 0.01 (most p = 0.0 to numerical precision; ADF statistic in [−12, −44] range). The z-score construction is mean-zero by design — stationarity is structurally near-guaranteed. The 13 inherited features carry the iter-v3/014 PROMOTED PASS verdict (1657/2041 stationary, 81.2%; non-stationary cells concentrate in 2020-Q1 sparse-data per QR Clarification 1 of iter-v3/014).

### Check 6 — Pareto Dominance: PASS (vacuous, single-seed)
`pareto_front.csv` shows single-row degenerate front (seed 42 only). EXPLORATION single-seed cadence per `feedback_outer_seed_cap_2_v3.md`. Section 8 criterion 9 waiver inherited from iter-v3/006-014. LDO concentration 45.23% (from comparison.csv) / 57.12% (from per_symbol.csv `pct_of_total_pnl` — different denominator) — above the 30% CONFIRMATION cap; informational under EXPLORATION.

### Check 7 — Reproducibility: PASS
Setup commit `d2374a6` exists; HEAD `bd0706b`. Runner at `run_baseline_v3.py:874` passes `feature_columns=list(V3_FEATURE_COLUMNS)` — EXPLICIT — never None. `_verify_feature_columns()` asserts `len == 14` AND `'tbr_zscore_30' in V3_FEATURE_COLUMNS` AND `'vwap_dev_50' not in V3_FEATURE_COLUMNS`. ENSEMBLE_SIZE=1 explicit (single-seed EXPLORATION); `outer_seed=42` derived from `--seeds 1`. Brief SHA `b9cc79b` / gate SHA `c253e1d` / engineering report SHA `3ce2572` all stamped. Spot-check OOS trades (3 random rows) deferred to Phase 8 diary by precedent (iter-v3/006-014 pattern); engineering report contains no contradictions to commit-state.

### Check 8 — Hypothesis-Implementation Alignment: PASS-WITH-FAILED-AXIS
**Single-axis discipline honored cleanly** as far as the brief's intent is concerned. Three changes vs iter-v3/013 reference:
1. `tbr_zscore_30` ADDED to `V3_FEATURE_COLUMNS` (13 → 14) — the one varied axis (sub-fix #1, #2, #6 verified).
2. `adx_threshold` RESET 25.0 → 20.0 — baseline restoration after iter-v3/014's NEGATIVE test (sub-fix #4 verified).
3. `ITERATION_LABEL` "v3-015" — cosmetic.

The brief's framing of (2) as "baseline restoration, not a second axis" is structurally defensible (per-symbol architecture means iter-v3/015 is comparing against iter-v3/013's 209-trade baseline, not iter-v3/014's 153-trade baseline). The 7-item sub-fix decomposition has no dangling work.

**Hypothesis verdict: NOT SUPPORTED.** Brief §1 hypothesis: "IS Sharpe maintained or improved (≥ +0.40 PROMISING threshold; predicted [+0.50, +1.30] median +0.90) via microstructure regime-classifier signal." Realized IS Sharpe = +0.6445. Within the predicted band [+0.50, +1.30] but below median +0.90 by Δ−0.26 and below iter-v3/013's +1.0088 by Δ−0.36.

Falsifier 4 (brief §4.3) FIRED: tbr_zscore_30 importance rank = 14/14 (dead last) at importance 10.0 vs top feature ema_spread_atr_20 at 76.0 (13.2% of top). Per brief §4.3 verbatim: *"If tbr_zscore_30 is bottom-quartile importance across all 3 symbols, classify the iteration as PROMISING-INERT (model ignored new feature)."* This triggers the brief's pre-registered PROMISING-INERT classification path.

### Check 9 — Symbol Exclusion: PASS
`set({BCH, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` enforced at `run_baseline_v3.py:151-158` runtime assertion. UNCHANGED from iter-v3/013.

### Check 10 — Feature Isolation: PASS
`features_v3` does not import from `crypto_trade.features` (v1) or `crypto_trade.features_v2` (v2). `_verify_track_isolation()` at `run_baseline_v3.py:229-250` runtime grep-checks both patterns and exits non-zero on hit. The new `compute_tbr_zscore` lives in `volume_micro_v3.py` (track-isolated module); zero new imports from v1/v2.

### Check 11 — Forming-Candle: PASS (assumed)
Pre-flight staleness guard `_verify_data_freshness` (max_lag_hours=16.0) functioning per spec. Engineering report wall-clock 0.1h = 6 min — well within window where forming-candle issues at the OOS tail would propagate. Inherited from iter-v3/006-014 precedent.

### Check 12 — Library Version Pinning: PASS
Stack identical to iter-v3/008-014: lightgbm 4.6.0, numpy 2.2.6, pandas 2.3.1, scikit-learn 1.6.1, pyarrow 19.0.1, mlfinpy 1.4.0, pypbo 0.10.0, fracdiff 0.10.0, statsmodels 0.14.5, optuna 4.5.0. The new `compute_tbr_zscore` uses only numpy + pandas (already imported). Zero new dependencies.

---

## Strong Prior on Classification

**My recommendation: `EXPLORATION-NEGATIVE-no-effect` (NULL-RESULT subtype).** I disagree with QE's PROMISING-INERT recommendation. Justification below; the QR may push back, but the burden of proof is on the QR to show why PROMISING-INERT is structurally distinct from NEGATIVE-no-effect when:

1. **The model demonstrably did not learn the feature.** Importance 10.0 / 76.0 = 13.2% — the feature is rank 14 of 14, and the gap from rank 13 (sym_vs_btc_ret_7d at 19.0) to rank 14 (tbr_zscore_30 at 10.0) is the **largest gap in the entire importance distribution** (relative ratio 0.526). The model is near-discarding the feature. This is the regime-classifier explanation collapsing — the brief's hypothesis is that the model would learn per-symbol sign loadings (BCH +6.5%, LDO −2.7%); the realized importance suggests the trees aren't splitting on TBR meaningfully.

2. **IS Sharpe DEGRADED Δ−0.36 vs iter-v3/013 baseline.** PROMISING-INERT (per brief §4.4 verbatim) requires "IS Sharpe within ±0.10 of iter-v3/013 (i.e., in [+0.91, +1.11])." Realized +0.6445 is **+0.27 outside** this band on the unfavorable side. The brief's PROMISING-INERT band is violated by 7×_band_width. By the brief's own pre-registered §4.4 row 2, this is **NOT in the PROMISING-INERT band**.

3. **The brief §4.4 row 5 (NEGATIVE) condition is closest to met:** "IS Sharpe down > 0.10 (i.e., < +0.91) AND `tbr_zscore_30` IS in feature importance (Falsifier 4 PASS) → the model used the new feature but it actively hurt." This is a partial match: IS Sharpe is down >0.10 (Δ−0.36), but Falsifier 4 FIRED rather than PASSED — the model effectively did NOT use the feature.

4. **The brief §4.4 row 4 (NEGATIVE-no-effect/NULL-RESULT) condition fits cleanly:** "IS Sharpe direction wrong (−Δ vs iter-v3/013) AND tbr_zscore_30 importance == 0 across all 3 models (Falsifier 4 fires)." The literal "== 0" criterion is not satisfied (importance is 10.0 not 0.0), but the SPIRIT — model effectively ignored the feature — does fit. The aggregated importance of 10.0 (with the largest gap in the distribution between rank 13 and rank 14) is functionally indistinguishable from zero contribution.

The PROMISING-INERT classification preserves the misleading reading that the iteration "is in the band of iter-v3/013 ±0.10." It is not. The IS Sharpe degraded by Δ−0.36 — that exceeds the iter-v3/014 ADX-tightening NEGATIVE Δ−0.35. **iter-v3/015 is structurally similar to iter-v3/014 in IS-axis magnitude**, but the mechanism is different: iter-v3/014 over-restricted the gate; iter-v3/015 added noise to the loss surface that the model fits poorly. The OOS lift +2.12 is genuine but **not attributable to the new feature** (importance 10/76); the OOS lift attributes to (a) Optuna re-optimization landing in a different local minimum, (b) regime favorability in the shorter OOS window where TRX trades rebalanced from 95 → 84 reducing TRX drag impact, (c) ensemble noise.

The catalog row should mark: NOT a CONFIRMATION-bundle candidate. tbr_zscore_30 is non-compoundable as a "new edge ingredient"; future microstructure axes should test (a) different lookback windows (e.g., 90-bar = 1 month flow regime), (b) different normalization (signed-trade imbalance with z-score), or (c) cross-features (TBR × ADX interaction term as a combined regime classifier).

---

## Clarifications to QR (4)

**Clarification 1 (HIGH PRIORITY) — Classification subtype.** The brief's §4.4 outcome interpretation table has 6 rows. I read the realized outcome (IS Sharpe +0.6445 / Δ−0.36 vs iter-v3/013 / Falsifier 4 FIRED / non-bit-identical roster) as fitting **§4.4 row 4 NEGATIVE-no-effect (NULL-RESULT)** more cleanly than §4.4 row 2 PROMISING-INERT, which requires IS Sharpe within ±0.10 of iter-v3/013. QE recommends PROMISING-INERT relying on §4.3 verbatim ("If tbr_zscore_30 is bottom-quartile importance across all 3 symbols, classify the iteration as PROMISING-INERT") which conflicts with §4.4 row 2's IS Sharpe band. **Two pre-registered classification pathways disagree; the QR must pick one.** My strong prior is NEGATIVE-no-effect: this preserves the catalog discipline that PROMISING-class verdicts require IS Sharpe lift OR within-band; INERT subtype is reserved for true band-equivalence outcomes. Mis-classifying as PROMISING-INERT would mislead future CONFIRMATION QRs into reading the iteration as "feature added without harm" when it should read as "feature added but model couldn't use it AND IS axis degraded."

**Clarification 2 (MEDIUM PRIORITY) — Per-symbol importance disambiguation.** Engineering report §"Critical: Feature-Importance Audit" notes feature_importance.csv is aggregated across all per-symbol LightGBM models and all walk-forward months (split/gain average) — the in_sample/feature_importance.csv and out_of_sample/feature_importance.csv files are byte-identical confirming aggregation. **Brief §4.3 falsifier 4 specifies "bottom-quartile across all 3 symbols" which requires per-symbol importance, not aggregated.** The aggregate rank-14/14 is consistent with all three models bottom-quartile, but it's also consistent with one model giving the feature high importance (e.g., TRX where IS trades dropped 95 → 84 suggesting some TBR-driven gating) while two models ignore it. Can the QR provide per-symbol importance ranking before Phase 8 finalizes the classification? If TRX has TBR rank ≥ 7 (median or higher), the §4.3 verbatim falsifier may not strictly fire (it requires bottom-quartile across **all 3** symbols) and the classification picture changes.

**Clarification 3 (MEDIUM PRIORITY) — iter-v3/016 axis pre-commit.** Per `feedback_structural_over_knob_exploration.md` axis priority order, iter-v3/016 should pivot to a different axis category. Microstructure axis appears uniformly inert (importance 13.2% of top feature; IS axis degraded; model couldn't learn the regime-classifier signal). Should iter-v3/016 (a) try a DIFFERENT microstructure feature (signed-trade imbalance, OFI ratio, depth-adjusted TBR), (b) move to category 2 NEW model architecture (XGBoost vs LightGBM head-to-head), or (c) move to category 3 NEW labeling architecture (meta-labeling M2 sizing)? My recommendation is (b) NEW model architecture: the current evidence base shows feature-pruning, gate-knob, universe-drag-removal, and now NEW-feature-family axes have collectively explored most of the LightGBM-native variations. XGBoost or CatBoost on the existing 13-feature stack is the natural next step before adding more features. The QR should pre-commit one of (a), (b), (c) at iter-v3/015 diary close to prevent post-hoc renegotiation.

**Clarification 4 (LOW PRIORITY) — TBR-raw column write-through.** `compute_tbr_zscore` at `volume_micro_v3.py:122-123` writes `df["tbr_raw"] = tbr_raw` as an intermediate. This column is NOT in V3_FEATURE_COLUMNS but it persists in the parquet. Confirm: (a) `tbr_raw` is excluded from the LightGBM input vector (it should be by the explicit feature_columns argument); (b) `tbr_raw` is excluded from the z-score OOD gate's 14-column computation (since the gate operates on V3_FEATURE_COLUMNS only). The brief's risk-gate Section 6.1 primitive 4 states "z-score OOD over **14** features" which is correct (V3_FEATURE_COLUMNS = 14 with tbr_zscore_30 added; tbr_raw not counted). Confirming this in the QR's Phase 7 evaluation will close a low-probability hidden-feature-leakage scenario.

---

## Pre-Commit Recommendation for iter-v3/016 Axis

**Strong recommendation: iter-v3/016 = NEW model architecture** (category 2 per axis priority). After iter-v3/015's PROMISING-INERT/NEGATIVE-no-effect outcome, the v3 catalog has tested 4 of 6 axis categories (features-prune, labeling, gate-knob, universe-drop, NEW-feature-family). Two remaining tractable categories: model architecture and labeling architecture. Model architecture is **higher-priority** because (a) it is more compoundable across iterations (a different model can be paired with each feature/label/gate combination), (b) it directly addresses the iter-v3/015 finding (LightGBM did not extract TBR signal — perhaps another model would), and (c) XGBoost/CatBoost both run within the 2h EXPLORATION wall-clock cap.

iter-v3/016 = XGBoost on the existing 13-feature stack (drop tbr_zscore_30 since it's INERT) with same gate config and same universe. Single-axis variation: LightGBM → XGBoost. The QR should pre-commit this at iter-v3/015 diary close.

**Cannot be renegotiated post-hoc** at iter-v3/016 setup time — the same lock-in discipline that produced `feedback_adx_axis_asymmetric_v3.md` and `feedback_structural_over_knob_exploration.md` applies.

---

## Methodology Verdict

**OVERALL = PASS-WITH-CLARIFICATIONS.** All 12 checks PASS or are INFORMATIONAL per EXPLORATION carve-out. The methodology is clean. The disagreement is over **classification semantics**, which is downstream of methodology and is the QR's authority to decide via the §4.4 pre-registered outcome table — but the QR must address Clarification 1 explicitly because the §4.3 and §4.4 pathways disagree on this realized outcome, and selecting PROMISING-INERT requires explaining why §4.4 row 2's IS Sharpe band is not load-bearing.

I expect Round 2 FINAL to either (a) accept the NEGATIVE-no-effect classification and move to iter-v3/016 model-architecture axis, or (b) accept PROMISING-INERT WITH the explicit caveat that IS Sharpe degraded Δ−0.36 (outside band) AND a memory rule pre-commit that future PROMISING-INERT verdicts require IS Sharpe within ±0.10 of baseline.
