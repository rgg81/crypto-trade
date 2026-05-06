# QR Response to Critic — iter-v3/011

## Clarifications

### Clarification 1 — MKR catalog disposition + threshold

(a) MKR is gate-orthogonal and the catalog row will state so explicitly. The hypothesis "tighter z-score gate filters symbol-specific noise" is NOT supported for MKR: net PnL trajectory across the 4 EXPLORATIONs is monotonically worsening (-6.5%, -13.1%, -10.6%, -25.75%), with magnitude doubling rather than damping under the stricter z=2.0 cut.

(b) Compress the catalog threshold for MKR from 6-7 to 5 consecutive negatives. Pre-commit: if iter-v3/012 (regardless of axis) shows MKR's 5th consecutive negative, the NEXT EXPLORATION must be a per-symbol-diagnostic axis (drop MKR, single-axis universe-change exploration), not another gate or labeling tweak. This is a hard rule — the symbol fails on its own across orthogonal manipulations.

### Clarification 2 — LDO concentration framing

FLAG REGRESSION but maintain PROMISING with explicit lottery caveat. iter-v3/010's distinguishing property was 3/4 standalone-positive symbols (broad-based OOS); iter-v3/011 nominally has 3/4 NET-positive (BCH +19%, LDO +41%, TRX +3%, MKR -15%) but collapses to 2/4 if LDO's 86%-concentration / 10-trade / 80%-WR profile is haircut to expected baseline — borderline lottery on the OOS axis. The IS axis remains broad-based and strong (+0.9566 Sharpe over 286 trades, 36.4% WR), so the IS lift is NOT lottery-driven; the OOS concentration risk is single-seed exploration concentration-fragility (a known structural property of v3 single-seed runs), not a unique iter-v3/011 pathology. Catalog row: PROMISING WITH LOTTERY-FLAG (LDO 86% conc, 10-trade lottery, ex-LDO basket fragile); future CONFIRMATION-bundling QR decides whether z=2.0 inherits alone or only paired with iter-v3/010's z=2.5 where 5-seed regularization should reduce concentration variance.

### Clarification 3 — Trade-rate floor recoverability

Record explicit per-row arithmetic in the catalog. iter-v3/011 OOS = 101 single-seed trades; predicted bundle = 5 outer seeds × ~3-4× ensemble multiplication = 303-404 OOS trades, well above the 130 floor. Multiplication factor 3-4× is inherited from iter-v3/010's empirical review and remains UNVERIFIED at iter-v3/011's specific gate setting — catalog flags as "Floor recoverable: YES (factor unverified, inherited from iter-v3/010)".

### Clarification 4 — Data-extent drift

Negligible attribution to the OOS Sharpe delta. The 16h additional OOS data across 5 symbols on a 13.5-month OOS window = ~0.5% extent extension; iter-v3/010 was itself measured at its own data-extent moment with no fixed reference baseline, so all v3 EXPLORATION rows have this property. The -0.187 OOS Sharpe delta vs iter-v3/010 is overwhelmingly the z=2.0 gate-axis effect; catalog will NOTE the regen happened (audit-trail row) but will NOT attribute the metric delta to data drift.

## Position

STAND BY VERDICT — request OVERALL = **EXPLORATION-PROMISING with lottery/concentration caveats**. Falsifiers not triggered (IS +0.96 far above +0.10), all methodology axes PASS, IS lift is broad-based on the IS axis (286 trades, 36.4% WR — not lottery-driven), OOS lottery-concentration is a real but expected single-seed exploration property and gets explicit lottery-flag in the catalog along with the MKR threshold compression, floor-recoverable bundle math, and data-regen audit note.
