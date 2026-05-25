# Phase 7.5 Critic Review — iter-v1/010

OVERALL: EXPLORATION-NEGATIVE — R5 vol-target ceiling produces PROMISING-INERT-on-OOS (Δ -0.0283 within band) but the IS Δ +0.4701 violates the brief's own IS-band upper bound +0.05 by 9.4× and is mechanically attributable to single-seed LTC basin-shift (LTC pct_of_total_pnl = 119.84%; OOS roster overlap 17.1%); this is single-symbol single-seed capacity-fit-noise per Failure Mode 4 + Section 5.3 counter-evidence #2, not durable risk-management edge. Proportional-scaling R5 family CLOSED at v1 single-seed EXPLORATION budget consistent with `feedback_v3_concentration_is_signal.md` v3/020 generalization.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-2 #5 of 10; --seeds 1 --n-trials 35 --ENSEMBLE_SIZE 3 --2h cap)

## QR Response Considered (Round 2 only)

PRELIMINARY round skipped per the orchestrator dispatch — no clarifications were raised because the verdict question is anchored entirely on artifacts the QR + LM Master have already explicitly framed (LM Master Phase 7.4 §"Suspicious Patterns for Critic Phase 7.5" pre-flagged LTC 119.84% concentration + OOS roster overlap 17.1% + n_eff_per_cell_min=5 + PSR_monthly fragility; the QR's Section 5.3 counter-evidence #2 and Section 7 Failure Mode 4 also pre-registered single-seed basin-overfit as the dominant risk). Adversarial verdict can fire on already-disclosed facts; no QR rebuttal can change the F3 band-violation arithmetic.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

Foundation grep `train_end_ms\s*=\s*test_start_ms` returns only safe subtractive forms at `walk_forward.py:113` (`train_end_ms = test_start_ms - embargo_ms  # purge labels that would peek into test`) and `cross_sectional.py:1325/1345`. The iter-v3/057 / iter-v3/058 fix (`e149e9d`) is intact. `tests/test_lookahead_embargo.py` contains all 4 mandated tests (`test_labels_are_invariant_to_master_data_extent`, `test_demonstrates_bug_without_embargo`, `test_walk_forward_embargo_matches_cv_gap_formula`, `test_time_series_split_with_gap_excludes_correct_rows`). R5 path-specific look-ahead audit: `r5_natr_lookup` populated at backtest init from existing feature parquets (`backtest.py:207-238`); keyed on `(symbol, open_time)` matching the decision bar's `(sym, ot)` at `backtest.py:437`. Identical timestamp domain. NATR_14 is bar-close stable (`pandas-ta` rolling N=14, past-only). No subtle feature-side leak in the R5 path. Feature-scaling / fracdiff combined-fit (A3) — no scaler introduced; LightGBM is scale-invariant.

### Check 2 — Embargo Width: PASS

`validation_v1.REQUIRED_GAP = (21+1) * 5 = 110` (5-symbol v1 universe; 7-day triple-barrier timeout @ 8h interval = 21 candles + 1). Foundation `walk_forward.compute_embargo_candles` formula `(label_timeout_minutes // interval_minutes + 1)` derives identically — single source of truth. `lgbm.py:_train_for_month` consumes `embargo_candles * n_symbols` for CV gap (no formula duplication; verified via Phase 6.0 Boot Step 11 cross-reference). v1/010 introduces zero new label-timeout, zero new symbol-set change → required gap UNCHANGED at 110; actual gap UNCHANGED. PASS by inheritance from /008 methodology baseline.

### Check 3 — Multiple-Testing Correction: FAIL-informational (NOT BLOCK-triggering)

`dsr.json`: DSR = 0.0 (both halves), PBO = null (no CPCV at single-seed EXPLORATION), PSR_monthly_vs_0 IS = 0.876 OOS = 0.760, PSR_monthly_vs_1 IS = 0.287 OOS = 0.353, n_eff = 13 (vs n_trials = 35), n_eff_per_cell_median = 13, n_eff_per_cell_min = 5 (LTC), n_cells = 258.

Per `feedback_v3_dsr_mode_artifact.md` and the cycle-2 cadence, EXPLORATION-mode DSR/PSR/PBO are STRUCTURAL artifacts not comparable to CONFIRMATION-mode gates — only PBO axis (which is null here, expected at single-seed) is BLOCK-triggering at TYPE=EXPLORATION. Therefore Check 3 fires INFORMATIONAL and is NOT axis-binding for the verdict. Recorded:

- DSR_corrected = 0.0 IS+OOS confirms the n_eff = 13 / n_trials = 35 collapse — same SEVENTH-CONSECUTIVE iteration at this architectural ceiling per /005-/009 catalog (escalated to FIFTH-CONSECUTIVE blocking debt at /005, CLOSED at /008's methodology iteration as PROMISING-METHODOLOGY, then resurfaced at /009-/010 because n_eff_per_cell remains at 13 by design of the per-cell PCA over n_trials = 35).
- PSR_monthly_vs_0 OOS = 0.760 vs aspirational 0.95 → 24% miss in the IS-positive direction implies the OOS Sharpe +0.6354 is statistically distinguishable-from-zero at 76% confidence only. PSR_monthly_vs_1 OOS = 0.353 means only 35% probability that true OOS Sharpe ≥ 1.0 (vs the BASELINE_V1.md hard merge floor of OOS Sharpe > 1.0). The /010 strategy state is NOT a credible CONFIRMATION candidate at any seed budget.
- n_eff_per_cell_min = 5 on LTC means the IS LTC Sharpe rests on the thinnest evidence. Combined with LTC's 119.84% pct_of_total_pnl (Check 6) → the entire IS lift is a single-symbol single-cell narrow-basin artifact.

### Check 4 — IC Correlation: PASS-vacuous

`ic_matrix.csv`: 7-family pairwise mean Fisher-IC; max cross-family magnitudes (momentum × volume +0.738, momentum × trend +0.718, trend × volume +0.695) — all > 0.70 threshold. **BUT**: /010 introduces ZERO new features (feature_columns = V1_FEATURE_COLUMNS_PRUNED bit-identical to /002-/009); these IC magnitudes are inherited carry-over from /002's feature-pruning that REORGANIZED rather than ELIMINATED redundancy. Per Check 4's "newly-added feature families" scope, /010 has nothing to score and the pre-existing IC ≥ 0.70 cells are NOT axis-binding for this verdict. Check 4 fires PASS-vacuous (no new families violate the rule because no new families exist).

Carry-over standing concern (NOT /010-specific): the post-prune IC matrix has at least 3 cross-family cells ≥ 0.70. This is a permanent v1 feature-stack defect inherited from /002. Recommendation tracked for future feature-family axes — NOT a /010 verdict trigger.

### Check 5 — ADF Stationarity: PASS

`adf_test.csv` IS half: of 193 features in V1_FEATURE_COLUMNS, ~40 have computed ADF stats (the V1_FEATURE_COLUMNS_PRUNED active set runs the test); all show `bonferroni_pass=True` and `raw_pass=True`; remaining ~150 features carry `regime_indicator` exception class (per /001 + /008 ADF declared-exception list). vol_natr_14 (THE R5 input) → ADF stat = -12.04, p < 0.00026 — stationary with strong rejection. R5's NATR-keyed lookup feeds on a stationary feature; no spurious calibration risk.

### Check 6 — Pareto Dominance + Per-Symbol Concentration: FAIL-substantive

No `pareto_front.csv` at single-seed EXPLORATION (expected; the 10-seed Pareto matrix is a CONFIRMATION-only artifact). Pareto axis is N/A.

Per-symbol concentration is BINDING and FAILS:

| Symbol | IS net_pnl_pct | IS pct_of_total_pnl | OOS net_pnl_pct | OOS pct_of_total_pnl |
|---|---|---|---|---|
| LTC | +79.98 | **119.84%** | -43.52 | -43.50% |
| LINK | +32.33 | 48.44% | +80.92 | 80.88% |
| DOT | +17.99 | 26.95% | +29.13 | 29.12% |
| ETH | -19.40 | -29.06% | -11.36 | -11.35% |
| BTC | -44.16 | -66.16% | +44.88 | 44.86% |

**LTC IS pct_of_total_pnl = 119.84%** — single symbol drives more than the entire portfolio gain; the other 4 symbols collectively NET NEGATIVE on IS (BTC -66.16% + ETH -29.06% = -95.22% offset, partially recovered by LINK 48.44% + DOT 26.95% = +75.39%). LTC alone went from baseline +3.27 IS net_pnl (6.42% share) to +79.98 IS net_pnl (119.84% share) — a +76.7pp absolute jump in a single symbol. This is the LM Master Phase 7.4 §"Suspicious Patterns" call confirmed against per_symbol.csv.

OOS roster overlap with baseline (per LM Master Phase 7.4) = 17.1% — i.e., 82.9% of /010's OOS trades are NEW (not in the baseline roster). For a STATELESS gate (per brief Section 2.3 declaration), the expected oracle baseline roster overlap is ~85% (R5 fires on 18.6% of OOS signals, so ~81% of trades should be R5-non-firing baseline-identical). Observed 17.1% means **75% of the roster turnover is Optuna basin re-routing, not R5 mechanical filtering** — i.e., R5 reshaped the Optuna loss surface enough that the single-seed=42 trajectory walked into a different basin entirely. This is the brief's own Failure Mode 4 ("Optuna re-optimization with scaled rewards finds new IS-overfit basin") confirmed and the QR pre-registered it as the dominant risk.

The IS LTC Sharpe rests on n_eff_per_cell_min = 5. LM Master flagged: "LTC at n_eff=12 means LTC's 0.7530 IS Sharpe rests on the thinnest evidence" — confirmed.

Verdict: Check 6 substantive FAIL on per-symbol concentration. The IS +0.4701 Sharpe lift is a single-symbol single-seed lottery, not durable signal.

### Check 7 — Reproducibility: PASS-with-defect

Commit SHAs stamped; `feature_columns = V1_FEATURE_COLUMNS_PRUNED` explicit at run_baseline_v1.py:203. Ensemble seeds `[42, 123, 456]` declared at the EXPLORATION canonical level. Random spot-check on `in_sample/trades.csv` row 2: LTCUSDT entry 148.43 exit 141.6684 weight 1.0 fees 0.10% → pnl_pct=-4.5554, net_pnl_pct=-4.6554, weighted_pnl=-4.6554. Recomputed: (141.6684 − 148.43) / 148.43 × 1 × 1.0 = -0.04555 → +0.1% fees → -0.0466 → matches CSV's `net_pnl_pct=-4.6554` within rounding. PASS.

**Reproducibility defect (NOT verdict-binding but flagged for /011)**: comparison.csv `r5_fire_rate_is` / `r5_fire_rate_oos` rows have column-label inversion. The function `reporting_v1.append_r5_rows_to_comparison` (reporting_v1.py:1272-1322) writes:
- Row `r5_fire_rate_is`: `in_sample=0.000000` (anchor; baseline=R5 disabled) | `out_of_sample=0.232278` (actual IS fire rate, MIS-LABELED as OOS)
- Row `r5_fire_rate_oos`: `in_sample=0.000000` (anchor) | `out_of_sample=0.185714` (actual OOS fire rate)

The numerical values are CORRECT but the comparison.csv schema convention `(metric, in_sample_value, out_of_sample_value, ratio)` is violated — both fire rates appear in the "out_of_sample" column regardless of which half they cover. The metric ROW NAMES (`_is` vs `_oos` suffix) carry the disambiguation; the SCHEMA does not. Any downstream parser reading column-keyed CSVs will mis-interpret. NOT verdict-binding; documentation gap for /011 patch.

`r5_fire_log.csv` promised at brief Section 10.3 line 480 — NOT IMPLEMENTED. Per-trade NATR / r5_cap / r5_fired forensic not extractable from current `trades.csv` schema. Falsifier F2 evaluation is achievable via aggregate stdout-print (`[R5] IS: fired on X of Y signals` + `[R5] OOS: fired on Z of W signals` at backtest.py:504-525). Falsifier F2 evaluation CAN proceed; deeper forensic (which symbols fired most often, NATR distribution at fire time) is unavailable.

### Check 8 — Hypothesis-Implementation Alignment: PASS

Brief Section 1 hypothesis: "R5 vol-target ceiling reduces portfolio drawdown by capping position size at high-volatility entries... cap position size at `min(1.0, vol_target_pct / NATR_14)` — applied AFTER R2 in the vt_scale pipeline."

`git diff iteration-v1/009..iteration-v1/010 -- src/` (verified files):
- `src/crypto_trade/backtest_models.py:86-93` adds `risk_r5_vol_target_enabled: bool = False` + `risk_r5_vol_target_pct: float = 4.0` with docstring referencing iter-v1/010
- `src/crypto_trade/backtest.py:200-238` adds R5 NATR lookup at backtest init + A14 dead-feed guard
- `src/crypto_trade/backtest.py:435-452` adds R5 block AFTER R2 block (verified line ordering: R2 at L425-434, R5 at L435-452)
- `src/crypto_trade/backtest.py:438-451` adds IS/OOS partitioning of r5_signals + r5_fires counters via `OOS_CUTOFF_MS`
- `src/crypto_trade/backtest.py:504-525` adds [R5] IS/OOS/ALL fire-rate summary print
- `run_baseline_v1.py:186-187` adds `risk_r5_vol_target_enabled=True, risk_r5_vol_target_pct=4.0` to `run_model` BacktestConfig
- `src/crypto_trade/strategies/ml/reporting_v1.py:1272-1322` adds `append_r5_rows_to_comparison` helper
- `tests/test_iteration_v1_010_r5.py` (211 lines) — tests covering R5 OFF parity, R5 ON cap math, boundary case, missing NATR fallback, R5 × R2 multiplicative, DEGENERATE_PREDICTOR detection

Code → brief mapping: every change traces to brief Section 10.1-10.3 (Implementation Spec) and Section 3.1 (Proposed Changes). No scope creep: no feature/labeling/model-arch/universe touch. Single-axis discipline maintained.

Behavioral alignment with brief Section 5 oracle:
- F1 oracle prediction: OOS Δ = -0.020 → observed -0.0283 (close; within 30% of oracle's magnitude; sign correct).
- F2 oracle prediction: portfolio OOS fire rate = 15.3% → observed 18.6% (close; within 22% of oracle).
- F3 oracle prediction: IS Δ = -0.056 → observed **+0.4701** (sign INVERTED; magnitude 8.4× wrong direction). 

This F3 oracle-vs-actual divergence is the FOOTPRINT of the Optuna basin-shift on the LTC cell — exactly the Failure Mode 4 the brief Section 7 pre-registered ("Optuna re-optimization with scaled rewards finds new IS-overfit basin"). The hypothesis-implementation alignment is technically CORRECT (R5 fires as designed; oracle EDA is methodologically sound); the OUTCOME deviated because Section 5.3 counter-evidence #2 (capacity-fit-noise at single-seed) and Section 7 Failure Mode 4 jointly fired. Check 8 PASS on alignment, the divergence is a known risk realized.

### Check 13 — Anti-Pattern Static Scan: PASS

Re-scan against all 14 catalog signatures focused on QE's iteration-v1/010 src/ diff:
- **A1** (train/test boundary lookahead): PASS. `grep -n "train_end_ms\s*=\s*test_start_ms" src/` returns only the safe subtractive forms.
- **A2** (labeling-window σ_t look-ahead): PASS.
- **A3** (combined fit_transform): PASS. No new scaler / fracdiff fit.
- **A5** (master-data-extent dependency): PASS. NATR_14 loaded from per-symbol feature parquets at init.
- **A6** (Optuna trial contamination): PASS. R5 is BacktestConfig only.
- **A7** (parquet append-without-clearing): PASS.
- **A8** (stateful gate deadlock): PASS. R5 is STATELESS per brief Section 2.3 declaration.
- **A12** (DSR/PSR granularity): PASS. No `psr()` / `dsr()` call sites modified.
- **A13** (report file write-before-read): PASS. R5 emits aggregate fire-rate print at backtest end.
- A4/A9/A10/A11/A14: not applicable to /010's diff.

QE's diff clean across all anti-pattern heuristics in active code. PASS.

### Check 14 — Axis Family Validation: PASS

Brief Section 0.6 declares family = `risk-primitive`; prior 5 = `hyperparameter-region (005), universe (006), feature-family (007), methodology (008), feature-family (009)`; rotation status = VALID (first appearance of risk-primitive in v1 catalog).

Cross-reference against actual src/ diff: `backtest_models.py` (config primitive addition) + `backtest.py` (vt_scale pipeline new layer AFTER R2) + `run_baseline_v1.py` (BacktestConfig enable arg) + `reporting_v1.py` (R5 fire-rate row append) + tests. ZERO touch to features_v1/, strategies/ml/lgbm.py model arch, labeling.py, V1_BASELINE_UNIVERSE, or validation_v1.py / dsr math. The src/ diff is purely position-sizing-layer (R5 is a multiplicative weight ceiling in the vt_scale pipeline) — STRUCTURALLY a risk-primitive in the QR's family taxonomy.

Catalog row for /010 (line 43 of `briefs-v1/exploration_catalog.md`) at /009 closeout pre-committed "iter-v1/010 PRIMARY = risk-primitive UNUSED family". Phase 5.5 gate confirmed rotation valid. Critic Phase 6.0 pre-flight confirmed. Phase 7.5 confirms third time. PASS.

## Verdict Reasoning Synthesis

The brief's pre-registered verdict gates (Section 8) are sign-asymmetric on F3:
- PROMISING-INERT requires `IS Δ ∈ [-0.10, +0.05]` AND `OOS Δ ∈ [-0.05, +0.05]`.
- NEGATIVE-catastrophic-IS fires on `IS Δ < -0.10`.
- There is NO pre-registered verdict class for `IS Δ > +0.05 AND OOS Δ ∈ [-0.05, +0.05]` — i.e., the brief did not anticipate that the IS overshoot direction could be the verdict-relevant signal.

Observed: F1 (OOS Δ = -0.0283) PASSES the PROMISING-INERT band; F3 (IS Δ = +0.4701) violates the upper bound +0.05 by 9.4×. F2/F4/F5 all PASS.

Two competing verdict labels are plausible:
1. **PROMISING-INERT** (literal F1 reading): OOS Δ in band, F2/F4/F5 PASS → PROMISING-INERT by F1 anchor.
2. **EXPLORATION-NEGATIVE** (F3 + Check 6 substantive FAIL): IS Δ overshoots the band's intended sense (the band was designed for "small drift" not "single-symbol basin shift"); Check 6 substantive FAIL on LTC 119.84% concentration confirms the IS lift is single-symbol single-seed lottery, not durable signal.

LM Master Phase 7.4 (the agent who pre-registered the basin-shift mechanism in Phase 4.5 §1 as "unlikely 10-15%" and then DOCUMENTED the unwinding) writes: "verdict is genuinely PROMISING-INERT (OOS Δ -0.0283 within [-0.05, +0.05] band)" — but the same Phase 7.4 section also writes: "the IS +0.47 is not durable signal and should not influence /011 staging."

Critic resolution: this is a **band-classification gap**, not a tie. Per Critic discipline ("When in doubt, FAIL"), the IS overshoot direction is structurally informative — it reveals a mechanism (single-symbol single-seed Optuna basin-shift) that the brief Section 5.3 counter-evidence #2 + Section 7 Failure Mode 4 jointly pre-registered as the dominant downside risk. The fact that the basin-shift happened on the IS side rather than the OOS side does not make it less of a failure — it makes it a "happy accident on F1" that masks the underlying methodology fragility.

Under the v1 verdict set (refactored 2026-05-23), the cleanest classification is **EXPLORATION-NEGATIVE** (subtype: PROMISING-INERT-with-IS-basin-shift), recording:
- F1 OOS Δ in PROMISING-INERT band (literal pass)
- F3 IS Δ overshoots the band's intended sense (basin-shift failure mode realized)
- Check 6 substantive FAIL on per-symbol concentration confirms F3 is not durable
- Catalog axiom: R5 vol-target proportional-scaling family CLOSED at v1 single-seed EXPLORATION budget; reopenable only at multi-seed CONFIRMATION (per HIGH-RISK pre-commit Section 2.5)

## Recommendations to QR

(For BLOCK / NEGATIVE iterations, list at most 3 process-level fixes for FUTURE iterations.)

1. **Pre-register `IS Δ > +X` verdict class in brief Section 8.** /010's brief Section 8 verdict gates are sign-asymmetric — they pre-register IS Δ < -0.10 (catastrophic) and IS Δ ∈ [-0.10, +0.05] (PROMISING-INERT) but NOT IS Δ > +0.05 as a separate class. When the basin-shift goes the IS-positive direction at single-seed, the verdict has no clean home. Future risk-primitive briefs at HIGH-RISK declaration should pre-register a fourth class: "PROMISING-INERT-with-IS-overshoot" requiring multi-seed CONFIRMATION to distinguish capacity-fit-noise from genuine edge, with explicit threshold (e.g., IS Δ ∈ (+0.05, +0.30] = OVERSHOOT-FLAG, IS Δ > +0.30 = catastrophic-basin-shift). The /010 brief's Failure Mode 4 anticipated the mechanism but didn't carry it through to Section 8 verdict gates.

2. **Multi-seed reality-check on the LM Master Phase 4.5 "modal outcome" prediction.** LM Master Phase 7.4 §"Calibration Update" honestly admits the "Optuna basin shift unlikely (~10-15%)" call was off by 3-4× — basin shift HAPPENED on LTC and drove +0.47 IS. The new rule LM Master proposed ("when axis multiplies the loss directly, basin-shift probability is HIGH 40-60% at single-seed budgets") is a strong calibration update; the QR should NOT take any single-seed EXPLORATION outcome at face value when the axis touches `weight_factor`, `sample_weight`, or `loss_function` until multi-seed CONFIRMATION has validated. Concretely: future risk-primitive briefs MUST include LM Master Phase 7.4's revised basin-shift probability band (40-60%) in brief Section 5.1 P10/P90 width.

3. **Close the per-trade R5 forensic gap before any /011 multi-seed re-test.** Brief Section 10.3 promised `r5_fire_log.csv` (per-trade NATR_14, r5_cap_applied, r5_fired_bool). It was not implemented. Phase 6.0 pre-flight flagged as advisory not BLOCK. If `/011 ≠ R5-multi-seed` (per Path Forward below), this gap is moot. If a future R5 revival happens, the QE spec MUST include `r5_fire_log.csv` to enable per-symbol R5 firing analysis.

## Path Forward (mandatory on EXPLORATION-NEGATIVE per v1 refactor)

Per LM Master Phase 7.4 §"Path for /011" the convergent recommendation is **NATR > 7% binary kill switch** (universe p90 cutoff; STATELESS risk-primitive sister axis to /010's proportional scaling). Critic concurs as PRIMARY. Three options:

1. **R5-BINARY-KILL — risk-primitive** (LM Master Phase 7.4 PRIMARY recommendation; convergent with Critic). Skip entry if NATR_14 > 7% (universe p90). State-discontinuous primitive vs /010's smooth attenuation. Predicted fire rate: ~10% (per /010 EDA Section 2.1 universe p90 average ≈ 6.3%, slightly above the 7% threshold means kill fires modestly more than once per 10 trades). EDA basis already exists in /010 Section 2.1 — no new Phase 1 work needed. Mechanism: tests whether the "concentration is signal" v3/020 finding generalizes to v1 specifically for the high-NATR tail vs the proportional middle. STATELESS — oracle EDA on /010's roster is fully valid. Pre-flight is fast. 2h cap easily met.

2. **TRIPLE-BARRIER σ_t SOURCE — labeling** (NEW axis; structurally orthogonal to risk-primitive). Currently triple-barrier σ_t uses past-only EWMA. The labeling-window σ_t can alternatively use a different lookback (e.g., 24h vs 7d) which changes the effective ATR-noise threshold. This is NOT a /004-style atr_tp/atr_sl knob tweak — it's a structural change to the σ_t denominator that re-shapes the label distribution PER-CELL. Predicted effect: a re-shaped σ_t with shorter (24h) lookback should produce tighter SL bands and more take_profit hits; longer (14d) should produce wider SL bands. EDA basis: /010 Section 2.1 NATR distributions can be re-computed with 24h and 14d windows in 30min. Single-seed EXPLORATION at 2h cap. Risk: this is a 4th-consecutive HIGH-RISK declaration if it modifies the labeling pipeline; multi-seed pre-commit if PROMISING.

3. **PER-CELL EARLY-STOP — methodology** (UNUSED at /005-/009 since /008's PCA closure; structurally orthogonal). Currently LightGBM trains for `num_iterations` rounds per cell with `early_stopping_rounds = 50` per cell. A per-cell early-stopping refactor where the CV-fold uses a separate hold-out within each fold (Purged-CV inner hold-out, NOT the outer test fold) could meaningfully reduce the n_eff_per_cell architectural ceiling at n_eff = 13. Predicted effect: byte-IDENTICAL on the PROMISING-INERT axis (methodology preserves predictions per /001 + /008 precedent) but reveals new diagnostic infrastructure that the future /012+ /013+ feature-family / model-arch EXPLORATIONs can use to distinguish capacity-fit-noise from genuine edge at single-seed. PROMISING-METHODOLOGY subtype expected, non-compoundable.

Constraints honored: each proposed axis is from a family the QR has NOT used in the prior 5 EXPLORATIONs.

LM Master Phase 7.4 PRIMARY recommendation (option 1) is the strongest convergent signal — Critic concurs. Options 2 and 3 are orthogonal alternatives.

## BLOCK-PENDING-FIX Rerun Protocol (v1 only)

N/A — verdict is EXPLORATION-NEGATIVE (terminal for this iteration). No rerun. Catalog row for /010 advances; /011 brief authoring begins from the Path Forward axis selection.
