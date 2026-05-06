# Phase 7.5 Critic Review — iter-v3/013 — PRELIMINARY

**Mode**: ROUND 1 PRELIMINARY (no OVERALL verdict; awaiting QR clarifications).
**Scope discipline**: Per Section 0.5 TYPE=EXPLORATION, methodology axes 1, 2, 4, 5, 6, 8 are enforced; edge axis (DSR/PSR Check 3) is INFORMATIONAL only.

---

## Per-Check Preliminary Status

### Check 1 — Look-Ahead Audit: PASS
13 V3_FEATURE_COLUMNS unchanged. `natr_21_raw` (regime_v3.py:135) is past-only rolling ATR. Triple-barrier multipliers act on past-only NATR. `natr_21_raw` is in V3_NON_FEATURE_COLUMNS — never a model feature. Universe-axis (drop MKR) introduces no new feature paths.

### Check 2 — Embargo Width: PASS-WITH-DOCSTRING-FAIL
REQUIRED_GAP = 66 confirmed at runtime. `validation_v3.REQUIRED_GAP=66` constant correct. CPCV n_paths=45 confirmed. Symmetric purge applied with embargo=27.

**Methodology hygiene FAIL (informational, not edge-axis)**: `run_baseline_v3.py:206` docstring still says "Assert gap == REQUIRED_GAP == 88"; lines 211/218 contain stale "= 88" comments. Runtime is correct (66) but docstrings lie. To be fixed in iter-v3/014 first commit.

### Check 4 — IC Correlation: PASS
Max off-diagonal |IC| ≈ 0.685 (max_dd_window_50 × range_realized_vol_50); below 0.7 threshold. No new feature families.

### Check 5 — ADF Stationarity: WARN
1657/2041 (81.2%) cells stationary. 384 non-stationary concentrate in early walk-forward. Inheriting iter-v3/006-012 acceptance posture; demotion to PASS contingent on Clarification 1.

### Check 6 — Pareto Dominance: PASS (vacuous, single-seed)

### Check 8 — Hypothesis-Implementation Alignment: PASS
V3_MODELS now 3 entries (BCH/LDO/TRX). ITERATION_LABEL=v3-013. REQUIRED_GAP=66. Run.log "Active models: 3/3" + "n_symbols=3 = 66 [matches REQUIRED_GAP=66] PASS". Single-axis discipline holds. IS trades 209 < 240 saturation falsifier PASS.

---

## EXPLORATION-Specific Methodology Notes

**Trade-roster identity verified**: BCH/LDO/TRX OOS rows byte-identical between iter-v3/012 and iter-v3/013. Spot-check on LDO row 5: net 11.07% × 0.88 weight = 9.74 weighted — matches.

**Per-cell PBO tail at 0.99**: 2 cells with PBO=1.00, both TRXUSDT (2025-10, 2025-11). Same TRX months as iter-v3/012's tail; iter-v3/012's MKR cells mechanically removed by universe shrinkage. Recurring TRX tail is real, not an iteration artifact.

**LDO concentration drop (87.57% → 65.65%) is denominator-driven, NOT diversification**: LDO numerator weighted_pnl=+40.60 IDENTICAL between iter-v3/012 and iter-v3/013; total OOS denominator grew (46.36 → 61.85) because MKR's −15.49% drag removed. Same 10-trade lottery flag carries forward unchanged.

**OOS Sharpe lift attribution (+1.11) is ENTIRELY mechanical**: BCH/LDO/TRX OOS trade rosters bit-identical (per-symbol architecture means MKR training was independent of other symbols). The +1.11 lift comes from removing MKR's −15.49% contribution from the aggregate; ZERO contribution from Optuna re-optimization on 3-symbol universe.

**3rd consecutive favorable IS calibration overshoot** (010, 011, 013; 012 was null-result exception). Process recommendation: iter-v3/014 should widen PROMISING band priors based on 3-iteration empirical record.

---

## Clarifications Requested from QR

### Clarification 1 — ADF non-stationary cells (Check 5 demotion)
(a) Confirm 384 non-stationary cells concentrate in early walk-forward months (2020-2021 sparse-data)? If TRUE: WARN → PASS.
(b) Confirm V3_FEATURE_COLUMNS unchanged from iter-v3/009; this Check 5 inherits iter-v3/009's audit, informational-only for iter-v3/013?

### Clarification 2 — Catalog row classification (THE MAIN QUESTION)

Observed IS +1.0088 is +0.20 above iter-v3/012's +0.81 → squarely PROMISING band. **HOWEVER**, trade-roster identity means this is *structurally similar* to iter-v3/012's NULL-RESULT — behavioral effect of zero on 3 retained symbols, headline improvement entirely from removing a bad component (mechanical accounting), not from any positive interaction effect.

(a) Catalog as **EXPLORATION-PROMISING (mechanical)**: documents drop-MKR is strictly accretive. Pre-commit caveats (i)-(v).

(b) Catalog as **EXPLORATION-PROMISING-MECHANICAL** (NEW subtype, sister to NEGATIVE-no-effect): distinguishes "MKR drop reveals existing edge by accounting cleanup" from "ATR labeling change found new edge". Parallels iter-v3/012's null-result classification.

Critic strong prior is (b) — more honest, parallel to iter-v3/012's discipline. QR's call.

### Clarification 3 — TRX 2025-Q4 PBO=1.00 carry-forward + drop-TRX rule check

(a) Confirm catalog row will include pre-commit caveat that TRX/2025-Q4 has 2 PBO=1.00 cells — future CONFIRMATION QR uses (1 − max_per_cell_pbo) NOT just (1 − mean_pbo)?

(b) Confirm TRX recurring tail does NOT trigger drop-TRX rule analogous to MKR? TRX OOS is +4.04% net positive (0/1 OOS-negative), unlike MKR's 5/5 negative. TRX is the diversifier role.

### Clarification 4 — Stale docstrings + saturation predictor parametrization

(a) Confirm stale "= 88" docstrings in run_baseline_v3.py:206, 211, 218 fixed in iter-v3/014 first commit?

(b) Confirm iter-v3/014 brief saturation falsifier reads from derived `1.2 × counterfactual_n_trades` rather than hardcoded 240, so predictor robustly tracks universe size in future variations?
