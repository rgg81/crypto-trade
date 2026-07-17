# team-10 IS report — t10-ts-trend-v1 (CANONICAL, QE `team-run`)

All Section-1 submission numbers come from `cli.py team-run --team team-10`
(`out/is_metrics.json` @1x and @2x cost) and reproduce the exp-016 research numbers stored in
`out/exp_results.json` BIT-FOR-BIT. The Section-2 experiment record is the research-phase log
(`tournament.engine.run_is`, keyed by experiment id in `out/exp_results.json`).

## 1. Selected configuration (FROZEN, exp-016) — canonical `team-run` output

Per-name 12-month sign trend with 1-week skip, inverse-vol sizing, EMA-21 weight smoothing
(exact spec: research_brief.md Section 9). Numbers below are verbatim from
`out/is_metrics.json` (`cli.py team-run --team team-10`) and match exp-016 in
`out/exp_results.json` to full float precision.

| metric | 1x cost | 2x cost |
|---|---|---|
| net IS Sharpe (monthly, ann.) | **0.8201** | **0.7653** |
| maxDD | -23.15% | -23.57% |
| annual turnover | 6.40x | 6.40x |
| total return (vol-targeted 15%) | +424.1% | +363.1% |
| median names long / short | 37 / 11 | 37 / 11 |
| mean gross / mean net | 0.970 / +0.195 | 0.970 / +0.195 |
| months scored | 174 | 174 |
| regime Sharpe bull / bear / chop | +1.19 / -1.13 / +0.64 | +1.13 / -1.17 / +0.58 |

Breadth floor: PASS (median short side 11 >= 5). Cost fragility: 1x->2x Sharpe drop is
0.055 at 6.4x turnover — the book is hold-dominated, as designed.

## 2. Full experiment record (21 material experiments, exp-003..exp-023)

Sharpe @1x / @2x, maxDD @1x, ann. turnover, median long/short. Source:
`out/exp_results.json`.

| id | config (K, transform, EMA m, skip s) | S@1x | S@2x | maxDD | turn | L/S |
|---|---|---|---|---|---|---|
| exp-003 | 21, sign, 0, 0 | -0.324 | -1.084 | -0.69 | 78.2 | 31/18 |
| exp-004 | 63, sign, 0, 0 | +0.424 | -0.023 | -0.38 | 45.7 | 33/16 |
| exp-005 | 126, sign, 0, 0 | +0.080 | -0.227 | -0.52 | 33.9 | 35/14 |
| exp-006 | 252, sign, 0, 0 | +0.589 | +0.375 | -0.31 | 24.9 | 37/11 |
| exp-007 | 63, clip2, 0, 0 | +0.184 | -0.220 | -0.33 | 46.0 | 33/16 |
| exp-008 | 63, tanh, 0, 0 | +0.263 | -0.139 | -0.34 | 44.5 | 33/16 |
| exp-009 | 252, clip2, 0, 0 | +0.511 | +0.349 | -0.25 | 22.3 | 37/11 |
| exp-010 | 252, tanh, 0, 0 | +0.565 | +0.402 | -0.27 | 21.6 | 37/11 |
| exp-011 | blend{63,126,252}, tanh, 0, 0 | +0.346 | +0.110 | -0.35 | 29.6 | 36/11 |
| exp-012 | blend{63,126,252}, sign, 0, 0 | +0.211 | -0.088 | -0.44 | 33.7 | 36/11 |
| exp-013 | 252, sign, 5, 0 | +0.699 | +0.581 | -0.29 | 13.6 | 37/11 |
| exp-014 | 252, sign, 10, 0 | +0.740 | +0.658 | -0.28 | 9.6 | 37/11 |
| exp-015 | 252, sign, 21, 0 | +0.764 | +0.708 | -0.25 | 6.5 | 37/11 |
| **exp-016** | **252, sign, 21, 5** | **+0.820** | **+0.765** | **-0.23** | **6.4** | **37/11** |
| exp-017 | 252, sign, 42, 0 | +0.753 | +0.713 | -0.22 | 4.6 | 37/11 |
| exp-018 | 252, tanh, 21, 0 | +0.643 | +0.603 | -0.24 | 5.2 | 37/11 |
| exp-019 | 126, sign, 21, 0 | +0.362 | +0.275 | -0.36 | 9.5 | 35/13 |
| exp-020 | 189, sign, 21, 5 | +0.528 | +0.448 | -0.27 | 8.2 | 37/12 |
| exp-021 | 315, sign, 21, 5 | +0.893 | +0.841 | -0.25 | 5.6 | 38/11 |
| exp-022 | 252, sign, 10, 5 | +0.892 | +0.809 | -0.25 | 9.4 | 37/11 |
| exp-023 | 378, sign, 21, 5 | +0.536 | +0.484 | -0.25 | 5.2 | 38/9 |

## 3. Selection audit trail (pre-registered rule, brief Section 6)

Eligible = breadth floor met AND 2x Sharpe > 0. Best eligible: exp-021 (0.893); within-0.05
band {exp-021, exp-022}. Peak-only ban (one-step neighbor average must be >= 90% of the
config's Sharpe, computed over all one-step neighbors actually run):

- exp-021: neighbors {exp-016: 0.820, exp-023: 0.536} -> avg 0.678 < 0.804 -> **BANNED**
  (K=315 is an edge peak; K=378 collapses).
- exp-022: neighbors {exp-016: 0.820, exp-014: 0.740, exp-020: 0.528, exp-021: 0.893} ->
  avg 0.745 < 0.803 -> **BANNED**.
- exp-016: neighbors {exp-020: 0.528, exp-021: 0.893, exp-022: 0.892, exp-017: 0.753,
  exp-015: 0.764, exp-018: 0.643} -> avg 0.746 >= 0.738 -> **PASS**. No other passing
  config within 0.05 (next: exp-015 at 0.764, -0.056). **SELECTED: exp-016.**

Falsifier check (brief Section 4): plateau-median across the K-axis cells at the selected
transform/smoothing (K in {126, 189, 252, 315, 378}: 0.362, 0.528, 0.820, 0.893, 0.536) =
0.536 >= 0.30 -> family NOT falsified. Minimum one-step neighbor of the selected config =
0.528 = 64% of 0.820 >= 50% -> not an isolated peak. Breadth floor and 2x > 0 both met.

## 4. Negative results (reported with equal precision)

- 1-month TSMOM (exp-003): -0.324 @1x / -1.084 @2x — killed by 78x turnover at 6 bps/side.
- Multi-horizon blends (exp-011/012: +0.346 / +0.211) UNDERPERFORM pure 12m — the canonical
  "blend beats single horizon" prior fails on this universe because the 6m component
  (exp-005: +0.080) is dead weight.
- Continuous transforms (clip2/tanh) do not beat sign at any horizon once smoothing is on
  (exp-018: 0.643 vs exp-015: 0.764); smoothed-sign already delivers the churn reduction.
- Skip-week helps at K=252 (+0.056) — consistent with short-term reversal contamination.

## 5. Honest caveats

- **Horizon-axis noise**: the K response is not a clean plateau (dip at 126/189, spike at
  315, collapse at 378). With 174 monthly points the Sharpe standard error is roughly 0.26;
  most K-axis differences are within ~1.5 SE. The selected cell K=252 is the canonical
  literature horizon, NOT the empirical argmax (0.893 at K=315 was rejected by the
  pre-registered peak ban); we judge this the honest plateau-over-peak choice, and expect
  holdout Sharpe well below the IS point estimate.
- **Bear-regime weakness is structural** (regime Sharpe -1.13): per-name trend is late at
  V-reversals; this is pre-registered behavior (brief Section 3), not a surprise. No bear
  gate is permitted (RESERVED family) and none is used.
- **Long-heavy book**: median 37 long / 11 short; the engine's net cap (|net| <= 0.25)
  trims the long side in strong bull phases (mean net +0.195, mean gross 0.97). Short-side
  breadth (11) clears the floor with margin but thins to 9 at K=378 — another reason the
  spec stays at K=252.
- n_months = 174 covers 2010-01..2024-06 with ragged name starts (fewer names active early).
