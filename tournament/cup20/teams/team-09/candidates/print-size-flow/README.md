# print-size-flow

**Lane:** taker-flow / price-volume pressure (team 09)
**Roles traded:** long and short
**Shape:** dollar-neutral cross-sectional book over the point-in-time top-20 universe

## The one-sentence version

Aggressive taker buying predicts, but only after you ask *how it arrived*: the informative
component is the imbalance carried by the bars whose prints were unusually small, confirmed by the
large prints leaning the same way — and with the price move, the coin's size and the coin's
turnover all regressed out, so what is left is flow structure and nothing else.

## Why this is not the obvious version of the lane

The obvious reading is "buy the names with the highest taker-buy ratio". That is measured here as
the transparent baseline: same universe, same book shape, same three controls, signal replaced by
the plain USDT-weighted taker imbalance. It produces a 2×-cost Sharpe near 0.5 with a worst fold
near −1.3 and a ranking score near 8. It is close to worthless on this window.

Everything this candidate earns above that comes from two conditioning terms, both of which read
`trade_count` — the field that says whether a bar's USDT arrived in many prints or a few.

## The signal, exactly

For each eligible symbol at each 8h boundary, from bars closing at or before that boundary:

```
imb_t   = (2 * taker_buy_quote_volume_t - quote_volume_t) / quote_volume_t
ats_t   = quote_volume_t / trade_count_t
shock_t = clip( log(ats_t) - mean(log ats over the NORM_BARS bars before t), -3, +3 )
```

Over the last `FORMATION_BARS` bars:

```
COVATS = sum( imb_t * shock_t * quote_volume_t ) / sum( quote_volume_t )
IMBSML = sum( imb_t * quote_volume_t  |  shock_t <= 0 ) / sum( quote_volume_t | shock_t <= 0 )
```

`COVATS` is the USDT-weighted covariance between flow direction and print-size shock: positive when
the unusually-large prints leaned the same way as the flow. `IMBSML` is the imbalance carried by
the below-norm-print bars only: the granular, many-participant half of the tape.

The score is `rank(COVATS) + rank(IMBSML)`, cross-sectionally, then residualised — same boundary,
ordinary least squares, intercept included — against three controls, each also cross-sectionally
ranked:

* the log price change over `FORMATION_BARS` bars (so this is not price momentum);
* mean `log(ats)` over `NORM_BARS` bars (the coin's print-size class);
* mean `log(quote_volume)` over `NORM_BARS` bars (the coin's turnover class).

The last two matter more than they look: without them roughly half of the raw flow signal's
in-sample edge is a big-coin-beats-small-coin tilt that this particular window pays, and that is
not taker flow.

## The book

`HOLD_BARS` overlapping sleeves, one opened every boundary, each held `HOLD_BARS` boundaries. Each
sleeve is long the top `SLEEVE_NAMES` residual scores and short the bottom `SLEEVE_NAMES`, equal
weight per name, dollar neutral. The emitted book is the average of the live sleeves, restricted to
currently-eligible names.

This is exactly the average over all `HOLD_BARS` phase offsets of a cadence-`HOLD_BARS` book. It is
built this way because phase is a first-order axis and this window proves it: a single-phase
cadence-42 book on an earlier version of this signal spanned 2×-cost Sharpe −0.00 to +1.36 across
its 42 offsets, with a ranking score from 0 to 86. The overlapping construction is the mean of that
distribution and cannot be lucky in phase.

## Declared parameters

| Constant | Value | What it is |
|---|---:|---|
| `FORMATION_BARS` | 81 | bars of flow accumulated into the score (27 days) |
| `NORM_BARS` | 126 | bars forming the per-symbol print-size norm and the two level controls (42 days) |
| `HOLD_BARS` | 72 | boundaries each sleeve is held, and the number of overlapping sleeves (24 days) |
| `SLEEVE_NAMES` | 4 | names per side per sleeve — one fifth of a 20-name universe |

`NORM_BARS > FORMATION_BARS` by construction: a print-size *shock* only means anything against a
baseline slower than the window it is measured in.

## Risk policy

`team-09-flat` — every primitive disabled, `volatility_target.enabled` false. The charter's common
risk unit owns scale; this book's risk control lives in its shape (dollar neutral, equal weight,
eight names per sleeve, averaged over 72 sleeves), which is the half a team actually owns.
