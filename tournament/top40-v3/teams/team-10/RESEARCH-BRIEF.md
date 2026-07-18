# Team 10 research brief: UTC-clock-conditioned continuation/reversal

## Mandate

Test whether the sign and strength of short-horizon return predictability repeat in specific UTC
trading cells. The mechanism is a causal clock-conditioned response slope: some cells may
continue the previous residual move and others may reverse it.

Primary evidence: [Intraday return predictability in cryptocurrency markets: Momentum, reversal, or both](https://www.sciencedirect.com/science/article/abs/pii/S1062940822000833)
documents both intraday momentum and reversal.
[Periodicity in Cryptocurrency Volatility and Liquidity](https://research.cbs.dk/en/publications/periodicity-in-cryptocurrency-volatility-and-liquidity/)
documents weekday, hour, and funding-time periodicity for Bitcoin and Ether. Extending that
mechanism to the broader eligible cross-section is this team's test, not a fact assumed from the
paper.

## Causal feature

Label every completed bar by its 00:00, 08:00, or 16:00 UTC slot and weekday. Subtract the
eligible-crypto median return from each coin return. At decision time t:

1. The UTC label of the next bar is known.
2. Using only response pairs completed before t, estimate each coin's target-cell slope, its
   all-cell slope, and an equal-coin median target-cell slope across the eligible universe.
3. Shrink each target-cell slope with a 104-observation prior. The prior is the fixed 50/50 blend
   of that coin's all-cell slope and the robust cross-coin target-cell slope.
4. Multiply the shrunk target-cell slope by the latest completed residual move. Positive slope
   routes continuation; negative slope routes reversal.
5. Rank the expected next-bar residual into broad, net-neutral sleeves, but admit a coin only if
   its forecast magnitude clears the frozen 15 bp round trip (5 bp fee plus 2.5 bp slippage on
   both entry and exit). Require at least eight qualifying coins on each side and require the
   average long-minus-short forecast to clear 30 bp before entering next open.

Predeclare whether the primary model uses three UTC slots or 21 weekday-slot cells. Do not search
arbitrary minute, holiday, month-end, or named-event calendars.

## Required research

- Baselines: pooled continuation slope with no clock; fixed one-bar momentum; fixed one-bar
  reversal; clock-cell unconditional mean; and zero forecast.
- Estimation windows: 13, 26, and 52 weeks. Lag horizons: 1, 3, and 6 bars. Holding periods: 1
  and 3 bars.
- Sign tests: fitted cell slopes, exact score inversion, all-continuation slopes, and all-reversal
  slopes.
- Placebos: fixed permutation of UTC cell labels and a one-slot shift. Do not repeat shuffles
  until one loses.
- Neutralization: raw, median-residual, and causal beta-residual returns.
- Cost hurdles: zero, 1x (the primary 15 bp round trip), and 2x only as declared diagnostics; do
  not tune a hurdle from realized PnL.
- Report cell observation counts, shrinkage, cell/branch PnL, turnover, costs, folds, and
  bull/bear/chop plus sleeve roles.

## Risk controls

Sparse cells must shrink toward the predeclared blended prior. Require minimum history and
liquidity, bounded slopes, broad sleeves, small symbol caps, the explicit per-coin round-trip
cost hurdle, a 20% one-way turnover cap, downward volatility scaling, close-confirmed stops, and
cooldown. Eight-hour bars may be too coarse for the academic intraday effect, so doubled-cost
performance is especially important.

## Falsifiers

Pivot if clock conditioning does not beat the pooled slope, label permutation or one-slot shift
performs similarly, the inversion wins, turnover consumes the edge, or aggregate train, stitched
validation, or doubled-cost performance is nonpositive. Cell or day concentration, shrinkage
sensitivity, and regime or sleeve weakness reduce the robustness rank and trigger repair but are
not standalone vetoes.

## Collision guard

Do not trade the unconditional weekday mean owned by Team 01, a liquidity-state router owned by
Team 07, multi-week residual momentum owned by Team 08, or funding carry owned by Team 09. The
alpha must be the interaction between the known target UTC cell and the lagged-return response
slope.
