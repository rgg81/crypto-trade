# iter-v3/067 — Cycle 1 #8 INERT-AT-EXPLORATION / Ensemble parameter axis (confidence-floor=0.60) NON-ACTIVATION

**Date**: 2026-05-14
**Type**: EXPLORATION (cycle 1 #8 of 10; NON-FEATURE PIVOT CONTINUATION; ENSEMBLE PARAMETERS axis)
**Axis**: Path D — UNIVERSAL `inference_threshold_floor = 0.60` via `max(np.mean(self._confidence_thresholds), 0.60)` at `lgbm.py:516` + REVERT /066 vol_scale_ceiling=0.8 → default 1.0
**Verdict**: EXPLORATION-MERGE per Critic FINAL (review committed)
**Classification**: INERT-AT-EXPLORATION (Path D mechanism non-activation)
**BASELINE_V3.md**: UNCHANGED (/059 canonical)

## 1. What was done

Per orchestrator autopilot + Critic /066 Rec #2 universal-symmetric-clip avoidance, /067 tested ENSEMBLE PARAMETERS axis. QR EDA `aa5b0c8` chose Path D (confidence floor at 0.60).

Commit chain: EDA `aa5b0c8` → setup `65a9094` → impl `ae50dfd` → gate `3a19fd1` → pre-flight fix (.inner_strategy → .inner attribute) → engineering report `ca3d72a`. Wall-clock 0.70h.

Pre-flight blocked once on `inner_strategy` attribute typo (should be `inner` per RiskV2Wrapper). One-line fix by orchestrator; re-launched cleanly.

## 2. Results

| Metric | /060 anchor | /067 (floor 0.60) | Δ |
|---|---|---|---|
| IS Sharpe | +0.8325 | +0.8069 | -0.026 |
| OOS Sharpe | +0.1403 | +0.1523 | +0.012 |
| IS trades | 159 | 156 | -3 |
| OOS trades | 102 | 103 | +1 |
| frac_positive_paths | 0.6444 | 0.6444 | 0 |
| DSR_relative | 0.0 | 0.0 | 0 |
| PSR | 0.9763 | 0.985 | +0.01 |

Per-symbol OOS:
- BCH +1.9078 — **BIT-IDENTICAL** to /060 (37 trades byte-for-byte)
- LDO -19.80 (12 tr, 16.7% WR) vs /060 -19.72 (11, 18.2%); +1 trade is end_of_data boundary artifact
- TRX +23.87 (54 tr, 48.1% WR) vs /060 +23.31 — weight differences = vol_scale_ceiling revert, not Path D

## 3. Path D mechanism non-activation analysis

Floor `max(mean, 0.60)` returns `mean` when `mean ≥ 0.60`. BCH OOS bit-identity confirms floor non-binding for all BCH cells — every per-cell Optuna mean was ≥0.60.

**EDA prediction vs reality**:
- EDA T1/T2 predicted 30-50% trade-roster pruning (marginal-confidence trades in [Optuna_mean, 0.60] gap)
- Observed: -1.89% IS / +0.98% OOS — far less than predicted
- Root cause: EDA used structural reasoning about Optuna's [0.50, 0.85] search range; actual TPE re-convergence produced per-cell means mostly ≥0.60 in this rerun

**Methodology lesson**: Confidence-threshold-floor EDAs require per-cell threshold persistence (not yet implemented in runner). Structural distributional reasoning alone is insufficient when the floor is near the expected distribution mean — Optuna re-convergence noise dominates.

## 4. Critic verdict summary

OVERALL=EXPLORATION-MERGE. 13/13 Checks PASS. §11 Anti-Pattern Scan: CLEAN. Foundation Audit verified. Anchor-byte-correctness PASSES (no /065-style anchor error recurrence). BCH OOS bit-identity is the strongest possible reproducibility signal.

Critic's three lines of evidence for non-activation:
1. BCH OOS bit-identity (37 trades match /060 exactly)
2. LDO -0.0770 wpnl delta arithmetic-traceable to entry-fee on end_of_data boundary trade
3. TRX trade count identical (54); weight Δ from vol_scale_ceiling revert

## 5. PATH classification

**INERT-AT-EXPLORATION** per brief Section 8.2 LOCKED. Pre-registered ~45% probability outcome HIT precisely. Axis CLOSED — does NOT advance to /070 CONFIRMATION bundle. Confidence-threshold-floor family CLOSED at 0.60 (higher floors would require per-cell threshold logging first).

## 6. Hypothesis check — pre-registered mode fired correctly

Brief Section 7 4-mode probability: INERT 45%, PROMISING 25%, NEGATIVE 25%, SUSPICIOUS-OOS 5%. INERT HIT (45% mass). Brief Section 1 hypothesis explicitly named INERT-AT-EXPLORATION as most likely (~45%) given /060 local-optimum sensitivity. No hypothesis-faking; pre-registration honored.

## 7. BASELINE_V3.md status

UNCHANGED — /059 stays canonical at `v0.v3-059`.

## 8. Critic Recommendations carried forward

1. **Path D family CLOSED at 0.60**. Do NOT retest higher floor values (0.65, 0.70) without per-cell threshold logging FIRST. Future axis must add `threshold_history.csv` persistence as methodology-axis prereq.

2. **/068 axis: respect Critic /066 Rec #2 (universal-symmetric-clip exhausted) AND /067 (gate-modifier non-activation at single-seed local optimum)**. Cycle-1-fresh axes remaining: universe expansion, labeling variant orthogonal to /065, per-symbol customization (with mandatory IS-preservation pre-falsifier).

3. **/070 CONFIRMATION bundle composition — pre-register at /069 brief**: current bundle candidates = /065 SL widening (PROMISING) + /062 Path B4 (deferred spec). /067 does NOT contribute. Pre-register bundle composition in /069 brief Section 8 to prevent post-hoc rationalization at /070.

## 9. Next Iteration Ideas

Cycle 1 progress: 8/10 EXPLORATIONs done.

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE (anchor) | PROMISING-EXPLORATION |
| #2 | /061 | TRX RiskV2 anti-Kelly (vol_scale_floor) | INERT (closed; floor=0.5 preserved) |
| #3 | /062 | DSR_relative recalibration (Path C passive) | PASSIVE-DIAGNOSTIC (Path B4 → /070) |
| #4 | /063 | MASS FEATURE EXPANSION 14→46 | SUSPICIOUS-OOS-DOMINANT + IS-COLLAPSE |
| #5 | /064 | Phased mass-expansion #1 (+adx_14) | NEGATIVE (closed) |
| #6 | /065 | UNIVERSAL labeling Path D (SL=1.5) | **SUSPICIOUS-OOS-DOMINANT** (FIRST /070 candidate) |
| #7 | /066 | UNIVERSAL vol_scale_ceiling=0.8 | INERT (closed; ceiling family STRUCTURALLY EXHAUSTED) |
| **#8** | **/067** | **Confidence-threshold floor=0.60** | **INERT-AT-EXPLORATION (Path D mechanism non-activation; closed)** |
| #9 | /068 | TBD per QR EDA (NON-FEATURE; respect /066+/067 lockouts) | TBD |
| #10 | /069 | TBD; /070 bundle pre-registration brief | TBD |
| CONFIRMATION | /070 | Bundle: /065 SL widening + /062 Path B4 | TBD |

**iter-v3/068 axis candidates** (NON-FEATURE per Critic /064 Rec #4 + AVOID universal symmetric clip/cap per /066 Rec #2 + threshold logging prerequisite per /067 Rec #1):
- Universe expansion (4th symbol; potentially adds Kelly-aligned diversifier)
- Labeling variant orthogonal to /065 (TP multiplier widening or timeout adjustment)
- Per-symbol customization (CAREFUL per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`; mandatory IS-preservation pre-falsifier)
