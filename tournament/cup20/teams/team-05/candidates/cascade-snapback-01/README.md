# cascade-snapback-01

Team 05, lane `short-horizon-liquidity-shock-reversal`.

## What it does

At every 8h boundary the strategy looks at one bar -- the one that closed `ENTRY_DELAY` boundaries
ago -- and asks of each point-in-time member three questions:

1. **Did the move outrun its own recent scale?** The bar's close-to-close return divided by the
   standard deviation of the previous `LOOKBACK_BARS` returns must be at or below `SHOCK_Z`. The
   scale is measured strictly before the bar, so a shock cannot inflate its own reference.
2. **Was it printed by a burst of orders?** The bar's trade count divided by the median trade count
   of the previous `LOOKBACK_BARS` bars must be at or above `FLOW_SPIKE`. A liquidation ladder is
   many small forced orders in a short window, so the trade count spikes harder than notional does.
3. **Did it happen to several names at once?** At least `MIN_BREADTH` eligible members must satisfy
   both of the above in the same bar. A margin engine unwinds correlated collateral simultaneously;
   a single-name story does not.

If all three hold, the book goes equal-weight long the up-to-`MAX_NAMES` most-shocked names,
returns `None` for the rest of the `HOLD_BARS` window (holding quantities, which costs no
turnover), and then emits `{}` to flatten. It is flat between episodes and never re-enters while
positioned.

## Why the timing is what it is

From an event study over the in-sample window, the mean open-to-open return of a qualifying name
runs: bar +1 about flat, bar +2 **+61 bp** (t = 4.3), bar +3 **+99 bp** (t = 7.6), bar +4 flat,
bars +5 and +6 negative. The forced selling finishes in the bar after the shock and the repayment
lands in the two bars after that. `ENTRY_DELAY = 1` skips the first, `HOLD_BARS = 3` covers the
repayment and stops before the drift back. Neither number was chosen from a Sharpe surface.

## Long only

Short-side reversal was tested and rejected on evidence, not on preference: shorting after an up
shock lost at every horizon from 8h to 72h, at every threshold, and under every conditioning tried
(flow spike high, flow spike low, market-wide squeeze, calm market). Up moves in this universe
continue. The research certificate carries the table.

## Declared parameters

| Name | Value | Role |
|---|---:|---|
| `SHOCK_Z` | -2.0 | how far the move must outrun its own scale (**neighbourhood coordinate**) |
| `FLOW_SPIKE` | 2.0 | trade-count spike that marks forced flow (**neighbourhood coordinate**) |
| `MIN_BREADTH` | 2 | simultaneous shocked members that make it a cascade (**neighbourhood coordinate**) |
| `LOOKBACK_BARS` | 60 | the window "its own recent scale" is measured over |
| `ENTRY_DELAY` | 1 | boundaries waited so the cascade completes before the entry |
| `HOLD_BARS` | 3 | boundaries held, covering the measured repayment window |
| `MAX_NAMES` | 8 | cap on basket size |

Risk policy: everything declared off, `volatility_target.enabled = false` (charter section 6,
amendment A3). The book's shape is entirely in the signal; scale belongs to the common risk unit.
