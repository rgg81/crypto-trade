# Phase 7.5 Critic Review — iter-v1/022

OVERALL: BLOCK-PENDING-FIX — engineering_report.md MISSING (brief Section 10.4 BINDING violation, 4th cycle-3 incident post-/021 RESOLVED at `502d66e`)

## Iteration Type
TYPE: EXPLORATION — cycle-3 #7/10 — per-cohort-specialization-LTC (NEW 14th family)

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
`walk_forward.py:113` unchanged. 4 mandated regression tests at `tests/test_lookahead_embargo.py` lines 120/163/232/261. BTC trend gate past-only by construction. New asymmetric `long_only_mode` branch at `risk_v2.py:1409-1418` structurally past-only.

### Check 2 — Embargo Width: PASS
No labeling or walk-forward changes. `long_only_mode=False` default preserves /019 ETH call site bit-identically.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)
DSR -81.84 (legacy z-score artifact near zero IS Sharpe); LdP DSR 0.0; PSR_monthly_vs_0 OOS **0.0112** (deeply below 0.10 floor); n_eff 8 inside [4,10]. EXPLORATION-mode FAILs do NOT trigger BLOCK.

### Check 4 — IC Correlation: PASS (vacuous; no new features)

### Check 5 — ADF Stationarity: PASS
Documented exceptions only (cal_hour_norm, vol_atr_14).

### Check 6 — Pareto Dominance: N/A (single-seed EXPLORATION)

### Check 7 — Reproducibility: PASS
HEAD `374bf39`. Explicit feature_columns. Gate constants pinned. 117 IS + 48 OOS trades all LTCUSDT.

### Check 8 — Hypothesis-Implementation Alignment: FAIL (brief-internal inconsistency)
- Asymmetric gate matches brief Section 3.1 spec exactly. 1:1 on gate mechanism.
- **Feature_importance generation gap**: Brief Section 10.6 watch item #2 BINDS Critic verification of non-zero FI; runner code at `run_baseline_v1.py:1902` gates on `_iter021_fi_strategies` populated ONLY at /021 elif branch. /022 elif does NOT populate analogous list → FI CSV NEVER WRITTEN. Brief Section 3.1 code-change spec was incomplete relative to Section 10.6 promise. Brief-internal inconsistency, NOT Engineer deviation.

### Check 13 — Anti-Pattern Static Scan: PASS
A1-A14 clean. A8 N/A (gate stateless). A12 dual-DSR is carry-forward from /020+, not /022-introduced.

### Check 14 — Axis Family Validation: PASS
`per-cohort-specialization-LTC` NEW 14th family. Prior 5 distinct. ROTATION_STATUS=VALID.

## Engineering Report Presence: **FAIL**

`engineering_report.md` MISSING at both `briefs-v1/iteration_v1-022/` and `reports-v1/iteration_v1-022/`.

Brief Section 10.4 binding: "if engineering_report.md is MISSING at Phase 7.5 dispatch, Critic emits BLOCK-PENDING-FIX (per /020/021 precedent — 3rd consecutive incident permits NO retrospective forgiveness; Phase 7.5 holds for the report)."

Cycle-3 violation history:
- /019: MISSING (Critic Rec #1)
- /020: MISSING (Critic Rec #1 elevated)
- /021: PRESENT at `502d66e` (**3-strike incident RESOLVED**)
- **/022: MISSING — RE-VIOLATION post-resolution**

## Empirical Verdict (informational; expected post-fix re-eval result)

| Falsifier | Value | Band | Outcome |
|---|---|---|---|
| F-AXIS #1 (dispatch) | 117/117 IS + 48/48 OOS LTCUSDT | unique=={LTCUSDT} | **PASS** |
| F-AXIS #2 (trade count) | IS 117 / OOS 48 | QR [80,180]/[20,60] | **PASS** |
| F-AXIS #3 (LOAD-BEARING fire-rate) | IS 17.95% / OOS 29.17% | [15%,40%]/[5%,30%] | **PASS both bands** |
| F-AXIS #4 (n_eff) | 8 | [4, 10] | **PASS** |
| F1 OOS Sharpe Δ | -1.44 - (-0.27) = **-1.17** | ≤ -0.55 catastrophic | **NEG-CATASTROPHIC** |
| F3 IS Sharpe Δ | -0.009 | INERT band | INERT |
| F5 PSR OOS | 0.011 | ≥ 0.10 floor | **F5 catastrophic** |
| F7 sign agreement | IS +67.5% / OOS -34.9% | IS+OOS positive | **F7 FAIL** |

Section 8 hierarchy: F-AXIS #1 PASS, F-AXIS #3 within band, F3 INERT → NEGATIVE-CATASTROPHIC cell fires (F1 ≤ -0.55).

**Anchor-frame ambiguity** (Critic concern #4 CARRY-FORWARD from /020 Rec #2): comparison.csv "sharpe" is annualized daily Sharpe (`iteration_report.py:69`); brief Section 8 prose "F1 reads as per-trade Sharpe" is mathematically false. Under per-trade frame, OOS Δ = +0.148 borderline PROMISING-INERT; under daily-annualized binding (brief pre-registered), Δ = -1.17 catastrophic. **/023+ briefs MUST formalize.**

## LM Master 7.4 Cross-Check

- **Jaccard 0.10 IS / 0.093 OOS**: Verified qualitatively. ~90% new roster confirms basin relocation.
- **Direction shift 96% → 76% LONG**: gate operates on wrong subset because basin relocation dissolved the targeted phenomenon. Active short-side drag (-8.34%) structurally untouchable by long-suppress gate. **Critic CONCURS with LM Master 7.4 §3.**
- **PER-COHORT SATURATION RULE**: ASYMMETRIC_ROTATION cohorts (BTC /020, LTC /022) BOTH catastrophically failed under single-cohort isolation regardless of gate symmetry. LINK /018 + ETH /019 succeeded. Prior-class taxonomy partitions success cleanly. **Critic CONCURS: any cohort ASYMMETRIC_ROTATION is STRUCTURALLY INVIABLE for single-cohort isolation at current EXPLORATION budget. Codify in `feedback_v1_per_cohort_exploration_strategy.md`.**
- **Cycle-3 cumulative tracker**: 2 NEGATIVE-CATASTROPHIC in 7 iterations (/020 + /022); 3-in-a-row mandate NOT triggered (separated by /021); but axis-type saturated. Critic recommends /023 MANDATORY from feature-family / risk-primitive / labeling.

## Recommendations to QR

1. **Engineering-report contract — codify NON-RETROSPECTIVE-FORGIVENESS at orchestrator dispatch level**, NOT just brief prose. The brief pre-committed; the orchestrator dispatched Phase 7.5 with the report missing.

2. **Feature_importance generalization**: refactor `run_baseline_v1.py:1902` to use generic `_post_dispatch_fi_strategies` populated by EVERY elif branch that trains a model. Current `_iter021_fi_strategies` literal is fragile.

3. **Anchor-frame formalization** (CARRY-FORWARD from /020 Rec #2; ELEVATED to BINDING): pre-compute per-cohort daily-annualized Sharpe directly on baseline roster; lock F1 frame to comparison.csv "sharpe" semantics. The cycle-3 mixed-frame convention introduces verdict ambiguity.

## Path Forward (mandatory on BLOCK)

Per LM Master 7.4 §5 + /020 Critic convergence — /023 MANDATORY from these candidates (each from family NOT used in /018-/022):

1. **Funding-rate z-score (8h funding) — family `feature-family`** [PRIMARY]. NEW signal source; stateless; v1 LightGBM never had access; sidesteps cohort-isolation axis trap.

2. **Per-cohort drawdown brake — family `risk-primitive`**. Binary off/on at -25% per-cohort cumulative loss; addresses /020 + /022 symptomatically. STATEFUL → MANDATORY deadlock-impossibility proof per A8 + iter-v3/054.

3. **Meta-labeling architecture — family `labeling`**. AFML Ch. 3 secondary "trust/distrust" model. Risk: v3/017 NEGATIVE PATH C (over-filter).

Critic CONCURS with LM Master ordering: funding-rate > drawdown-brake > meta-labeling.

## BLOCK-PENDING-FIX Rerun Protocol

- **Specific defect**: `engineering_report.md` MISSING at `briefs-v1/iteration_v1-022/` and `reports-v1/iteration_v1-022/` — brief Section 10.4 binding violation.
- **Required fix**: Engineer writes `reports-v1/iteration_v1-022/engineering_report.md` per Section 10.4 + 10.2 spec. Required content: gate fire stats (fire_rate 21.21% long_only=True), F-AXIS-MECHANISM #1-4 reconciliation, Jaccard IS 0.10 / OOS 0.093, ORACLE EDA reconciliation against observed -1.17 outcome, basin-vector evidence per Section 10.6 watch item #3. SHA-stamp of HEAD `374bf39`.
- **Secondary**: feature_importance_*.csv files absent due to brief Section 3.1 ↔ Section 10.6 inconsistency. Document gap in engineering_report as known limitation deferred to /023's generic refactor.
- **Re-eval scope**: After engineering_report.md committed, Critic single-pass re-evaluation focused on report content completeness + basin-vector cite + Check 8 re-verification.
- **Final verdict after rerun**: empirically expected **EXPLORATION-NEGATIVE-CATASTROPHIC**. Rerun is contract enforcement, NOT empirical reversal. Critic verdict post-fix CANNOT be EXPLORATION-PROMISING.
