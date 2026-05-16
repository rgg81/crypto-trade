# Phase 7.5 Critic Review — iter-v3/064

OVERALL: EXPLORATION-NEGATIVE — IS Sharpe Δ -0.68 violates brief Section 8.4 NEGATIVE classification (disjunctive "OR" condition); proposed NEGATIVE-IS-DEGRADATION-WITH-OOS-LOTTERY subtype is REDUNDANT with Section 8.4 as written.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle 1 #5 of 10; PHASED MASS-EXPANSION #1).

## Per-Check Status

### Foundation Audit (Boot Steps 9-11): PASS

- `walk_forward.py:113`: `train_end_ms = test_start_ms - embargo_ms` — lookahead-fix INTACT.
- `validation_v3.py:54`: `REQUIRED_GAP = (21 + 1) * 3 = 66` — correct for 3-symbol universe.
- `lgbm._train_for_month` ensemble plumbing: EXPLORATION_ENSEMBLE_SIZE=3; ENSEMBLE_SEEDS[0:3] = [191664963, 1662057957, 1405681631].
- `ITERATION_LABEL = "v3-064"` at L128. PASS.
- `V3_FEATURE_COLUMNS_TOP_N` at `features_v3/__init__.py:133-204` has 15 entries; BIT-IDENTICAL to brief Section 3. PASS.
- `adx_14` PRESENT (L177). 6 BANNED features ABSENT. 31 /063-NEW features REVERTED. PASS.
- `adx_14` implementation at `technical_v3.py:71-167` verified past-only via `prev_close`, `prev_high`, `prev_low` causal shifts.

### Check 1 — Look-Ahead Audit: PASS

adx_14 was audited at /063 Critic FINAL `7cbc136`. Re-spot-verified causal at `technical_v3.py:117-119`. No new features added at /064 beyond adx_14. PASS by construction.

### Check 2 — Embargo Width: PASS

`(21+1) * 3 = 66`. Applied symmetrically at outer (walk_forward.py:113) and inner (lgbm.py:457) boundaries. PASS.

### Check 3 — Multiple-Testing Correction: N/A-INFORMATIONAL

DSR=0.0, PSR=0.9972, PBO=0.0822, DSR_relative=3e-06, n_eff=18, frac_positive_paths=0.6444. EXPLORATION-mode informational per `feedback_v3_dsr_mode_artifact.md`. PASS-INFORMATIONAL.

### Check 4 — IC Correlation: PASS

`ic_matrix.csv` (15×15) row 16 adx_14: max |IC|=0.157 with `range_realized_vol_50` (EDA T3 predicted 0.162; within 0.005 reproducibility). No |IC| ≥ 0.30. Clean orthogonality. PASS.

### Check 5 — ADF Stationarity: PASS

adx_14 at last walk-forward month 2025-03: BCH stat=-7.808, LDO stat=-8.085, TRX stat=-6.801, all p=0.0. Rock-solid stationary. Early-window NaN reflects warm-up insufficiency (standard). PASS.

### Check 6 — Pareto Dominance: N/A (single-seed EXPLORATION)

### Check 7 — Reproducibility: PASS

Commit SHAs verified. ENSEMBLE_SEEDS[0:3] = [191664963, 1662057957, 1405681631] deterministic. Trade-math spot check on 3 OOS trades matches CSV to 4dp. LDO OOS WR=7.1% (1/14) verified by direct grep.

### Check 8 — Hypothesis-Implementation Alignment: FAIL (HYPOTHESIS DOUBLE-FALSIFIED)

Brief Section 1 hypothesis: "Adding adx_14 to /060 14-feature anchor produces ≥+0.10 IS Sharpe AND ≥+0.20 OOS Sharpe primarily via stronger LDO trend-regime signal."

Observed:
- IS Sharpe Δ = -0.6798 (required ≥ +0.10; FAILS by 0.78). HYPOTHESIS FALSIFIED on IS.
- OOS Sharpe Δ = +0.1503 (required ≥ +0.20; FAILS by 0.05). HYPOTHESIS FALSIFIED on OOS.
- LDO OOS WR collapsed 18.2% → 7.1% — OPPOSITE direction of "stronger LDO trend-regime signal".

Falsifier Gate A.1 (IS ≥ -0.20): observed -0.6798, FAILS by 0.48 units. Implementation IS aligned to brief Section 3, but predicted DIRECTION OF EFFECT is falsified on every measured dimension.

### Check 9 — Symbol Exclusion: PASS
### Check 10 — Feature Isolation: PASS
### Check 11 — Forming-Candle: PASS (8.0h lag, within 16h)
### Check 12 — Library Version: PASS (carry-over; no new modules)

### Check 13 — Phased-Expansion-Specific: FAIL (CLASSIFICATION REDUNDANCY + EDA METHODOLOGY)

**13a — Proposed NEGATIVE-IS-DEGRADATION-WITH-OOS-LOTTERY subtype is REDUNDANT with Section 8.4.** Brief Section 8.4 NEGATIVE definition reads: "IS Δ < -0.20 **OR** OOS Δ < -0.30 (either gate FAIL) AND no methodology FAIL." Observed IS Δ = -0.6798 < -0.20 → Section 8.4 NEGATIVE TRIGGERED. The disjunctive "OR" means a single-gate IS failure alone classifies as NEGATIVE. The QE's claim of "CLASSIFICATION GAP" is INCORRECT — there is no gap. The proposed new subtype is a descriptive refinement (lottery framing of OOS +0.15), not a category gap-fill. **/064 IS NEGATIVE per Section 8.4 as written.** No taxonomy amendment required.

**13b — EDA-to-runner importance rank divergence at LDO (singleton 2/15 → walk-forward 10/15) is a real methodology vulnerability.** EDA T4 uses `colsample_bytree=1.0` for singleton importance preview. The actual runner uses Optuna-tuned `colsample_bytree` (sampled per trial). The runner's ensemble aggregate reflects the sampled colsample, which routinely excludes adx_14, producing the 10/15 rank vs the EDA's 2/15. **EDA-singleton-at-colsample-1.0 is systematically OPTIMISTIC** for actual Optuna-driven importance.

## §11 Anti-Pattern Static Scan: PASS (with 1 WARN on A14)

13/13 PASS. New WARN on proposed A14 (EDA-prediction-vs-actual divergence): EDA T4 singleton at colsample=1.0 is systematically optimistic vs Optuna walk-forward aggregate. Recommend codifying.

## Per-Symbol Forensic — LDO Catastrophe Severity

**/060 LDO OOS** (actual): 11 trades, 2 wins, **18.2% WR** (NOT 25% as engineering report Section 3.2 claims; the 27.3% figure is IS WR, not OOS), -19.72 wpnl.

**/064 LDO OOS**: 14 trades, 1 win, 7.1% WR, -40.42 wpnl.

**Delta**: WR -11.1pp absolute; wpnl -20.70.

Two consecutive iterations (/063 mass→14, /064 single-feature add) produced sub-20% LDO OOS WR. Adding adx_14 ALONE worsened LDO from -19.72 to -40.42 wpnl. The pattern is structural: LDO has near-zero edge at 14-15 feature configurations under single-seed n_trials=35.

## Adversarial-Specific Questions — Answered

### Q1 — Is the proposed classification real or invented?

**INVENTED.** Section 8.4 OR condition unambiguously classifies /064 as NEGATIVE. The QE misread Section 8.4 as conjunctive ("AND") when it is disjunctive ("OR"). Cross-symbol math: BCH +48.62 + LDO -40.42 + TRX -0.10 = +8.10 net OOS wpnl — BCH luck masks LDO catastrophe + TRX flat. OOS lift is lottery, NOT signal.

### Q2 — Should future EDAs use Optuna-mimicking colsample sampling?

**YES, with caveat.** For future feature-axis EDAs, T4 must additionally report importance rank range across 3-5 colsample samples in [0.3, 1.0]. The colsample=1.0 singleton remains valid as an upper-bound diagnostic but must be LABELED AS UPPER BOUND not PREVIEW.

### Q3 — Is LDO 7.1% OOS WR historically anomalous?

**YES, but /060 was already an outlier.** Across cycle 1:
- /060 LDO OOS: 18.2% WR (was already "worst LDO OOS in v3 history")
- /063 LDO OOS: 33.3% WR (only 3 trades; too thin to measure)
- /064 LDO OOS: 7.1% WR (NEW worst; 1 winner of 14)

### Q4 — Was brief's probability over-confident in INERT?

**YES.** Section 7 assigned NEGATIVE=10%; observed NEGATIVE with magnitude 3.4× the threshold. Brief's own Section 4.1 cited `iter-v3/023 funding_rate_zscore_30 at n_trials=35 → OOS -1.46 NEGATIVE` precedent. NEGATIVE should have been weighted ~25-30%.

## Recommendations to QR

1. **Anchor-value correctness gate in brief Section 2 + engineering report.** Brief Section 2.5 cites "+24.75 OOS wpnl (BCH)" as the /060 anchor for D.9 falsifier; engineering report propagates this. Actual /060 BCH OOS wpnl from `comparison.csv:18` = **+1.9078**. Similar issue: engineering report cites "/060 LDO OOS wpnl -6.18"; actual is -19.72. Add a Phase 5.5 sub-check: Section 2.5 anchor values must match `reports-v3/iteration_v3-XXX/comparison.csv` and `per_symbol.csv` byte-exactly.

2. **EDA T4 colsample-sampling discipline.** For future feature-axis EDAs, EDA T4 must report importance rank range across 3-5 colsample samples in [0.3, 1.0]. Update `feedback_v3_axis_selection_quant_discipline.md`. Label colsample=1.0 singleton as "UPPER BOUND" not "preview".

3. **Section 7 failure-mode probability calibration.** Single-feature axes at single-seed n_trials=35 with documented Optuna-overfit mechanism (`feedback_v3_inert_features_at_higher_budget.md`) should weight NEGATIVE ≥25% (NOT 10%). Update `feedback_v3_cycle1_axis_pass_criteria.md`.

4. **/065+ axis-selection mandate per QE Section 10.** /065 should be a NON-FEATURE axis (labeling, ensemble parameters, risk primitive, or universe expansion) selected by QR with EDA backing per `feedback_v3_axis_selection_quant_discipline.md`. Defer phased-mass-expansion #2-N to CONFIRMATION-mode multi-seed runs. The /060 14-feature anchor is empirically a fragile local optimum at single-seed n_trials=35 — feature-axis EXPLORATIONs at this budget cannot safely add/remove features around it.

5. **Engineering report IS-vs-OOS WR clarity.** Engineering report mixed IS WR (27.3%) with OOS WR (18.2%) for LDO. Future engineering reports must explicitly label IS vs OOS for each WR/PnL reference.

6. **Drop NEGATIVE-IS-DEGRADATION-WITH-OOS-LOTTERY subtype proposal.** It does NOT belong in `feedback_v3_cycle1_axis_pass_criteria.md`. Section 8.4 already classifies /064 unambiguously. The QE's misreading of Section 8.4's "OR" as "AND" is the root error; future engineering reports must read Section 8 thresholds as written before proposing taxonomy amendments.
