# Team 06 research brief — relative-rank persistence v1

Status: author-implemented and organizer-validated second mechanism pivot. No test, validator,
evaluator, lifecycle, or Git command was run by the author. After handoff, organizer formatting,
lint, JSON, 14 focused tests, risk/source preflight, independent A5 review, and A7 metadata rebind
passed. Family registration, canonical A5 first-adds, exact source hashing, and evaluation remain.
This document makes no performance claim.

## Why the direct parent family is terminal

The exact no-control `t06-relative-rank-acceleration-v1-base` visible-development result strongly
falsified rank-acceleration reversal. Net Sharpe was `-1.587344094268312`, annualized return was
`-0.1808286621124474`, maximum drawdown was `0.4948179135020112`, doubled-cost Sharpe was
`-2.533098193879541`, and only `0.21428571428571427` of quarters were positive. Regime Sharpe was
`-2.7698181411008513` in bear, `-2.3350736294964585` in bull, `-0.013447000471358682` in chop, and
`-0.45042125791257903` in stress. The run generated 16,761 trades. Under its preregistered
noncompensatory rule, the no-control family is terminal; no stop, volatility target, drawdown
brake, turnover cap, neighbor, diagnostic, or private ticket may rescue or reinterpret it.

The sign and regime breadth of that failure motivate testing whether relative-rank displacement
persists instead of reverting. A mechanical sign flip is not an adequate pivot: the large gap
between base and doubled-cost Sharpe also identifies turnover and a two-day horizon as mechanism
risks. The new family therefore changes the economic direction, incorporates persistent relative
leadership rather than acceleration alone, doubles both signal subwindows, and moves to a fixed
four-day construction cycle. It is neither a risk-control variation nor a parameter neighbor of
the failed family.

## New identity and hypothesis

- Family: `t06-relative-rank-persistence-v1`.
- Exact reference: `t06-relative-rank-persistence-v1-base`.
- Parent: terminal `t06-relative-rank-acceleration-v1`.
- Seed: `20260801`.
- Runtime entrypoint: zero-argument root `strategy.py:build_strategy`.
- Risk: the same completely disabled no-control policy; controls are not part of the pivot.

The hypothesis is that information and attention diffuse unevenly across native crypto assets.
When a coin moves coherently from weak to strong relative returns, or remains a persistent
relative leader, that state can continue over the next four days. The opposite applies to
deteriorating or persistently weak coins. Cross-sectional ranking removes the common crypto move,
so the mechanism does not require a bullish or bearish market forecast.

At every completed 8-hour interval, rank the exact eligible coins by that interval's log return,
average exact ties, and map ranks to `[-1, 1]`. Adding any common crypto return to every coin leaves
these ranks unchanged. No benchmark, stablecoin, equity, index, metal, commodity, or other
non-crypto contract is introduced.

For each coin, use 96 past rank observations:

- the first 72 bars (24 days) estimate sample volatility in relative-rank space;
- the next 12 bars form the prior four-day mean relative rank;
- the final 12 bars form the recent four-day mean relative rank.

Let `A = recent_mean_rank - prior_mean_rank`, `L = recent_mean_rank`, and
`D = max(0.20, sample_std(baseline_ranks))`. Let `C` be the absolute sum of the recent ranks'
deviations from the prior mean divided by the sum of their absolute deviations, clamped to
`[0, 1]` and set to zero for an effectively empty path. The raw score is:

```text
raw = (0.65*A/D + 0.35*L/D) * (0.50 + 0.50*C)
```

The positive `A` coefficient follows relative-rank displacement; the positive `L` coefficient
requires current relative leadership to contribute independently. Thus a steady winner or loser
can receive a persistence score even with zero acceleration, and an improving but still weak coin
is not equivalent to an established leader. This is not the failed reversal score with a new
label. Average-rank the raw values cross-sectionally to `[-1, 1]`; higher final scores enter the
long sleeve and lower final scores enter the short sleeve.

## Causal and universe contract

The organizer's Amendment 0006 authority supplies point-in-time membership containing native
crypto coins/tokens only. Stablecoins, tokenized TradFi/equities, commodities/metals, and indexes
remain excluded even if Binance offers perpetual contracts. The strategy never expands or
classifies the universe from symbol strings.

For each selected decision, the implementation requires a canonical `RangeIndex` frame with
`open_time` and `close`, and exactly one finite positive close at each of 97 required 8-hour open
times. Every retained close satisfies `open_time + 8h <= decision_time`. Missing, duplicate,
malformed, nonpositive, incomplete, or future observations fail that coin closed. At least 24
complete currently eligible coins are required. Funding, next-open prices, volume, fills, costs,
positions, equity, drawdown, labels, private data, and final OOS data are unused.

The schedule is every 12 exact 8-hour bars (96 hours) from the Unix epoch. Aligned nonscheduled
decisions hold; off-grid decisions fail flat. At each scheduled decision, after the final scores
exist and before selection or sizing, `strategy.py` directly calls the organizer-owned identity
hook exactly once. A scheduled feature failure calls it once with `{}`. Its returned dictionary is
the sole construction input. The prospective A5 manifest uses the same epoch anchor, 96-hour
schedule, and 96-hour executable-open-to-open label.

## Portfolio and intended regime roles

Select `K=max(8,floor(N/5))` names per side. Long the highest scores and short the lowest, allocate
`0.20` to each side, cap every coin at `0.025`, retain unused budget as cash, and target exact zero
net with at most `0.40` gross. Rebalance only every 96 hours and hold between decisions. These
fixed construction choices reduce the failed parent's turnover and isolate stronger tails; they
are part of this prospective reference and are not dynamic risk controls.

- Bull: long persistent relative leaders and short persistent laggards after the common positive
  market move is removed.
- Bear: long coins with resilient or improving relative ranks and short coins with persistently
  weak or deteriorating ranks after the common negative market move is removed.
- Chop: the level-plus-shift blend and fixed path-coherence weight favor sustained cross-sectional
  leadership over one-bar flips; profitability is still an empirical gate.
- Stress: broad sleeves, exact zero net, the `0.025` coin cap, and `0.40` maximum gross limit
  common-market and single-name concentration; stress profitability remains empirical.

These are hypotheses, not claims. Visible-development evidence must demonstrate all roles.

## Noncompensatory evaluation rule

After new-family registration, A5 score controls, and exact post-family source hashing, run the
exact no-control reference as Team 06 material trial 3. Organizer validation and A7 package
rebinding are already complete.
Reject this family immediately unless net Sharpe is at least `0.75`, annualized return is strictly
positive, Calmar is at least `0.40`, maximum drawdown is at most `0.30`, doubled-cost Sharpe is at
least `0.35`, doubled-cost return is strictly positive, and trial-adjusted probability positive is
at least `0.90`. Also require at least four profitable frozen folds, positive-quarter fraction at
least `0.55`, worst-regime Sharpe at least `-0.25`, at least three positive regime Sharpes,
positive bull/bear/chop returns and Sharpes, positive long-bull, short-bear, and combined-chop
return, both sleeves to pass exposure and activity minima, and positive-PnL concentration at most
`0.40`.

The score diagnostic is required only after a materially positive core. Globally pooled Pearson
IC between the exact captured rank and simple executable-open-to-open 96-hour return must be
strictly positive, at least four of six fold ICs must be positive, and scheduled score coverage
must be complete. Unavailable evidence is failure. Controls cannot rescue a failed core. No
parameter search, controlled batch, or private ticket activates unless this exact no-control
mechanism clears every gate.
