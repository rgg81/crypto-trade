# team-01 IS report — t01-funding-carry-xs-v1

Strategy: cross-sectional funding carry — short the coins whose crowded longs pay funding,
long the coins shorts pay for. Funding EWM (halflife 2 candles) → centered cross-sectional
percentile rank (negated) → inverse-vol sizing (63-candle) → causal weight EWM (span 2).
Full specification: `research_brief.md` (QE SPEC section). Implementation: `strategy.py`.

**Number provenance.** Every metric in §1–§4 is copied from
`out/is_metrics.json` (schema 1, window 2020-01-01 → 2024-07-01 exclusive), produced by
`cli.py team-run --team team-01`. §5–§6 additionally cite scratch-provenance decomposition
numbers from ledgered experiments (ids given inline; computed with the evaluator's own
scoring functions but NOT part of the team-run artifact — labeled accordingly).
Harness: all six checks pass (`out/harness.json`: scan, determinism, truncation ×12,
corruption, same-bar, widening — `"ok": true`, zero violations).

## 1. Headline

| Metric (IS, 54 months) | @1× costs | @2×-stress (cost AND slippage doubled) |
|---|---|---|
| **Net Sharpe** (monthly-summed, √12) | **2.4067** | **1.7023** |
| Max drawdown | −24.16% | −25.84% |
| Total return (vol-targeted stream) | 37.67× | 11.38× |
| Annualized turnover | 188.36× | 188.36× |

## 2. Per-regime Sharpe (fixed tags)

| Regime group | @1× | @2×-stress |
|---|---|---|
| Bull | 3.2122 | 2.6725 |
| Bear | 1.9997 | 1.4147 |
| Chop | 0.8280 | 0.0929 |

All three groups positive at 1×; at the stress tier the chop group is approximately flat
(+0.09) while bull/bear retain clear margins. Stated plainly: under doubled costs this book
earns essentially nothing in chop regimes and its edge lives in bull/bear dispersion.

## 3. Breadth, book shape, validity floors

| Check | Value | Floor | Verdict |
|---|---|---|---|
| Median names long | 20.0 | ≥ 5 | PASS (4× margin) |
| Median names short | 20.0 | ≥ 5 | PASS (4× margin) |
| Mean gross | 0.9935 | — | fully invested book |
| Mean net | +0.0188 | \|net\| ≤ 0.25 (engine cap) | effectively market-neutral |
| Months scored | 54 | — | full IS window |

## 4. Costs and funding P&L (team-run artifact)

| Component (raw-net units, pre-vol-target) | @1× | @2× |
|---|---|---|
| Total funding P&L collected | **+0.71347** | +0.71347 |
| Total trading cost (taker + slippage) | −0.53143 | −1.06287 |

The mechanical carry stream alone more than covers ALL trading costs at 1× (134% coverage)
and covers 67% of them at the stress tier.

## 5. Carry vs price-leg attribution (scratch-provenance, ledgered)

From ledgered experiment **e10** (final-candidate deep check, evaluator scoring functions in
`out/scratch/`): with funding P&L switched off, the price leg alone scores Sharpe ≈ 1.51,
versus 2.4067 with funding on — i.e. the mechanical carry contributes ≈ +0.9 Sharpe and the
crowding-unwind price leg is independently positive. Both pre-registered mechanism channels
are present; the strategy is not a pure fee-collection book, nor a price bet dressed as
carry. Supporting decomposition experiments: e02/e03 (freshness structure), e06 (transform),
e11 (inverse-vol ablation).

Per-window profile (e10, scratch-provenance): 8 of 9 pre-registered regime windows positive
— COVID crash +7.2, May-2021 crash +4.2, 2022 macro bear +1.5, FTX chop +1.2, ETF bull
+2.8; the single negative window is the post-halving chop 2024-03→07 at −0.6, the most
recent IS window. Excluding the best window (COVID crash) still leaves Sharpe 2.33
(falsifier F2 pass); falsifiers F1 (2.4067 > 0) and F3 (1.7023 > 0) pass on the team-run
numbers above.

## 6. Alpha-compression caveat (mandatory, as pre-registered)

The alpha COMPRESSES over the sample: funding dispersion shrank after the 2022
deleveraging, and the yearly Sharpe declines monotonically — 2020 = 3.56, 2021 = 3.32,
2022 = 2.44, 2023 = 1.35, **2024H1 = 0.68** (ledgered experiment e10, scratch-provenance;
split-half 3.49 / 1.44 at a 2022-04 split). The last 3.5 IS months (post-halving chop) are
negative. I expect holdout Sharpe well below the IS 2.4 — the right mental model is the
**late-sample run-rate of ≈ 0.7–1.4**, not the full-IS number.

What would NOT surprise me on the holdout: Sharpe anywhere in roughly 0.5–1.5; multi-month
flat-to-negative stretches in low-dispersion chop (per §2, the stress-tier chop number is
already ~0); drawdowns in violent alt melt-ups where the short-crowded-longs leg bleeds
faster than it collects. What WOULD surprise me and make me doubt the mechanism rather than
the regime: a deeply negative holdout (≤ −0.5) over the full 24 months — the carry leg is a
mechanical cash flow and the book is ~market-neutral with 20/20 breadth, so a sustained
large negative requires the price leg to systematically invert, i.e. crowded-funding coins
persistently CONTINUING to outperform, which the whole IS window contradicts. A holdout
repeat of the IS 2.4 would also surprise me (it would mean funding dispersion re-expanded to
2020–21 levels).

## 7. Verdict

Freeze-ready from the QR side: falsifiers pass, breadth floor passes with 4× margin, both
cost tiers positive, mechanism attribution confirmed, caveats stated. Numbers above are
byte-reproducible via `cli.py team-run --team team-01` (`out/is_metrics.json`,
`out/net_is.csv`).
