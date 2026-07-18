# team-05 IS report — t05-taker-flow-imbalance-v2

Strategy: cross-sectional taker-flow imbalance, continuation direction. Frozen config per
`research_brief.md` §9: sign=+1, W=21 (7 days), min_periods=16, quote-volume TBR
(rolling-21 sums ratio − 0.5), eligibility-gated demeaned percentile ranks, no sharpening,
no smoothing.

All performance numbers in §1–§4 are from the evaluator artifact
`out/is_metrics.json` (team-run, window 2020-01-01 → 2024-07-01 exclusive, 54 monthly
points). Diagnostics in §5–§6 are NOT in `is_metrics.json`; they come from the logged
scratch experiments (`experiments.jsonl` ids cited, CSVs under `out/scratch/`) and are
labelled as such. Harness: all six checks PASS (`out/harness.json`: scan, determinism,
truncation ok over 12 truncations, corruption, same-bar, widening; violations: none).

## 1. Headline

| metric | 1× costs | 2×-stress (cost AND slippage doubled) |
|---|---|---|
| net Sharpe (monthly, √12) | **1.5013** | **1.0492** |
| max drawdown | −43.01% | −48.70% |
| total return (vol-targeted, cumulative) | +1344.5% | +514.5% |
| total cost (raw, cumulative) | 0.4954 | 0.9908 |
| total funding P&L (raw, cumulative) | **+0.3688 (collected)** | +0.3688 |

Annualised turnover 173.15; mean gross 0.9929; mean net ≈ 0 (1.5e-16 — sum-zero book);
n_months 54.

## 2. Breadth vs floor

Median active names: 20 long / 20 short at both tiers — 4× the charter floor (median ≥ 5
per side). Rank-based construction over the full eligible top-40 set; no breadth risk from
universe churn.

## 3. Per-regime Sharpe (fixed crypto regime tags)

| regime | 1× | 2× |
|---|---|---|
| bull | 1.858 | 1.386 |
| bear | 1.633 | 1.337 |
| chop | 0.330 | **−0.250** |

Stated plainly: the chop-regime edge does NOT survive doubled costs — at the 2×-stress
tier chop Sharpe is −0.25. The strategy's chop edge is thin and cost-fragile; bull and
bear edges survive stress comfortably. This matches the pre-registered regime expectation
(brief §3: "weakest/negative in chop").

## 4. Funding & costs

The book COLLECTS funding: +0.3688 raw cumulative (identical at both tiers — funding is
not cost-multiplied). This is the opposite of the pre-registered expectation (brief §3
predicted funding DRAG on the continuation book: long crowded-buy names should pay
funding). Experiment e01 (`experiments.jsonl`, `out/scratch/results_e01.csv`) showed
funding collect (+0.32…+0.37 raw) across the whole H1 band — empirically, the highest
taker-buy-share names are not the highest-funding names, and the short side (persistently
sold names) pays more funding than the long side costs. Documented as a surprise, not
engineered. Cumulative raw cost is 0.4954 at 1× (0.9908 at 2×) against a raw price+funding
gross that sustains Sharpe 1.05 even at the doubled tier.

## 5. Negative result — H2 exhaustion band (scratch provenance, ledger e01)

The pre-registered secondary hypothesis (H2: fade names aggressively bought over 63–270
candles) FAILED across its entire band: 1× Sharpe −1.81 (W=63) to −1.00 (W=270), all
2×-stress more negative (`out/scratch/results_e01.csv`). Continuation persists at every
tested horizon inside IS; there is no exhaustion reversal. Per the pre-registered
discipline (brief §2) the band's sign was not flipped; H2 is dead and reported as a
negative result with the same precision as the positive one.

## 6. Decay disclosure (scratch provenance, ledger ids e01/e06)

The edge is NOT stationary across the IS window (diagnostics from
`out/scratch/results_e01.csv` and the e06 confirmation run, same evaluator code path as
team-run):

- Yearly monthly-Sharpe at the frozen config: 2020: 1.43 · 2021: 3.50 · 2022: 1.32 ·
  2023: 0.88 · 2024-H1: 0.22.
- Split-half: 2.29 (2020-01 → 2022-03) vs 0.72 (2022-04 → 2024-06).

Positive in every calendar year, but monotonically decaying since 2021 and weakest in the
post-halving chop that ends the IS window. The 4.5-year headline of 1.50 is NOT the
forward run-rate.

## 7. Honest expectations for the sealed holdout

The recent-regime evidence (2023: 0.88; 2024-H1: 0.22; chop 2×: −0.25) is the best
predictor of forward behavior, not the full-window 1.50. My honest holdout expectation is
a net Sharpe in the ~0.2–0.9 range if the 2022-24 decay level persists, with wide bands:
24 monthly points carry a Sharpe standard error of roughly ±0.7, so outcomes from ~−0.5
(mechanism fully decayed plus cost bleed in extended chop) to ~+1.5 (trending, flow-rich
regimes where the mechanism is strongest) would not be statistically surprising. A holdout
result below ~−0.5 would suggest the continuation mechanism inverted (crowding/fade
dominance) — the outcome my dead H2 band makes unlikely but cannot exclude out-of-sample.
The strategy's stress margin (2× Sharpe 1.05 overall, but −0.25 in chop) means a
low-liquidity, choppy holdout is the main downside scenario; sustained directional
regimes (either direction — bear Sharpe 1.63 ≈ bull 1.86) are the upside scenario.

## 8. Freeze readiness

- `strategy.py` implements brief §9 exactly (QE); team-run reproduces the research anchors
  to float precision; untouched by the QR after QE handoff.
- `test_strategy.py`: 7 tests pass, including the future-corruption self-check (QE).
- Harness: 6/6 PASS (`out/harness.json`).
- Ledger: 6 evaluator-stamped experiments, 6/40 budget used, zero unlogged material
  experiments, no adopted post-hoc variants.
- Falsifier (brief §4): did not fire. No pivot used.

team-05 is freeze-ready for `cli.py freeze --team team-05 --family-id
t05-taker-flow-imbalance-v2`.
