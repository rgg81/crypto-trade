# REVIEW-006 — Critic Adversarial Review of EXPLORATION-006 Results (IS-only phase)

**Reviewer:** Quant Critic (read-only). **Date:** 2026-07-10. **Persisted by orchestrator.**
**Quarantines honored:** no CONFIRMATION-005.md / baseline artifacts / sibling worktrees. IS-only.

## OVERALL VERDICT: **SUCCESS-WITH-CAVEATS**

The frozen §5.5 interpretation map, applied honestly to the tree-resolved candidate **L1 (C1+C2)**,
lands in the SUCCESS tier (all 7 HARD + all 5 SOFT gates pass). The goalpost is not moved. The
caveats — thin G-crash margin, an inflated C2 lift, mandatory deflation, and the
mechanism-efficacy (not-alpha) reading of G-mania — bar "SUCCESS-CONFIRMED". This is an
**IS design-validation, not a deployability claim**; a separate forward-validation is mandatory.
Engineer scope respected (observations only); single frozen pass; parity exact; 46/46 tests green
incl. both new indicator leak positive-controls (verified non-vacuous).

## 1. Decision-tree resolution (frozen §5.2) → candidate = L1

Marginals: m_C1 +0.0918 (ΔMania +1.431pp) · m_C2 +0.1586 (+1.874pp) · m_C3 −0.1805 (−1.906pp) ·
m_C4 −0.2472 (−1.375pp).

- **R2 drops C3:** m_C3 < −0.05 AND ΔMania_C3 ≤ 0 — unambiguous. (Pinned crash clause does NOT
  fire: crash(L2) +1.607% ≥ +1.55%.)
- **C4 drops by nesting** (C4 in-stack requires C3 in-stack), regardless of R1.
- **R3 retains C2** (m_C2 +0.159 ≥ −0.05). **C1 never dropped.** → **Candidate = L1.**
- **[F1] Rule-1 formula sign error (non-dispositive):** `maxDD(L3) ≥ maxDD(L2) − 0.01` contradicts
  its gloss ("does not tighten by ≥1pp"; C4 tightened 2.78pp). Correct form:
  `maxDD(L3) < maxDD(L2) + 0.01`. As written the escape clause is nearly always TRUE. Candidate is
  L1 under either reading (nesting governs). Correct before any future reuse of the tree.

## Gate scorecard — L1 (frozen §4)

| Gate | Type | Threshold | L1 | Result |
|---|---|---|---|---|
| G-years | HARD | all years ≥ 0 | min-PY +0.10 (2023) | PASS |
| G-crash | HARD | ≥ +1.55%/mo AND >0 | +1.754%/mo | **PASS (thin, +0.20pp)** |
| G-mania | HARD | ≥ +4.52%/mo | +5.829%/mo | PASS |
| G-sharpe-floor | HARD | ≥ +0.45 / 2× ≥ +0.35 | +1.164 / +1.028 | PASS |
| G-dd-floor | HARD | ≥ −35% | −28.58% | PASS |
| G-turnover | HARD | ≤ 100x | 50.1x | PASS |
| G-worst-month | HARD | ≥ −15.0% | −12.72% | PASS |
| G-crash-win / G-crash-leg / G-mania-worst / G-sharpe-target / G-dd-target | SOFT | — | 70% / +1.373 / −10.63% / +1.164,+1.028 / −28.58% | all PASS |

## 2. Central suspicion — controls that RAISE IS Sharpe

**Ruling: mechanism direction genuine; magnitude inflated — C2 is the least trustworthy component
[F3].** Genuine: pre-registered adverse-selection mechanism (excluded parabolic shorts −4.08 fwd
short_px); sparse (5.6% of short-name-candles); improvement in the right leg/months; broad
per-year lift; crash short_px barely moves. Overfit-side: Q=+0.30/K=21 is a single un-scanned,
P&L-adjacent point; ~+4.8pp of the mania improvement concentrates in 2024-11 — the exact month the
threshold was audited against (textbook tailoring signature); +0.287 is large for so sparse an
intervention. **Deflated C2 OOS contribution ~+0.10–0.15.** No post-hoc Q scan permitted on this
IS window; forward-validation must stress C2 on non-2024-11 squeezes.

## 3. Prediction scoring (§6)

C1: 3 HIT + mild crash MISS (−0.32pp, = corrected-§3.3 behavior). C2: 3 HIT + mild crash MISS
(−0.63pp, bear-rally exclusions). C3: 2 HIT / 2 MISS (Sharpe −0.12, maxDD worsened) —
mis-calibrated (vol-target lag + winner-clip). C4: mania MISS BIG (pred small+, obs −1.61pp; brake
stickiness = RISK-006 §4.1's "locks out the rebound" materialized). **C5: 4/4 HIT — falsification
confirmed.** Pattern: surgical past-only market-signal controls (C1/C2) well-calibrated; symmetric/
stateful governors (C3/C4) mis-calibrated. The tree retained the right pair.

## 4. Anomalies — none invalidate a number or gate; two material caveats

- **[F4] C4 own-equity feedback:** 76 braked rebal steps (28%) vs RISK-006's "~4 episodes/0.8-yr"
  — ~2× stickier in-loop (halved gross slows recovery to the −10% release). Echoes the
  stateful-gate ORACLE-EDA-invalid lesson. No effect on L1 (C4 dropped); recalibrate on the braked
  path before any re-introduction.
- **[F2 input] 2022-08 C1-fires-on-winning-short** (cov 30%, capitulation month, V0 short_px
  +0.065): the unexamined 2022-07→08 turn. Contributes to the thin crash margin. Bounded,
  disclosed.
- top10>100% for de-grossing variants = valid ratio. **L1 top10 = 83.0% < V0 98.8% — genuine
  concentration improvement.**

## 5. Deflation

Phase n_eff ≈ 5–6, cumulative ≈ 15–21 → ~0.15–0.30 haircut, PLUS the un-counted C2-threshold DOF
and second-IS-redesign compounding. L1 = V0(+0.913, itself REVIEW-005-deflated to ~+0.65–0.80) +
m_C1(+0.09) + m_C2(+0.16, least trustworthy). **Honest forward expectation ≈ +0.75–0.95, wide
band. +1.164 is an IS upper bound.** IS-only/no-deployability framing respected throughout.

## 6. Mechanism-efficacy caveat

G-mania at L1 (+5.83 ≥ +4.52) is NOT independent regime alpha: the bucket is 12/13 C1-help months
+ one genuine clip-hurts winner (2020-12, short_px +0.143). **[F5] The engineering report §7(iii)
repeats the winner-clip miscount (cites 2024-02, short_px −0.041 → C1 helps); PHASE7-006 must use
the corrected 2020-12-only framing.**

## 7. Reproducibility / integrity — PASS

IS-slice + runtime assert; frozen params match brief §2 exactly; 2×-cost twin exact; common-slice
§2.6-F4 implemented; MANIA-rule regeneration asserted in-run; leg reconciliation ≤2.8e-17; parity
ABORT-guard armed; both new leak tests non-vacuous, importing the SAME builders the matrix uses.
**[F6 LOW]** crash sub-regime split hardcoded (diagnostic-only) — regenerate from the market rule
for full reproducibility.

## §5.4 mandatory verdict inputs

- **C5 falsification:** V5 Sharpe −0.072 vs V0; crash −1.094pp; mania ≈0. All pre-registered
  NEGATIVE directions. **Diagnostic thesis AFFIRMED** (BTC-crash de-risking attacks the wrong regime).
- **C1 anchor:** ΔMania_C1 +1.431pp > 0. **Anchor validated.**

## Ranked findings
F1 [MED] Rule-1 sign error (non-dispositive; fix before reuse) · F2 [MED] thin G-crash margin with
materialized erosion mechanism · F3 [MED] C2 lift inflated/2024-11-concentrated · F4 [MED] C4
stickiness 2× calibration miss · F5 [LOW] report §7(iii) winner-clip slip · F6 [LOW] hardcoded
sub-regime split.

## Caveats PHASE7-006 MUST carry
1. IS design-validation only; NO deployability claim; forward-validation mandatory.
2. Deflate +1.164 → honest ~+0.75–0.95 forward expectation (wide band). [SUPERSEDED by the
   phase addendum below: re-anchored band +0.55–0.80.]
3. G-mania = mechanism-efficacy, not regime alpha; 2020-12-only clip-hurts framing.
4. G-crash thin (+0.20pp); F2 bear-rally/capitulation C1-firing is a named OOS crash risk.
5. C2 = the fragile contribution; stress on non-2024-11 squeezes; no post-hoc Q scan.
6. Mania fix rests on C1/C2; C3/C4 correctly dropped; C4 stickiness lesson recorded.
7. C5 falsification NEGATIVE on all axes + C1 anchor validated — record both §5.4 paragraphs.
8. Correct the Rule-1 formula sign error before any future reuse of the decision tree.

---

# ADDENDUM 2 — Rebal-phase fragility ruling (same date, pre-T0 of the forward protocol)

**Trigger:** while building the forward paper-trade runner, the QE discovered the weekly rebal=21
construction has 21 possible 8h phase offsets; all /005 and /006 evidence was generated at the
phase inherited from the panel's 2020-01-01 (Wednesday) start — never chosen, never scanned. A
committed IS-only sweep (`blind_phase_sweep_006.py` → `paper-l1/phase_sweep_is.csv`) evaluated
all 21 phases.

## Addendum verdict
**SUCCESS-WITH-CAVEATS SURVIVES on the DESIGN/MECHANISM axis — strengthened there — but is
DOWNGRADED on the LEVEL axis.** The +1.164 Sharpe / −28.58% maxDD are a favorable, never-chosen
phase draw; L1 maxDD breaches the −35% floor at 7/21 phases (to −70.4%; phase-agnostic mean
≈ −37.3%). Had the panel started Monday, /006 would have FAILED its own gates.

## Key numbers (all IS, frozen params, warmup=63)
- V0: phase mean +0.334, median +0.502, std 0.509, min −0.795 (Mon@00h), max +1.109; the /005
  headline +0.913 ranks **3/21** (top ~14% of its own phase distribution).
- L1: phase mean +0.947, median +1.008, std 0.443, min +0.085, max +1.589; **21/21 positive**;
  frozen Wed@00h +1.164 ranks 8/21.
- Overlay delta (L1−V0): **positive at ALL 21 phases**, mean +0.614, min +0.250 (at the frozen
  phase itself — the frozen evidence UNDERSTATED the control benefit), max +0.919 (at the worst
  base phase). C1+C2 convert a phase-fragile base (4/21 negative) into a phase-robust Sharpe
  book (0/21 negative). Robustness claim is Sharpe/overlay-scoped, NOT maxDD-scoped.
- Dispersion mechanism: concentrated in violent squeeze months (2024-11 swings 35.3pp across
  phases) — a 1-2 day rebal-boundary shift decides whether the short leg holds through a squeeze.

## Rulings
1. **Sweep ADMISSIBLE** as falsification-directed robustness analysis (analogous to /005's
   cadence table): selection-free, IS-clean (front-trim only; OOS seal asserted), fully
   disclosed, drift-proof (reuses the runner's frozen run functions). Condition: the
   phase-selection ban is mandatory — adopting Wed@08h (the max) would convert it to best-of-21
   search and void the accounting.
2. **Forward anchor = Wed@00h** (the a-priori panel-start phase; the phase all frozen evidence
   was generated at). The Mon@00h pin (orchestrator operational choice, worst-of-21, ~zero IS
   edge, near-guaranteed FF-1 breach) is REJECTED and corrected pre-T0 — a pre-registration
   correction, NOT a clock reset (no forward data contaminated). Wed@08h FORBIDDEN (selection).
   All-21 equal-weight ensemble = a genuinely more robust NEW construction — recommended as a
   future design iteration, not this test.
3. **Phase-ensemble forward diagnostics BELONG in the protocol:** 21-phase distribution logged
   weekly, INFORMATIONAL; gates bind only to the Wed@00h book; phase-selection ban pre-registered.
   A one-sided mechanism-contradiction gate is LEGITIMATE (tests direction, aggregates across
   phases, selects nothing): forward overlay delta < 0 at ≥11/21 phases (trailing window,
   evaluated at the 12-month primary, minimum-N) → CONTRADICTION. Positive overlay grants
   nothing. FF-1 stays at −35% (do not widen to accommodate fragility); log the overlay delta at
   any FF-1 breach for attribution (breach+positive overlay = base phase-tail; breach+negative
   overlay = mechanism failure; either way FF-1 fails).
4. **Ledger:** zero best-of-k inflation (nothing selected) + 1 researcher-DOF bump → cumulative
   n_eff ≈ 16–22. The material move is a LEVEL RE-ANCHOR: expectation base +1.164 → phase-
   agnostic +0.947, then standard deflation → **revised honest forward band ≈ +0.55–0.80**;
   forward maxDD honest expectation −35%…−50% plausible (FF-1 breach risk elevated, phase-driven).
5. **Retroactive /005 note:** a substantial fraction of /005's +0.91 was phase luck
   (phase-agnostic base ≈ +0.33–0.50; maxDD mean ≈ −49%, worst −82.9%; 4/21 phases negative) —
   a deflation vector REVIEW-005 did not capture, and a plausible IS-side mechanism for the
   /005 forward underperformance. Track lesson: **rebal phase is a first-order robustness axis
   for any cadence > 1 candle; sweep it before believing a headline.**

## New findings (ranked)
- **F7 [HIGH]** L1 maxDD phase-fragile; the passing G-dd-floor reading was a favorable draw
  (breaches −35% at 7/21 phases). Forward FF-1 at elevated phase-driven breach risk.
- **F8 [HIGH]** The Mon@00h forward pin was the single worst of 21 phases — corrected pre-T0.
- **F9 [MED]** /005's +0.91/−33% headline substantially phase luck (rank 3/21).
- **F10 [POSITIVE/MED]** C1+C2 overlay phase-robust on Sharpe (21/21 positive; frozen phase
  understates it). Strongest orthogonal design-validation evidence the track has.
