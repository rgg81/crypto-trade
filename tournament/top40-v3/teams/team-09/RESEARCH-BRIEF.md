# Team 09 research brief: funding carry with crowding-crash confirmation

## Mandate

Trade the actual cash-transfer economics of perpetual funding while controlling the crash risk
of crowded positioning. The book should receive expected net funding at formation and use price
only to avoid or confirm a crowding unwind—not to disguise a generic momentum strategy.

Primary theory: [Fundamentals of Perpetual Futures](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4301150)
derives perpetual-futures valuation and funding-linked arbitrage bounds. Binance's official
[USD-M market-data documentation](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data)
specifies funding history, funding time, rate, and associated mark.
[Crypto carry](https://www.bis.org/publ/work1087.htm) documents large crypto carry and links it to
leveraged trend-chasing and scarce arbitrage capital. The price-weakness confirmation below is an
explicitly exploratory crash-control hypothesis, not an established result of those sources.

## Causal feature

At decision time, use only funding events whose actual funding timestamp is strictly earlier than the
decision. Never assign a rate to an earlier 8-hour bar merely because the timestamps are close.
Infer interval changes only from already-settled timestamp gaps unless the frozen worker contract
explicitly exposes the event's interval field.
For each coin:

- estimate expected funding from robust time-weighted means over the last 7, 14, and 28 days;
- measure persistence as same-sign event share and short-versus-long-window agreement;
- define expected carry for signed weight w as minus w times expected funding;
- rank low or negative funding toward the long sleeve and high positive funding toward the short
  sleeve, requiring the proposed whole book's expected net funding to be positive;
- let funding alone choose both sleeves and their signs, so a missing price confirmation can
  never veto an otherwise valid carry book;
- continuously tilt an admitted high-funding short by up to 50% of its base sizing score as the
  product of its cross-sectional funding crowding and clipped 3-/9-bar residual weakness;
- continuously discount, but never remove, an admitted low-funding long by at most 25% of its
  sizing score during a clipped 3-/9-bar residual collapse; and
- renormalize each sleeve to the frozen side gross and re-check coin caps, net exposure, and the
  whole book's positive expected funding carry.

Use a broad, low-gross, net-neutral portfolio with next-open execution. Funding is charged on the
carried position at its true frozen timestamp before rebalance.

## Required research

- Baselines: latest settled funding rate; robust funding mean; persistence-only rank; price-only
  residual signal; equal-weight carry; and carry without the continuous crash overlay.
- Funding windows: 7, 14, and 28 days. Decision schedules: 1, 3, and 7 days. Confirmation
  horizons: 3, 9, and 21 bars.
- Sign tests: carry-collecting sign and exact carry-paying inversion; confirmation and its
  inversion.
- Timestamp tests: exact-event alignment, event-count differences, variable funding intervals,
  missing events, and a one-event artificial delay.
- Attribution: realized funding PnL separately from price PnL, each sleeve's carry, pre- and
  post-confirmation results, costs, folds, and all regimes.

## Risk controls

Use strict funding staleness and event-count gates, robust caps on anomalous rates, broad sleeves,
very small coin weights, low gross, quote-volume/history eligibility, a downward volatility
target, close-confirmed price stops, cooldown, turnover limits, and a portfolio drawdown brake.
The overlay has a strictly positive sizing floor, so price weakness cannot accidentally create a
flat book. Funding income never justifies unlimited exposure to a widening crowded trade.

## Falsifiers

Pivot if expected net carry is not positive at formation, realized funding attribution is
negative, price PnL alone explains the result, paying carry wins, or aggregate train, validation,
or doubled-cost performance is nonpositive. A useless exploratory confirmation, timestamp
sensitivity, extreme-rate concentration, and fold, regime, or sleeve weaknesses trigger risk
repair and lower robustness rather than acting as separate vetoes.

## Collision guard

Do not build another generic funding z-score, relaxation, or price-reversal blend. The distinct
core is realized cash carry using exact funding timestamps plus a narrowly defined
continuous crowding-crash sizing overlay. Premium-index convergence is reserve-only: the current freeze lacks premium
index history, and funding marks may not be used to synthesize it.
