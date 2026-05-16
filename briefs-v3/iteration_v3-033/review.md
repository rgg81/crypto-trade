# Phase 7.5 Critic Review — iter-v3/033

OVERALL: **EXPLORATION-NEGATIVE (clean)** — VET dragged portfolio (-19.23 OOS, 27.8% WR). Per-symbol-feature-signature alignment methodology is NECESSARY but NOT SUFFICIENT for symbol expansion.

## §4.4 PATH B Triggers

- VET OOS contribution: -19.23 (negative)
- VET WR: 27.8% (structurally bad)
- IS Sharpe drop: -0.12 vs anchor
- OOS Sharpe drop: -0.32 vs anchor

PATH B fires. Verdict: NEGATIVE-DILUTION clean.

## Methodology Lesson

iter-v3/029 ALGO succeeded (alignment 0.4642, WR 40%, +20.87 OOS).
iter-v3/033 VET failed (alignment 0.5176, WR 27.8%, -19.23 OOS).

Higher alignment did NOT predict better performance. The methodology has a ceiling — EDA-based candidate selection cannot replace empirical OOS validation. Symbol expansion remains a high-variance axis.

**Memory rule recommendation**: `feedback_v3_alignment_necessary_not_sufficient.md` — codify that feature-signature alignment is a SCREENING filter (eliminates obviously-bad candidates) but cannot guarantee OOS success. Symbol expansion success rate from this methodology: 1 of 2 attempts (ALGO ✓, VET ✗).

## Recommendations to QR

iter-v3/034 axis: DROP VET (V3_MODELS 5→4) + ADD `fracdiff_d05_close` (López de Prado AFML Ch. 5).

Rationale:
- 4-symbol baseline (BCH+LDO+TRX+ALGO) is the validated configuration
- Fracdiff is the v3 skill's iter-v3/001 mandate that was never delivered
- Different mechanism (memory preservation) than regime_momentum (sign-flip)
- iter-v3/026 (vol_adj_autocorr) failed at stacking on 3-sym; 4-sym + LDO ATR may have different stacking dynamics
- IS Sharpe lift is the priority; fracdiff theoretically captures regime-persistence info that's lost in raw returns

Predicted bands:
- IS Sharpe [+0.20, +0.55] median +0.38 (anchor +0.24; modest lift if fracdiff useful)
- OOS Sharpe [+1.60, +2.10] median +1.85 (anchor +1.93)

PATHS:
- PATH A (PROMISING-STACKING): both regime_momentum AND fracdiff get importance ≥30, IS Sharpe lifts → bundle ingredient
- PATH B (PROMISING-INERT): fracdiff rank 15/15 → INERT
- PATH C (NEGATIVE): IS Sharpe drops > 0.10 OR regime_momentum gets crowded out → fracdiff stacks badly with regime_momentum

## Catalog Row

`| iter-v3/033 | 2026-05-08 | ADD VETUSDT (V3_MODELS 4→5; per-symbol-feature-signature alignment selection); REQUIRED_GAP 88→110 | -0.12 (vs iter-v3/032 +0.2360) | +1.6096 (Δ -0.32; VET drags -19.23 OOS at 27.8% WR; bundle OOS 147 cleared 130 floor mechanically) | EXPLORATION-NEGATIVE (clean) | NO — VET drag despite alignment 0.5176 (higher than ALGO's 0.4642 which succeeded); methodology lesson: alignment NECESSARY NOT SUFFICIENT; iter-v3/034 = DROP VET + ADD fracdiff_d05_close (LdP AFML Ch. 5; iter-v3/001 mandate never delivered) |`
