# entry-delay-0

ENTRY PHASE. Buy at the first boundary after the shock instead of waiting one, which is
the only phase offset an event-triggered book has.

Team 05, lane `short-horizon-liquidity-shock-reversal`. Generated from the single
template in `research/make_candidates.py`, so every candidate in this family differs
from the nominee only in the constants listed below.

| constant | value |
|---|---:|
| `SHOCK_Z` | -2.0 |
| `FLOW_SPIKE` | 2.0 |
| `BASKET_NAMES` | 8 |
| `MIN_BREADTH` | 2 |
| `LOOKBACK_BARS` | 60 |
| `ENTRY_DELAY` | 0 |
| `HOLD_BARS` | 3 |

Risk policy: everything off, `volatility_target.enabled = false` (charter section 6, amendment A3).
