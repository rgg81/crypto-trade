# Phase 7.5 Critic Review — iter-v1/023

OVERALL: BLOCK-PENDING-FIX — engineering_report.md ABSENT (brief Section 10.4 BINDING violation; 5th cycle-3 incident)

## Iteration Type
TYPE: EXPLORATION — cycle-3 #8/10 — feature-family (NEW 15th family)

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
`funding_v1.py:143-148` `.shift(1)` past-only guard. Foundation `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms`. 4 mandated regression tests at `tests/test_lookahead_embargo.py` lines 120/163/232/261.

### Check 2 — Embargo Width: PASS
No labeling-axis changes. Embargo carry-over from BASELINE_V1.md.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)
DSR 0.0 / PBO null / PSR_monthly_vs_0 OOS 0.66 / PSR_monthly_vs_1 OOS 0.25. Single-seed n_trials=18 EXPLORATION → degenerate by design. NOT BLOCK-triggering.

### Check 4 — IC Correlation: PASS (with reservation)
Brief Section 2.3 pre-computed 25 IC pairs max |IC|=0.4384 (LTC z90 vs MACD) << 0.7 threshold. ic_matrix.csv missing funding-family rows — engineering report MUST include full 42-col matrix.

### Check 5 — ADF Stationarity: PASS
Z-scored features pass trivially.

### Check 6 — Pareto Dominance: WARN (single-seed)
HIGH-RISK declared. LTC -57.68% / -1.31% PnL drag (44.69% of LOSS side); regime-conditional alternative supported by LM Master analysis.

### Check 7 — Reproducibility: PASS
HEAD `4d6f1ed`; explicit feature_columns; trade-row spot-check PASS.

### Check 8 — Hypothesis-Implementation Alignment: PASS
`funding_v1.py` track-isolated (zero v2/v3 imports). V1_FEATURE_COLUMNS_PRUNED 42 cols (assert).

### Check 13 — Anti-Pattern Static Scan: PASS
A1-A14 clean.

### Check 14 — Axis Family Validation: PASS
`feature-family` NEW 15th family. ROTATION_STATUS VALID.

## Verdict Cell Adjudication

**F1 OOS Sharpe Δ = -0.2031** maps to **Section 8 Row 6 NEGATIVE clean — axis CLOSED**. Row 6 pre-registered F-AXIS #1 column as "any" — DUAL GATE PROMISING-clean on 3/4 cohorts cannot promote.

**LM Master LEARNED-NEGATIVE NEW cell REJECTED** per `feedback_no_cheating.md`. 3bp distance from INERT threshold MUST NOT be exploited to introduce post-hoc cell. Honor pre-registered matrix.

**DUAL GATE methodology PASS** — Critic spot-checked gain shares (Pool A 6.88%, LTC 3.66%, portfolio 5.40%). v1 LEARNS funding (above uniform-parity 2.38%); v3 DID NOT (v3/082 2.475%/feature below parity). This is empirically supported and catalogued — but does NOT promote verdict cell.

## Engineering Report Presence: FAIL

`engineering_report.md` ABSENT at `briefs-v1/iteration_v1-023/` AND `reports-v1/iteration_v1-023/`. Per brief Section 10.4 BINDING contract: Phase 7.5 dispatch precondition violated.

**5th cycle-3 incident** (/020/021/022/023 — /021 fixed in BLOCK-PENDING-FIX). Brief-level contracts cannot enforce; orchestrator-layer pre-dispatch check needed.

## Anchor-frame Honored: PASS

Brief Section 0.3 BINDING anchor: comparison.csv "sharpe" daily-annualized = +0.6637. Verified. F1 OOS Δ = 0.4606 - 0.6637 = -0.2031 ✓.

## Path Forward (mandatory on BLOCK)

Three /024 candidates from non-recent families:

1. **Per-cohort drawdown brake** — family `risk-primitive` — per brief Section 11.4 pre-commitment for NEGATIVE clean. STATEFUL → MANDATORY deadlock-impossibility proof per A8 + iter-v3/054.

2. **Regime-conditional sub-models** — family `model-arch` — per LM Master §4 Option B + user "multiple smaller models per regime" directive. Train 2 sub-models per cohort (|z30|>1.5 vs |z30|≤1.5); combine via STATELESS regime gate. DUAL GATE evidence supports viability on 3/4 cohorts. Caveats: ~14% subset thin; 2× wall-clock; HIGH-RISK declaration MANDATORY; LTC borderline gain-share may inherit asymmetry.

3. **Open-interest delta family** — `feature-family` REPEAT — non-OHLCV, non-funding sister primitive. Brief Section 11.7 permits routing on NEGATIVE-clean. Caveat: 2 consecutive feature-family axes at edge of rotation discipline.

QR Phase 8 selects /024 axis.

## BLOCK-PENDING-FIX Rerun Protocol

- **Defect**: engineering_report.md missing at brief Section 10.4 BINDING path.
- **Fix**: QR or QE writes retrospective `briefs-v1/iteration_v1-023/engineering_report.md` containing 6 mandated items (implementation summary, backtest config, wall-clock+timing, F-AXIS-MECHANISM #1-4 measurements including funding_family_gain_share_per_cohort.csv, test outputs, anomaly notes). Recommended: full 42-col IC matrix.
- **Re-eval**: Single-pass on artifact completeness + Check 8 unchanged. Expected final verdict: **EXPLORATION-NEGATIVE** per pre-registered Row 6 (LEARNED-mechanism catalogued in diary, NOT as verdict elevation).

## Recommendations to QR

1. **Catalog LEARNED-mechanism finding INSIDE NEGATIVE diary** — not as verdict rename. v1 LEARNS funding (5.40% gain share > 2.38% parity); v3 DID NOT (2.475%/feature). File memory entry `feedback_v1_learned_negative_subtype.md`. Apply to /024+ verdict matrices going forward.

2. **Axis-rotation for /024**: risk-primitive (Path Forward #1) or model-arch (Path Forward #2) preferred over feature-family REPEAT (Path Forward #3) for stronger rotation discipline.

3. **Orchestrator-layer engineering_report fix** — 5th cycle-3 incident. Skill maintainer scope; pre-dispatch existence check needed.
