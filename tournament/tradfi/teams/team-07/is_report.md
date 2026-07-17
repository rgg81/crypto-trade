# team-07 IS report — t07-overnight-tugofwar-v1 (CANONICAL, team-run confirmed)

STATUS: canonical. Every number below comes from the tournament evaluator
(`tournament.engine.run_is` — the same scoring core `cli.py team-run` wraps), full precision
archived per-experiment in `out/e-*.json`. `cli.py team-run --team team-07` has now been run
against the frozen `strategy.py`; it wrote `out/is_metrics.json` + `out/net_is.csv` and
reproduced the numbers below bit-identically to the spec rerun e-018 (which was itself
bit-identical to e-012) — Sharpe@1x 0.44780065218805115, Sharpe@2x 0.417076087873868, maxDD
-0.3497940349655483, ann. turnover 3.8874611181288348, 24/24, 174 months.

## Submitted configuration

Long/short cross-sectional sort on the **trailing 252-day mean overnight return**
(`on[t] = open[t]/close[t-1] - 1`), centered pct-rank weights, EMA(halflife=5) weight
smoothing. No sector adjustment, no skip, no VIX, no volume. Deterministic; seed unused.

## Headline IS metrics (2010-01-01 → 2024-06-30, 174 monthly points)

| metric | @1x cost | @2x cost |
|---|---|---|
| net Sharpe (monthly-summed, √12) | **+0.448** | **+0.417** |
| max drawdown | -0.350 | -0.355 |
| total return (vol-targeted stream) | +130.1% | +114.6% |
| annualised turnover | 3.89x | 3.89x |
| median names long / short | 24 / 24 | 24 / 24 |
| mean gross / mean net | 1.00 / +0.0005 | 1.00 / +0.0005 |

Breadth floor (median >= 5/side): PASS by ~5x margin. Cost sensitivity: the 1x->2x Sharpe
give-up is 0.031 — the book is effectively cost-insensitive at 3.9x/yr turnover, which was a
deliberate design axis (EMA smoothing bought turnover 12.9 -> 3.9 at zero Sharpe cost, e-007
vs e-012).

## Regime decomposition (@1x)

| regime | Sharpe |
|---|---|
| bull | +0.74 |
| chop | +0.23 |
| bear | -1.31 |

Matches the pre-registered expectation (research_brief.md §3): the clientele mechanism earns
in bull/chop and bleeds in bear windows when overnight gaps turn macro-driven; the engine's
vol-target de-levers there. The bear bleed was declared acceptable ex-ante; the bull-regime
edge (where the mechanism must work) is the strongest bucket, as required.

## Honest read of the evidence

- The edge sits on a genuine PLATEAU, not a peak: min(S1x,S2x) for the champion is 0.417 with
  neighbors at 0.405 (ema10), 0.340 (no smoothing), 0.280 (W=126+ema5), 0.412 (tercile),
  0.456 (zscore) — every neighbor same-sign, all within the pre-registered 0.30 band. The
  champion was selected by the pre-registered rule (simpler config within 0.15), NOT by
  taking the best cell (e-017 was numerically higher and was passed over).
- With 174 monthly points, the 1-sigma noise floor on an IS Sharpe of ~0.45 is roughly ±0.27
  (√((1+SR²/2)/N_months)·√12). The claim is a modest, robust, cheap-to-trade edge — not a
  high-Sharpe discovery.
- Within-family negatives, reported with equal precision: intraday-fade leg -0.435 @1x
  (e-003), canonical ON-ID spread +0.058 (e-004), sector-neutralized variant +0.314 (e-011),
  21d-skip variant +0.257 (e-013), W=21 fast variant -0.316 @2x (e-005). The family's
  tradeable content at this contract (fill at next open, 6 bps/side) is specifically:
  slow overnight-clientele persistence, unhedged by sector, unskipped, heavily smoothed.

## Ledger accounting

18 lines total in experiments.jsonl: reg-001 (registration) + 17 material experiments
(e-002..e-018), each appended before its result was read. Budget remaining: 22 of 40.
One documented axis addition beyond the §5 grid (21d skip, e-013, negative). No pivots used.
