# team-03 — IS Report

Family: `t03-btc-residual-momentum-v1` — BTC/market-beta-residual cross-sectional momentum.
Spec: research_brief.md §10 (frozen; implemented by QE in `strategy.py`).

Source of ALL numbers in Section 1: `out/is_metrics.json` (produced by `cli.py team-run
--team team-03`; window 2020-01-01 → 2024-07-01 exclusive, 54 monthly points).
Section 2 cites evaluator-stamped ledger experiments (`experiments.jsonl`) and is labeled as
scratch-evaluator provenance (same engine code path; NOT team-run output).

## 1. Headline (team-run)

| metric | @1× | @2×-stress |
|---|---|---|
| **net IS Sharpe (objective)** | **1.3040** | **0.9273** |
| maxDD (vol-targeted net) | −36.75% | −41.48% |
| total return (compounded) | +402.0% | +192.9% |
| ann. turnover | 118.56× | 118.56× |
| regime Sharpe bull / bear / chop | 1.929 / 1.326 / **−0.213** | 1.618 / 1.011 / **−0.762** |
| total cost (cum., unlevered book) | 0.3369 | 0.6738 |
| total funding P&L (cum., unlevered) | +0.1106 | +0.1106 |

Breadth vs floor: median names long/short = **19 / 19** vs required ≥ 5 — passed with ~4×
margin; mean gross 0.999, mean net +0.0013 (dollar-neutral by construction).

Funding P&L share: funding is a small TAILWIND, not a drag — cumulative +0.1106 on the
unlevered book, offsetting ≈ 33% of the 1× cost total (0.3369). The short side of the
residual-loser book collects more funding than the crowded-long winners pay.

Pre-registered chop weakness, stated plainly: the chop bucket is **negative** (−0.213 @1×,
−0.762 @2×). This was predicted in research_brief.md §2 BEFORE any experiment: fast
narrative-rotation chop is this mechanism's worst weather. We did not patch it in-sample
(any chop-specific fix would have been regime-fitting). Bull and bear buckets are both
strongly positive at both cost tiers — the strategy is a two-of-three-weather book.

## 2. Robustness evidence (ledgered scratch experiments; same evaluator code path)

- Residualization earns its keep (e01 vs e02): plain XS momentum Sharpe 0.885 → residual
  1.136 at identical settings; bear bucket 0.50 → 1.22. The improvement concentrates exactly
  where the mechanism predicts (regime turns).
- Formation plateau (e03/e04): falsifier F1 median over L∈{42,63,126,168} ≈ 1.05 (both
  scalings) — no configuration in the pre-registered 2–8-week band was near zero.
- Beta-estimation robustness (e05): all 6 (W_beta × factor) combos min-Sharpe ≥ 0.83 over
  L∈{42,63,126} — the factor definition is not load-bearing.
- Ex-bull-2021 robustness (e09): recomputing monthly Sharpe with the entire
  2020-03-13→2021-04-14 bull EXCLUDED gives **0.904** (falsifier F2 passed) — the edge is
  not a 2020-21-bull artifact. Funding-off Sharpe 1.178 vs funding-on 1.304 (F4 passed).
- Plateau confirmation (e10): all nine one-step perturbations of the final spec
  (L, W_beta, g, K, DVW factor) score 0.97–1.49 @1× and ≥ 0.61 @2× — plateau, not peak.
- Yearly Sharpe (e09 readout): 2020 +2.08, 2021 +2.04, 2022 +0.91, 2023 −0.11, 2024H1 +1.02;
  30/54 positive months, worst month −13.4% (2023-03).
- Disclosed non-adopted peaks (e06/e03): g=0 (1.49 @1×) and L=168 (1.28 @1×) scored above
  the selected spec but were NOT adopted — the pre-registered selection rules (§7) bind.

Experiment budget: 10 of 40 used (e01–e10), all logged before results were read.

## 3. Honest expectations for the sealed holdout (2024-07 → 2026-06)

The holdout is 24 monthly points — the noise floor on a 2-year Sharpe is large, and our IS
estimate carries some selection optimism despite plateau rules (10 experiments, pre-registered
selection, but non-zero researcher degrees of freedom remain).

Would NOT surprise us:
- A haircut to roughly half the IS Sharpe (≈ 0.5–0.9) from selection decay + regime mix.
- A near-zero or mildly negative stretch if the holdout is chop-dominated — that is the
  documented weakness (chop −0.21 IS), and calendar-2023 (−0.11) shows what a chop-heavy
  year looks like for this book.
- Elevated turnover cost impact on new thin-liquidity listings entering the top-40.

WOULD surprise us (and would argue the thesis is wrong, not just unlucky):
- Strongly negative holdout Sharpe (worse than ≈ −0.5) during a period containing at least
  one sustained trending phase (bull or bear) — IS says trends are where this book earns.
- A bear-phase wipeout: residualization + dollar-neutrality + the engine vol-target kept the
  IS bear buckets positive at both tiers; a structural bear failure would contradict the
  mechanism, not merely underperform it.
- Holdout Sharpe exceeding IS (> 1.3) — we would attribute that to favorable regime mix
  (trend-rich holdout), not to skill beyond the IS estimate.

We submit this as an honest two-of-three-weather book with a documented chop weakness, a
plateau-selected parameterization, funding as a mild tailwind, and 4× breadth margin.
