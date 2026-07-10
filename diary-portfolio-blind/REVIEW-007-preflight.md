# REVIEW-007-preflight — Critic Pre-Flight of the EXPLORATION-007 Brief (phase-ensemble L1)

**Reviewer:** Quant Critic (read-only). **Date:** 2026-07-10. **Persisted by orchestrator.**
**Scope:** frozen brief (briefs-portfolio-blind/EXPLORATION-007.md) + single-source runner
verification, BEFORE any ensemble run. Quarantines honored; IS-only.

## VERDICT: **PASS-WITH-CONDITIONS** (4 minor pre-run prose/spec fixes; none touch any frozen
value, list, threshold, gate number, or run output)

## Per-check results
1. **§2 honesty framing: mostly honest; ONE smuggle (Condition A).** The known-ex-ante Sharpe
   level is correctly declared non-discovery; G-sharpe-floor (+0.60 HARD) is a pure
   implementation-catastrophe catch (honest). BUT §5.1 made G-sharpe-target (+0.90) and
   G-2xcost-target (+0.75) — both near-known to pass — SUCCESS conditions, letting an observed
   quantity co-determine SUCCESS. Fix: G-dd-target (−30%) is the discriminating SUCCESS
   condition; demote the Sharpe/2x targets to prediction-scoring lines (or add the
   arithmetic-anomaly-flag clause: sub-band Sharpe with a maxDD win = investigate, not demote).
2. **G-mania reference = V0-ENSEMBLE: PASS.** Apples-to-apples; reusing the frozen 13-month
   market-only bucket for an ensemble book is coherent (the bucket labels calendar months, not
   books; re-deriving from ensemble coverage would reintroduce the F1 circularity). Ensure
   V0-ENSEMBLE mania mean computed on the same common [83:] slice.
3. **Selection-free: PASS.** Equal-weight all-21 chooses nothing — the ban-compatible
   phase-luck-removal construction; any other weighting would be a DOF/selection.
4. **Predictions: PASS.** Ten tight point+band pairs, scoreable. The maxDD band −28%
   [−22%,−36%] straddling both floors is legitimate two-sided mechanistic uncertainty, not an
   unscoreable hedge — the §5.1 gates pre-adjudicate every maxDD sub-region sharply.
5. **Engineer spec: PASS — both cruxes VERIFIED.** (i) Index arithmetic: tranche p's first
   metric-valid candle = original index p+63; common region starts max(p)+63 = 83 — exact, no
   off-by-one. (ii) Analytic 2×-cost twin EXACT for L1: no vol-target/dd-brake/gross-scalar →
   target weights cost-invariant; the drifted-weight equity ratio between rebals cancels cost
   dependence → rets_2x[t] = rets_1x[t] − turnover[t]·cost_side exactly. Admissible; the full
   84-backtest matrix is NOT needed. Tolerance: ≤1e-15 only elementwise on rets; ~1e-12 on
   recompounded quantities (Condition D).
6. **§5 forward-relationship: PASS-WITH-CONDITION (B).** Switch logic coherent with the
   sibling-forward ban (a switch chooses ONE book) and no-clock-reset rules (switch = new
   T0/protocol version, USER decision). T0=2026-07-15 verified as a genuine Wed@00h rebal.
   Hazard: "switch before T0 is cleanest" mildly incentivizes rushing the verdict — add: T0
   timing MUST NOT pressure the verdict; missing T0 costs only a few days of single-phase paper
   data as prior; verdict quality takes absolute precedence.
7. **Ledger: PASS.** +1 DOF honest (mildly conservative — the ensemble was ADDENDUM-2-directed);
   cumulative ≈17–23. Correct note: the ensemble Sharpe is already phase-deflated by
   construction.
8. **Gate/decision-map coherence: PASS.** 8 HARD + 6 SOFT; every outcome maps to exactly one
   tier; maxDD axis coherent across gates; mutually satisfiable. Only wrinkle = Condition A.

## Construction note (Condition C, low)
Mean-of-returns ensemble = constant equal 1/21 weights, implicitly assuming costless
cross-tranche weight maintenance (small OPTIMISTIC idealization) — disclose alongside the
no-netting CONSERVATIVE bias (tranches ~88–94% correlated; both tiny; net likely conservative).

## Conditions (all pre-run, prose/spec only)
- **A [low-med]** §5.1 SUCCESS tier: G-dd-target (−30%) is the discriminating SUCCESS condition;
  Sharpe/2x SOFT targets demoted to prediction-scoring (or arithmetic-anomaly-flag clause).
- **B [low-med]** §5.3: T0-timing decoupling clause (verdict quality over beating T0).
- **C [low]** §2/§4: costless equal-weight-maintenance disclosure.
- **D [low]** §7: analytic-2× assert tolerance ~1e-12 on recompounded quantities.

## Passed cleanly
Known-level honesty; catastrophe-catch framing of G-sharpe-floor; V0-ENSEMBLE reference + frozen
bucket coherence; selection-free equal-weight; falsifiable predictions incl. the legitimate maxDD
straddle; verified index-83 arithmetic; verified-exact analytic 2×-twin; +1-DOF ledger; complete
decision map; sound leak/integrity spec (IS hard-slice + OOS assert, front-trim only, sweep
row-for-row reproduction, tranche-0 parity +1.1638).
