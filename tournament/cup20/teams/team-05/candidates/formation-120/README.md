# formation-120

FORMATION HORIZON. The window 'its own recent scale' is measured over, doubled to 120
bars.

Team 05, lane `short-horizon-liquidity-shock-reversal`. Generated from the single
template in `research/make_candidates.py`, so every candidate in this family differs
from the nominee only in the constants listed below.

| constant | value |
|---|---:|
| `SHOCK_Z` | -2.0 |
| `FLOW_SPIKE` | 2.0 |
| `BASKET_NAMES` | 8 |
| `MIN_BREADTH` | 2 |
| `LOOKBACK_BARS` | 120 |
| `ENTRY_DELAY` | 1 |
| `HOLD_BARS` | 3 |

Risk policy: everything off, `volatility_target.enabled = false` (charter section 6, amendment A3).
