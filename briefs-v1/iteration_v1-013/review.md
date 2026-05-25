# Phase 7.5 Critic Review — iter-v1/013

OVERALL: EXPLORATION-NEGATIVE — multi-falsifier catastrophic failure (F1 OOS Δ -1.02, F3 IS Δ -0.92, F9 IS Δ 1.30σ below band [+0.38, +0.58]); 2-property substrate decomposition decisively refuted at n=4; verdict subtype `BASIN-LOTTERY-CATASTROPHIC` adopted

## Iteration Type
TYPE: EXPLORATION (cycle-2 #8 of 10; pre-committed /014 = labeling EXPLORATION precursor + /015 = labeling CONFIRMATION)

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

Foundation re-audited. `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms`. 4 mandated regression tests present. /013 src/ diff EMPTY by design (`--ensemble-seeds-offset 6` value-only change). No feature look-ahead — only RNG initialization differs from /011/012.

### Check 2 — Embargo Width: PASS

`validation_v1.REQUIRED_GAP = 110` for v1 5-symbol universe × (timeout_candles+1). BIT-IDENTICAL to /011/012.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)

DSR_IS=0.0, DSR_OOS=0.0 (both nullified by negative Sharpe). PSR_monthly_vs_0: IS 0.119 / OOS 0.372 (catastrophic vs 0.95). PSR_monthly_vs_1 OOS 0.068. Per EXPLORATION-mode artifact rule, Check 3 informational. The collapse to PSR=0.002/0.068 confirms iteration is decisively in negative-edge regime; consistent with F1+F3 sign-flipped headlines.

### Check 4 — IC Correlation: PASS

ic_matrix.csv BIT-IDENTICAL to /012 (same features). Pre-existing cross-family IC carry-over from BASELINE_V1 (momentum↔trend 0.718, momentum↔volume 0.738) unchanged. Not /013-introduced.

### Check 5 — ADF Stationarity: PASS

40 active features in V1_FEATURE_COLUMNS_PRUNED all bonferroni_pass=True. Empty rows correspond to candidates not in PRUNED set.

### Check 6 — Pareto Dominance: PASS (N/A for EXPLORATION)

Single-seed-window; 10-seed Pareto reserved for CONFIRMATION.

### Check 7 — Reproducibility: PASS (with process concern)

Trade spot-checks reproduce: LINK long PT, BTC short PT, LTC long SL — all match reported PnL within rounding.

**PROCESS CONCERN (3rd strike)**: `reports-v1/iteration_v1-013/engineering_report.md` is MISSING despite brief Section 10.2 #4 + Critic /012 Rec #2 + critic_preflight.md "Engineering Report Deliverable: PASS". Phase 6 dispatch did not enforce the hard-reject contract. /011 and /012 both produced the report (/012 retroactive). For /014, this is the third strike — escalate to Critic Phase 7.5 dispatch hard-reject if missing.

### Check 8 — Hypothesis-Implementation Alignment: PASS

Brief Section 1 + 3.1: only CLI value change `--ensemble-seeds-offset 6`. Verified `_derive_ensemble_seeds(3, offset=6) = [3003, 4004, 5005]`. Banner printed at runtime. Hypothesis IS tested. Outcome (catastrophic refutation) is hypothesis-decisively-refuted, exactly what Section 8.1 Row 7 + Section 8.2 row 3 pre-registered.

### Check 13 — Anti-Pattern Static Scan: PASS

A1/A2/A3/A4/A5/A7/A8/A12/A13 all PASS. Zero unexplained matches.

### Check 14 — Axis Family Validation: PASS

`methodology-substrate-test` 3rd consecutive. Rotation VALID (prior 5 EXPLORATIONs span 4 families; 5-of-5 saturation does NOT fire). NOT a new family declaration. Methodology-probe discipline flag for /014+ per user feedback 2026-05-25 (memory `feedback_v1_methodology_probe_discipline.md` — methodology probes consume EXPLORATION budget without edge-finding; cap at 1 per cycle).

## Substrate-Decomposition Catastrophic Refutation — Diagnostic Summary

| Falsifier | Pre-registered band | Observed | Result |
|---|---|---|---|
| F1 OOS Δ | [+0.05, +0.55] PROMISING; <-0.05 NEGATIVE | **−1.017** | **FIRE NEGATIVE catastrophic** |
| F2 R5-BINARY-KILL fire rate | [10%, 60%] both halves | IS 19.05% / OOS 21.55% | PASS (mechanism intact) |
| F3 IS Δ | [+0.38, +0.58] substrate-magnitude | **−0.9223** | **FIRE catastrophic-undershoot** (sign-flipped) |
| F4 DEGENERATE_PREDICTOR | none fired | clean | PASS |
| F5 PSR ≥ 0.50 | both halves | IS 0.119 / OOS 0.372 | FAIL (informational at EXPLORATION) |
| F6 OOS baseline overlap | informational | 16.30% | within /011/012 range (14-17%) |
| F7 LTC IS overlap vs /011 | [15%, 40%] | LTC 25.0% / portfolio 36.19% | PARTIAL |
| F8 LTC IS overlap vs /012 | [25%, 50%] | LTC 33.0% / portfolio 36.38% | PARTIAL |
| F9 IS Δ ∈ [+0.38, +0.58] | substrate-MAGNITUDE LOCK | **−0.9223 OUTSIDE band** | **FAIL — substrate-magnitude lock REFUTED** |

IS Δ trajectory across 4 data points: +0.4701 / +0.4849 / +0.5167 / **−0.9223**. Std jumps from 0.025 to 0.66. Per-symbol IS PnL: LINK retains dominance (+128) but LTC loses dominance (+32 vs /011 +110, /012 +119), ETH catastrophically reverses (−139.78), BTC catastrophically reverses (−79.13). **2/5 symbols are now catastrophic losers** — up from 0/5 at /011, 1/5 at /012 — confirming LM Master Phase 7.4 §3 "catastrophic-loser ROTATES and AMPLIFIES" observation.

The 2-property decomposition committed at /012 closeout is **decisively refuted at n=4**. At v1 single-seed-window EXPLORATION, basin draws are fully seed-driven with high variance; adjacent seed offsets land in catastrophically distinct basins. Memory file `feedback_v1_substrate_basin_lock.md` REFUTED-IN-FULL.

Verdict subtype `BASIN-LOTTERY-CATASTROPHIC` (LM Master Phase 7.4 recommended) is the appropriate new row for the v1 catalog.

## Recommendations to QR (process-level, for /014+)

1. **Engineering report deliverable enforcement gap (3rd strike)**: `reports-v1/iteration_v1-013/engineering_report.md` missing despite brief mandate + Critic /012 Rec #2 + critic_preflight.md acceptance. /011 and /012 produced it. Future iterations: Critic Phase 6.0 explicit precondition check (currently only checks SPEC, not produced artifact). For /014, escalate to Critic Phase 7.5 dispatch hard-reject if missing.

2. **Substrate-decomposition memory file update**: `feedback_v1_substrate_basin_lock.md` marked REFUTED-IN-FULL at n=4 per LM Master Phase 7.4 §2 commitment. Future v1 EXPLORATION briefs must not cite the decomposition as if it still holds.

3. **PRE-COMMITTED CONDITIONAL FIRES — /015 axis LOCKED as labeling CONFIRMATION**: F1 OOS Δ ≤ 0 (observed -1.017) → /015 = UNUSED-family CONFIRMATION (labeling). Conditional binding; cannot be post-hoc renegotiated. /014 MUST be labeling EXPLORATION precursor with HIGH-RISK declaration to legitimize /015 by 10:1 cadence.

## Path Forward (mandatory on EXPLORATION-NEGATIVE)

Pre-committed conditional locks /014 as labeling EXPLORATION precursor. UNUSED families in cycle-2: labeling, universe, model-arch.

1. **labeling — triple-barrier σ_t via past-only EWMA at 14-day window** (UNUSED in cycle-2; pre-committed at /015 CONFIRMATION conditional). Replace fixed-fraction ATR multipliers with EWMA-σ_t-scaled barriers (regime-adaptive). Changes per-cell IS label distribution → different Optuna loss surface → potentially genuine basin-shift edge OR null OR negative. **HIGH-RISK declaration MANDATORY**. **THIS IS THE PRE-COMMITTED /014 AXIS.**

2. **universe — equal-weight portfolio with LTC weight cap at 25%** (UNUSED in cycle-2 since /006). Tests whether basin-lottery is partly concentration artifact. NORMAL-RISK with mitigation simulated effect required.

3. **model-arch — XGBoost head-to-head on V1_FEATURE_COLUMNS_PRUNED with depth-wise growth** (UNUSED in cycle-2). v3 precedent at /016 was NEGATIVE clean at n_trials=10; v1 at n_trials=35 materially changes applicability. Structural orthogonality test.

**Option 1 is pre-committed for /014** — binding, cannot be renegotiated. Options 2 and 3 are RESERVE proposals if /014 labeling EXPLORATION produces NEGATIVE-catastrophic and cycle-2 needs structural-axis breakout.

## BLOCK-PENDING-FIX Rerun Protocol

N/A — verdict is EXPLORATION-NEGATIVE catastrophic. Defects (engineering report missing, memory file revision) are forward-looking process-discipline lessons, not backtest defects. /013 closed as EXPLORATION-NEGATIVE BASIN-LOTTERY-CATASTROPHIC.
