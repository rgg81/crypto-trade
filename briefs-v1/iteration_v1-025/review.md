# Phase 7.5 Critic Review — iter-v1/025

OVERALL: BLOCK-PENDING-FIX — engineering_report.md MISSING (brief Section 10.4 BINDING violation; 6th cycle-3 incident). Underlying iteration outcome is **EXPLORATION-NEGATIVE-CATASTROPHIC** (LEARNED-NEGATIVE subtype) — final verdict after retrospective fix.

## Iteration Type
TYPE: EXPLORATION (cycle-3 #10/10 — LAST before /027 CONFIRMATION)

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
`open_interest_v1.py:127-138` past-only `.shift(delta_window)` + `.shift(1)` on rolling stats. Foundation `walk_forward.py:113` unchanged. 4 mandated regression tests at lines 120/163/232/261. No `fit_transform(combined)`, no forward-window std.

### Check 2 — Embargo Width: PASS
`embargo_candles = 21` (10080 min / 480 min). Symmetric walk-forward + CPCV gap = (21+1) × n_symbols.

### Check 3 — Multiple-Testing Correction: INFORMATIONAL (EXPLORATION)
DSR=0.0 / PSR_monthly_vs_1 OOS 0.055 / PBO=null. EXPLORATION budget; informational only.

### Check 4 — IC Correlation: PASS
Max |IC(oi_delta_30_z90, baseline TOP5)| = 0.154 << 0.7. Max |IC vs funding| = 0.135 << 0.5. Orthogonal. NOTE: `ic_matrix_oos.csv` missing (under engineering_report scope).

### Check 5 — ADF Stationarity: PASS
oi_delta_30_z90 stationary by construction (ADF p≈0). 42 other features pass Bonferroni p=0.000259.

### Check 6 — Pareto Dominance: N/A (single-seed EXPLORATION)

### Check 7 — Reproducibility: PASS
HEAD `94fb3e1`; `feature_columns=list(V1_FEATURE_COLUMNS_PRUNED)` (43 cols, explicit); dispatch keyed on `iteration_label == "v1-025"`. Trade-row spot check PASS.

### Check 8 — Hypothesis-Implementation Alignment: PASS (on what shipped)
Brief Section 1 H1 ↔ implementation 1:1. V1_FEATURE_COLUMNS_PRUNED 42→43 (assert verified). Track isolation: zero v2/v3 imports.

### Check 13 — Anti-Pattern: PASS
A1-A13 all clean.

### Check 14 — Axis Family Validation: PASS
`feature-family` REPEAT under Critic /024 §11.7 permission for borderline 2-consecutive on NEW data class. NEW open_interest_v1.py + GROUP_REGISTRY entry + dispatch branch. NO scope creep.

## Headline Outcome (verdict after BLOCK-PENDING-FIX)

- **F1 OOS Sharpe Δ = -1.40** (-0.7353 - 0.6637) → **NEGATIVE-CATASTROPHIC** per Section 8 Row 7 (≤ -0.55)
- 2nd-worst cycle-3 (after /020 -0.86, /022 -1.17)
- **F-AXIS #1 DUAL GATE PASS 4/4 cohorts** (Pool A rank 4 / 7.53%; LINK rank 5 / 6.39%; LTC rank 5 / 8.00%; DOT rank 4 / 7.69%; portfolio 7.49%)
- F1 magnitude OVERRIDES DUAL GATE per pre-registered hierarchy
- F3 IS Δ +0.05 INERT (no IS basin collapse)
- 498 IS / 261 OOS trades within bands
- Classification: **LEARNED-NEGATIVE-CATASTROPHIC** (NEW subtype — feature learned above parity AND OOS catastrophic; not in v1 catalog before /025)

## Critic-Specific Concerns Adjudicated

1. **F1 -1.40 overrides DUAL GATE PROMISING-clean**: CONCUR. Pre-registered Section 8 Row 7 binding.

2. **Engineering report missing (6th cycle-3 incident)**: CONFIRMED. /023 closed via BLOCK-PENDING-FIX retrospective fix; /024 broke streak; /025 regresses. BLOCK-PENDING-FIX trigger.

3. **/027 bundle LOCKED**: CONCUR. LM Master Post-Mortem §4: 2 specialists (LINK + ETH+gate) at --seeds 2 / n_trials=35 / cross-corr pre-validation MANDATORY.

4. **/023+/025 n=2 structural verdict**: CONCUR. Pool Model A joint training + n_trials=18 below TPE saturation = LEARNED-NEGATIVE for ANY NEW feature reaching rank ≤5. Codify as `feedback_v1_pool_a_new_feature_lneg.md`.

5. **EDA Sharpe-proxy discount ~50% for non-trade-attributed bands**: CONCUR. Brief Q4 ORACLE was distribution-level not trade-conditioned. Codify as `feedback_v1_oracle_eda_trade_attribution.md`.

## Path Forward (mandatory on BLOCK)

3 candidates from non-recent families (post-/020/021/022/023/024):

1. **DOT/LTC-specialist with NEW risk gate** — `per-cohort-specialization`. Per-cohort specialists with INDEPENDENT priors (like LINK +0.80, ETH+gate +0.50) are the ONLY cycle-3 OOS survivors. Cycle-4 should EXTEND specialist strategy AVOIDING the Pool A joint-loss-surface trap.

2. **Sample-weighting / class-balancing** — `sample-weighting` (UNUSED cycle-3). AFML Ch.4 inverse-concurrency weighting. Mechanism: reduce basin formation around overlapping windows; push Optuna toward robustness.

3. **XGBoost head-to-head** — `model-arch` REPEAT (different axis instance vs /024 partition). Level-wise growth + cross-entropy may distribute split allocation more uniformly than LightGBM leaf-wise (which amplified /025 rank-4 basin pull).

## BLOCK-PENDING-FIX Rerun Protocol

- **Defect**: `briefs-v1/iteration_v1-025/engineering_report.md` MISSING + 4 mandated CSV deliverables absent (`oi_coverage_check.csv`, `feature_importance_per_fold.csv`, `ic_matrix_oos.csv`, `oracle_q4_oos_attribution.csv`).
- **Required fix**: QE writes engineering_report.md per Section 10.4 8-item template + 4 CSVs computed retrospectively from existing trades.csv + comparison + feature_importance artifacts. NO backtest re-run.
- **Re-eval**: Single-pass Check 8 re-check + deliverable completeness.
- **Final verdict post-fix**: EXPLORATION-NEGATIVE-CATASTROPHIC (LEARNED-NEGATIVE subtype). /027 bundle 2-component LOCKED. Target +1.10 to +1.30 OOS Sharpe at multi-seed.
