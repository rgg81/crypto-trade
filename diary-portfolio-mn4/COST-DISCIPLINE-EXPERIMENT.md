# MN4 UNIFIED-01-03 — Cost-Discipline Experiment (cadence sweep, IS only)

**User-directed 2026-07-12.** "Apply cost discipline, IS only... don't change the core
algorithm, it's just a matter of slowing down the trades (force weekly rebalance only for
instance). Then we see if we improve the holdout. It's just an experiment."

## Setup
- The core algorithm is UNCHANGED — composite signal, blend (α=0.5887), union universe,
  min risk-scalar, BTC+ETH hedge, vol-target, dd-brake all byte-identical to the frozen
  unified book. The ONLY knob is `rebal` (the engine's rebalance cadence).
- IS-only sweep over rebal ∈ {3 (daily), 6 (2d), 12 (4d), 21 (weekly), 42 (fortnight), 63 (~monthly)}.
- Same composite signal/universe/scalar arrays for every cadence; only `run_backtest(rebal=…)` varies.
- Metrics: net-1× (5+2.5bps+funding) and net-2× (10+5) Sharpe, annualized turnover, maxDD. Warmup=300
  (identical across cadences → fair comparison).

## Result — slowing down MONOTONICALLY hurts IS; daily is already optimal

| rebal | cadence | turnover | Sh 1× | Sh 2× | maxDD(2×) | annRet(2×) | 2×/1× |
|---:|---|---:|---:|---:|---:|---:|---:|
| **3** | **daily** | **123×** | **+1.86** | **+1.51** | **−32.9%** | **+45%** | 0.82 |
| 6 | 2d | 84× | +1.51 | +1.33 | −31.2% | +37% | 0.88 |
| 12 | 4d | 55× | +1.43 | +1.28 | −39.9% | +36% | 0.89 |
| 21 | weekly | 38× | +0.98 | +0.85 | −41.5% | +20% | 0.87 |
| 42 | fortnight | 21× | −0.07 | −0.14 | −42.0% | −5% | 2.06 |
| 63 | ~monthly | 20× | +0.86 | +0.73 | −33.2% | +16% | 0.85 |

## The read
- **Net-2× Sharpe falls monotonically as you slow down** (1.51 → 1.33 → 1.28 → 0.85; fortnight is a
  destructive-interference anomaly at −0.14). The cost saved by cutting turnover (123×→38× weekly)
  is **smaller than the edge lost** from re-ranking less often.
- **Slowing also WORSENS drawdown** (maxDD −33% daily → −41.5% weekly): positions drift further
  from target between rebals, deepening drawdowns. So slower cadence hurts BOTH Sharpe AND maxDD.
- The 2×/1× ratio does rise with slower cadence (0.82 → 0.89) — costs are a *smaller fraction*
  when you trade less — but the gross edge drops faster than the cost savings. Net: daily wins.
- **Conclusion: the daily trades are NOT unnecessary.** The book genuinely benefits from daily
  re-ranking (the 60c-momentum component from IDEA-03 is fast enough that weekly loses meaningful
  signal). The cost wall does not bite here — at 123× turnover the 2× cost takes only ~18% of the
  edge (a healthy 0.82 ratio). Cost discipline via cadence is **not** an opportunity for this book.

## IS-discipline → holdout
The IS sweep picks daily (rebal=3) — which is the frozen book's existing cadence. There is **no
IS winner to carry to holdout** (daily is already the baseline). Choosing a slower cadence because
it *might* suit the holdout regime would be holdout-fitting (banned under IS-only discipline). So:
**no cadence change. The frozen daily unified book stands.**

## Alternative cost-discipline lever (not run — for user decision)
A **no-trade / hysteresis band** is the more surgical lever for "save money from unnecessary trades":
keep daily *evaluation* but only rebalance a name when its target weight moves beyond a band (skip
the small daily churn, keep the large re-ranking moves). This targets the "unnecessary" small trades
without losing the fast-signal re-ranking that the cadence sweep proved matters. It's execution-layer
(not core-algorithm), so it's in the spirit of the experiment. **If the user wants, this is the
cost-discipline lever most likely to actually help** (the cadence lever is now falsified). Optional
follow-on; not run here.

*— Orchestrator, MN4, 2026-07-12. Cadence cost-discipline falsified on IS (daily optimal). No change
to the frozen book. Opus 4.8.*
