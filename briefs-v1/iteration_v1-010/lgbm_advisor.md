# LightGBM Master Advisor — iter-v1/010 — Phase 4.5 (Pre-Design)

## Context Read
- Track: v1; baseline `v0.v1-baseline-corrected` (IS +0.2829 / OOS +0.6637; 5-seed); 5-symbol universe; 40-feature `V1_FEATURE_COLUMNS_PRUNED`.
- Prior iter /009: NEGATIVE-NEGATIVE feature-family deletion; 3-way convergence on R5 as next axis.
- QR's axis: R5 vol-target ceiling at uniform `vol_target_pct = 4.0%` (revised from /009-spec 2.5% via EDA — sharp, well-justified).
- Track record: 1/6 directional with PARTIAL credit only. Defaulting LOW confidence per /007 closeout.

## 1. Mechanism Critique — Will Optuna Re-Optimize Into a New Roster?

**Most likely: NO, Optuna will NOT meaningfully re-route.** Single-seed=42 + n_trials=35 + ENSEMBLE_SIZE=3 is below the variance-reduction threshold needed to discover a NEW high-confidence-low-vol entry distribution. The oracle's -0.020 OOS Δ is the modal outcome. The mechanism for Optuna substitution requires the GBM to demote IS-overfit basins that correlate with high-NATR entries — but with `min_data_in_leaf` defaults and 5-fold pooled CV, the loss gradient on R5-scaled targets is only ~5% different from baseline (mean cap 0.954 IS). Below the SNR floor where Optuna shifts basins.

**Empirical evidence**: per Section 2.4 oracle, R5 cuts LINK IS by 28.62pp + LTC IS by 12.28pp. ETH IS gains +7.10pp because R5 caps ETH's IS losers more than its winners. Net IS portfolio Δ = -35.67pp wpnl. For Optuna to FLIP this NEGATIVE → POSITIVE, it would need to find a hyperparameter region where LINK's high-vol entries are predicted as LOWER-confidence (so position size redirects to BTC/ETH at lower NATR). The signal:noise ratio for that flip at n_trials=35 single-seed is ~10-15% — possible but unlikely.

**Most likely path**: Optuna re-converges to a near-baseline basin; trade roster ~85% identical to oracle; F1 verdict = -0.05 to +0.02 (PROMISING-INERT). The /009 brief's pre-registered PROMISING-INERT-to-marginal-NEGATIVE call is correctly framed.

## 2. Per-Symbol R5 Heterogeneity — Should Calibration Be Per-Symbol?

**No — DO NOT per-symbol calibrate at /010.** Three reasons:

1. **Bundling discipline**: per-symbol thresholds = 2-axis change (axis A: R5 enable; axis B: per-symbol calibration). v1 cycle-2 has burned 5 consecutive HIGH-RISK NEGATIVES partially because of axis stacking. /010 should be SINGLE-axis EXPLORATION at uniform 4.0%.
2. **The "ceiling" semantics is universe-level**: R5's design intent is "cap exposure when vol exceeds a universe-level safety band." Per-symbol thresholds would be R5'=per-symbol-vol-target-ratio — a DIFFERENT primitive. The brief's framing as "anchored on universe p75 ≈ 4.7%" is the correct conceptual home.
3. **Per-symbol calibration is the /011 path IF /010 PROMISING**: per Section 11 alternates, vol_target ∈ {3.5, 4.0, 4.25} as a 3-point ablation at CONFIRMATION is the right venue. Per-symbol ablation at multi-seed CONFIRMATION is even better but requires PROMISING first.

The BTC-rarely-fires / LINK-72%-fires asymmetry is **information**, not a calibration defect. It tells us R5 will mostly act on LINK + DOT + LTC — which is the design intent (cap the high-NATR top contributor and laggers, not BTC).

## 3. /011 Pre-Stage Conditional on /010 Outcome

- **/010 PROMISING (OOS Δ ≥ +0.05)**: /011 = multi-seed CONFIRMATION at ENSEMBLE_SIZE=10 + 10 seeds + n_trials=50, vol_target ∈ {3.5, 4.0, 4.25} 3-point ablation. HIGH-RISK pre-commit fires per Section 2.5. Tag for BASELINE_V1 update if it strictly beats /009 on IS AND OOS.
- **/010 PROMISING-INERT (OOS Δ ∈ [-0.05, +0.05])**: R5 vol-target ceiling axis CLOSED at single-seed. /011 PIVOTS to UNUSED `risk-primitive` SUBTYPE — recommend per-symbol regime-conditional binary kill switch (e.g., "if NATR_14 > 7%, skip entry") rather than proportional scaling. This is OPC-orthogonal to /010 per v3/020 lesson.
- **/010 NEGATIVE marginal (-0.05 to -0.10 OOS Δ)**: R5 proportional-scaling family CLOSED at v1 (matching v3/020 universal pattern). /011 PIVOTS to UNUSED `risk-primitive` BINARY family or `labeling` axis (triple-barrier σ_t source).
- **/010 NEGATIVE-catastrophic (OOS Δ < -0.20)**: /011 = methodology audit + reconsider Failure Mode 4 Optuna basin-shift. Not the expected path.
- **/010 NEGATIVE-mis-calibrated**: /011 = vol_target re-grid at {3.0, 5.0, 6.0}. Not the expected path; F2 oracle pre-registers 15.3% well inside band.

## 4. Honest Confidence

**LOW confidence on directional Sharpe prediction; HIGH confidence on verdict CLASS.**

Track record after /005-/009: 0/6 directional Sharpe predictions correct; 1 PARTIAL. My calibration on signed deltas is broken. I will NOT pretend otherwise.

What I AM confident in (HIGH):
- **Verdict class is PROMISING-INERT or marginal-NEGATIVE** (~70% probability). The oracle EDA is well-constructed, R5 is STATELESS per /054, and the QR's Section 2.4 per-symbol decomposition is honest. The Δ is small enough that Optuna re-optimization noise will dominate the directional sign.
- **F2 fire rate band check will PASS** (~85% probability). Oracle 15.3% is mid-band; even ±50% deviation from oracle keeps it in [10%, 60%].
- **F4 DEGENERATE_PREDICTOR will not fire** (~95%). R5 is position-sizing only; no label or feature surface modified.

What I am NOT confident in (LOW):
- The sign of OOS Δ (could be +0.05 or -0.05 with similar probability).
- Whether /010 advances to /011 CONFIRMATION. ~25% probability of clearing the PROMISING gate at +0.05 OOS Δ given single-seed=42 variance.

**The one thing the QR should NOT ignore**: Failure Mode 5 (LINK edge erosion) is the central tension. If the /010 reports show LINK OOS net_pnl reduced by >20% AND portfolio OOS Δ ≤ 0, this is informative even at NEGATIVE verdict — it confirms v3/020 generalizes to 5-symbol universe and CLOSES proportional-scaling R5 family universally at v1. That's a useful structural finding even from a NEGATIVE outcome.

## What I Did NOT Recommend, and Why

I did NOT recommend: (a) per-symbol R5 calibration (axis-stacking trap; defer to /011 if PROMISING); (b) running a 3-point vol_target grid at /010 (would exceed 2h cap and stack axes); (c) lowering n_trials to 20 to save time (no — TPE warmup saturation needs ≥30); (d) raising ENSEMBLE_SIZE=3 → 5 (no — that's a CONFIRMATION knob); (e) changing seed from 42 (no — frozen baseline per `feedback_v3_single_seed_frozen_baseline.md`).

## Closing Note

QR has done strong EDA work. The 2.5% → 4.0% recalibration is exactly the "EDA designs the sharpest experiment" pattern at its best. Brief is HIGH-quality; Section 2.4 per-symbol PnL decomposition is the single most valuable artifact (read it twice). The experiment is well-framed even if the verdict lands PROMISING-INERT — it generates a clean structural finding either way. Proceed.

---

## Orchestrator Workflow Note

LM Master Phase 4.5 fired AFTER QR Phase 5 brief authoring (post-`5506507`) rather than between Phase 4 and Phase 5 due to single-session compaction boundary. Functional alignment verified:
- QR's brief pre-registers PROMISING-INERT-to-marginal-NEGATIVE outcome class — matches LM Master's HIGH-confidence verdict-class prediction (70%).
- QR's vol_target=4.0% calibration (revised from 2.5% via EDA) — LM Master endorses as "exactly the EDA designs the sharpest experiment pattern at its best".
- QR's single-axis discipline (no per-symbol calibration) — LM Master endorses as bundling-discipline-correct.
- QR's Section 11 alternates list vol_target ∈ {3.5, 4.0, 4.25} for /011 CONFIRMATION — matches LM Master's /011 PROMISING branch prescription.

Net: no brief revisions required; LM Master content is integrated retroactively as Section 3.7 of brief is structurally LM-Master-response-aware (QR pre-authored "If LM Master suggests per-symbol calibration: defer to /011 CONFIRMATION" — exactly what LM Master recommends).

Proceeding to Phase 5.5 gate.
