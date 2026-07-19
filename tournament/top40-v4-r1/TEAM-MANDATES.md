# Top-40 V4 team mandates

Every team builds a complete causal portfolio: signal, sizing, turnover control, funding treatment,
long/short roles and risk controls. Academic evidence is a hypothesis source, never a result.

## Team 01 — slow per-coin trend

Test own-coin time-series momentum over multi-week to multi-month formation horizons. Prefer smooth
position transitions, persistence and volatility scaling. Falsifier: the sign or 2x-cost edge is
not stable across formation horizons and bull/bear roles.

## Team 02 — fast breakout trend

Test causal breakouts and faster time-series momentum with explicit false-breakout protection.
Turnover bands and cooldowns are central. Falsifier: apparent gross alpha vanishes under modest
rebalance slowing or 2x/3x costs.

## Team 03 — volume-confirmed trend

Test whether lagged quote volume, trade count or taker participation improves a transparent trend
baseline. Volume must confirm rather than merely rescale hindsight winners. Falsifier: confirmation
fails its ablation or depends on the most recent liquidity vintage.

## Team 04 — residual cross-sectional momentum

Rank market-residual returns with causal beta estimation and balanced long/short sleeves. Include
an exact reversal sign test. Falsifier: winner-minus-loser ordering is weak, unstable or carried by
common market beta.

## Team 05 — liquidity-shock reversal

Test short-horizon reversal after abnormal, lagged price/volume/taker-flow shocks. Avoid catching
persistent trends through trend-state filters declared before results. Falsifier: reversal exists
only before costs or only in a few crash observations.

## Team 06 — downside risk and low volatility

Test whether lagged downside semivariance, drawdown and idiosyncratic volatility identify resilient
longs and fragile shorts. Do not use price as market capitalization. Falsifier: low-risk selection
is a disguised directional market exposure or lacks a profitable short role.

## Team 07 — funding carry with crash protection

Trade only settled, causally known funding information and require whole-book positive expected
carry. Price weakness and crowding controls must be individually ablated. Falsifier: carry is
consumed by adverse price moves, funding timing or 2x/3x costs.

## Team 08 — funding crowding reversal

Test whether extreme settled funding plus causal price/flow confirmation predicts unwinds rather
than continued carry. This is distinct from passive carry. Falsifier: extremes continue trending
or signal timing cannot survive next-open execution.

## Team 09 — taker-flow and price-volume pressure

Use lagged taker-buy share, quote volume and trade count to distinguish accumulation, distribution
and exhaustion. All signals must survive raw-volume, residualized and liquidity-normalized
ablations. Falsifier: performance is a liquidity-size proxy or disappears outside one era.

## Team 10 — dynamic relative-value convergence

Build causal two-coin or small-basket relationships with rolling fits, strict history requirements
and bounded convergence horizons. Pair selection must be point-in-time and deterministic.
Falsifier: relationships are unstable, one-sided or overwhelmed by rebalance and funding costs.

## Team 11 — UTC and weekday seasonality

Test preregistered calendar effects only with labels known at decision time. Residualize common
market direction and use shrinkage across calendar cells. Falsifier: effects fail adjacent-cell,
era or sign checks, or require high daily churn.

## Team 12 — simple regime ensemble

Combine a small preregistered set of transparent base signals using lagged BTC direction and
volatility regimes. The router may scale or choose frozen components; it may not discover new
signals after seeing performance. Falsifier: the router adds no 2x-cost value over a static blend
or relies on regime-boundary timing.

## Shared role requirement

The final portfolio must have positive long and short gross contribution over IS, positive combined
performance in bull, bear and chop, and bounded stress behavior. A team may stay flat when its
mechanism has no role; it must not force a complex regime router merely to manufacture activity.
