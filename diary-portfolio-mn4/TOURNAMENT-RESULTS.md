# MN4 TOURNAMENT RESULTS — 10 ideas, 2-year holdout, the verdict

**Date:** 2026-07-12. **Track:** MN4 (blind parallel tournament). **Phase A** (10 QR+QE pairs, IS-only,
parallel) + **Phase B** (reveal all 10 on sealed `[2024-07-01, 2026-07-01)`) COMPLETE. **Phase C**
(Critic tournament review) in flight. All 10 `MN4-NN` tokens spent (`REVEAL-LEDGER.md`). 20 quantstats
tearsheets in `reports-portfolio-mn4/` (IS + holdout per strategy). Model: Opus 4.8 throughout
(Fable rate-limited; user-directed).

## THE FIELD — sorted by holdout result

| # | Idea | IS Sh (1×/2×) | Holdout Sh (1×/2×) | Holdout verdict | Generalization read |
|---|---|---|---|---|---|
| 10 | Born-diverse ensemble | +0.50/+0.28 | **+0.45/+0.49** | **PASS** | **HELD** — genuine; maxDD shallower than every member; crash +2.2; β-neutral |
| 06 | Funding prediction | −0.04/−0.61 | **+1.60/+1.13** | **PASS** | **INVERTED (IS-fail→holdout-pass)** — self-diagnosed regime artifact (funding-regime flip; model still < persistence baseline) |
| 03 | Regime-adaptive | +1.55/+1.28 | +1.09/+0.92 | FAIL (mania-β gate) | **HELD** — alpha held, crisis defense fired on real unseen crashes (Aug-24, Oct-25) |
| 01 | TS-momentum | +0.96/+0.83 | +1.13/+0.97 | FAIL (t-stat gate, 1.59) | **HELD + IMPROVED** — Sharpe up, maxDD down, crash flipped positive |
| 02 | Meta-breakout | +1.92/+1.43 | +0.91/+0.15 | FAIL (maxDD, per-half) | DECAYED — real edge, partial generalization; crash-fragile (−5.9) |
| 08 | Vol-targeted RP (dir) | +1.19/+1.18 | −0.12/−0.22 | FAIL | **INVERTED** — bull-regime luck; chops-bleed (−12% in chop) |
| 04 | Slow ML flagship | +1.02/+0.84 | flat/−0.88 (diag) | FAIL | **CRASH EDGE INVERTED** (+33%→−192%); IC HELD (+0.05) but book inverted — regime shift |
| 09 | Calendar | null | −0.33/−0.47 | FAIL | null confirmed |
| 05 | Kalman stat-arb | −2.91/−4.82 | −2.28/−4.66 | FAIL | null deepened (IS diagnostic predictive) |
| 07 | XS reversal | −1.01/−1.10 | −1.68/−1.74 | FAIL | null deepened |

## THE CLEAR SIGNAL — trend/momentum generalized; ML residual-alpha and static beta did not

Three books built on **trend or momentum** (01 TS-mom, 03 regime-momentum, 10 ensemble-with-trend)
all **held or improved their alpha** across two genuinely unseen years — including through the real
Aug-2024 yen-carry crash and Oct-2025 deleveraging. This is the canonical quantitative-finance prior
(time-series momentum is the all-weather edge) finally tested on crypto after four tracks of
cross-sectional attempts, and it held. **IDEA-10** (which carries a trend+carry core inside a
diversified ensemble) is the one clean PASS and the tournament's strongest generalizer: +0.45 Sharpe
on unseen data, maxDD shallower than every member, beta-neutral, positive in crashes.

The **ML residual-alpha flagship (04) confirmed — for the second time — that its crash edge is an
in-sample artifact that inverts on this holdout** (MN3-G inverted +11→−2.9; MN4-04 +33→−192). The
deep finding: the model's rank-IC *held* (+0.05, t+11.8) — it still ranks coins correctly on unseen
data — but the long-short *spread inverted in crashes* (high-ranked coins cratered harder), a
structural regime shift from 2020–24 retail flow to 2024–26 ETF/institutional flow. Positive IC
masked by crash-regime inversion.

## THE TWO PASSes — one genuine, one suspect (the Critic's call)

- **IDEA-10 PASS (genuine generalizer candidate):** held on every dimension, robustness-first
  (modest Sharpe, shallow DD, beta-neutral, crash-positive). The trustworthy survivor.
- **IDEA-06 PASS (self-diagnosed regime artifact):** the unusual IS-fail→holdout-pass inversion.
  The pair's forensics showed the model's prediction quality was stable but still worse than a naive
  persistence baseline in BOTH periods; the holdout win came from the funding regime flipping
  (longs-pay → shorts-pay, 2.7× vol, 4.4× income) — a leveraged carry win suiting the holdout's
  bear regime, not funding-prediction alpha. Two red flags self-flagged: small-sample regime wins,
  and one PASS out of 10 at +1.6 is right at the expected false-positive rate after multiplicity
  correction. This is the case the Critic's correction exists to catch.

## Two narrow-gate FAILs whose alpha held (the Critic should weigh these)

- **IDEA-01** failed only statistical significance (t=1.59 vs 2.0 — a 2-year weekly window cannot
  reach t=2.0 without extreme Sharpe); Sharpe +1.13, maxDD improved, crash flipped positive.
- **IDEA-03** failed only mania-regime beta hedging (β+0.34 vs <0.20 — a fixable construction flaw);
  Sharpe held at +1.09, and its crisis defense demonstrably fired and protected on real unseen crashes.
- Both are real trend/momentum edges that generalized; the FAILs are one narrow gate each, not alpha
  failures. Whether they "count" as survivors is a judgment for the Critic.

## Multiplicity framing for the Critic
10 ideas tested, 2 PASS (06, 10), 2 narrow-gate FAILs with held alpha (01, 03). The honest question
the Critic must answer: **of {10, 06, 01, 03}, which (if any) is a genuine generalizer vs a
multiplicity artifact?** IDEA-06 is the prime false-positive suspect (IS-fail/holdout-pass,
regime-coupled). IDEA-10 is the prime genuine candidate (held cleanly). 01/03 are alpha-confirmed
but gate-failed. A rigorous answer likely crowns **IDEA-10** (and possibly 01/03 on the alpha-held
read) and **rejects 06** on the multiplicity + regime-artifact analysis.

## What generalizes on this dataset (the tournament's structural output)
1. **Trend / time-series momentum** — held across three independent constructions. The all-weather
   prior is real on crypto, at weekly/daily cadence, beta-hedged.
2. **The BTC-only minimal-L2 beta projection** — neutrality generalized cleanly across the whole
   field (confirmed for the Nth time).
3. **ML cross-sectional residual-alpha does NOT generalize through regime shifts** — IC can hold
   while the book inverts (the ranking-to-return relationship is regime-dependent). Twice confirmed.
4. **Funding carry is regime-coupled**, not a free all-weather premium — it pays in some regimes
   (holdout's bear) and bleeds in others (IS mania). 6× confirmed now.
5. **Static directional managed-variance bleeds in chop** — vol-targeting handles sharp crashes but
   cannot exit downtrends; all-weather directional needs a trend EXIT, not just de-risk.

*— Orchestrator, MN4 tournament, 2026-07-12. 10/10 revealed; 2 PASS (one suspect); trend/momentum
is the signal. Phase C: Critic adjudicates the generalizer.*
