# Top-40 V5 mechanism-family mandates

## Why lanes are assigned

Free choice converges. V4-R9 gave fifteen teams an open mandate and four of its five finalists were
order-flow books — `flow-imbalance-gate08`, `flow18-trigger`, `flow-short-role-h18`,
`flow-pressure-inverted-long-role`. tradfi-cup-01 saw eight of ten teams choose residual momentum;
crypto-cup-01 seven of ten. Assigned lanes are the only construction in this repository's history
that has prevented it, and they produce the negative results nobody volunteers for: a prior edition
recorded three lanes whose own teams falsified their premise, which a self-selected field would
never have run.

A mandate names an **economic source of return**. It never names a parameter, a horizon, an
implementation, or an expected sign. Two lanes reaching a similar conclusion independently is a
finding; reading another lane's work is not permitted.

## What this dataset can and cannot support

State this before choosing anything, so no team spends trials discovering it.

**Available**: 8h OHLCV; `quote_volume`; `trade_count`; `taker_buy_volume`;
`taker_buy_quote_volume`; `funding_rate`; `mark_price`; point-in-time weekly membership.

Derived quantities that follow from those, several of them under-used in prior editions:

| quantity | from | note |
|---|---|---|
| multi-horizon return, realized and range volatility | OHLC | Parkinson / Garman-Klass available |
| taker-pressure ratio | `taker_buy_quote_volume / quote_volume` | four of five V4-R9 finalists used this; **rationed to one lane** |
| **average trade size** | `quote_volume / trade_count` | participant-mix proxy. **No prior edition has used it** |
| Amihud illiquidity | `abs(return) / quote_volume` | |
| realized carry, funding term structure | `funding_rate` | the basis is *implied* by funding, never observed |
| mark-versus-last dislocation | `mark_price` vs `close` | stress and liquidation-pressure proxy |
| cross-sectional dispersion, correlation, beta | returns vs an equal-weight member index | |
| universe entry and exit events | membership | point-in-time clean attention events |

**Not available, and no substitute exists**: open interest; liquidations; order book depth, spread
or queue; spot prices and any directly observed basis; cross-venue data; options and implied
volatility; on-chain flows; borrow and lending rates; news and social sentiment; anything below 8h.

That rules out, in their real form: OI crowding and squeeze detection, liquidation-cascade
strategies, market making and microprice, cash-and-carry, cross-exchange arbitrage and venue
lead-lag, variance-risk-premium and gamma trades, and intraday reversal.

## The fifteen lanes

Organised by economic source rather than technique, so the field spans different return drivers
rather than fifteen implementations of one.

### Risk-premium harvesting

**team-01 — funding carry with crowding protection.** Harvest the funding premium across the
cross-section. The premium is real and it is compensation for a crash risk that arrives exactly
when the carry is largest; the mandate is to earn it without being the last holder.

**team-02 — funding convexity.** Trade the realized-funding term structure against realized
volatility. Funding is an insurance premium with a jump component; this is the nearest thing this
dataset supports to a variance-risk-premium trade.

**team-03 — defensive, beta-controlled allocation.** Betting-against-beta and quality-minus-junk in
their crypto form: short high-volatility, high-illiquidity names against low, neutral to an
equal-weight member index.

### Cross-sectional mispricing

**team-04 — residual cross-sectional momentum.** Momentum on returns orthogonalised to the market
factor, so the book is not a levered index position wearing a momentum label.

**team-05 — illiquidity-conditioned short-horizon reversal.** Reversal is a liquidity-provision
premium; the mandate is to condition it on when liquidity was actually scarce.

**team-06 — cluster relative value.** Rolling correlation clusters, trading deviation from cluster
mean. Sector-neutral statistical arbitrage where the sectors are discovered rather than declared.

**team-07 — cointegration convergence.** Rolling pairwise cointegration on log prices, with a
preregistered half-life and a divergence stop. The stop is the mandate's hard part.

### Time-series trend

**team-08 — multi-horizon time-series momentum.** The CTA transplant: per-contract, volatility
scaled, multiple lookbacks. The most-studied premium in the literature and a genuine baseline.

**team-09 — volume-confirmed breakout.** Channel breakout gated on participation, so the book does
not buy every false break.

### Microstructure and participation

**team-10 — taker-flow pressure.** **The only lane permitted to use taker-buy ratios as its primary
signal.** Rationing this is the direct structural fix for V4-R9's convergence.

**team-11 — participant mix.** Average trade size as a retail-versus-institutional proxy. A family
this dataset uniquely supports and that no prior edition has attempted.

### Event and state

**team-12 — volume-shock events.** Extreme quote-volume z-scores as events; trade the subsequent
drift or reversal, whichever the evidence supports.

**team-13 — universe inclusion and attention.** Trade weekly membership entry and exit. This
deliberately assigns the RIVER phenomenon to a lane that must model it explicitly and prove it
under the seasoned-universe rerun, rather than leaving it to be discovered by accident by a book
that then dies of it.

**team-14 — breadth and market state.** Time net exposure from cross-sectional breadth and
dispersion. **Mandated to run non-zero net** within the |net| ≤ 0.25 cap, so the field contains at
least one directional lane rather than fifteen market-neutral ones.

### Combination

**team-15 — regime-allocated ensemble.** Allocate across mechanism states. In a prior edition this
was the only naive seed to clear its bar, and its ensemble was the best object that edition
produced.

## The organizer seed

Each lane receives its idea in the least clever form that could work, and the team's **first
charged trial must be the unmodified seed**. Two reasons. It makes the fifteen seed scores a
measured distribution against which every calibrated threshold is placed in an observed gap. And it
means a team that ends up far from its seed has to have learned something, which the leaderboard
reports as distance from seed.
