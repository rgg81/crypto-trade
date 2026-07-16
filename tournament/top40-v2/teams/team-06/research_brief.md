# Team 06 research brief — relative-rank acceleration v1

Status: implemented mechanism pivot; organizer lint, JSON, focused synthetic validation, source
preflight, independent A5 review, and A7 metadata rebind passed; unregistered and unevaluated.
This document makes no performance claim.

## Why the parent family is terminal

The exact no-control `t06-balanced-trend-reversal-v1-base` visible-development result falsified
its core thesis: net Sharpe was `-0.524809872995251`, annualized return was
`-0.24452542046360337`, maximum drawdown was `0.7380842004083039`, and doubled-cost Sharpe was
`-0.799922357968985`. Regime Sharpe was `-1.4458380733522744` in bear, only
`0.0640641950162595` in bull, and `0.9867176235750049` in chop. Under the preregistered
noncompensatory rule, the failed no-control core is terminal. The run generated 30,503 trades and
became still worse at doubled cost, so churn is also a mechanism-design concern. No volatility
target, drawdown brake, turnover cap, stop, or parameter neighbor may rescue or reinterpret it.

The positive chop readout is compatible with, but does not prove, a short-horizon relative
reversal effect. The decisive negative evidence is that the parent continuously increased its
trend share as the absolute market move grew and also added a directional net tilt. The resulting
mechanism was least successful in bear and did not establish useful bull performance. This pivot
therefore removes raw price-level trend, market-direction mixing, the net tilt, and the daily
schedule. It is not a risk-control variation or a parameter neighbor of the parent.

## New identity and hypothesis

- Family: `t06-relative-rank-acceleration-v1`.
- Exact reference: `t06-relative-rank-acceleration-v1-base`.
- Parent: terminal `t06-balanced-trend-reversal-v1`.
- Seed: `20260801`.
- Runtime entrypoint: zero-argument root `strategy.py:build_strategy`.
- Risk: the same completely disabled no-control policy; controls are not part of the pivot.

The hypothesis is that abrupt changes in *relative leadership* across native crypto coins partly
reflect temporary inventory and liquidation pressure, while a persistent relative rank is not by
itself a reversal signal. The strategy therefore reverses relative-rank acceleration rather than
the direction or level of market returns.

At every completed 8-hour interval, rank the exact eligible coins by that interval's log return,
average exact ties, and map ranks to `[-1, 1]`. Adding any common crypto return to every coin leaves
these ranks unchanged, so bull and bear market direction are removed at the feature boundary
without using a benchmark, stablecoin, equity, index, metal, or other non-crypto contract.

For each coin, use 75 rank observations:

- the first 63 bars (21 days) estimate the coin's sample volatility in relative-rank space;
- the next six bars form the prior two-day mean relative rank;
- the final six bars form the recent two-day mean relative rank.

Let `A = recent_mean_rank - prior_mean_rank`. Let `C` be the absolute sum of recent deviations
from the prior mean divided by their absolute path, clamped to `[0, 1]` and set to zero for an
effectively empty path. The raw score is:

```text
raw = -A / max(0.15, sample_std(baseline_ranks)) * (0.50 + 0.50*C)
```

Average-rank the raw values cross-sectionally to `[-1, 1]`. Higher final score means a sharper
negative change in relative leadership and is assigned to the long sleeve; lower score means a
sharper positive change and is assigned to the short sleeve. A coin that remains a steady relative
winner or loser has little acceleration and is not automatically fought.

## Causal and universe contract

The organizer's Amendment 0006 authority supplies point-in-time membership containing native
crypto coins/tokens only. Stablecoins, tokenized TradFi/equities, commodities/metals, and indexes
remain excluded even if Binance offers perpetual contracts. The strategy never expands or
classifies that universe from symbol strings.

For each selected decision, the implementation requires a canonical `RangeIndex` frame with
`open_time` and `close`, and exactly one finite positive close at each of the 76 required 8-hour
open times. Every retained close satisfies `open_time + 8h <= decision_time`. Missing, duplicate,
malformed, nonpositive, incomplete, or future observations fail that coin closed. At least 24
complete currently eligible coins are required. Funding, next-open prices, volume, fills, costs,
positions, equity, drawdown, labels, private data, and final OOS data are unused.

The schedule is every six exact 8-hour bars (48 hours) from the Unix epoch. Aligned nonscheduled
decisions hold; off-grid decisions fail flat. At each scheduled decision, after the final scores
exist and before selection or sizing, `strategy.py` directly calls the organizer-owned identity
hook exactly once. A scheduled feature failure calls it once with `{}`. Its returned dictionary is
the sole construction input. The prospective A5 manifest uses the same epoch anchor, 48-hour
schedule, and 48-hour executable-open-to-open label.

## Portfolio and intended regime roles

Select `K=max(8,floor(N/4))` names per side. Long the highest scores and short the lowest, allocate
`0.24` to each side, cap every coin at `0.03`, retain unused budget as cash, and target exact zero
net with at most `0.48` gross. Rebalance only every 48 hours and hold between decisions.

- Bull: the common positive crypto move is removed before the signal; the portfolio trades only
  unusual changes in relative leadership and remains dollar neutral.
- Bear: the common negative crypto move and the parent's harmful directional tilt are absent;
  accelerating relative squeezes populate shorts and accelerating relative liquidations populate
  longs.
- Chop: repeated two-sided changes in relative leadership are the mechanism's primary expected
  opportunity, consistent with—but not established by—the parent's positive chop evidence.
- Stress: broad sleeves, the 0.03 coin cap, and exact zero net limit single-name and common-market
  concentration, but stress profitability remains an empirical falsifier.

These are hypotheses, not claims. The visible-development result must demonstrate them.

## Noncompensatory evaluation rule

After family registration, A5 score controls, and exact post-family source hashing, run the pivot's
exact no-control reference as the next material Team 06 trial. Independent source review and the
A7 package rebind are already complete.
Reject this family immediately if aggregate return or Sharpe is nonpositive; doubled-cost return or
Sharpe is nonpositive; bull, bear, or chop return is nonpositive; bull, bear, or chop Sharpe is
nonpositive; long-bull, short-bear, or combined-chop return is nonpositive; fewer than four frozen
folds are profitable; positive-quarter fraction is below `0.55`; either sleeve misses exposure or
activity minima; or positive-PnL concentration exceeds `0.40`.

The score diagnostic is required evidence: globally pooled Pearson IC between the exact captured
rank and simple executable-open-to-open 48-hour return must be strictly positive, at least four of
six fold ICs must be positive, and scheduled score coverage must be complete. Unavailable evidence
is failure. Controls cannot rescue a failed pivot core. No parameter search, controlled batch, or
private ticket activates unless this exact no-control mechanism clears every gate.
