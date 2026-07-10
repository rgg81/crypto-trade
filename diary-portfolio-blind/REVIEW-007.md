# REVIEW-007 — Critic Adversarial Review of EXPLORATION-007 Results (phase-ensemble L1, IS-only)

**Reviewer:** Quant Critic (read-only). **Date:** 2026-07-10. **Persisted by orchestrator.**
**Quarantines honored** (no CONFIRMATION-005 / baseline / forward-artifact reads). IS-only.

## OVERALL: **FAIL** — G-crash HARD breach (+0.933%/mo < the frozen +1.55% floor). Frozen map
governs; no re-anchoring. Adjudication: **a genuine FAIL of a mis-specified gate, not a
construction failure** — attached below; it explains the tier, it does not overturn it.

## 1. Gate scorecard
7 of 8 HARD pass. G-crash FAILS (+0.933% < +1.55%). All other gates pass with wide margins:
Sharpe +1.2826 (floor +0.60), 2×-cost +1.0921 ground-truth (floor +0.45), maxDD −18.59%
(floor −35%, SOFT target −30% also cleared), turnover 50.3x, worst-mo −8.17%, min-PY +0.709.
PARTIAL/SUCCESS both require ALL 8 HARD → **TIER = FAIL.**

## 2. Adjudication — nature of the failure
**Gate-localized, decisive evidence:** the +1.55% floor = 60% of SINGLE-PHASE V0 crash
(+2.586%) — now quantified as ~2.76× the phase-honest level (V0-ENSEMBLE crash +0.935%); crash
months are violent squeeze months, i.e. exactly the most phase-sensitive bucket. The overlay is
crash-NEUTRAL at ensemble level: ENS-L1 +0.933% ≈ V0-ENS +0.935%, short_px +1.204 > 0, win 70%
— on the metric the floor was designed to protect ("does the overlay preserve crash defense?"),
the ensemble passes cleanly. **Contract defect:** G-mania was re-anchored to the V0-ENSEMBLE
reference; G-crash was left on the single-phase-derived absolute floor — an asymmetry BOTH
pre-flights missed (Critic owns its share). The crash point-prediction (+1.7% [1.3,2.1]) was
also wrong — the QR did not anticipate staggering averages the crash bucket down like
everything else. Implications: construction NOT disqualified on crash merits; the FAIL indicts
the gate specification and the ex-ante crash model.

## 3. What any follow-up can honestly claim
- **NO clean IS re-gate** — all numbers revealed; a "corrected-floor /008" on this window would
  be post-hoc gate-fitting. The IS crash gate for this construction is SPENT; it failed.
- **Exploratory findings stand** (descriptive, not gate-certified): (i) phase-tail IS
  time-diversifiable — ensemble maxDD −18.59% shallower than EVERY tranche (best −21.31%, mean
  −37.3%); 0/21 tranche troughs coincide with the ensemble trough; (ii) overlay mechanism
  preserved at ensemble level (mania −1.242% → +4.535%, win 38%→77%; crash short leg intact);
  (iii) all IS years positive (min +0.709 vs V0-ENS 2021 −0.35); (iv) phase-honest level +1.28.
- **The only clean venue for a properly-anchored crash gate is genuinely unseen FORWARD data**,
  pre-registered to a PRINCIPLE not the revealed number: forward crash mean > 0 AND short_px > 0
  AND ≥ forward V0-ENSEMBLE crash (apples-to-apples).
- **§5.3(4) binds on the ACTION** — no switch; a FAILED phase does not promote its construction;
  the single-phase Wed@00h forward book continues. But §5.3(4)'s reason ("crash alpha lost") is
  wrong per §2. The PHASE7 verdict must present SEPARATELY, decoupled from /007's frozen logic:
  the ensemble as a candidate for a NEW freshly-pre-registered forward protocol with the
  crash-defense-preserved gate — a user decision, not a rescue.

## 4. Prediction scorecard: 4 HIT / 6 MISS
rho_bar +0.5245 vs +0.88 [0.80,0.94] = the root MISS (holdings-overlap intuition ≠ return-stream
correlation; fixed-share drift + staggered timing decorrelate 8h streams; max pairwise +0.84).
It cascades into 4 favorable misses (Sharpe +1.2826, vol 0.737×, maxDD −18.59%, 2×-cost
+1.0921). The 6th miss is the consequential one: crash +0.933% vs +1.7% [1.3,2.1] — independent
of rho_bar. HITs: turnover 50.3x, mania +4.535%, worst-mo −8.17%, min-PY +0.709. Ledger: the §2
"Sharpe level known ex-ante" over-claimed — the MEAN was known arithmetic; the Sharpe's
denominator (vol via rho_bar) was a genuine unknown and the real discovery (~74% of +1.28 is
known arithmetic; ~26% is the discovered diversification benefit).

## 5. Critic-owned errors (corrected record)
1. **"Analytic 2×-twin verified EXACT" was WRONG.** Fixed-share drift re-normalizes by
   cost-dependent equity: shares set at rebal k use E[k−1]; the next candle's drifted weight
   divides by E[k], which contains the rebal candle's own cost-bearing return — the cost does
   NOT cancel. Twin exact ONLY at rebal candles; elementwise drift ≤7.13e-05, Sharpe impact
   −0.00009 (negligible; ground-truth rerun used as authoritative — the engineer's handling was
   exemplary). Future briefs: cost-independence claims on this engine must be verified
   EMPIRICALLY (ground-truth diff), never by analytic argument alone.
2. **Pre-flight miss of the G-crash/G-mania anchoring asymmetry** — the defect that caused the
   FAIL.

## 6. Integrity — all PASS
IS hard-slice + OOS assert; tranche-0 parity (L1 +1.1638/V0 +0.9134/−28.58%/50.14x); 21-row
sweep reproduction ≤1.28e-15; leg reconciliation ≤3.12e-17; common-slice first index == 83
asserted; two full runs bit-identical; 53/53 tests; ruff clean.

## 7. Deflation / forward expectation
Ensemble adds no best-of-k surface (selection-free, pre-committed, FAILED); +1 DOF already
booked (cumulative n_eff ≈ 17–23). **Honest forward expectation for the ensemble book:
~+0.70–0.95, central ~+0.80** — above single-phase L1's +0.55–0.80 (phase-luck structurally
removed + a structural ~1.35× vol reduction whose decorrelation mechanism is regime-general),
well below the IS +1.28 (base-edge deflation + transfer uncertainty; forward tranche
correlation could rise in stress).

## Findings (ranked)
F1 [HIGH] G-crash HARD breach → FAIL (frozen map; no IS re-gate admissible — gate SPENT).
F2 [HIGH] Failure is gate-localized: mis-anchored floor (60% of ~2.76× phase-inflated number) +
anchoring asymmetry missed by both pre-flights + wrong ex-ante crash prediction. Crash defense
itself intact.
F3 [HIGH, positive] Phase-tail empirically time-diversifiable (F7 of ADDENDUM 2 resolved):
ensemble maxDD shallower than every tranche; troughs unsynchronized.
F4 [MED] rho_bar conceptual error (holdings-corr ≠ return-corr) + independent crash-level error
— calibration-quality gap, ledgered; discipline intact (falsifiable bands, misses diagnosed).
F5 [MED, self-owned] Analytic-twin "exact" ruling wrong + anchoring-asymmetry pre-flight miss.

## Caveats PHASE7-007 MUST carry
1. TIER = FAIL (G-crash); the IS crash gate for this construction/window is spent.
2. Failure is mis-anchored-gate, NOT crash-defense collapse (localize per F2).
3. NO switch (frozen §5.3(4) binds on action; single-phase Wed@00h forward book continues).
   SEPARATELY: ensemble = strong candidate for a NEW pre-registered forward protocol with a
   crash-defense-preserved gate (forward crash > 0 AND short_px > 0 AND ≥ forward V0-ENSEMBLE)
   on unseen data — a user decision, decoupled from /007.
4. Exploratory findings stand, not validated: tail time-diversifiable, mechanism preserved,
   all-years-positive, phase-honest +1.28.
5. Ensemble forward expectation ~+0.70–0.95 (central ~+0.80); +1.28 = ~74% known arithmetic +
   ~26% discovered diversification.
6. Corrected technical record on the analytic 2×-twin (not exact; ground-truth reruns required).
