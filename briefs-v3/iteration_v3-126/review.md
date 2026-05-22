# Phase 7.5 Critic Review — iter-v3/126

OVERALL: EXPLORATION-NEGATIVE — NEGATIVE-catastrophic on F1 (IS Δ −1.21, OOS Δ −1.08 vs /121 PUBLIC); 5th cycle-7 NEGATIVE-class result and 3rd recurrence of the EDA-vs-production walk-forward disagreement pattern; the methodology itself, not the axis, is now systemically suspect.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle 7 slot #5 of 10; FEATURE-CADENCE-STACK axis class)

## QR Response Considered (Round 2 only)
Single-round emit. No QR clarifications requested — every check is unambiguous on the artifacts.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
The /126 axis introduces `d24_ret_autocorr_lag1_50` via `add_multifreq_v3_24h_features` at `multifreq_v3.py:243-352`. merge_asof uses `direction='backward'` + `allow_exact_matches=True` with `left_on='open_time'` and `right_on='bar_close_time'` — guarantees `bar_close_time <= open_time` for every joined row. T2 audit: 0 violations across 14,130 joined rows. No look-ahead.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP = 66 unchanged. /058 walk-forward fix intact.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)
DSR=0.0, PSR=0.1016 (catastrophic), PBO=0.1189 PASS, frac_pos=0.6444 PASS. PSR collapse reflects the −0.11 OOS daily Sharpe. PBO axis (only EXPLORATION-mode hard gate) passes.

### Check 4 — IC Correlation: PASS
Production max |IC| 0.127 with btc_ret_14d (EDA predicted 0.160 — production LOWER). Feature is structurally orthogonal. NEGATIVE outcome cannot be attributed to redundancy.

### Check 5 — ADF Stationarity: WARN-BORDERLINE
Feature stationary in 66/157 monthly windows (~42%); fully stationary only after 50-bar warmup. Early IS (2020-2023) non-stationary; later IS (2024-2025-03) stationary. Causal contributor to TRX 2020-2022 training on noisy partial-warmup feature → over-trading low-WR direction → IS-OOS sign inversion. WARN — pre-registered prediction in brief did not surface this risk explicitly.

### Check 6 — Pareto Dominance: N/A (single-seed EXPLORATION)

### Check 7 — Reproducibility: PASS
Setup `70a6b3c` verified. Explicit feature_columns. Trade-arithmetic spot-checks clean.

**Note — comparison.csv per_symbol aggregation defect**: `comparison.csv` per_symbol numbers don't match granular `out_of_sample/per_symbol.csv` (defect in aggregation writer; headline metrics intact). Flag for QE to investigate in /127 setup — not blocking.

### Check 8 — Hypothesis-Implementation Alignment: PASS
All 5 brief Section 3 changes verified. V3_MODELS revert (ATOM/RUNE/UNI → BCH/LDO/TRX) is baseline-restore not second axis. No scope creep.

## Verdict Mechanism Analysis

F1 falsifier fires by wide margin on both axes (IS Δ −1.21 / 3× threshold; OOS Δ −1.08 / 3.6× threshold). Most aggressive IS-OOS sign inversion in cycle-7 (TRX IS −30.88 / OOS +27.05 with WR 28.7% → 48.1%, 19.4pp reversal).

EDA T5 ranks 1-3 collapsed to production ranks 4-11 — **3rd cycle-7 occurrence** (after /122, /123). Pattern is structural to single-window EDA importance methodology at depth-3 vs production Optuna depth-3-5 across rolling walk-forward windows.

**Load-bearing finding**: The /126 EDA was the CLEANEST in v3 history (6/6 pre-flight gates PASS at substantial margins). Result catastrophic. **EDA methodology should be considered FALSIFIED for NEW-feature axes** pending replacement with production-walk-forward-simulating pre-flight gate. Single-window EDA importance + 5-fold AUC lift is a BIASED ESTIMATOR for rolling-walk-forward production performance.

## Recommendations to QR for /127 Axis Selection

1. **EDA methodology overhaul before any further feature axis.** 3-occurrence pattern (/122 /123 /126) is sufficient evidence that single-window EDA gates are biased estimators. Future feature-axis briefs must either (a) include closed-loop walk-forward simulator running Optuna across N=10+ training-window-starts computing importance/Sharpe-Δ DISTRIBUTIONS (not point estimates), OR (b) abandon NEW-feature axes entirely for cycle-7.

2. **Behavioral-effect predictor MUST become strict pre-merge falsifier.** /126 actual IS trade-roster change was +5.8%, BELOW brief's predicted [10, 30]% band. Engineering report cited wrong /121 reference; future briefs must compute predictors against verified comparison.csv n_trades row.

3. **/127 axis recommendation — DRAWDOWN BRAKE CREATIVE OUT-OF-BOX (Critic Priority 1 from /124).** Cycle-7: 5/10 NEGATIVE; universe + frequency UNLOCKED but feature-axis methodology FALSIFIED; LightGBM locked; RiskV2 knob saturated. Candidates:
   - **PRIMARY (1) Drawdown brake creative out-of-box** — RECOMMENDED. Closed-loop simulator with explicit deadlock-impossibility proof (per /054). LAST viable structural axis class; cycle-7 has exhausted NEW-feature axes + universe-substitution.
   - (2) Vol-kurtosis-matched universe — DEPRECATED at /125 NEGATIVE-catastrophic.
   - (3) "Yet another creative axis" — REJECTED. Cycle-7 has run out of creative-feature variations with negative prior.
   - (4) Cycle-7 close-early — VIABLE-FALLBACK ONLY. 10:1 cadence canonical (`feedback_v3_strict_10_to_1_cadence.md`); closing at 5/10 requires user override + CONFIRMATION at /127 against /121.

   **PRIMARY: /127 = drawdown brake creative out-of-box, closed-loop simulator as part of EDA, deadlock-impossibility proof in brief Section 2.** SECONDARY: close-early cycle-7 with bootstrap CONFIRMATION re-validating /121.

## Clarifications Requested from QR — NONE
