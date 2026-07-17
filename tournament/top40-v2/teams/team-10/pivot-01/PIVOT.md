# Team 10 pivot-01 — defensive anchor convergence

Status: **prospective, unregistered, unevaluated**

## Terminal evidence and bounded diagnosis

The initial no-control candidate `t10-rtre-core-v1` is terminal. Its organizer-owned trial result in
`experiments.jsonl` is `failed` with exact reason:

```text
ValueError: portfolio insolvent at 2022-05-13 00:00:00+00:00
```

The result produced no metrics or artifacts. Therefore no coin, sleeve, or subperiod can be blamed
from available evidence. The defensible mechanism-level diagnosis is narrower: the initial family
requested five 0.08 shorts and five 0.08 longs every eight hours, admitted extreme residual movers,
and exposed the book to an unbounded short open-to-open rebound. One sufficiently large move, or a
small cluster, could exhaust equity before any performance report existed. Its preregistered rule
forbids every risk overlay after core failure, so no control trial is permitted.

The registered initial family, trial reservation, terminal result, and completed A5 artifacts remain
unchanged in `families.jsonl`, `experiments.jsonl`, and `score-adapters/t10-rtre-core-v1*`.

## Genuine mechanism change

Pivot-01 is not a gross adjustment or sign reversal. It removes the adaptive residual trend/reversal
regime ensemble and replaces it with moderate convergence toward a 63-bar volume-weighted log-price
anchor. The tradable cohort is causally quarantined for recent one-bar gaps, cumulative tail moves,
drawdown, total price range, missing volume, and annualized volatility. Nine-bar market-residual
confirmation avoids buying a still-falling discount or shorting a still-rising premium.

The pivot scores only at 00:00 UTC, uses a matching 24-hour A5 open-to-open label, retains incumbents
within a two-rank buffer, and returns hold when sleeves do not change. It selects four coins per side
at 0.025 each: 0.20 gross and zero net. These are inseparable portfolio-construction consequences of
the new defensive convergence thesis, not an overlay on the failed signal.

Expected roles remain explicit: moderate confirmed discounts support the long sleeve in bull,
moderate confirmed premiums support the short sleeve in bear, and two-sided anchor convergence is
the primary chop role. Amendment 0006 remains the only universe classifier; no ticker heuristics are
present.
