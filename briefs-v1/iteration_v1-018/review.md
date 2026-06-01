# Phase 7.5 Critic Review — iter-v1/018

OVERALL: EXPLORATION-PROMISING (favorable-INERT side; conditional carry-forward to /027 CONFIRMATION substrate)

## Iteration Type
TYPE: EXPLORATION (cycle-3 #3 of 10; FIRST per-cohort specialization; HIGH-RISK declared)

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
walk_forward.py:113 carries `train_end_ms = test_start_ms - embargo_ms` UNCHANGED. Zero changes to labeling.py, lgbm.py, optimization.py. Section 2 EDA reads committed baseline reports (read-only consumption ≠ data snooping).

### Check 2 — Embargo Width: PASS
Single-symbol = no cross-symbol overlap. Gap scales correctly.

### Check 3 — Multiple-Testing Correction: INFORMATIONAL
DSR_OOS=-12.52 (deflated by single-cohort cross-cell aggregation). PSR_monthly_vs_0 OOS=**0.885**; PSR_monthly_vs_1 OOS=**0.553**. PBO N/A (single-cohort). Per EXPLORATION-mode rule, informational only. CONFIRMATION /027 must clear all thresholds at multi-seed.

### Check 4 — IC Correlation: PASS (vacuous)
No new feature families.

### Check 5 — ADF Stationarity: PASS (vacuous)
40 V1_FEATURE_COLUMNS_PRUNED unchanged.

### Check 6 — Pareto Dominance: N/A (single-seed EXPLORATION)

### Check 7 — Reproducibility: PASS
ENSEMBLE_SEEDS[0:3]=[42,123,456]; iter-stamped OOF parquet; explicit feature_columns; `set(symbols)==set(V1_ITER018_UNIVERSE)` guard verified.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Model C exclusive dispatch; A/D/E/F dropped; all other knobs frozen. per_symbol.csv 100% LINKUSDT IS+OOS — F-AXIS-MECHANISM #1 binary PASS. Single-axis SYMBOL DIMENSION isolation maintained.

### Check 13 — Anti-Pattern Static Scan: PASS
A1-A14 all PASS. QE diff scope is runner dispatch branch only.

### Check 14 — Axis Family Validation: PASS
`per-cohort-specialization-LINK` NEW 9th family. Prior 5 EXPLORATIONs all distinct. Rotation VALID. Orthogonality justification valid.

## Verdict Cell Assignment

- F1 LINK OOS Sharpe Δ vs LINK-in-pool +0.8184: **+0.9789 − 0.8184 = +0.1605** → INERT band
- F3 LINK IS Sharpe Δ vs LINK-in-pool +0.3724: **+0.3407 − 0.3724 = -0.0317** → INERT band
- F-AXIS #1 dispatch correctness: PASS (per_symbol.csv 100% LINKUSDT)
- F-AXIS #2 trade count: IS=154 [120,200] PASS / OOS=48 [25,75] PASS
- F5 PSR_monthly_vs_0 OOS=0.885 (≥0.40 PROMISING-INERT floor PASS)
- F7 LINK IS +52.58 / OOS +53.80 same-sign positive basin PASS
- n_eff_per_cell=9 (in [4,9] band)

**Section 8 row 2: PROMISING-INERT favorable-direction**. LINK-only specialist CONDITIONALLY CARRIED to /027 CONFIRMATION substrate; re-evaluate at multi-seed.

## Recommendations to QR

1. **/027 LINK-only specialist regression target = +0.80 NOT +0.98** (LM Master 7.4 §4). WR 50% identical = same signal cleaner Optuna trajectory; multi-seed will REGRESS toward LINK-in-pool +0.82 anchor. CONFIRMATION /027 bundle must size LINK-only at ~+0.80 contribution — over-anchoring on /018's +0.98 risks post-hoc rationalization when multi-seed delivers +0.78.

2. **Treat PSR_monthly_vs_0 0.885 as informational, NOT "near aspirational 0.95"**. 14-OOS-month sample; PSR CI wide. Don't cite 0.885 as edge significance at /019+ catalog rows.

3. **/019 ETH-only regime-gate**: keep single-axis isolation. Stateful gate requires deadlock-impossibility proof per A8.

## Path Forward (advisory)

1. **/019 ETH-only with stateless BTC-trend regime gate** — `per-cohort-specialization-ETH` (NEW 10th family). Mechanistically-orthogonal test (NEGATIVE-prior cohort + binary regime filter).
2. **/020 BTC-only specialization** — BTC IS catastrophic rotation vs OOS positive: isolating BTC characterizes intrinsic vs pool-borrowed.
3. **/021 LINK-only ATR follow-on** — CONDITIONAL on /019+/020 establishing 2+ cohort-baselines first (avoid burning /021 slot prematurely).

Constraints honored: per-cohort-specialization-{ETH,BTC} NEW family declarations; none in prior 5.

## BLOCK-PENDING-FIX Rerun Protocol

N/A — verdict is EXPLORATION-PROMISING favorable-INERT. /018 closes; /019 advances per Path Forward.
