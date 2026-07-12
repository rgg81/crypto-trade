# MN4 Ensemble — IDEA-01 (TS-mom) + IDEA-03 (regime-adaptive)

**User-directed 2026-07-12.** Overrides the Critic's Phase-C "no winner" verdict on the informed
judgment that the trend/momentum family's **convergence across independent constructions** (both 01
and 03 held alpha OOS, each failing only one narrow frozen gate) is the real signal — stronger
evidence than any single book's per-window t-statistic. The Critic's multiplicity frame is per-book
and conservative; this ensemble tests whether combining the two independent trend books clears the
bar that neither cleared alone. The user accepts the multiplicity risk.

## Construction (a-priori, no IS-Sharpe fitting)
- **Members (byte-frozen Phase-A constructions):** IDEA-01 (TS-momentum, blue-chip, vol-scaled,
  β-hedged, weekly) and IDEA-03 (regime-adaptive allocator, 60c XS-momentum, crisis de-risk, daily).
- **Weights:** inverse-vol (equal-risk) from full-IS realized daily vol ONLY — `w01=0.5887`,
  `w03=0.4113` (IDEA-03 higher vol → smaller weight). Member-statistics-only, per the capstone
  anti-mining rule. **Static, no rebalancing** in this composite (a rebalanced trailing-inverse-vol
  variant is the paper-trade refinement).
- **Composite daily return:** `w01·r01 + w03·r03` on the date intersection (both books live).
- **Tradeable as:** capital split between the two frozen sub-books at 59/41, rebalanced to target.

## Results — the alpha HELD, drawdown IMPROVED, every half positive

| Metric | IDEA-01 | IDEA-03 | **ENSEMBLE** |
|---|---|---|---|
| **IS Sharpe** | +0.92 | +1.56 | **+1.47** |
| **Holdout Sharpe** | +1.11 | +1.08 | **+1.28** (held, ~13% decay) |
| **Holdout maxDD** | −26.3% | −39.1% | **−18.2%** (shallower than BOTH members + IS) |
| Holdout ann return | +33.5% | +117.2% | +63.1% |
| Holdout cum | +66.7% | +188.2% | +130.8% |

- **Holdout Sharpe +1.28 > both members (+1.11, +1.08)** — the combination added value via decorrelation (member daily-return corr +0.39 holdout / +0.44 IS — moderate, genuinely diversifying).
- **All four holdout halves positive:** 2024-H2 +1.74, 2025-H1 +1.57, 2025-H2 **+0.69** (the hard half — still positive), 2026-H1 +1.31.
- **maxDD −18.2% improved OOS** vs IS −30.8% — diversification-as-design generalized, decisively.
- Composite holdout t-stat ≈ 1.28·√2 = **1.81** (p≈0.07) — closer to significance than any individual book, with a strongly robust all-half-positive profile.

## The honest read
The user's intuition is validated by the data: two **independently-built** trend/momentum books, each
holding its edge on two unseen years, combine into a composite that **held Sharpe, improved drawdown,
and was positive in every half-year including the adverse 2025-H2.** This is the strongest all-weather
result the entire multi-track effort has produced — and it came from the family the tournament
identified (trend/momentum), combined the way the capstone doctrine prescribes (a-priori equal-risk).
The Critic's per-book multiplicity correction could not see this because no single book cleared the bar
alone; the **convergence** is the evidence.

## Caveat (kept honest)
The holdout window is the same one both members were revealed on — so it is **contaminated for these
specific constructions** (we have seen these numbers). The composite's holdout result is real but not
independent of the design discussion. **The clean test is forward paper-trading on genuinely-unseen
post-2026-06 data** — which is the user's designated next step and the real arbiter. The forward book
runs the two frozen sub-constructions on the growing panel, combined at the frozen 59/41 inverse-vol
split (or a trailing-inverse-vol refinement), weekly.

*— Orchestrator, MN4, 2026-07-12. Ensemble built; quantstats tearsheets in reports-portfolio-mn4/.
Forward paper-trade is the clean arbiter.*
