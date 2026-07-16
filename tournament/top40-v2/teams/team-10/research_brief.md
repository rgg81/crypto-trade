# Team 10 research brief — residual trend/reversion regime ensemble

Status: **prospective, unregistered, unevaluated**

## Mechanism

Crypto assets repeatedly separate into leaders and laggards even after removing the contemporaneous
cross-sectional market move. Continuation should be more plausible when the common market path is
directional; short-horizon overshoots should be more plausible when that path is inefficient and
choppy. The preregistered family therefore combines two economically different residual sleeves:

1. a medium/slow residual-continuation score over 18 and 63 closed 8-hour bars; and
2. a six-bar residual-reversal score.

At every decision, the market return is the median return across sufficiently covered eligible
coins. Each coin's market residual is scored at all three horizons. A past-only 63-bar path-
efficiency statistic sets the common trend/reversion mixture. Robust cross-sectional standardization
and deterministic ranks select five leaders and five laggards. Each side receives 0.40 gross, so
the requested portfolio is 0.80 gross and zero net with 0.08 per selected coin.

Amendment 0006 is the sole asset-eligibility authority. The strategy neither recognizes nor admits
symbols by name, and funding is deliberately excluded from this mechanism.

## Causal rules

- A candle is usable only after its 8-hour close is at or before the decision boundary.
- Every signal window must be exactly adjacent at 8-hour spacing; missing candles are not compressed.
- The most recent usable candle for a scored symbol must close exactly at the decision boundary.
- A cross-sectional market observation requires at least 12 eligible coins.
- At least 16 fully scored coins are required; otherwise the requested book is flat.
- No full-period coefficients, learned scalers, timestamp lookup tables, auxiliary data, funding, or
  future rows enter the strategy.
- The seed does not alter ranks; deterministic symbol order resolves exact ties.

## Expected regime and sleeve roles

- **Bull:** directional path efficiency shifts weight toward continuation. The long sleeve owns
  residual leaders; the short sleeve hedges residual laggards. The required long-bull attribution
  must be positive.
- **Bear:** the same balanced ranking should place the most persistent residual losers in the short
  sleeve. The required short-bear attribution must be positive.
- **Chop:** low market efficiency shifts weight toward fading six-bar residual overshoots. Combined
  chop return must be positive.
- **Stress:** the raw signal remains balanced. The separately preregistered central volatility target,
  drawdown brakes, position stop, and turnover cap are intended to constrain gap and liquidity risk;
  they receive no optimistic execution.

Both sleeves must independently satisfy the frozen activity and notional gates. A strong combined
return cannot excuse an inactive side.

## Primary falsifiers

Reject or pivot this family if any of the following occurs in visible chronological evidence:

- any non-compensatory development gate fails, including net Sharpe below 0.75, non-positive
  annualized return, Calmar below 0.40, drawdown above 0.30, or doubled-cost Sharpe below 0.35;
- bull, bear, or chop net return is not positive, fewer than three regimes have positive Sharpe, or
  worst-regime Sharpe is below -0.25;
- long-bull, short-bear, or combined-chop attribution is non-positive;
- fewer than four of six true out-of-fold folds are profitable or fewer than 55% of quarters are
  profitable;
- fewer than 70% of declared neighbors are profitable, their median Sharpe is below 0.50, or the
  result is an isolated parameter peak;
- doubled costs, a single sleeve, or one fold/quarter explains away the apparent edge;
- adaptive mixing does not improve robustness relative to both preregistered pure-mode controls;
- the no-residualization ablation is indistinguishable, contradicting the proposed relative-value
  mechanism.

The team will not submit a negative or merely least-bad in-sample model. It will simplify, use at
most two documented mechanism pivots inside the cumulative budget, or record DNF.

## Prospective accounting

The planned first family uses 31 material configurations at most: one reference configuration,
seven signal/mechanism ablations, twelve two-sided parameter neighbors, six risk-policy choices,
and five confirmatory reservations. A base-cost and doubled-cost result are paired outputs of one
risk-policy evaluation and do **not** count as two configurations. No item is evidence until it is
registered through the active A5 superset lifecycle, with its delegated A6 preflight, and evaluated
by the organizer.
