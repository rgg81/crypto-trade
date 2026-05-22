# iter-v3/069 — Cycle 1 #10 (FINAL) INERT-AT-EXPLORATION / Universe expansion +ADA closed

**Date**: 2026-05-15
**Type**: EXPLORATION (cycle 1 #10 of 10 — FINAL before /070 CONFIRMATION; NON-FEATURE PIVOT; UNIVERSE EXPANSION axis)
**Axis**: Add ADAUSDT to V3_MODELS (4 syms: BCH+LDO+TRX+ADA); REQUIRED_GAP 66→88; REVERT /068 timeout
**Verdict**: EXPLORATION-MERGE per Critic FINAL — INERT certified clean (corrected re-run)
**Classification**: INERT-AT-EXPLORATION per Section 8.2
**BASELINE_V3.md**: UNCHANGED (/059 canonical)

## 1. What was done

Per orchestrator autopilot + Critic /068 Rec #3 LDO-targeted axis directive, /069 tested universe expansion (denominator-expansion mechanism per `feedback_v3_concentration_is_signal.md`). QR EDA `95038dd` chose ADAUSDT per composite ranking (lowest feature-space distance to BCH+LDO+TRX, $390M liquidity).

**Process correction event**: Initial backtest (engineering report `05388c9`) had a CRITICAL methodology defect — `BacktestConfig.timeout_minutes` at line 1407 was NOT reverted from /068's 20160 (only `label_timeout_minutes` at line 1425 was correctly reverted). This produced a COMPOUND axis (+ADA × 14-day-trade-exit-holdover) instead of clean +ADA. Critic /069 PRELIMINARY (Round 1) caught the defect via 3-symbol byte-identity falsification (BCH OOS +10.64 vs anchor +1.9078 — 5× deviation impossible under clean +ADA single-axis change). Fix at commit `4239646` reverted line 1407 → 10080. Re-run produced corrected results.

Commit chain: EDA `95038dd` → setup `cde507b` → backfill `b62ef11` → Phase 5.5 gate `b61bee0` (+docstring fix `ac401ea`) → INVALIDATED engineering report `05388c9` → fix `4239646` → corrected engineering report `003c8b4` → Critic Round 2 review (this commit). Wall-clock 1.07h re-run.

## 2. Results (corrected, vs /060 anchor)

| Metric | /060 anchor | /069 corrected | Δ |
|---|---|---|---|
| IS Sharpe | +0.8325 | +0.7943 | -0.038 |
| OOS Sharpe | +0.1403 | +0.1222 | -0.018 |
| OOS/IS daily ratio | 0.28 | 0.20 | -0.08 |
| IS WR | 28.99% | 33.05% | +4.05pp |
| OOS WR | 36.17% | 37.19% | +1.0pp |
| IS PF | 1.49 | 1.25 | -0.24 |
| OOS PF | 1.21 | 1.04 | -0.17 |
| IS MaxDD | 30.97% | 27.49% | -3.5% |
| OOS MaxDD | 34.53% | 43.47% | +8.94% |
| IS trades | 159 | 233 | +74 (4-sym scale) |
| OOS trades | 102 | 121 | +19 |
| frac_positive_paths | 0.6444 | 0.6000 | -0.044 (PASS @0.55) |
| DSR_relative | 0.0 | 0.0 | 0 |
| PSR | 0.9763 | 0.9833 | +0.01 |
| CPCV_Q75 | 0.8378 | 1.4496 | +0.61 (4-sym path scale) |

Per-symbol OOS:
- **BCH +1.9078** — BIT-IDENTICAL to /060 (byte-identity invariance RESTORED post-fix)
- ADA +0.42 (18 tr, 27.8% WR, 6.69% concentration)
- LDO -20.73 (12 tr, 16.7% WR; +1 trade vs /060) — slightly worse than /060 -19.72
- TRX +24.72 (54 tr, 48.1% WR; identical count to /060) — slightly higher than /060 +23.31

## 3. Critic verdict summary

OVERALL=MERGE (INERT-AT-EXPLORATION certified clean). 13/13 Checks PASS or PASS-equivalent. §11 Anti-Pattern Scan CLEAN. Foundation Audit: walk-forward fix INTACT, BacktestConfig.timeout=10080 (FIX APPLIED), label_timeout=10080, REQUIRED_GAP=88.

**BCH byte-identity restoration verified**: 5-row spot-check confirms /069 BCH OOS rows match /060 BCH OOS BYTE-FOR-BYTE (every field). Defect-fix process worked end-to-end.

Adversarial questions resolved:
- BCH byte-identity confirmed across 5 spot-checks
- /070 bundle composition correctly final (/065 + /062 Path B4; /069 does NOT carry forward universe-expansion as structural)
- Anchor-byte correctness gate clean (no /065-style recurrence)
- Cycle 1 closeout 10/10 done; /070 = CONFIRMATION (not collapsed)

## 4. PATH classification

**INERT-AT-EXPLORATION** per brief Section 8.2 LOCKED. Both shifts within ±band. Pre-registered ~45% modal outcome HIT. Universe-expansion axis CLOSED at catalog level — does NOT advance to /070 CONFIRMATION bundle.

The prior "PROMISING-DEFERRED" classification was the ARTIFACT of unreverted 14-day BacktestConfig.timeout. With clean 7-day timeout, both metrics collapse to within-band INERT.

## 5. Defect retrospective + lessons

The `BacktestConfig.timeout_minutes` (line 1407) and `LightGbmStrategy.label_timeout_minutes` (line 1425) fell out of sync during the /069 setup. /068 had set BOTH to 20160; /069 reverted only line 1425. The two parameters represent the SAME conceptual quantity (label horizon = trade exit horizon = 21 candles at /069) but live as separate config sources.

Detection: BCH OOS byte-identity falsification was the diagnostic. The /060 anchor BCH OOS = +1.9078; broken-axis /069 produced +10.64 (5× deviation). This impossibility under a clean +ADA single-axis change exposed the compound axis.

Lesson: Critic Rec #1 — add runtime assertion that `BacktestConfig.timeout_minutes == _build_v3_model.label_timeout_minutes` for every model. Single source of truth via shared module constant. Cross-line-number drift is a recurring failure mode (this is the THIRD such case after iter-v3/065 anchor-value drift and iter-v3/067 inner_strategy attribute typo).

## 6. Hypothesis check — INERT mode HIT cleanly

Brief Section 7 4-mode probability: INERT 45%, PROMISING 20%, NEGATIVE 25%, SUSPICIOUS-OOS 10%. INERT HIT (45% mass). Calibration was accurate.

## 7. BASELINE_V3.md status

UNCHANGED — /059 stays canonical at `v0.v3-059`. INERT-AT-EXPLORATION does not update BASELINE_V3.

## 8. Critic Recommendations carried forward to /070 CONFIRMATION

1. **Anchor-byte correctness gate ENFORCEMENT at runner-level**: /070 setup MUST add runtime assertion `BacktestConfig.timeout_minutes == _build_v3_model.label_timeout_minutes`. Centralize the constant via shared module-level definition.

2. **Universe expansion follow-up at multi-seed CONFIRMATION-spec**: Future cycle 2 should test universe expansion at --seeds 2 + ENSEMBLE_SIZE=10 to discriminate single-seed lottery vs genuine "universe-expansion does not lift" finding. Pre-register multi-seed prediction band BEFORE running.

3. **Inherited IC violation MUST be addressed in /070 brief**: vwap_dev_20 × regime_momentum_signed_5d = 0.7797 exceeds 0.70 hard gate. /070 brief Section 2 must either (a) explicitly document Category 2 composed-feature carve-out per `feedback_v3_engineered_feature_pivot.md` with importance ≥30 evidence (current: vwap_dev_20 LDO importance 249.67 rank 1; regime_momentum_signed_5d 122.0 rank 12 — both above 30), or (b) drop one. Failing to address = automatic Critic Check 4 FAIL at /070 CONFIRMATION.

## 9. CYCLE 1 FINAL CLOSEOUT — 10/10 EXPLORATIONs DONE

| Slot | Iter | Axis | Verdict | /070 Bundle Contribution |
|---|---|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE | PROMISING (anchor) | anchor only |
| #2 | /061 | TRX vol_scale_floor | INERT | none |
| #3 | /062 | DSR_relative recalibration (Path C passive) | PASSIVE-DIAGNOSTIC | **Path B4 deferred spec** |
| #4 | /063 | MASS FEATURE EXPANSION 14→46 | SUSPICIOUS-OOS+IS-COLLAPSE | none |
| #5 | /064 | Phased +adx_14 | NEGATIVE | none |
| #6 | /065 | UNIVERSAL labeling Path D (SL=1.5) | **SUSPICIOUS-OOS-DOMINANT** | **+SL widening** |
| #7 | /066 | UNIVERSAL vol_scale_ceiling=0.8 | INERT | none |
| #8 | /067 | Confidence threshold floor=0.60 | INERT | none |
| #9 | /068 | Label timeout 21→42 | NEGATIVE | none |
| **#10** | **/069** | **Universe expansion +ADA** | **INERT (corrected)** | none |
| **CONFIRMATION** | **/070** | **Bundle: /065 SL widening + /062 Path B4** | **TBD** | **2 components FINAL** |

**Cycle 1 cadence COMPLETE per `feedback_v3_strict_10_to_1_cadence.md`** (10 EXPLORATIONs + 1 CONFIRMATION).

**/070 CONFIRMATION bundle FINAL composition**: /065 SL widening (DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5)) + /062 Path B4 methodology spec (annualized-both-sides DSR_relative reformulation; integration test + backward-compat validation per /062 brief Section 3).

**Cycle 1 outcome distribution**:
- 1 PROMISING-EXPLORATION (anchor)
- 1 PASSIVE-DIAGNOSTIC (methodology axis)
- 1 SUSPICIOUS-OOS-DOMINANT (advancement candidate)
- 4 INERT (axis closures)
- 3 NEGATIVE (failure modes)

## 10. Next: iter-v3/070 CONFIRMATION

- Multi-seed unified 10-seed ensemble (CONFIRMATION mode; ENSEMBLE_SIZE=10)
- 2-component bundle: /065 SL widening + /062 Path B4
- 3-symbol universe (BCH+LDO+TRX) — REVERT /069 ADA addition; REQUIRED_GAP back to 66
- MUST beat /059 multi-seed anchor IS +1.0894 / OOS +0.5791 on BOTH axes per `feedback_v3_strict_both_is_oos_baseline.md`
- Anchor-byte correctness gate maintained per Critic /064-/069 Rec carry-forward
- Path B4 implementation per /062 brief Section 3 (with end-to-end smoke test + 6th integration test + backward-compat /058+/059 re-run)
- Address inherited IC violation per Critic /069 Rec #3
- Wall-clock target: ~3.6h CONFIRMATION mode
