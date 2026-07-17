# Team09 pivot-02 research brief

Status: **prospective, unregistered, unevaluated final mechanism pivot**

## Repeated-failure diagnosis

The initial no-control funding-crowd strategy had net Sharpe `1.1061` but `53.33%` drawdown and
bear Sharpe `-2.1891`. Pivot-01 changed security selection in broad declines yet kept the same
`0.45` gross per side and became insolvent on `2022-05-13` before metrics. The repeated evidence
does not support another router, sign change, or portfolio-state brake. Both prior families are
terminal for controls.

Pivot-02 instead changes the alpha and construction together. It removes funding and regime
routing, slows rebalancing from 24 to 72 hours, broadens each sleeve to as many as eight names,
cuts center gross from `0.90` to at most `0.20`, cuts the symbol ceiling from `0.09` to `0.015`,
excludes the most crash-fragile fifth from both sides, and lets captured score magnitude shrink
weights without restoring lost exposure.

## Mechanism

At each epoch-anchored 72-hour boundary:

- require 270 contiguous completed eight-hour returns for at least 20 A6-certified symbols;
- subtract each bar's pure-crypto median return and rank each symbol's residual return over three
  successive 90-bar blocks;
- reward persistent block agreement to identify relative leaders and laggards under one rule in
  bull, bear, and chop;
- rank 90-bar downside semideviation, maximum absolute return, and maximum drawdown with fixed
  weights `0.40/0.35/0.25`;
- encode fragility percentile above `0.80` as zero for both sleeves, then shrink every remaining
  persistence score by its fragility percentile;
- cross the A5 boundary once, select up to eight positive and eight negative returned scores, map
  returned magnitude directly to weights, and scale only the larger sleeve downward.

At center, base weight is `0.10 / 8 = 0.0125`, score multipliers lie in `[0.35, 1.0]`, the hard
symbol cap is `0.015`, and requested gross cannot exceed `0.20`. These are signal/portfolio
mechanics using only contemporaneous cross-sectional data, not optional risk actions or responses
to portfolio drawdown.

Amendment 0006 remains the sole universe authority. Only certified native crypto is eligible;
stablecoins and direct TradFi, metal, commodity, equity, ETF, index, FX, premarket, or leveraged
token exposures are excluded even when Binance lists a perpetual.

## Falsifier and sequencing

The no-control center fails on any insolvency, nonpositive ordinary or doubled-cost return/Sharpe,
nonpositive bull/bear/chop return or Sharpe, drawdown above `0.25`, inactive role or sleeve, failed
fold/quarter/A5 diagnostic, or other frozen non-neighborhood gate. Only a fully passing center may
activate the already-frozen ten-neighbor read-barrier process. Controls remain dormant until the
center and complete neighborhood pass every full development gate. A failed pivot-02 is DNF; no
further mechanism pivot or rescue submission is permitted.

## Prospective accounting

Pivot-02 consumes the final permitted mechanism pivot. Its center, six mechanism ablations, ten
predeclared neighbors, and any later authorized policy are separate material configurations. No
private or final-OOS view is a research round or selection input.
