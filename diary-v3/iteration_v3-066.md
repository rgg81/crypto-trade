# iter-v3/066 — Cycle 1 #7 INERT-AT-EXPLORATION / Risk primitive axis closed

**Date**: 2026-05-14
**Type**: EXPLORATION (cycle 1 #7 of 10; NON-FEATURE PIVOT CONTINUATION; RISK PRIMITIVE axis)
**Axis**: UNIVERSAL `vol_scale_ceiling = 0.8` (cap weight_factor universally) + REVERT /065's DEFAULT_ATR_MULTIPLIERS to (2.0, 1.0)
**Verdict**: EXPLORATION-INERT-CERTIFIED-CLEAN per Critic FINAL (review committed below)
**Classification**: INERT-AT-EXPLORATION per Section 8.2
**BASELINE_V3.md**: UNCHANGED (/059 canonical)
**Branch**: `iteration-v3/066`

## 1. What was done

Per Critic /064 Rec #4 NON-FEATURE pivot continuation + autopilot decision 2026-05-14, cycle 1 #7 tested RISK PRIMITIVE axis (orthogonal to /065 labeling axis). QR EDA at SHA `1d75cb0` chose Path E0.8 (UNIVERSAL vol_scale_ceiling 1.0 → 0.8) per ORACLE evidence:
- ONLY Path with sign-aligned positive ORACLE ΔSharpe (IS +0.008, OOS +0.022)
- Primary mechanism: LDO OOS anti-Kelly correction (6 of 11 LDO OOS trades at wf≥0.8 at /060)
- Universal mechanism preserves discipline per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`
- Reverts /065 DEFAULT_ATR_MULTIPLIERS for clean single-axis attribution

Commit chain: EDA `1d75cb0` → setup `ddc90e8` → impl `8598f1c` → gate `59821fa` → engineering report `2c3e160` → Critic review (this commit). Wall-clock 0.69h.

## 2. Results

| Metric | /060 anchor | /066 (ceiling=0.8) | Δ |
|---|---|---|---|
| IS monthly Sharpe | +0.8325 | +0.8308 | -0.002 |
| OOS monthly Sharpe | +0.1403 | +0.1756 | +0.035 |
| OOS/IS daily ratio | 0.28 | 0.26 | -0.02 |
| IS PF | 1.49 | 1.28 | -0.21 |
| OOS PF | 1.21 | 1.06 | -0.15 |
| IS MaxDD | 30.97% | 28.86% | -2.1% |
| OOS MaxDD | 34.53% | 32.47% | -2.1% |
| IS trades | 159 | 159 | 0 |
| OOS trades | 94 | 103 | +9 |
| frac_positive_paths | 0.6444 | 0.6444 | 0 |
| DSR_relative | 0.0 | 0.0 | 0 |
| PSR | 0.9763 | 0.9935 | +0.02 |

ORACLE-vs-actual reconciliation: predicted IS Δ +0.008 / OOS Δ +0.022; observed -0.002 / +0.035 — both within ±0.04 (TIGHTEST in cycle 1).

## 3. Per-symbol forensic

- BCH OOS +1.04 (37 tr, 32.4% WR, 16.5% concentration) — near-flat vs /060
- LDO OOS -17.14 (12 tr, 16.7% WR) — slight improvement vs /060 -19.72 (LDO anti-Kelly correction +2.59 wpnl matches ORACLE +2.66 within 0.07)
- TRX OOS +22.37 (54 tr, 48.1% WR, 357% concentration) — near-flat vs /060 +23.31 (Kelly cost -0.87 matches ORACLE -0.87 exactly)

**Per-symbol Kelly heterogeneity** is the STRUCTURAL falsifier per Critic Q5: ceiling=0.8 binds asymmetrically because trade-level wf distributions differ. BCH IS Kelly cost -9.40 dominates; LDO IS near-neutral; TRX IS mixed. Net IS -3.92, Net OOS +0.28. Mutual cancellation produces near-zero Sharpe shift.

## 4. Critic verdict summary

OVERALL=EXPLORATION-INERT-CERTIFIED-CLEAN. 13/13 Checks PASS (1 disclosure on Check 8 for /061 TRX-floor carry-forward — ORACLE under-modeled actual config but stayed within ±0.04). §11 Anti-Pattern Scan: 13/13 PASS.

Key Critic finding: **Universal-ceiling family is STRUCTURALLY EXHAUSTED** for the current 3-symbol bundle. Per-symbol Kelly heterogeneity (BCH+TRX Kelly-aligned vs LDO anti-Kelly) means UNIVERSAL ceiling cannot produce PROMISING without violating `feedback_v3_per_symbol_lifts_oos_breaks_is.md`. INERT verdict is structurally inevitable.

## 5. PATH classification

**INERT-AT-EXPLORATION** per brief Section 8.2 LOCKED. Pre-registered ~50% probability outcome HIT. Axis CLOSED — does NOT advance to /070 CONFIRMATION bundle.

## 6. Hypothesis check — confirmed at modest scale

Brief Section 1 hypothesis correctly predicted INERT-AT-EXPLORATION most likely. ORACLE prediction accuracy was tightest in cycle 1 (within ±0.04 on both axes). The mechanism (LDO anti-Kelly correction) was real and matched ORACLE quantitatively — just too small in net effect (universal mechanism, asymmetric binding).

## 7. BASELINE_V3.md status

**UNCHANGED** — /059 stays canonical at tag `v0.v3-059`. INERT-AT-EXPLORATION does not update BASELINE_V3.

## 8. Critic Recommendations carried forward

1. **Anchor consistency for /070 CONFIRMATION bundle**: document explicitly whether anchor includes /061's TRX vol_scale_floor=0.5 (and any "INERT-but-preserved" carry-forwards). The /060 anchor predates the TRX floor.

2. **Per-symbol Kelly heterogeneity = structural ceiling-axis falsifier**. Future /067-068 risk-primitive EXPLORATIONs should AVOID universal symmetric clip/cap mechanisms. Universal-ceiling family STRUCTURALLY EXHAUSTED.

3. **Orchestrator dispatch anchor-value error pattern (SECOND RECURRENCE)**: /065 Critic Rec #1 recurrence in /066 dispatch prose. Brief and runner were CLEAN; error stayed in dispatch only. Recommend: orchestrator dispatch prose ALWAYS sources headlines from `comparison.csv` byte-exact lookups.

## 9. Next Iteration Ideas

Cycle 1 progress: 7/10 EXPLORATIONs done. /070 = CONFIRMATION per strict 10:1 cadence.

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE (anchor) | PROMISING-EXPLORATION |
| #2 | /061 | TRX RiskV2 anti-Kelly (vol_scale_floor) | INERT (closed; floor=0.5 preserved) |
| #3 | /062 | DSR_relative recalibration (Path C passive) | PASSIVE-DIAGNOSTIC (Path B4 → /070) |
| #4 | /063 | MASS FEATURE EXPANSION 14→46 | SUSPICIOUS-OOS-DOMINANT + IS-COLLAPSE |
| #5 | /064 | Phased mass-expansion #1 (+adx_14) | NEGATIVE (closed) |
| #6 | /065 | UNIVERSAL labeling Path D (SL=1.5) | **SUSPICIOUS-OOS-DOMINANT** (FIRST /070 candidate) |
| **#7** | **/066** | **UNIVERSAL vol_scale_ceiling=0.8** | **INERT-AT-EXPLORATION (closed; universal-ceiling family STRUCTURALLY EXHAUSTED)** |
| #8-10 | /067-069 | TBD per QR EDA (NON-FEATURE; AVOID universal symmetric clip/cap) | TBD |
| CONFIRMATION | /070 | Bundle: /065 SL widening + /062 Path B4 | TBD |

**iter-v3/067 axis candidates** (NON-FEATURE per Critic /064 Rec #4 lock; AVOID universal symmetric clip/cap per /066 Critic Q5):
- Ensemble parameters (confidence threshold calibration; median vs mean aggregation)
- Universe expansion (4th symbol; potentially adds Kelly-aligned diversifier)
- Labeling variant orthogonal to /065 (e.g., TP multiplier widening or timeout adjustment alongside /065 SL widening at /070)
- Per-symbol kill-switch (asymmetric — may violate per-symbol anti-pattern; only viable with strong EDA justification)

**iter-v3/070** bundle so far (cycle 1 CONFIRMATION):
- /065 SL widening (PROMISING)
- /062 Path B4 methodology deferred spec
