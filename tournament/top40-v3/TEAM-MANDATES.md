# Top-40 V3 team mandates

## Tournament director's brief

This is a model-building tournament, not a mechanism demonstration. Each team must deliver a
complete, causal trading system: forecast, portfolio construction, execution-aware turnover,
funding treatment, and risk controls. A clever score with a losing portfolio is not a candidate.

**Do not submit a negative train or validation result.** If net return or net Sharpe is negative
in either the chronological training evidence or the stitched out-of-fold validation evidence,
keep working, simplify, invert the sign, change the horizon, neutralize the common market,
document a genuine pivot, or finish DNF. Time spent is not a reason to submit. Risk controls may
improve an already credible mechanism; they may not cosmetically rescue a structurally losing
one.

Every team must pursue a system that can contribute in bull, bear, and chop. At minimum, test
total performance in all three regimes, long-sleeve performance in bull, short-sleeve performance
in bear, and combined market-neutral performance in chop. A failed role or regime is a research
problem to solve, not a metric to hide.

## Frozen research boundary

Only the current frozen Binance USD-M data may be used:

- completed 8-hour transaction-bar timestamps and OHLC;
- base volume, quote volume, trade count, taker-buy base volume, and taker-buy quote volume;
- point-in-time eligible membership and trailing liquidity supplied by the tournament;
- actual funding rate, funding timestamp, and associated frozen funding mark. A strategy derives
  any interval estimate causally from already-settled event timestamps unless the frozen V3
  worker contract explicitly exposes the row's interval field.

All features must be available at the decision boundary and all requested trades execute under
the organizer's next-open rules. A target cell's known calendar label is allowed; its return is
not. Missing observations may be filtered or shrunk but never backfilled from the future.

The universe is pure native crypto coins traded as Binance perpetuals. Stablecoins, fiat
proxies, wrapped or tokenized TradFi, stocks, funds, commodities, metals, indexes, dominance
products, and other synthetic baskets are forbidden even if Binance lists a perpetual contract.
No on-chain, social, search, spot-market, options, open-interest, liquidation, order-book, or
cross-venue data is authorized.

Binance documents the frozen kline and funding fields in its official
[USD-M futures market-data API](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data).

## Mandatory research program

Before selecting a candidate, every team must:

1. Write the economic mechanism and a falsifier before reading the result.
2. Run a simple transparent baseline, the assigned mechanism, and the required ablations.
3. Test at least three economically distinct formation horizons and at least two holding or
   rebalance horizons unless the brief gives a stricter grid.
4. Test the exact sign inversion. If the inversion wins, admit that the original thesis failed
   and register the inverted mechanism rather than silently relabeling it.
5. Compare raw, cross-sectional-median-residual, and—where relevant—causal beta-neutral
   versions. Neutralization must be fitted using past data only.
6. Report base and doubled costs, chronological fold dispersion, quarter breadth, turnover,
   concentration, long/short attribution, bull/bear/chop results, funding PnL, and the effect of
   membership changes.
7. Test the signal without controls, each justified control alone, and the final combined policy.
   Stops are close-confirmed and execute at the next open; no intrabar fiction is permitted.
8. Kill weak variants promptly. Parameter spikes, one lucky quarter, a single coin, one sleeve,
   or one regime do not constitute a model.
9. Record every material trial, including negative, interrupted, inverted, and abandoned work,
   in the team's append-only lab before inspecting its result. Optimize honestly inside the
   logged budget.

The minimum submission condition is positive after-cost train and stitched validation return and
Sharpe, positive doubled-cost performance, and passage of the frozen public core screen. Passing
that floor is necessary, not sufficient. The selected neighborhood should be stable and the
proposed mechanism should add value over its baseline.

A single losing fold, quarter, regime, or sleeve role is not an automatic falsifier. It creates a
diagnosis and lowers the robustness rank. Teams must repair serious weakness where possible, but
they must not abandon an otherwise strong system merely because a disclosed diagnostic is
imperfect. Only the charter's narrow integrity and public core floors are noncompensatory.

## Portfolio and risk expectations

Use broad sleeves, deterministic ranking and tie-breaking, point-in-time eligibility, explicit
minimum-history rules, bounded symbol weights, and a declared net-exposure policy. Measure
turnover before choosing a rebalance interval. Examine volatility targeting, drawdown brakes,
close-confirmed position stops, time stops, cooldowns, and turnover limits only against a stated
failure mode. Report both pre-control and post-control evidence.

Each team owns a distinct mechanism:

| Team | Primary mandate |
|---|---|
| 01 | Weekday residual seasonality |
| 02 | Low-MAX anti-lottery |
| 03 | Positive-jump variance and residual skew |
| 04 | Downside-risk premium net of lottery risk |
| 05 | Dynamic cointegration spread convergence |
| 06 | Pure per-coin time-series momentum with volatility management |
| 07 | Liquidity-conditioned momentum/reversal router |
| 08 | Market-neutral multi-horizon residual momentum |
| 09 | Funding carry with crowding-crash confirmation |
| 10 | UTC-clock-conditioned continuation/reversal |

The collision guard in each brief is binding. Shared risk controls and common causal
normalization are not collisions; copying another team's alpha construction is.

## Reserve mechanism: premium-index convergence

Relative premium-index or spot-perpetual basis convergence is scientifically attractive and is
supported by [Fundamentals of Perpetual Futures](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4301150).
It is **reserve-only** in V3 because the current freeze does not contain historical premium-index
klines or a survivorship-safe spot leg. No team may synthesize premium from OHLC, funding marks,
or future API calls. It can become a mandate only in a new, explicit, pre-research data freeze.

Likewise, genuine size, value, and network factors are not authorized: price is not market
capitalization, quote volume is not size, and no point-in-time circulating-supply or on-chain
network series exists in the freeze.
