# Phase 7.5 Critic Review — iter-v1/017

OVERALL: EXPLORATION-NEGATIVE — F1 OOS Δ -0.0908 anti-direction (INERT-negative), F-AXIS-MECHANISM #3 (n_eff) FAIL, F8 OOS trade-count breach; universe expansion is structural-cell candidate not a merge ingredient.

## Iteration Type
TYPE: EXPLORATION (cycle-3 #2 of 10; HIGH-RISK declared)

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
walk_forward.py:113 carries `train_end_ms = test_start_ms - embargo_ms` UNCHANGED. No features added. SOL feature regen verified pre-launch. 4 mandated regression tests present.

### Check 2 — Embargo Width: PASS
6-sym universe at 21-candle timeout × 480-min × 8h candles; required gap wired through compute_embargo_candles. Symmetric application verified.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)
DSR=0.0, PBO=null, PSR_monthly_vs_1 OOS=0.4173. Per EXPLORATION-mode artifact rule, informational ONLY. **Notable positive**: PSR_monthly_vs_0 OOS=0.808 (+0.68 jump from /016's 0.125) — load-bearing basin-health signal.

### Check 4 — IC Correlation: PASS
No new features added. Family-level IC ic_matrix.csv shows structural pre-existing baseline relationships unchanged.

### Check 5 — ADF Stationarity: PASS
All scored features bonferroni-pass; sparse MACD rows with n_obs=0 are not predictors driving Sharpe.

### Check 6 — Pareto Dominance: N/A (single-seed EXPLORATION)

### Check 7 — Reproducibility: PASS
HEAD `f0dccd3`; active_feature_columns passed explicitly through all 5 models; inner ensemble seeds [42, 123, 456] literal.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 1 hypothesis tested with attributable evidence: (a) LINK OOS share dropped 137%→107%; (b) ETH OOS share moved /016 +76% → /017 -56% (4 positive symbols dilute); (c) SOL OOS 51 trades PASS. Single-axis clean.

### Check 13 — Anti-Pattern Static Scan: PASS
A1-A14 all PASS.

### Check 14 — Axis Family Validation: PASS
`universe` family in NONE of prior 5 EXPLORATIONs. Rotation VALID. HIGH-RISK declaration honest.

## Verdict Cell Determination (Section 8)

- F1 OOS Δ = **-0.0908** → INERT band [-0.20, +0.20]
- F3 IS Δ = **+0.0509** → INERT band
- F7 per-symbol direction: 4/6 same-sign portfolio = PARTIAL
- F8 trade band: IS 842 PASS; OOS **301 EXCEEDS upper-end 284** by +17 trades (mechanical band breach)
- F-AXIS-MECHANISM: #1 PASS, #2 PASS, **#3 FAIL** (n_eff=9, below [10, 18])

**Strict Section 8 reading**: F1 anti-direction + F-AXIS-MECHANISM #3 FAIL + F8 OOS breach → **EXPLORATION-NEGATIVE** (anti-direction-INERT subtype).

**LM Master Phase 7.4 reframing**: PROMISING-INERT (PSR jump 0.68; ETH dilution partial; basin-health positive). Critic accepts the basin-health evidence as informative but NOT as merge signal — strict adherence to verdict matrix per cycle-3 discipline requires NEGATIVE label when F1 Δ is anti-direction.

**Critic-LM Master delta matters**: PROMISING-INERT implies "carry SOL forward to /027 substrate"; NEGATIVE implies "axis closed at +SOL alone, evaluate /018 carefully". For cycle-3 conservative anchor: NEGATIVE. QR/CONFIRMATION-bundling decision at /027 should re-validate at multi-seed before treating SOL as load-bearing substrate.

## Process-Level Findings

1. **Engineering report MISSING (6th-strike)**. `reports-v1/iteration_v1-017/engineering_report.md` does not exist. Phase 6 contract addition needed: fail-loud if report absent at handoff.

2. **F-AXIS-MECHANISM #3 REFUTED 3rd time** (n_eff band [11, 17] failed). LM Master corrected to [8, 13] at Phase 7.4 §4 + demoted to INFORMATIONAL for universe axes. Critic accepts forward-binding for /018+.

3. **PSR jump 0.125→0.808 is load-bearing**. PSR_monthly_vs_0 should be elevated to first-class basin-health metric in cycle-3.

4. **USER STRATEGIC RECOMMENDATION at /017 closeout (2026-05-26)**: pivot cycle-3 EXPLORATION methodology from "global axes on pooled universe" to "per-cohort specialization (1-3 symbols); CONFIRMATION bundles specialists for diversification edge". v3-architecture-precedent (V3-BCH, V3-LDO, V3-TRX). Justified by cycle-2 NO-MERGE + cycle-3 /016 NEGATIVE + /017 PROMISING-INERT (global axis approach saturated).

## Recommendations to QR

1. **/018 axis selection (REVISED per user directive)**: pivot to per-cohort EXPLORATION methodology:
   - LM Master Phase 7.4 §5 recommended +XRP (universe continuation, 65%) — DEFERRED per user pivot
   - NEW /018 candidate: **LINK-only specialized EXPLORATION** (LINK has structural OOS edge across 7+ iterations — under-exploited by pooled training)
   - Alternative: ETH-only with regime-conditional gate (address known drag)
   - Alternative: BTC-only with BTC-specialized config (separate from pooled Model A)

2. **Process: engineering_report.md MUST EXIST** at Phase 7.5 dispatch. Phase 6 contract addition needed.

3. **n_eff band corrected to [8, 13]** for universe + sample-weighting axes; outside-band only when axis structurally touches label-shape or weight-distribution.

## Path Forward (cycle-3 strategy pivot per user 2026-05-26)

**NEW EXPLORATION methodology**: per-cohort specialization (1-3 symbols) with cohort-specialized features/config; CONFIRMATION at /027 bundles specialists for diversification edge.

Candidates ordered by structural prior strength:

1. **LINK-only specialized** — strongest structural OOS edge across 7+ iterations (LINK OOS positive at /011, /012, /013, /014, /015, /016, /017). Test LINK-specific features (e.g., DeFi-correlation features, LINK-specific volatility scaling). Risk: single-symbol model can't diversify; if LINK OOS edge is regime-bound (post-2024 DeFi cycle), it may not generalize. **HIGH STRUCTURAL PRIOR.**

2. **ETH-only with regime-conditional gate** — ETH structural drag is the strongest negative pattern; ETH-specific gate addresses head-on. Mechanism: BTC-trend-conditional kill OR per-symbol drawdown brake stateless. Pre-committed at /017 brief Section 11.3 — explicit conditional fire. **MEDIUM STRUCTURAL PRIOR.**

3. **BTC-only with specialized config** — BTC IS at /017 was -93.81 (catastrophic rotation); BTC OOS +15.11 (positive). Pooled Model A (BTC+ETH) trains badly on BTC. Separating BTC may reveal BTC-specific edge. Risk: BTC-only model may underperform vs BTC-in-pool. **MEDIUM STRUCTURAL PRIOR.**

LM Master Phase 7.4 staked +XRP at 65% MEDIUM-HIGH; this is now SUPERSEDED by user strategic recommendation. /018 brief should justify per-cohort axis selection with explicit reference to user 2026-05-26 directive.

## BLOCK-PENDING-FIX Rerun Protocol

N/A — verdict EXPLORATION-NEGATIVE anti-direction-INERT. /017 closes; /018 advances under NEW per-cohort specialization methodology.
