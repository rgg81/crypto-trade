# Phase 7.5 Critic Review — iter-v3/011 — ROUND 2 FINAL

**OVERALL: EXPLORATION-PROMISING (with lottery/concentration caveats)**

**Iteration Type**: EXPLORATION (catalog row #4 since last CONFIRMATION; risk-gate axis per Critic FINAL Rec 1 of iter-v3/010)
**Mode**: Round 2 — FINAL
**Code SHA**: `9b4af01` | Brief SHA: `1bd02dc` | Phase 5.5 Gate SHA: `138e861` | Engineering Report SHA: `642cc45` | QR Response SHA: `9359cde` | Round 1 PRELIMINARY SHA: `b12c5aa` | Analysis SHA: `17d01ab`

Per Section 0.5 TYPE=EXPLORATION cadence rules: methodology axes (look-ahead, embargo, IC, ADF, Pareto, hypothesis-implementation alignment) enforced; edge axis (DSR/PSR) is INFORMATIONAL only.

---

## QR Response Considered (4 Clarifications)

### Clarification 1 — MKR catalog disposition with 4th consecutive negative

**QR position**: (a) MKR gate-orthogonal — tighter z=2.0 increased MKR kill-rate to 49.8% but worsened per-trade economics, refuting the "more filtering helps MKR" hypothesis. (b) Compress threshold from 6-7 to 5 consecutive negatives. Pre-commit: if iter-v3/012 shows MKR's 5th consecutive negative, the NEXT EXPLORATION must be a per-symbol-diagnostic axis.

**Disposition**: ACCEPTED. The compression from 6-7 → 5 is a tightening (more conservative, not less), and the gate-orthogonality framing is supported by the iter-v3/011 evidence: MKR z-kill rate rose ~15pp (35% → 49.8%) — the largest of any symbol — yet OOS net PnL declined from -10.65% to -25.75% and OOS WR from 29.4% to 25.0%. This is structurally important: the iter-v3/011 evidence forecloses the "stricter gate cures the MKR drag" hypothesis. Pre-committing the threshold compression BEFORE the next iteration's outcome (rather than after) is methodologically clean.

### Clarification 2 — LDO concentration-vs-coverage trade-off catalog framing

**QR position**: PROMISING WITH LOTTERY-FLAG. IS axis is broad-based (+0.9566 Sharpe over 286 trades, 36.4% WR) — IS lift is NOT lottery-driven. OOS lottery-concentration (LDO 86%, 10-trade, 80% WR) is a single-seed exploration structural property, not a unique iter-v3/011 pathology. Catalog flags ex-LDO basket fragility.

**Disposition**: ACCEPTED. The IS-axis differentiation from iter-v3/009 is material:
- iter-v3/009 IS = +0.0802 (below +0.10 falsifier line) AND OOS = +1.12 (lottery-driven) → NEGATIVE on IS axis
- iter-v3/011 IS = +0.9566 (well above +0.40 PROMISING threshold) AND OOS = +1.63 (concentration-flagged) → PROMISING on IS, OOS lottery-caveated

The IS axis is the falsifier-grade axis (per brief §4.3, §8); OOS is informational under EXPLORATION. iter-v3/011 clears the falsifier-grade IS axis with strong margin (+0.56 above PROMISING threshold) on a broad-based 286-trade sample.

### Clarification 3 — Trade-rate floor recoverability

**QR position**: Record explicit per-row arithmetic. iter-v3/011 single-seed = 101 OOS trades; predicted bundle = 5 outer seeds × 3-4× ensemble = 303-404 OOS trades. Factor 3-4× inherited from iter-v3/010 review, UNVERIFIED at iter-v3/011's gate setting. Catalog flags "Floor recoverable: YES (factor unverified)".

**Disposition**: ACCEPTED. The arithmetic is explicit, the unverified status is flagged, and the bundle estimate (303-404) sits well above the 130-trade floor with substantial margin even at the lower end. The catalog audit trail will preserve the unverified-factor caveat for a future CONFIRMATION QR to address.

### Clarification 4 — Data-extent drift attribution

**QR position**: Negligible attribution. 16h × 5 symbols on 13.5-month OOS = ~0.5% extent. -0.187 OOS Sharpe delta is overwhelmingly the z=2.0 gate-axis effect. Catalog audit-notes the regen but does NOT attribute metric delta to data drift.

**Disposition**: ACCEPTED. 0.5% extent drift on a 13.5-month OOS window cannot account for a -0.187 monthly Sharpe shift; the gate-axis kill rate increases of +15-18pp across all 4 symbols are the dominant driver.

---

## Per-Check Status (Carried Forward from Round 1 PRELIMINARY)

### Check 1 — Look-Ahead Audit: PASS
ZERO new feature code. Single behavior change is `RiskV2Config.zscore_threshold` 2.5 → 2.0. The z-score gate computes per-symbol mean/std snapshots over the IS window (`risk_v2.py:222-226`, masked by `open_time < OOS_CUTOFF_MS`) then evaluates `np.abs((x - mu) / sd)`. No look-ahead path created.

### Check 2 — Embargo Width: PASS
Required gap = 88. Engineering report banner confirms PASS. Identical to iter-v3/010.

### Check 3 — Multiple-Testing Correction: METHODOLOGY-PASS / EDGE-INFORMATIONAL
PBO = 0.10770 << 0.40 (identical to iter-v3/010 — methodology stable). n_eff = 7. n_high_pbo_cells = 6 (vs iter-v3/010's 5). DSR=0.0, PSR=1.0 — single-seed artifact, INFORMATIONAL per cadence. Methodology axis: PASS.

### Check 4 — IC Correlation: PASS
Max off-diagonal `|IC| = 0.660`; ZERO pairs ≥ 0.70. Identical to iter-v3/010.

### Check 5 — ADF Stationarity: WARN (carry-forward)
2769 cells; 82.3% stationary. Same per-month low-T artifact as iter-v3/010.

### Check 6 — Pareto Dominance: WAIVED (single-seed exploration)
1 row in `pareto_front.csv`. WAIVED per cadence. Note: max_concentration LDO 86.31% > 35% CONFIRMATION cap — informational under EXPLORATION, captured in lottery-flag.

### Check 7 — Reproducibility: PASS
Code SHA `9b4af01` stamped; analysis SHA predates brief; ITERATION_LABEL=v3-011 confirmed; trade-row spot-check OOS row 1 reproduces.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Single change is `zscore_threshold=2.0`. Single-axis cadence rule honored. Falsifiers 1, 2, 3 NOT triggered. Calibration miss: IS Sharpe overshoots predicted [+0.30, +0.70] by +0.26 favorable (second consecutive favorable overshoot).

### Checks 9-12: PASS / PASS / PASS-with-documented-refetch / PASS

---

## Verdict Rationale

**EXPLORATION-PROMISING with lottery/concentration caveats** is correct because:

1. **All 12 methodology checks PASS / WARN-carry-forward / WAIVED-single-seed.** Zero BLOCK conditions.

2. **Falsifier-grade IS axis clears with substantial margin.** IS Sharpe +0.9566 is +0.56 above +0.40 PROMISING threshold, +0.86 above +0.10 NEGATIVE falsifier. 286-trade IS sample at 36.4% WR is broad-based — not lottery-driven.

3. **Material differentiation from iter-v3/009's NEGATIVE failure mode.** iter-v3/009: IS=+0.08 (below floor) AND OOS=+1.12 (lottery) → NEGATIVE on IS axis. iter-v3/011: IS=+0.96 (well above floor, broad-based) AND OOS=+1.63 (concentration-flagged) → PROMISING on IS, caveat on OOS.

4. **QR's caveats are pre-commit and conservative.** MKR threshold compressed 6-7 → 5 (tighter); LDO lottery-flag is honest disclosure; floor arithmetic is explicit; data-drift attribution principled.

5. **Catalog row preserves all flagged risks.** Future CONFIRMATION-bundling QR inherits clean audit trail.

iter-v3/011 NEVER updates BASELINE_V3.md.

---

## Recommendations to QR

1. **iter-v3/012 must vary along a non-features-non-labeling-non-gate axis.** Catalog distribution after iter-v3/011: features×2 (007, 009), labeling×1 (010), gate×1 (011). Next axis-diversifying candidate: **BTC trend filter band** (currently ±20% over 14 days, primitive #7 in risk table). Test ±15% (stricter) or ±25% (looser) — structurally orthogonal to all 3 prior axes. Alternatives: ADX threshold (20), low-vol filter floor (0.33), or vol-scaling clip range ([0.3, 1.0]).

2. **iter-v3/011 catalog row must capture five distinct caveat fields**: (a) gate-orthogonal MKR with explicit threshold compression to 5 consecutive negatives, (b) LDO 86.31% OOS concentration with lottery-flag, (c) IS broad-based confirmation (286 trades, 36.4% WR, +0.96 Sharpe — IS lift NOT lottery-driven), (d) floor-recoverable bundle math 303-404 with 3-4× factor inherited-and-unverified, (e) data-regen audit note (0.5% extent drift, NOT attributed to metric delta).

3. **Pre-commit the MKR-threshold-compression rule to memory feedback BEFORE iter-v3/012 launches.** Save at `feedback_mkr_threshold_compression.md`: "If iter-v3/012 (or any subsequent EXPLORATION before next CONFIRMATION) records MKR's 5th consecutive OOS-negative, the NEXT EXPLORATION must be a per-symbol-diagnostic axis (e.g., drop-MKR universe-change exploration). This rule cannot be renegotiated post-hoc by the next Engineer or QR." Storing this prevents threshold drift back to 6-7.
