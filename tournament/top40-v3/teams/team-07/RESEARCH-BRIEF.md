# Team 07 research brief: liquidity-conditioned momentum/reversal router

## Mandate

Determine when a recent market-residual price move is informed continuation and when it is a
temporary liquidity displacement. The router must be specified from causal OHLCV and trade-flow
proxies and must beat always-momentum and always-reversal baselines.

Primary evidence: [Momentum and liquidity in cryptocurrencies](https://arxiv.org/abs/1904.00890)
finds momentum concentrated among liquid cryptocurrencies.
[Intraday return predictability in cryptocurrency markets: Momentum, reversal, or both](https://www.sciencedirect.com/science/article/abs/pii/S1062940822000833)
documents both effects and state dependence involving jumps and liquidity. Binance's official
[USD-M market-data documentation](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data)
defines the frozen quote-volume, trade-count, and taker-buy fields.

## Causal feature

At each decision, subtract the eligible-crypto median return from each completed 8-hour return.
Define a recent residual move over 1, 3, or 6 bars. Estimate the liquidity state from a trailing
window ending before that move wherever practical:

- quote-volume and trade-count ranks relative to the coin's own history;
- absolute return or high-low range per unit of quote volume;
- taker-buy quote share as a secondary confirmation, not a standalone score.

The reference router continues a residual move when liquidity is deep, participation is broad,
and taker direction confirms it; it reverses a move when price impact is high relative to volume
or flow fails to confirm. Predeclare a smooth bounded router rather than dozens of state cells.
Cross-sectionally rank the routed expected return into a broad net-neutral book.

## Required research

- Baselines: always continuation, always reversal, liquidity-only rank, recent return only, and
  an equal-turnover zero-information rank.
- Signal horizons: 1, 3, 6, and 12 bars. State windows: 21, 63, and 126 bars. Holding periods:
  1, 3, and 6 bars.
- Sign tests: invert the routed score; invert only the continuation branch; invert only the
  reversal branch.
- Neutralization: raw move, median-residual move, and causal beta-residual move.
- Ablations: quote volume only, price impact only, remove taker data, remove trade count, fixed
  router, and delayed state. The full router must beat both pure branches.
- Report branch frequency/PnL, state transitions, turnover, costs, sleeve roles, folds, and
  bull/bear/chop results.

## Risk controls

Use a minimum-liquidity/history gate, winsorized price impact, broad sleeves, low coin caps,
turnover hysteresis, a downward volatility target, close-confirmed stops for failed continuation,
time stops for failed reversal, and cooldown after a gap. Signals from missing or zero-volume
bars must be flat, never imputed.

## Falsifiers

Pivot if the router is nonpositive after costs, either pure branch dominates in every fold,
routing adds no value over a fixed blend, the result depends solely on taker-buy share, or profit
comes from names that cannot pass participation costs. Nearby-horizon sign changes and sleeve or
regime weaknesses trigger a router diagnosis and reduce robustness rather than automatically
invalidating the candidate.

## Collision guard

Do not use within-bar closing location or auction-absorption logic, a raw high-volume shock
reversal, dynamic leader diffusion, calendar identity, or multi-week residual ranking. Liquidity
must decide between continuation and reversal; it may not merely filter another team's alpha.
