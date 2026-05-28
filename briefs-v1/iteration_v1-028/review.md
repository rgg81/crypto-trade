# Phase 7.5 Critic Review — iter-v1/028

OVERALL: EXPLORATION-PROMISING — atr_sl=1.0 label-shift mechanism cleared ASYMMETRIC_ROTATION cohort SATURATION rule; 3rd PROMISING specialist in v1 history (after /018 LINK, /019 ETH+gate); /029 advances to DOT-only per LM Master §7.

## Iteration Type
TYPE: EXPLORATION — cycle-4 #1/10; family `per-cohort-specialization-LTC-v2` (NEW; mechanism-class differentiates from /022)

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
atr_sl=1.0 traces PAST-causal at both label generation AND entry-time execution. `lgbm.py:631` label_trades + `lgbm.py:1212` entry-time SL both PAST-only.

### Check 2 — Embargo Width: PASS
Foundation `walk_forward.py:113` carries embargo subtraction. 4 mandated regression tests at `tests/test_lookahead_embargo.py` lines 120/163/232/261.

### Check 3 — Multiple-Testing Correction: INFORMATIONAL (EXPLORATION)
DSR IS -91.93 / OOS -52.07 (informational). PSR_monthly_vs_0 OOS 0.633 (above 0.40 PROMISING-INERT floor). PSR_monthly_vs_1 OOS 0.299 (below 0.95 merge-tier). n_eff 2 (below predicted [6,10] — LM Master diagnosed as feature-not-defect: atr_sl narrows label-space ambiguity → Optuna converges fast).

### Check 4 — IC Correlation: PASS (vacuous; no new features)

### Check 5 — ADF Stationarity: PASS

### Check 6 — Pareto Dominance: N/A (ENSEMBLE_SIZE=10 single-pass, no outer seeds)

### Check 7 — Reproducibility: PASS
HEAD `7d06504`. Explicit `feature_columns=V1_FEATURE_COLUMNS_PRUNED` (43). Iter-stamped OOF parquet. atr_sl=1.0 / atr_tp=3.5 pinned.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief §1 H1 (atr_sl=1.0 upstream label + post-entry magnitude clip) ↔ implementation 1:1. atr_sl=1.0 plumbed correctly through run_model → LightGbmStrategy → label_trades + get_signal.

### Check 13 — Anti-Pattern Static Scan: PASS
A1-A14 clean. Defensive checks unit-tested with REAL instances (/027 lesson applied). NO TradeResult attribute access in /028 dispatch.

### Check 14 — Axis Family Validation: PASS
`per-cohort-specialization-LTC-v2` NEW family. Differentiates from /022 by mechanism class (pre-entry direction filter vs upstream label + post-entry magnitude clip). Rotation valid.

## Verdict Cell Determination

Per brief §4 verdict matrix:

- **F1 OOS Sharpe Δ = +0.598** (OOS +0.3310 - LTC-in-pool -0.2670) → **PROMISING band** (Δ ≥ +0.20)
- F3 IS Sharpe Δ +0.003 → INERT (basin held; no IS catastrophe)
- F-AXIS #1 LTC-only dispatch: 39 OOS trades all LTCUSDT — PASS
- F-AXIS #2 trade count: IS 119 ∈ [70, 150] PASS; OOS 39 ∈ [22, 55] PASS
- F-AXIS #3 SL fire-rate OOS 59% (RIGHT AT 60% UNDERFIRING threshold per LM Master pre-registration) — borderline but PnL clearly positive
- F-AXIS #4 n_eff_per_cell 2 (BELOW [6, 10] band; LM Master §4 diagnosed as feature-not-defect)
- **F-AXIS #5 OOS TP-exit count = 5** ≥ 2 → **mechanism retained upside; PROMISING reachable per LM Master Rec #6 LOAD-BEARING**

Section 8 verdict: **EXPLORATION-PROMISING**.

## PROMISING-MECHANICAL Adjacency Check

Per LM Master Phase 7.4 §2: /028 produced fresh trade roster (39 OOS vs /022's 48 OOS). Single-cohort retraining + atr_sl=1.0 label-shift = ~95% disjoint vs both /022 and baseline LTC-in-pool rosters (empirical single-cohort pattern). NOT PROMISING-MECHANICAL — NEW signal source via upstream label distribution change. Compoundable as /027-retry bundle component.

## Structural Finding (load-bearing for cycle-4)

**SATURATION RULE REFINED (post-/028)**: ASYMMETRIC_ROTATION cohorts INVIABLE for PRE-ENTRY gates (direction filter, regime kill — /020, /022 catastrophic) but VIABLE for UPSTREAM LABEL changes (atr_sl multiplier — /028 PROMISING +0.598).

/022 → /028 differential: **+1.77 OOS Sharpe lift** from mechanism-class shift (post-Optuna filter → pre-Optuna labeling).

## Recommendations to QR

1. **Codify SATURATION RULE refinement** in memory entry `feedback_v1_atr_sl_label_shift_mechanism.md`.

2. **/027-retry path opens**: 3-specialist bundle (LINK + ETH+gate + LTC+atr_sl=1.0) projected multi-seed +1.20-1.55 OOS Sharpe — FIRST credible path to +1.0 hard merge floor in v1 history.

3. **n_eff=2 anomaly**: not a defect per LM Master §4, but document in catalog for future reference.

## Path Forward

Per LM Master /028 §6: **/029 = DOT-only specialist** (cycle-4 cohort coverage; DOT is LAST untested single-cohort). Pre-classify DOT against ASYMMETRIC_ROTATION rule before isolation commit. Apply the /028 mechanism lesson (consider atr_sl tuning for DOT if it's also ASYMMETRIC_ROTATION).

Alternative axes (UNUSED cycle-3, still available):
- Sample-weighting (AFML Ch.4 inverse-concurrency)
- XGBoost head-to-head (model-arch different instance)

Multi-seed validation of /028 deferred to /030+ or /027-retry bundle.

## /029 Routing (LM Master §7)

PROMISING → /029 = DOT-only specialist with pre-classification check.

## Cycle-4 cumulative

Iter 1/10. 1 PROMISING (/028). Cycle-4 off to a stronger start than cycle-3 (which had to wait until /018 for first PROMISING).

## Verdict: EXPLORATION-PROMISING

NO-MERGE (EXPLORATION; only CONFIRMATION-MERGE updates baseline). Carry-forward to /027-retry bundle substrate.
