# iter-v3/064 — Cycle 1 #5 EXPLORATION-NEGATIVE / Phased mass-expansion #1 failed

**Date**: 2026-05-14
**Type**: EXPLORATION (cycle 1 #5 of 10; PHASED MASS-EXPANSION #1: 14 + adx_14 = 15 features)
**Verdict**: EXPLORATION-NEGATIVE per Critic FINAL `452fcf2`
**Classification**: NEGATIVE per brief Section 8.4 (disjunctive OR; IS Δ -0.68 < -0.20)
**BASELINE_V3.md**: UNCHANGED (still anchors `v0.v3-059`)
**Branch**: `iteration-v3/064`

## 1. What was done

Per amended `feedback_v3_mass_feature_expansion.md` (post-/063 failure), cycle 1 #5 attempted phased single-feature expansion: REVERT V3_FEATURE_COLUMNS_TOP_N from 46 features (post-/063) back to /060's 14-feature anchor + ADD `adx_14` as the single phased feature = 15 features total.

`adx_14` selection rationale (orchestrator decision per /063 importance evidence):
- LDO importance rank 5/46 (gain 161.0) — highest of the 9 NEW features for LDO
- BCH rank 11/46, TRX rank 25/46 (moderate)
- Off-the-shelf Wilder (1978) trend indicator; walk-forward-safe per /063 Critic
- Already implemented at `technical_v3.py` from /063

Commit chain: EDA `4a9f9c9` → setup `8ce02e0` → backfill `35aa43e` → Phase 5.5 gate `0fdc86c` → engineering report `a7ed628` → Critic review `452fcf2`. Wall-clock 0.70h.

## 2. Results

| Metric | /060 anchor | /064 (+adx_14) | Δ |
|---|---|---|---|
| IS monthly Sharpe | +0.8325 | **+0.1527** | **-0.68** |
| OOS monthly Sharpe | +0.1403 | +0.2906 | +0.15 |
| OOS/IS daily ratio | 0.28 | 1.47 | sign flip (UP) |
| IS PF | 1.49 | 1.05 | -0.44 |
| OOS PF | 1.21 | 1.07 | -0.14 |
| IS MaxDD | 30.97% | 43.66% | +12.7% |
| OOS MaxDD | 34.53% | 38.60% | +4.1% |
| IS trades | 159 | 169 | +10 |
| OOS trades | 94 | 94 | 0 |
| frac_positive_paths | 0.6444 | 0.6444 | 0 |

**Per-symbol OOS** (extreme concentration):
- BCH +48.62 (34 trades, 50.0% WR, **599.77% concentration**)
- LDO **-40.42 (14 trades, 7.1% WR — 1 win of 14)**
- TRX -0.10 (46 tr, 34.8% WR — flat)

## 3. Per-symbol decomposition + EDA-vs-Optuna divergence

Critical forensic finding: **EDA T4 singleton rank (colsample=1.0) vs actual Optuna walk-forward rank diverges substantially**:
- adx_14 LDO EDA singleton rank: **2/15** (gain 227) — strong predicted signal
- adx_14 LDO actual Optuna walk-forward rank: **10/15** — bottom-third

The runner uses Optuna-tuned `colsample_bytree` (sampled [0.3, 1.0]), which routinely excludes adx_14 from trees. The EDA singleton at colsample=1.0 is systematically OPTIMISTIC.

**Cross-symbol math**: BCH +48.62 + LDO -40.42 + TRX -0.10 = +8.10 net OOS wpnl. The OOS Sharpe +0.15 lift is **BCH-concentration lottery** (599%) masking LDO catastrophe + TRX noise. Per Critic Q1, this is NEGATIVE iteration regardless of how the OOS aggregate reads.

## 4. Critic verdict summary

OVERALL=EXPLORATION-NEGATIVE per Critic FINAL `452fcf2`. 13/13 Checks PASS except Check 8 (Hypothesis double-falsified) and Check 13a (proposed taxonomy amendment REJECTED — Section 8.4 OR already covers /064).

§11 Anti-Pattern Scan: 13/13 PASS. NEW WARN on proposed A14 (EDA-prediction-vs-actual divergence).

## 5. PATH classification

**NEGATIVE** per brief Section 8.4 LOCKED (disjunctive OR; IS Δ < -0.20 OR OOS Δ < -0.30, either gate FAIL). IS Δ -0.68 triggers the IS gate.

The QE-proposed NEGATIVE-IS-DEGRADATION-WITH-OOS-LOTTERY subtype was REJECTED by Critic as redundant — QE misread Section 8.4 OR as AND. Section 8.4 unambiguously classifies /064.

## 6. Hypothesis check — DOUBLE-FALSIFIED

Brief Section 1 hypothesis: "Adding adx_14 to /060 14-feature anchor produces ≥+0.10 IS Sharpe AND ≥+0.20 OOS Sharpe primarily via stronger LDO trend-regime signal."

- IS Sharpe Δ = -0.68 (required ≥+0.10; FAILS by 0.78) — falsified on IS axis
- OOS Sharpe Δ = +0.15 (required ≥+0.20; FAILS by 0.05) — falsified on OOS axis
- LDO OOS WR collapsed 18.2% → 7.1% — OPPOSITE direction of "stronger LDO trend-regime signal"

Pre-registered failure mode probabilities (Section 7): INERT 55%, PROMISING 20%, SUSPICIOUS-OOS 10%, **NEGATIVE 10%** — NEGATIVE HIT at 3.4× the band threshold severity. Brief's Section 4.1 cited iter-v3/023 precedent (`feedback_v3_inert_features_at_higher_budget.md`) but didn't weight NEGATIVE adequately.

## 7. BASELINE_V3.md status

**UNCHANGED** — /059 stays canonical at tag `v0.v3-059`. Cycle 1 EXPLORATIONs do not update BASELINE_V3.md per `feedback_v3_baseline_update_policy.md`. NEGATIVE iterations cannot advance to CONFIRMATION.

## 8. Critic Recommendations carried forward

Six process-level recommendations from Critic `452fcf2`:

1. **Anchor-value correctness gate** — brief Section 2.5 cited "+24.75 OOS wpnl (BCH)" but actual /060 BCH OOS wpnl = +1.9078 (per `comparison.csv:18`); also cited "/060 LDO OOS wpnl -6.18" but actual is -19.72. Add Phase 5.5 sub-check: anchor values must match `comparison.csv` and `per_symbol.csv` byte-exactly.

2. **EDA T4 colsample-sampling discipline** — future feature-axis EDAs must report importance rank range across 3-5 colsample samples in [0.3, 1.0]. Label colsample=1.0 singleton as "UPPER BOUND" not "preview".

3. **Section 7 failure-mode probability calibration** — single-feature axes at single-seed n_trials=35 should weight NEGATIVE ≥25% (NOT 10%) per documented Optuna-overfit mechanism.

4. **/065+ axis-selection mandate** — /065 should be a NON-FEATURE axis (labeling, ensemble parameters, risk primitive, universe expansion) selected by QR with EDA backing per `feedback_v3_axis_selection_quant_discipline.md`. Defer phased-mass-expansion to CONFIRMATION-mode multi-seed runs.

5. **Engineering report IS-vs-OOS WR clarity** — engineering report mixed IS WR (27.3%) with OOS WR (18.2%) for LDO. Future reports must explicitly label.

6. **Drop NEGATIVE-IS-DEGRADATION-WITH-OOS-LOTTERY subtype** — does NOT belong in feedback rules. Section 8.4 already covers /064.

## 9. Structural inference — /060 is local optimum at single-seed n_trials=35

Two consecutive iterations show the same failure pattern:
- /063 mass 14→46: IS Δ -1.38, LDO 3 trades (75% drop)
- /064 single-feature 14→15: IS Δ -0.68, LDO 7.1% WR (1 win of 14)

**Both produced BCH-concentration + LDO-collapse**. The shared pattern is structural, not feature-specific. The /060 14-feature anchor stack is a LOCAL OPTIMUM at single-seed n_trials=35 — adding ANY feature destabilizes the LDO model toward BCH-concentration.

Implication: cycle 1 #6-9 EXPLORATIONs cannot productively add features. Pivot to non-feature axes (labeling, ensemble, risk primitive, universe) per Critic Rec #4.

## 10. Next Iteration Ideas

iter-v3/065 axis options (NON-FEATURE per Critic Rec #4):
- **(a) Universe expansion** — add 1 symbol (e.g., ALGO from cycle 4 history) to 4-symbol bundle. Tests whether universe diversification escapes /060 local optimum.
- **(b) Ensemble parameters** — modify confidence threshold calibration; test alternative ensembling (e.g., median vs mean of N seeds).
- **(c) Labeling parameter** — adjust triple-barrier σ_t multipliers or timeout. Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`, per-symbol customizations break IS aggregate at multi-seed; universal labeling change is the safer path.
- **(d) Risk primitive** — alternative vol-scaling formula (Sortino-based, downside-deviation), or alternative kill-switch (DSR-based).

Cycle 1 progress: 5/10 EXPLORATIONs done.

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE (anchor) | PROMISING-EXPLORATION |
| #2 | /061 | TRX RiskV2 anti-Kelly | INERT-AT-EXPLORATION (closed) |
| #3 | /062 | DSR_relative recalibration (Path C passive) | PASSIVE-DIAGNOSTIC (Path B4 to /069) |
| #4 | /063 | MASS FEATURE EXPANSION 14→46 | SUSPICIOUS-OOS-DOMINANT + IS-COLLAPSE (closed) |
| **#5** | **/064** | **Phased mass-expansion #1 (+adx_14)** | **NEGATIVE (closed)** |
| #6 | /065 | NON-FEATURE axis (TBD per QR EDA) | TBD |
| #7-9 | /066-068 | TBD | TBD |
| CONFIRMATION | /069 | Bundle + Path B4 implementation | TBD |
