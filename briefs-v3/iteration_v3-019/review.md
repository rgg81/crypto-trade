# Phase 7.5 Critic Review — iter-v3/019

OVERALL: EXPLORATION-PROMISING-INERT (Falsifier 4 FIRES; lift attributable to n_trials=10 Optuna lottery, NOT to funding-rate signal — same INERT pattern as iter-v3/015 microstructure precedent)

This iteration is NOT a BLOCK. All 12 standard methodology checks PASS. The classification is the EXPLORATION verdict ladder: PROMISING-INERT is the brief §4.4-locked outcome when (a) IS Sharpe Δ > +0.10 vs anchor AND (b) Falsifier 4 fires. Both conditions hold. Per `feedback_v3_iter019_axis_priorities.md` LOCKED 2026-05-07 + `feedback_promising_mechanical_subtype.md` precedent (sister classification), this iteration produces NO catalog candidate for future CONFIRMATION bundling.

## Per-Check Status (12 checks; all PASS or PASS-WITH-WAIVER per EXPLORATION carve-out)

### Check 1 — Look-Ahead Audit: PASS
`compute_funding_rate_zscore` at `funding_v3.py:131-144` strictly past-only via `s.shift(1)` then rolling. Funding rate at bar t corresponds to settlement-time, knowable from prior 8h close. Adversarial unit tests (`test_past_only_value_at_row_n`, `test_past_only_numerator_uses_bar_t_rate`) verify by spike-perturbation analysis.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP=66=(21+1)×3 verified at runtime via `_validate_label_leakage_gap()`. 14th feature does not affect gap formula.

### Check 3 — Multiple-Testing Correction: PASS-WITH-EXPLORATION-MODE-CAVEAT
DSR=+0.0167 (FIRST positive in v3) is EXPLORATION-mode structural artifact: at n_trials=30, E[max_SR]=√(2 ln 30)=2.608; observed annualized Sharpe=4.004 → marginal positive deflation. NOT comparable to CONFIRMATION-mode DSR (n_trials=1500, E[max_SR]=3.369). PBO mean 0.0971; max 1.0 (TRX/2025-Q4 carry-forward). PSR 1.0 saturated EXPLORATION artifact. None applicable as MERGE gates at EXPLORATION.

### Check 4 — IC Correlation: PASS
Max |IC| funding_rate_zscore_30 vs existing 13 = 0.287 (vs vwap_dev_20 Pearson). Below 0.50 strict target and 0.70 hard gate. NEW feature is structurally orthogonal — carries position/leverage info not captured by price/return/volume features. The 14/14 importance ranking is NOT a redundancy artifact.

### Check 5 — ADF Stationarity: PASS
funding_rate_zscore_30 ADF stat at IS-window-end: BCH -17.06, LDO -14.10, TRX ~-13.5, all p=0. Z-scoring is structurally stationary by construction.

### Check 6 — Pareto Dominance: PASS-WITH-EXPLORATION-WAIVER (single-seed)
**CRITICAL precedent flag**: iter-v3/013 produced +1.01 IS / +2.70 OOS at single-seed --exploration --n-trials 10, FALSIFIED at iter-v3/018 multi-seed (62% IS / 86% OOS reduction). iter-v3/019 produces +1.16 IS / +0.78 OOS — even larger IS overshoot on the same single-seed-lottery surface. Catalog row MUST flag "single-seed lottery suspect; do NOT bundle pre-multi-seed-validation".

### Check 7 — Reproducibility: PASS
Setup `d9f643b`, fix `9806dfb`, gate `f728e7f`, brief `db6e326`. Library stack pinned. `_verify_feature_columns()` asserts len==14 + funding_rate_zscore_30 present + tbr_zscore_30/vwap_dev_50 absent.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Single-axis discipline preserved: V3_FEATURE_COLUMNS 13→14 is the ONE varied axis. No labeling change, no risk gate change, no universe change, no model architecture change. The `funding_v3.py` module (209 lines) + new fetcher path are SUPPORTING infrastructure.

### Check 9 — Symbol Exclusion Enforcement: PASS
{BCH, LDO, TRX} ∩ V3_EXCLUDED_SYMBOLS = ∅.

### Check 10 — Feature Isolation Enforcement: PASS
Zero cross-track imports. funding_v3.py uses only stdlib + numpy + pandas.

### Check 11 — Forming-Candle Audit: PASS-INHERITED

### Check 12 — Library Version Pinning: PASS-WITH-FLAG
sklearn version drift 1.8.0→1.6.0 (brief vs report) — not BLOCK material since v3 ML pipeline does not use sklearn-version-sensitive functions; flag for future iterations to pin sklearn explicitly.

## Falsifier 4 Validation (CRITICAL)

Brief §4.3 Falsifier 4 verbatim: feature in top-half importance for ≥1 model = clean PROMISING; bottom-quartile across ALL = INERT.

Observed:
| Model | funding_rate_zscore_30 importance | Rank | Top-half (≤7)? |
|---|---:|---:|---|
| BCHUSDT | 25.0 | **10/14** | No (Q3) |
| LDOUSDT | 173.0 | **14/14** | No (dead last) |
| TRXUSDT | 118.0 | **14/14** | No (dead last) |
| Portfolio | 316.0 | **14/14** | No (dead last) |

Zero symbols clear rank ≤7 → §4.4 clean-PROMISING row does NOT clear. Available verdicts: PROMISING-INERT or NEGATIVE-no-effect; since IS Sharpe Δ=+0.78>0, direction is positive → **PROMISING-INERT** correctly mapped.

QE engineering report classification: **VALIDATED**. Same INERT pattern as iter-v3/015 microstructure (rank 14/14 across all 3 symbols at n_trials=10).

## Hard-Question Disposition: n_trials=10 Budget vs Genuine INERT

At n_trials=10 (30 total fits per cell), Optuna's TPE sampler does not have sufficient density to reliably surface a 14th feature whose univariate rank-IC is 0.04-0.05. The result is INDETERMINATE — could be true INERT OR budget-constraint mode collapse.

iter-v3/015 microstructure precedent is the calibrated prior: same single-axis NEW feature added at n_trials=10 → rank 14/14. This suggests the NULL-RESULT is the n_trials=10 mode collapse, not feature-specific.

**Process implication**: a CONFIRMATION at --n-trials 35 (post-iter-v3/018 default) would produce ~10× the EXPLORATION budget. The relevant question is NOT "did EXPLORATION definitively prove INERT" but "should iter-v3/020 spend 5h CONFIRMATION budget on funding-rate retest". Answer: NO — defer to iter-v3/028+ when multiple HIGH-priority axes have accumulated PROMISING evidence.

## IS Sharpe Overshoot Forensics

Predicted band [+0.45, +0.85] median +0.58. Observed +1.156 — +0.31 above upper, +0.57 above median.

SINGLE-SEED LOTTERY signal, same flavor as iter-v3/013 before being falsified. Optuna lands in favorable local minimum at --seeds 1 --n-trials 10 + colsample_bytree=1.0 that does not generalize. The catalog row MUST flag this overshoot as "single-seed lottery suspect; multi-seed re-evaluation required before bundling".

PROMISING-INERT iterations are marked NO candidate for future CONFIRMATION bundling. iter-v3/019's IS Sharpe overshoot does NOT promote it to clean-PROMISING because Falsifier 4 fires.

## DSR=+0.0167 Regime-Specific Interpretation

First positive DSR in v3. Mechanism: n_trials=30 → E[max_SR]=2.608 vs observed annualized 4.004 → marginal positive deflation. NOT comparable to BASELINE_V3.md DSR=0.0 at iter-v3/018 (n_trials=1500, observed_SR=1.7).

The +0.0167 is an EXPLORATION-mode artifact and SHOULD NOT be cited as evidence of edge significance to a future CONFIRMATION-bundling QR.

## Recommendations to QR

1. **iter-v3/020 axis = HIGH-priority axis #2 (concentration architecture)** per `feedback_v3_iter019_axis_priorities.md` LOCKED. Funding-rate axis is PROMISING-INERT and a NO-candidate for the next CONFIRMATION bundle. A funding-rate retest at higher trial budget requires CONFIRMATION-mode (~5h wall-clock) and is properly deferred to iter-v3/028+ when multiple HIGH-priority axes have accumulated. iter-v3/020 should NOT spend EXPLORATION budget on a funding variant; the axis is closed for the current 10-EXPLORATION cycle.

2. **DROP funding_rate_zscore_30 from V3_FEATURE_COLUMNS for iter-v3/020 (revert 14 → 13)**. Rationale: iter-v3/020's single-axis discipline requires a clean comparison surface against the iter-v3/018 anchor. Carrying an INERT feature forward into a different-axis EXPLORATION (e.g., concentration architecture) injects second-axis variance — Optuna would still see funding_rate_zscore_30 in the loss surface; the iter-v3/020 attribution would be contaminated. KEEP the `funding_v3.py` module + `fetch-funding` CLI + `data/funding_rates/<sym>.csv` cache (zero revert cost) — only remove from V3_FEATURE_COLUMNS_TOP_N. Preserves the option of revisiting at iter-v3/028+ CONFIRMATION without re-implementing the fetcher.

3. **Pre-commit EXPLORATION-mode DSR/PSR caveat as memory rule**. The iter-v3/019 +0.0167 DSR creates false-precedent risk. Add `feedback_v3_dsr_mode_artifact.md`: "EXPLORATION-mode DSR is NOT comparable to CONFIRMATION-mode DSR; only CONFIRMATION-mode DSR enters MERGE gate evaluation". Prevents iter-v3/019 INERT result from being mis-cited as edge evidence in a future bundle.
