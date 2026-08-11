# hold-2

HOLDING HORIZON. The snap-back window shortened from three boundaries to two.

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
| `ENTRY_DELAY` | 1 |
| `HOLD_BARS` | 2 |

Risk policy: everything off, `volatility_target.enabled = false` (charter section 6, amendment A3).
