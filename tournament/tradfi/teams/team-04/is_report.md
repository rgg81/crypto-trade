# team-04 IS report — t04-xs-momentum-12-1-v1

> STATUS: CANONICAL. All headline numbers below come from `team-run`'s
> `out/is_metrics.json` (@1x and @2x cost); the yearly Sharpe breakdown is computed from the
> same run's `out/net_is.csv`. The QE-built `strategy.py` reproduces the design-phase spec
> confirmation run (exp-023) bit-for-bit — Sharpe 0.5245 @1x / 0.4713 @2x, maxDD -0.2335,
> breadth 12/12, ann. turnover 8.48 — so no drift from the brief's final spec.

## Final strategy

Plain cross-sectional momentum: rank on trailing 252-day return (skip=0) over the eligible
cross-section; long top 20% / short bottom 20% equal-weighted, with rank-hysteresis
membership (stay band 35%) and a 5-name-per-side validity floor. Full spec:
`research_brief.md` §2.

## Headline IS metrics (2010-01-01 .. 2024-06-30, evaluator-scored)

| metric | @1x cost | @2x cost |
|---|---|---|
| net Sharpe (monthly, sqrt-12) | **0.5245** | **0.4713** |
| max drawdown | -0.2335 | -0.2394 |
| total return | +174.9% | +144.2% |
| annual turnover | 8.48 | 8.48 |

- Months scored: 174. Breadth: median 12 names long / 12 short (floor: 5/side; charter
  minimum satisfied with 2.4x margin). Mean gross 1.0; mean net ~0 (dollar-balanced by
  construction).
- Regime scorecard: bull **+0.75** / bear **-1.14** / chop **+0.47**.
- Yearly Sharpe (1x): 2011 -0.31 | 2012 0.51 | 2013 1.54 | 2014 1.17 | 2015 0.67 |
  2016 0.56 | 2017 0.26 | 2018 0.47 | 2019 -0.33 | 2020 0.95 | 2021 1.28 | 2022 0.80 |
  2023 -0.02 | 2024 0.78 — 11 of 14 positive; no single-period carry.

## Evidence trail (all pre-registered in experiments.jsonl; 24 material experiments)

- **A (exp-001..009)** formation x tail grid, skip=21, daily: positive everywhere
  (0.08..0.43); monotone preference for F=252 and narrower tails at every width.
- **B (exp-010/011)** skip axis: pre-registered hypothesis FALSIFIED — skip=0 (0.516)
  beats skip=21 (0.433) and skip=10 (0.378); modern large caps lack the 1-month reversal
  the classic skip protects against. Axis dispersion is within monthly-Sharpe noise
  (~0.26 SE) but consistent in direction across architectures (see exp-024).
- **C (exp-012/013)** weighting schemes: rank-linear (0.290) and vol-scaled momentum
  (0.339) both underperform equal-weight tails (0.516) — negative results, kept.
- **D (exp-014..016)** turnover control: EMA-5 (0.506/0.462), hysteresis 20/35
  (0.525/0.471), hold-21d (0.506/0.477); turnover 26 -> 5-8.5. The 1x/2x gap collapses
  from 0.13 to ~0.05 — the overlay is what makes the strategy cost-robust.
- **E (exp-017..021)** robustness: formation blends dilute (0.435); tail-width plateau
  interior confirmed (0.15 -> 0.460, 0.20 -> 0.525, 0.25 -> 0.508); hold-21d phase sweep
  exposes rebalance-phase luck (mean 0.532, std 0.084, min 0.353) — hysteresis chosen
  because it is phase-free and matches the phase-agnostic mean.
- **F (exp-022..024)** final checks: F=189 neighbor on final architecture scores 0.249 —
  formation-axis sensitivity FLAGGED honestly (F=252 kept on a-priori canonical grounds,
  pre-registered central case); exp-023 confirms the final spec (0.5245/0.4713);
  exp-024 fixes the skip decision on the final architecture (skip=21: 0.395 < skip=0:
  0.525).

## Known weaknesses (stated, not hidden)

1. Bear-regime Sharpe -1.14 — classic momentum-crash exposure; damped by the organizer's
   vol target and caps, not eliminated. We did not and may not bolt on regime gates.
2. Formation axis is a gradient toward 252, not a flat plateau; specification risk at
   shorter formations is real and documented (exp-022).
3. 2019 and 2011 were negative years (leadership rotation); 2023 flat.
