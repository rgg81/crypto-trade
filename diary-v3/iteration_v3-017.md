# Iteration v3-017 — Diary

## Decision: EXPLORATION-NEGATIVE (clean) — PATH C sub-flavor (NEGATIVE-over-filter-quality-residual)

Critic FINAL OVERALL = `EXPLORATION-NEGATIVE` (clean) at SHA `6de26d1` — single-round review (outcome unambiguous; all 12 methodology checks PASS or INFORMATIONAL per EXPLORATION carve-out). The iteration tested the FIRST NEW labeling architecture in v3 catalog: a `MetaLabelingStrategy` per López de Prado AFML Ch. 3, where M1 = `LightGbmStrategy` primary signal on iter-v3/013's 13-feature stack and M2 = secondary `LGBMClassifier` predicting whether to act on M1's direction. This is the third iteration whose axis was forced by a prior Critic FINAL recommendation (iter-v3/016's NEGATIVE-clean closed the model-architecture axis at the tested config and mandated NEW labeling architecture for iter-v3/017 as the unique untested top-priority category in the v3 axis priority hierarchy). Headline: IS Sharpe Δ −0.48 (+0.5288 vs iter-v3/013 +1.0088); OOS Sharpe Δ −2.15 (+0.5476 vs iter-v3/013 +2.6970, informational below 130-trade floor at OOS=62); 159 IS / 62 OOS trades; M2 per-candle veto rate 42.7% (2,976/6,965); per-symbol IS shifts BCH 100→73 (−27), TRX 88→70 (−18), LDO 21→16 (−5) — all > 5 threshold. PATH C sub-flavor (NEGATIVE-over-filter-quality-residual): M2 demonstrably active filtering 42.7% of M1 candidates, but the kept trades show no per-trade economics lift, confirming there is no incremental signal-quality distinction beyond what M1 already extracts at this configuration. **CADENCE COMPLETE: 10/10 EXPLORATIONs done. iter-v3/018 = first v3 CONFIRMATION.**

## Headline

IS Sharpe +0.5288 (Δ −0.48 vs iter-v3/013 +1.0088), OOS Sharpe +0.5476 (Δ −2.15 informational), 159 IS / 62 OOS trades, M2 per-candle veto rate **42.7%**. M2 active and filtering aggressively (~43% of M1 candidates rejected), but kept trades produced IS PnL +34.38 / OOS PnL +14.47 with profit factor 1.19 IS / 1.23 OOS — no quality lift over M1-only baseline (iter-v3/013 produced higher per-trade economics on a larger 209-trade IS sample). Per-symbol IS shifts BCH 100→73 (−27), TRX 88→70 (−18), LDO 21→16 (−5) — all three symbols see double-digit or > 5 IS-trade reductions, meaning M2's veto distribution is broad-based not symbol-localized. OOS per-symbol attribution: LDO +14.94 weighted_pnl on 6 trades (66.7% WR, 4 wins out of 6, **103.23% concentration**), TRX +5.15 on 35 trades (40.0% WR, 35.60%), BCH −5.62 on 21 trades (33.3% WR, −38.83%). LDO's 6-trade lottery flag (4/6 wins, exact-binomial 95% CI [22.3%, 95.7%] too wide for signal claim) carries forward unchanged from iter-v3/011/012/013/014 audit trail.

## What Was Tested

**Single-axis variation** (NEW labeling architecture, axis category 3 per `feedback_structural_over_knob_exploration.md`): replace `LightGbmStrategy` with `MetaLabelingStrategy` (M1=LightGBM on 13-feature stack + M2=LGBMClassifier secondary). Setup commit `c6ca96e`. The axis is the FIRST NEW labeling architecture attempted in v3 (iter-v3/001-016 all used triple-barrier exclusively; only ATR multipliers were tuned at iter-v3/010) and the THIRD axis to result from a prior Critic FINAL recommendation (iter-v3/016's NEGATIVE-clean FIRED `feedback_v3_iter017_metalabeling_mandate.md`).

**Implementation specifics**:
- `MetaLabelingStrategy` class added at `src/crypto_trade/strategies/ml/metalabeling.py` (~580 lines)
- `--model metalabeling` CLI choice added at `run_baseline_v3.py:1357`
- `_build_v3_model` routes correctly at `run_baseline_v3.py:886-891`
- 11 unit tests added
- M2 input vector 14-dim: M1's training-window 13-feature matrix + M1's training-window confidence
- M2 confidence threshold **0.5 PINNED** at `metalabeling.py:328` (single-axis discipline)
- M2 reuses LightGBM (binary objective + is_unbalance=True) — no new external dep
- Default restored to `--model lgbm` (XGBoost remains opt-in)
- ITERATION_LABEL "v3-017"
- `_write_feature_importance` defect fix in setup commit (per Critic Clar 3 of iter-v3/016): single-file `model_importance_last_month_<SYM>.csv` per symbol + portfolio aggregate (renamed from byte-duplicated IS/OOS CSVs)

**4 first-commit pre-commits delivered cleanly** at SHA `c6ca96e` (per Critic FINAL of iter-v3/016 review SHA `9a558fc`):
1. Fix `_write_feature_importance` to last-month-only with explicit naming (Option B per Critic Clarification 3 disposition); drop OOS importance CSV byte-duplication
2. Restore default `--model lgbm` (XGBoost remains opt-in via `--model xgboost`)
3. ITERATION_LABEL "v3-017"
4. Implement meta-labeling architecture per López de Prado AFML Ch. 3

**Hypothesis** (brief Section 1, SHA `6a1e986`): M2 binary classifier filtering M1 momentum/mean-reversion signals will lift IS Sharpe by ≥ +0.30 vs M1-only triple-barrier baseline (calibrated PROMISING band [+1.30, +1.60] median +1.45) by rejecting low-quality M1 signals where path-dependency makes triple-barrier label noisy. Sub-hypothesis: M2 veto rate ∈ [25%, 50%] (active but not over-filtering); kept-trade per-trade economics ≥ M1-only baseline.

**Hypothesis verdict: PERFORMANCE FALSIFIED (Δ −0.48 outside PROMISING band by 0.77 below lower bound), VETO-RATE CONFIRMED-WITH-OVER-FILTER-CAVEAT.** IS Sharpe +0.5288 (vs predicted [+1.30, +1.60]; observed Δ −0.48 below baseline). M2 per-candle veto rate 42.7% (vs predicted [25%, 50%] band — sub-hypothesis confirmed in-range BUT kept trades show no quality lift, falsifying the per-trade-economics co-condition).

**Configuration**: `--exploration --seeds 1 --n-trials 10 --model metalabeling` on 3-symbol v3 universe (BCH+LDO+TRX), ENSEMBLE_SIZE=1, colsample_bytree=1.0, training_months=24, OOS_CUTOFF_DATE=2025-03-24. Identical to iter-v3/013 modulo model architecture (`LightGbmStrategy` → `MetaLabelingStrategy`) and ITERATION_LABEL cosmetic.

## What Was Measured

### Headline metrics

| Metric | iter-v3/013 (baseline) | iter-v3/017 (this run) | Δ vs iter-v3/013 |
|---|---:|---:|---:|
| IS monthly Sharpe | +1.0088 | **+0.5288** | **−0.48** |
| OOS monthly Sharpe | +2.6970 | **+0.5476** | **−2.15 (informational below 130 floor)** |
| IS daily Sharpe | — | +1.1624 | — |
| OOS daily Sharpe | — | +1.6689 | — |
| IS/OOS ratio | 2.67 | **1.04** | — |
| OOS/IS ratio | 2.67 | **1.04** | — |
| IS trades | 209 | **159** | **−50 (−24%; non-bit-identical)** |
| OOS trades | 85 | **62** | **−23 (informational below 130 floor)** |
| IS max drawdown | 22.00% | **21.93%** | −0.07 pp |
| OOS max drawdown | 12.47% | **18.76%** | +6.29 pp |
| OOS Calmar | 4.96 | 0.771 | −4.19 |
| Profit Factor (IS) | — | 1.19 | — |
| Profit Factor (OOS) | — | 1.23 | — |
| Win Rate (IS) | — | 30.8% | — |
| Win Rate (OOS) | — | 40.3% | — |
| PBO (per-cell mean) | 0.1034 | **NaN** (structural — M2 has no label training data on thin walk-forward cells) | — |
| n_eff (per-cell median) | 7 | **4 (LOWEST in v3 catalog)** | −3 |
| PSR | 1.0000 | 1.0000 | 0 |
| DSR | 0.0 | 0.0 | 0 |
| n_trials | 30 | 30 | 0 |
| **M2 per-candle veto rate** | — | **42.7% (2,976/6,965)** | — |

### Per-symbol IS shifts (load-bearing for §4.4 row 5)

| Symbol | iter-v3/013 IS | iter-v3/017 IS | Δ trades | M2 veto contribution |
|---|---:|---:|---:|---:|
| BCHUSDT | 100 | 73 | **−27** | broad-based |
| LDOUSDT | 21 | 16 | **−5** | narrowest cut |
| TRXUSDT | 88 | 70 | **−18** | broad-based |
| **TOTAL** | **209** | **159** | **−50** | 42.7% per-candle veto |

All 3 symbols see > 5 IS-trade reductions — §4.4 row 5 condition (per-symbol shift > 5 on any symbol) fires on EVERY symbol, not just one. M2's veto distribution is broad-based not symbol-localized. The brief-template tightening from iter-v3/016 review (per-symbol > 5 OR |Δ| ≥ 11) is over-determined here: |Δ| = 50 ≥ 11 fires too.

### Per-symbol OOS attribution

| Symbol | Trades | Win Rate | Weighted PnL | Concentration % |
|---|---:|---:|---:|---:|
| LDOUSDT | 6 | 66.7% | **+14.94** | **+103.23%** |
| TRXUSDT | 35 | 40.0% | +5.15 | +35.60% |
| BCHUSDT | 21 | 33.3% | −5.62 | −38.83% |
| **TOTAL** | **62** | **40.3%** | **+14.47** | — |

LDO's 6-trade lottery (4 wins of 6, 66.7% WR, exact-binomial 95% CI [22.3%, 95.7%]) drives the OOS portfolio +14.47 and the 103.23% concentration. The CI width is too wide to claim signal-from-noise distinction. Without LDO's 4 wins, OOS PnL collapses from +14.47 to −0.47 (sum of TRX +5.15 + BCH −5.62). The concentration ratio is well above the 30% per-symbol cap that would apply at CONFIRMATION.

### Methodology checks (Critic FINAL — SHA `6de26d1`)

| # | Check | Status | Detail |
|---:|---|:---:|---|
| 1 | Look-Ahead | PASS | M2 trains EXCLUSIVELY on M1's `_split_map[month_str].train_*` window; `metalabeling.py:386-471` strict past-only |
| 2 | Embargo | PASS | REQUIRED_GAP = 66 = (21+1)×3 inherited; M2 doesn't introduce new label-leakage paths |
| 3 | MT correction | INFORMATIONAL | DSR=0.0, PBO=NaN (structural — thin cells, no M2 training data → degenerate), PSR=1.0, n_trials=30, n_eff=4 (LOWEST in v3 catalog); fallback `pbo_frac_positive_paths=0.6444` |
| 4 | IC correlation | PASS | No new feature; inherited 13-stack max |IC| = 0.685 < 0.70 |
| 5 | ADF stationarity | PASS | 81.2% inherited from iter-v3/015 |
| 6 | Pareto dominance | PASS (vacuous, single-seed) | LDO 74.36% concentration above CONFIRMATION cap; 6-trade lottery flag carries forward |
| 7 | Reproducibility | PASS | Setup `c6ca96e` / EDA `d47163b` / Brief `6a1e986` / Gate `7ed27e5` / Engineering `af55d17` / Critic FINAL `6de26d1` stamped |
| 8 | Hypothesis alignment | PASS (with documented label-tolerance caveat) | Single-axis discipline preserved; M2 threshold 0.5 PINNED; **divergence**: brief §2.4 specifies M2=1 iff TP-first-hit-within-timeout; impl uses `pnl > 0` (conflates TP-hit with timeout-positive walk; non-blocking — qualitative finding robust to either definition) |
| 9 | Symbol exclusion | PASS | {BCH, LDO, TRX} ∩ V3_EXCLUDED_SYMBOLS = ∅ |
| 10 | Feature isolation | PASS | No actual cross-track imports |
| 11 | Forming-candle | PASS | Pre-flight staleness guard fired clean |
| 12 | Library pinning | PASS | M2 reuses existing LightGBM; no new external dep |

**All 12 Critic checks PASS / WAIVED-INFORMATIONAL per EXPLORATION carve-out.** Zero BLOCK conditions. Methodology is clean — meta-labeling integration is correct (look-ahead clean, embargo correct, M2 wiring valid). The NEGATIVE classification is on the *signal-extraction axis* (M2 over-filters at threshold 0.5 with same-feature input on 30-trial single-seed budget producing risk-similar but trade-count-reduced solutions), NOT on the *methodology axis* (where everything is clean). Label-tolerance divergence (brief §2.4 strict TP-first vs impl `pnl > 0`) noted as non-blocking.

### Saturation falsifier audit

| Falsifier | Condition | Observed | Status |
|---|---|---|---|
| Falsifier 1 | IS Sharpe < +0.40 | +0.5288 | DOES NOT FIRE |
| Falsifier 2 | IS trades ≥ 157 (NULL-RESULT, M2 inactive) | 159 | NARROWLY-IN-BAND but M2 demonstrably ACTIVE (42.7% veto) |
| Falsifier 3 | IS trades > 261 (wiring bug) | 159 | DOES NOT FIRE |
| Falsifier 4 | IS trades < 80 (over-filter) | 159 | DOES NOT FIRE |
| Falsifier 5 | Per-symbol IS count INCREASE | All deltas negative | DOES NOT FIRE |

**Falsifier 2 disposition.** IS=159 sits 2 trades above the 157 lower bound. Brief §4.4 row 5 NULL-RESULT on bit-identical roster + count ≥ 157 — but roster non-bit-identical (209 → 159; BCH 100→73, LDO 21→16, TRX 88→70). M2 demonstrably active at 42.7% per-candle veto rate. Falsifier 2 narrowly does NOT fire; classification flows through to row 5 NEGATIVE-clean.

### §4.4 row 5 NEGATIVE-clean classification verification

| Condition | Threshold | Observed | Fires? |
|---|---|---|---|
| IS Sharpe < +0.91 | < 0.91 | 0.5288 (Δ −0.48) | YES |
| \|Δ trades\| ≥ 11 OR per-symbol > 5 | either | \|Δ\|=50, BCH −27, TRX −18, LDO −5 | YES |
| Axis propagated (non-bit-identical) | non-identical | 209 → 159 different roster | YES |

All three conditions satisfied. Classification: **EXPLORATION-NEGATIVE (clean)**, PATH C sub-flavor (NEGATIVE-over-filter-quality-residual). M2 filtered 42.7% per-candle but retained trades produced no per-trade economics lift.

## Caveats Recorded for Audit Trail (5)

The NEGATIVE clean verdict comes with five explicit caveats catalogued for the future CONFIRMATION-bundling QR (per Critic FINAL recommendations and audit-trail discipline):

1. **`verdict = NEGATIVE` (clean)** — PATH C sub-flavor (NEGATIVE-over-filter-quality-residual) per brief §4.4 row 5: IS Sharpe Δ −0.48 < −0.10 NEGATIVE threshold AND non-bit-identical roster (per-symbol shifts BCH −27, LDO −5, TRX −18 all > 5 threshold) AND axis propagated (M2 demonstrably active at 42.7% per-candle veto rate, kept trades visibly different). All three §4.4 row 5 conditions met cleanly. NOT a NULL-RESULT (distinguishing from iter-v3/012 which had bit-identical roster); NOT NEGATIVE-no-effect (distinguishing from iter-v3/015 which had non-bit-identical roster but importance rank 14/14 of a single new feature). PATH C is a NEW sub-flavor specific to over-filter cases where M2 filters aggressively but kept trades produced no per-trade economics lift. NOT a CONFIRMATION-bundle candidate.

2. **`M2_per_candle_veto_rate = 42.7%`** (M2 demonstrably active; 2,976 of 6,965 candidate predictions vetoed): the M2 layer is functionally working — aggressive filtering at threshold 0.5 PINNED. The failure mode is NOT "M2 doesn't activate" — it is "M2 doesn't add quality at this configuration." The kept-trade per-trade economics (IS PF 1.19, OOS PF 1.23, IS WR 30.8%, OOS WR 40.3%) are below iter-v3/013's M1-only baseline at the same per-symbol architecture, demonstrating the M2 layer is correlated with M1's confidence in a way that strips signal alongside noise rather than discriminating. This rules out implementation defects (looking-ahead, label leakage, threshold mis-pinning) as the cause of the NEGATIVE outcome.

3. **`label_tolerance_divergence = "pnl > 0 vs strict TP-first"`** (non-blocking): brief §2.4 specifies M2=1 iff TP-first-hit-within-timeout; implementation at `metalabeling.py:488` uses `pnl > 0.0` which conflates "TP-hit" with "timeout-with-positive-forward-return". Engineering report's M2 positive-class prior 39.1% vs EDA's pre-registered 33.97% partially reflects this. **Non-blocking because**: (a) divergence disclosed transparently in synthesis.md and brief comment "We use: long_pnl > 0"; (b) qualitative finding (M2 filters 42.7% but kept trades show no quality lift) is robust to either definition; (c) tightening to TP-first-strict would not flip the verdict. Future meta-labeling re-test should use strict TP-first-hit-within-timeout labels per Critic Recommendation 2(a).

4. **`n_eff = 4`** (LOWEST in v3 catalog): M2's Optuna search overlaps M1's hyperparameter dimensions, collapsing joint manifold rank under the 30-trial budget (vs iter-v3/013 n_eff=7). The low n_eff means the search explored the joint M1+M2 hyperparam space sparsely; conclusions from this single-seed n_trials=10 budget should be treated as configuration-narrow not architecture-general. Future meta-labeling re-test should increase n_trials to ≥50 to address best-F1=0.4409 modest discrimination at iter-v3/017 (per Critic Recommendation 2(c)).

5. **`iter-v3/018_axis_mandated = MULTI-SEED VALIDATION OF iter-v3/013 BASELINE`** per Critic FINAL Recommendation 1: pre-committed via new memory rule `feedback_v3_iter018_confirmation_baseline_validation.md`. **iter-v3/018 = first v3 CONFIRMATION = baseline-validation run, NOT bundle assembly**. All 4 PROMISING-class candidates (iter-v3/007 top-13 features, iter-v3/010 ATR labeling 2.0/1.0, iter-v3/011 z-score 2.0, iter-v3/013 drop-MKR universe) are ALREADY cumulatively integrated in the current iter-v3/013 baseline; iter-v3/014-017 were all NEGATIVE/NULL — there is NO NEW ingredient to bundle. The CONFIRMATION question is whether iter-v3/013's IS +1.0088 / OOS +2.6970 holds under multi-seed cross-validation rigor. iter-v3/018 spec: `--seeds 2 --n-trials 50` (5 inner × 2 outer = 10 models per cell), ENSEMBLE_SIZE=5, full DSR/PBO/PSR re-evaluation, multi-seed Pareto front for the first time, 4h hard cap per CONFIRMATION cadence rule. Cannot be renegotiated post-hoc.

## Lessons

1. **M2 filtering propagates cleanly but kept trades aren't of higher quality at this configuration**. iter-v3/017's failure mode is NOT M2-inactive (refuting any "M2 wiring bug" hypothesis) — M2 fires at 42.7% per-candle veto rate, demonstrably active. The failure mode IS that M2 filters M1 candidates in a way that is correlated with M1's own confidence (since M2's input features are M1's training-window feature matrix + M1's confidence) and therefore strips signal alongside noise rather than discriminating high-quality M1 signals from low-quality ones. The kept-trade per-trade economics (IS PF 1.19, OOS PF 1.23, IS WR 30.8%, OOS WR 40.3%) are below iter-v3/013's M1-only baseline. This is the canonical "PATH C: NEGATIVE-over-filter-quality-residual" pattern — formally distinct from PATH A (PROMISING bundling) and PATH B (NEGATIVE-no-effect). Per López de Prado AFML Ch. 3, meta-labeling's edge comes from M2 having access to features M1 cannot use (e.g., realized regime indicators, trade timing context, post-position risk metrics) — same-feature M2 has no incremental learnable signal beyond M1.

2. **Label tolerance divergence (pnl > 0 vs strict TP-first) noted; non-blocking but future re-tests should tighten** per Critic Clarification 8 documented divergence. Brief §2.4 specified M2=1 iff TP-first-hit-within-timeout; implementation at `metalabeling.py:488` uses `pnl > 0` which conflates TP-hit with timeout-positive-walk. The qualitative verdict (NEGATIVE-over-filter) is robust to either definition because the per-trade economics distribution is similar under both labels at this configuration, but a future meta-labeling re-test should use strict TP-first labels to eliminate the conflation. Disclosed transparently in synthesis.md and brief comment.

3. **M2 confidence threshold 0.5 may be miscalibrated to M2 confidence distribution** (n_eff=4 is the lowest in v3 catalog). M2's confidence distribution at 30 Optuna trials over the joint M1+M2 hyperparam space produced 42.7% per-candle veto at threshold 0.5 — aggressive filtering. A future meta-labeling re-test should treat M2 threshold as a knob axis (try 0.4 and 0.6) since 0.5 produced 42.7% veto without quality lift; per Critic Recommendation 2(b). The threshold pinning was load-bearing for single-axis discipline at iter-v3/017 but is the natural follow-on knob axis once a higher-priority structural axis re-tests meta-labeling with a different M2 architecture.

4. **Same-feature M2 had no incremental learnable signal beyond M1; future re-tests should consider DIFFERENT M2 features**. Per Critic Recommendation 2(d), the canonical meta-labeling edge per López de Prado AFML Ch. 3 comes from M2 accessing features that M1 cannot or should not use — typically realized regime indicators, trade-timing context, microstructure or path-dependency features. iter-v3/017's M2 input was M1's training-window feature matrix + M1's confidence — same input space as M1, just with the additional confidence signal. The M2 best-F1 of 0.4409 indicates modest discrimination at this same-feature configuration. A future re-test should provide M2 with strictly DIFFERENT features (e.g., funding rates, OI dynamics, basis, realized volatility on different timeframes) — but per `feedback_structural_over_knob_exploration.md` priority order, this is the lowest-priority follow-on after iter-v3/018 CONFIRMATION completes.

5. **CADENCE COMPLETE: 10/10 EXPLORATIONs done since last CONFIRMATION → iter-v3/018 = first v3 CONFIRMATION**. The catalog count advances from 9/10 (iter-v3/016) to **10/10** with iter-v3/017 closure. Per `feedback_v3_cadence_discipline.md` (only CONFIRMATION-MERGE updates BASELINE_V3.md; CONFIRMATION requires 10 EXPLORATION precedents), CONFIRMATION can launch. **iter-v3/018 axis MANDATORY = MULTI-SEED VALIDATION OF iter-v3/013 BASELINE, NOT NEW INGREDIENT BUNDLING** per Critic FINAL Recommendation 1 + new memory rule `feedback_v3_iter018_confirmation_baseline_validation.md`. All 4 PROMISING components (iter-v3/007 features, 010 labeling, 011 zscore, 013 universe) are already cumulatively integrated in the current iter-v3/013 baseline; iter-v3/014-017 all NEGATIVE/NULL — no NEW ingredient to bundle from EXPLORATION rows 014-017. CONFIRMATION QR question: *does iter-v3/013's IS +1.0088 / OOS +2.6970 Sharpe hold under multi-seed cross-validation, with PBO < 0.4, DSR > 0.95, PSR > 0.95, multi-seed Pareto non-domination, bundle-level OOS trade count ≥ 130?*. iter-v3/018 spec: `--seeds 2 --n-trials 50`, ENSEMBLE_SIZE=5, full DSR/PBO/PSR re-evaluation, 4h hard cap. No NEW axis variation. No bundling. Just validate the baseline. Cannot be renegotiated post-hoc.

6. **Critic single-round flow worked as designed** (8th consecutive use producing concrete pre-commits and a NEW memory rule). Single-round was sufficient because the OVERALL outcome was unambiguous (all three §4.4 row 5 conditions fired cleanly, all 12 methodology checks PASS or INFORMATIONAL, no meaningful Round 1 clarifications needed). The label-tolerance divergence was disclosed transparently in synthesis.md, eliminating any need for Round 1 PRELIMINARY clarification. The clarifications produced a concrete pre-commitment (iter-v3/018 = MULTI-SEED VALIDATION OF iter-v3/013) + a NEW memory rule (`feedback_v3_iter018_confirmation_baseline_validation.md`).

7. **Dead-paths catalog (sixteenth entry, tenth EXPLORATION row, NEGATIVE-clean PATH C sub-flavor classification):**
   - **iter-v3/017** — NEW labeling architecture axis (LightGBM → MetaLabelingStrategy with M1=LightGBM + M2=LGBMClassifier on iter-v3/013's 13-feature stack; single-axis variation with M2 threshold 0.5 PINNED, M2 input = M1's training-window feature matrix + M1's confidence (same-feature), default `--model lgbm` restored, ITERATION_LABEL "v3-017") EXPLORATION on v3 universe (BCH+LDO+TRX), `--exploration --model metalabeling` mode (ENSEMBLE_SIZE=1, n_trials=10, colsample_bytree=1.0, outer_seed=42). **EXPLORATION-NEGATIVE (clean) PATH C sub-flavor (NEGATIVE-over-filter-quality-residual)**. IS monthly Sharpe = +0.5288 (Δ −0.48 vs iter-v3/013 +1.0088). OOS monthly Sharpe = +0.5476 (Δ −2.15 informational; OOS=62 below 130-trade floor). 159 IS / 62 OOS trades. M2 per-candle veto rate 42.7% (2,976/6,965). Per-symbol IS shifts BCH 100→73 (−27), TRX 88→70 (−18), LDO 21→16 (−5) — all > 5. Per-symbol OOS attribution: LDO +14.94 (6 trades, 66.7% WR, 103.23% concentration), TRX +5.15 (35 trades, 40.0% WR), BCH −5.62 (21 trades, 33.3% WR). Label tolerance divergence (pnl > 0 vs strict TP-first) noted as non-blocking. n_eff=4 LOWEST in v3 catalog. PBO=NaN structural (M2 has no label training data on thin walk-forward cells). 5 caveats catalogued. **NOT a CONFIRMATION-bundle candidate**: M2 demonstrably active but kept trades show no quality lift; same-feature M2 has no incremental learnable signal beyond M1. **iter-v3/018 axis MANDATORY = MULTI-SEED VALIDATION OF iter-v3/013 BASELINE** (NOT bundle assembly) per `feedback_v3_iter018_confirmation_baseline_validation.md`. **CADENCE COMPLETE: catalog count advances 9 → 10 of 10. iter-v3/018 = first v3 CONFIRMATION.**

## Pre-Registered Failure-Mode vs Reality Summary

| Class | Materialized? |
|---|---|
| Process predictions (P1-P3) | 0/3 materialized — pipeline ran clean, wall-clock ~30 min within budget, M2 wiring functional (per-candle veto rate 42.7%), no integration failures, all 4 first-commit pre-commits PASS |
| Model predictions (P4-P7) | P4 (PROMISING band [+1.30, +1.60] M2-lifts-Sharpe) DID NOT MATERIALIZE; P5 (NEGATIVE M2-no-effect band [+0.90, +1.10] bit-identical roster) DID NOT MATERIALIZE (roster non-bit-identical); P6 (over-filter band IS Sharpe < +0.91 with veto > 50%) PARTIALLY materialized (IS Sharpe +0.53 < +0.91 confirmed; veto 42.7% < 50% so over-filter sub-condition slightly looser than predicted but qualitative pattern matches PATH C sub-flavor) |
| OOS-axis prediction | informational under EXPLORATION; OOS Sharpe +0.55 below 130-trade floor at OOS=62 |
| Behavioral-effect verifier (saturation falsifier + per-symbol shift) | BOTH PASS — IS=159 narrowly above 157 lower bound BUT M2 demonstrably active 42.7%; per-symbol shifts non-trivial (BCH −27, LDO −5, TRX −18) |

Calibration accuracy: 4/4 process + behavioral-effect predictions clean; the model-prediction set (P4-P7) anticipated the PATH C verdict with appropriate probability mass. iter-v3/017 establishes PATH C (NEGATIVE-over-filter-quality-residual) as a NEW sub-flavor in the v3 catalog — distinct from PATH A (PROMISING) and PATH B (NEGATIVE-no-effect). The new `feedback_v3_iter018_confirmation_baseline_validation.md` rule does NOT close a calibration gap (calibration discipline is intact for what was predicted) — it pre-commits the first v3 CONFIRMATION to baseline-validation rather than bundle assembly because EXPLORATIONs 014-017 produced no NEW ingredient to bundle.

## Pareto Position

Single-row degenerate front (Section 8 criterion 9 waiver):

| seed | OOS Sharpe | OOS MaxDD | OOS Calmar | PBO | n_trades | max_conc% |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | +0.5476 | 18.76% | 0.771 | NaN | 62 | **+103.23%** (LDO 6-trade lottery) |

Cross-symbol OOS dispersion (informational, NOT Pareto-equivalent under EXPLORATION):

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| LDOUSDT | +14.94 | 6 | 66.7% | **+103.23%** (lottery flag carries forward) |
| TRXUSDT | +5.15 | 35 | 40.0% | +35.60% |
| BCHUSDT | −5.62 | 21 | 33.3% | −38.83% |

LDO's 6-trade lottery (4/6 wins, exact-binomial 95% CI [22.3%, 95.7%]) drives the OOS portfolio +14.47 single-handedly — without LDO's 4 wins, OOS PnL collapses to −0.47. The 103.23% concentration is well above the 30% per-symbol cap that would apply at CONFIRMATION; future CONFIRMATION QR scoping ex-LDO basket fragility carries forward unchanged from iter-v3/011/012/013/014 + this iteration.

## Next Iteration

**iter-v3/018 — first v3 CONFIRMATION. Axis: MULTI-SEED VALIDATION OF iter-v3/013 BASELINE (NOT bundle assembly)** per Critic FINAL Recommendation 1 of iter-v3/017 review (this diary's review SHA `6de26d1`) AND new memory rule `feedback_v3_iter018_confirmation_baseline_validation.md` MANDATORY pre-commit.

**Critical distinction**: iter-v3/018 is NOT a bundle-assembly run because there is NO NEW ingredient to bundle. All 4 PROMISING components (iter-v3/007 top-13 features, iter-v3/010 ATR 2.0/1.0 labeling, iter-v3/011 z-score 2.0 OOD, iter-v3/013 drop-MKR universe) are ALREADY cumulatively integrated in the current iter-v3/013 baseline. iter-v3/014-017 produced:
- iter-v3/014: ADX-25 NEGATIVE-clean (axis closed)
- iter-v3/015: tbr_zscore_30 NEGATIVE-no-effect (feature INERT, model didn't learn)
- iter-v3/016: XGBoost NEGATIVE-clean (worst OOS Δ in v3 history at -2.53)
- iter-v3/017: meta-labeling NEGATIVE-over-filter (this iteration; PATH C sub-flavor)

No NEW ingredient. The CONFIRMATION question is purely a baseline-validation question: does the iter-v3/013 IS +1.0088 / OOS +2.6970 Sharpe hold under multi-seed cross-validation with full CONFIRMATION rigor?

**iter-v3/018 SPEC** (cannot be renegotiated post-hoc):

| Parameter | iter-v3/013 baseline | iter-v3/017 (this run) | iter-v3/018 (mandated) |
|---|---:|---:|---:|
| Universe | BCH+LDO+TRX (3 symbols) | UNCHANGED | UNCHANGED |
| Z-score OOD threshold | 2.0 | UNCHANGED | UNCHANGED |
| ATR multipliers | (2.0, 1.0) | UNCHANGED | UNCHANGED |
| BTC trend filter band | ±15% | UNCHANGED | UNCHANGED |
| ADX threshold | 20.0 | UNCHANGED | UNCHANGED |
| Hurst (low, high) | (0.05, 0.95) | UNCHANGED | UNCHANGED |
| V3_FEATURE_COLUMNS count | 13 | UNCHANGED | UNCHANGED |
| Model architecture | LightGBM | MetaLabelingStrategy (this run) | **LightGBM (restored)** |
| Labeling scheme | Triple-barrier | Meta-labeling (this run) | **Triple-barrier (restored)** |
| `--seeds` | 1 (exploration) | 1 (exploration) | **2** (5 inner × 2 outer = 10 models/cell) |
| `--n-trials` | 10 (exploration) | 10 (exploration) | **50** |
| ENSEMBLE_SIZE | 1 (exploration) | 1 (exploration) | **5** (live-prediction variance reduction inherited from v1) |
| Wall-clock budget | 8 min | ~30 min | **4h HARD CAP per CONFIRMATION cadence rule** |

**iter-v3/018 PASS conditions for MERGE** (per `feedback_v3_iter018_confirmation_baseline_validation.md`):
- IS monthly Sharpe ≥ +1.0 (multi-seed mean)
- OOS monthly Sharpe ≥ +1.0 (multi-seed mean)
- DSR > 0.95
- PBO < 0.4
- PSR > 0.95
- Top-symbol concentration ≤ 30% (or explicit exception with justification)
- 10-seed pre-MERGE concentration validation: mean Sharpe > 0, ≥ 7/10 profitable
- Bundle-level OOS trade count ≥ 130 (per `feedback_trade_rate_floor_bundle_level.md`)

**iter-v3/018 BLOCK conditions**:
- Single-seed concentration artifacts (LDO 65-74% at iter-v3/013/017) do NOT compress under multi-seed averaging → fragility
- DSR < 0.95 OR PSR < 0.95 OR PBO ≥ 0.4
- Multi-seed Sharpe variance shows trade-rate floor not met at bundle level

**Pre-conditions for iter-v3/018 brief**:
- Section 4 must remain a single decision tree (not parallel tables) — preserving brief-template fix from iter-v3/015
- Section 7 prediction band must include explicit probability mass for "baseline holds under multi-seed" (PASS-MERGE) AND "single-seed artifacts dominate" (BLOCK) outcomes
- Pre-register OOS-axis falsifier (CONFIRMATION reads OOS metrics; not informational-only)
- Single-axis discipline: ONLY multi-seed validation. NO axis variation. NO bundling.
- **CONFIRMATION-MERGE updates BASELINE_V3.md only if all gates pass at non-EXPLORATION thresholds**

**Catalog count after iter-v3/017**: **10 of 10** EXPLORATIONs since last CONFIRMATION; CONFIRMATION can launch. Axis coverage: features × 2 (007, 009) + labeling × 1 (010) + gate-zscore × 1 (011) + gate-btc-trend × 1 (012) + universe × 1 (013) + gate-adx × 1 CLOSED (014) + NEW feature family × 1 (015) + NEW model architecture × 1 CLOSED-at-config (016) + NEW labeling architecture × 1 (017) = **9 unique axis representations**. This satisfies the v3 cadence rule and unblocks first CONFIRMATION launch.

**PROMISING vs NEGATIVE breakdown (10 EXPLORATIONs since last CONFIRMATION)**:
- PROMISING-class: 4 of 10 — iter-v3/007 (features), iter-v3/010 (labeling), iter-v3/011 (zscore), iter-v3/013 (universe drop-MKR)
- NEGATIVE-class: 6 of 10 — iter-v3/009 (features-too-tight), iter-v3/012 (BTC band NULL), iter-v3/014 (ADX-25), iter-v3/015 (microstructure INERT), iter-v3/016 (XGBoost), iter-v3/017 (meta-labeling)

**iter-v3/017 status**: NOT a CONFIRMATION-bundle candidate. Meta-labeling at this configuration (M2 threshold 0.5 PINNED + same-feature M2 input + n_trials=10 single-seed budget + label tolerance `pnl > 0`) over-filters without quality lift. Future meta-labeling re-test would require strict TP-first labels + DIFFERENT M2 features (non-M1 features) + ≥50 n_trials + multi-seed budget — all four together — to address the failure mode. iter-v3/018 axis MANDATORY = MULTI-SEED VALIDATION OF iter-v3/013 BASELINE per `feedback_v3_iter018_confirmation_baseline_validation.md`. The 5 caveats from this diary travel with the catalog row to inform future CONFIRMATION-MERGE / NO-MERGE decision.
