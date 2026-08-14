# volofvol-regime — team-10

**Volatility-regime risk-on / risk-off timing over a transparent equal-weight base book.**

## What the book is

The base book is the most transparent thing available on this universe: **equal weight, long,
every eligible name, rebalanced at every 8h boundary**. It has no selection, no tilt and no
cross-sectional opinion. On its own it is a poor book on this window — Sharpe 0.19, maximum
drawdown 0.32, two of four folds positive — and that is the point. Everything this candidate
claims is claimed by the layer that sits on top of it.

The layer is a single binary decision taken at every boundary: **risk-on or risk-off**. Risk-on
holds the base book. Risk-off returns `{}` and the book goes to cash. The book never emits a
negative weight, so its declared role is **long only**.

## The regime variable

Not the level of volatility. The **coefficient of variation of short-horizon realised volatility**
— how *steady* the variance process has been, not how large it is:

```
m[t]    equal-weight market log return observed at decision t, over the symbols eligible at t
rv[j]   sqrt(mean(m[j-FORMATION_BARS+1 .. j]^2))
vov[t]  std(rv[t-OUTER_BARS+1 .. t]) / mean(same)          <- scale free
z[t]    (vov[t] - mean(vov[t-BASELINE_BARS+1 .. t])) / std(same)

risk-on  <=>  z[t] <= REGIME_THRESHOLD
```

`vov` is a ratio of two moments of the same series, so multiplying every return by a constant
leaves it unchanged. A quiet market and a violent one can both be *steady*; only a market whose
variance keeps bursting and collapsing scores high.

**Why steadiness and not size.** In a market whose leverage is renewed continuously through
perpetual funding, a variance process that repeatedly spikes and collapses is one where positioning
is being forcibly reset — liquidation clusters, funding whipsaw, gap risk — and that is where the
drift is negative. A variance process that is steady is one absorbing flow without breaking, and
that is where the drift is positive. The statistic is deliberately blind to which of those two
levels it is steady *at*.

The obvious reading of this lane — "volatility is high, go flat" — was measured through identical
machinery and is signed the wrong way: a gate on the volatility **level** in that direction has a
negative median ranking score at every formation window tried, and in either direction it cannot be
told apart from a random gate that is flat for the same fraction of the window. See the research
certificate.

## Parameters

| constant | value | what it is |
|---|---:|---|
| `FORMATION_BARS` | 5 | inner window for short-horizon realised volatility (~40 h) |
| `OUTER_BARS` | 150 | window over which that volatility's steadiness is measured (~50 d) |
| `BASELINE_BARS` | 360 | window the steadiness is standardised against (~120 d) |
| `REGIME_THRESHOLD` | −0.30 | z below which the regime is risk-on |
| `REBALANCE_CADENCE` | 1 | every boundary — **no phase offset exists to choose** |

Cadence is 1 deliberately. Phase offset was the single largest source of variation measured
anywhere in this study: at cadence 5 the same signal spans 25 ranking-score points across its five
phases. A cadence-1 book has no phase, so there is no phase luck in the result. Turnover (5.5×) and
trade count (36 k) sit far inside their limits, so nothing forced a slower cadence.

Every window must be fully populated before the layer takes a view; the book stands flat until
boundary 543 (2021-02).

## Risk policy

`team-10-flat` — every primitive disabled, `volatility_target.enabled = false`. A declared drawdown
brake would supply exactly the protection the timing layer is being tested for, and would make the
lane's own question unanswerable. The comparison against a brake is run as a journaled ablation
instead.

## Neighbourhood

Four coordinates, nine points: each of `FORMATION_BARS` (4/6), `OUTER_BARS` (120/180),
`BASELINE_BARS` (270/450) and `REGIME_THRESHOLD` (−0.45/−0.15) varied one at a time around the
nominee. The nominee was fixed before the declaration.
