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
2. Deflate +1.164 → honest ~+0.75–0.95 forward expectation (wide band).
3. G-mania = mechanism-efficacy, not regime alpha; 2020-12-only clip-hurts framing.
4. G-crash thin (+0.20pp); F2 bear-rally/capitulation C1-firing is a named OOS crash risk.
5. C2 = the fragile contribution; stress on non-2024-11 squeezes; no post-hoc Q scan.
6. Mania fix rests on C1/C2; C3/C4 correctly dropped; C4 stickiness lesson recorded.
7. C5 falsification NEGATIVE on all axes + C1 anchor validated — record both §5.4 paragraphs.
8. Correct the Rule-1 formula sign error before any future reuse of the decision tree.
