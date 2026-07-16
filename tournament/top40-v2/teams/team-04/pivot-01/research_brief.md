# Team 04 pivot 01 research brief: Broad Exhaustion Reversal

## Identity

- Family: `team-04-broad-exhaustion-reversal-v1` (`BER`).
- Exact reference: `team-04-ber-reference-001`.
- Parent: stopped `team-04-uncrowded-trend-carry-v1`.
- Status: implemented, not registered, not tested, not evaluated, and blocked until A5 is frozen.
- Runtime seed: `20260801`; Team 04 namespace: `2026080104`.

## Why this is a mechanism pivot

UTC's visible reference was inactive for two early quarters, concentrated its result in one fold,
and could not expose its preregistered composite score for causal IC. BER does not modify UTC's
weights, trend horizons, funding term, filter, or risk policy. It replaces continuation/carry with
a short-horizon inventory-exhaustion hypothesis and removes funding entirely.

Abrupt, coherent relative moves in perpetual contracts can reflect forced liquidation and dealer
inventory absorption. Over the following holding interval, the most negative moves should rebound
relative to the cross section while the most positive moves should retrace. BER measures that
pressure using only lagged closes, normalizes it by each symbol's preceding volatility, rewards
coherent paths, and takes the opposite side broadly.

## Exact causal score

At an exact 8-hour boundary `t`, the newest usable bar closes at `c=t-8h`. Require 72 exact 8-hour
returns from 73 positive closes through `c`: 63 returns (21 days) form a baseline and the following
9 returns (3 days) form the shock. Rows must have exact open spacing and `close_time=open_time+8h`.

Let baseline population standard deviation be `sigma`, requiring `sigma>=1e-6`. For the shock path
`r` define:

```text
R = fsum(r)
E = min(1, abs(R) / fsum(abs(r)))  (E=0 when the denominator <=1e-12)
Z = R / (sigma * sqrt(9))
raw = -Z * (0.50 + 0.50 * E)
```

Require at least 24 currently eligible symbols with complete features. Average-rank `raw` across
those symbols with exact numeric ties and map ranks to `[-1,1]`. That ranked value is the exact BER
preconstruction score: higher predicts higher next-holding-period relative return.

The mathematical efficiency ratio cannot exceed one. The explicit `min(1, ...)` is a deterministic
binary64 rounding clamp for a possible upward overshoot and is part of the reference, not a tunable
signal transform.

Immediately after ranking and before sleeve selection, `strategy.py` calls the organizer-owned A5
identity hook exactly as
`from crypto_trade.tournament.score_adapter_protocol_v5 import score_boundary` followed by
`scores = score_boundary(scores)`. A5 must return the exact input dictionary object and persist its
finite ranked contents without labels. Registration is blocked until that module and its authority
are frozen and a valid opt-in manifest replaces the prospective template.

`organizer_score_adapter.py` is retained only as a noncanonical audit aid for the pre-A5 design. It
is not promoted, is not an A5 adapter, is not an official score source, and must never be executed
by the organizer diagnostic. The A5 boundary is the sole canonical score source.

## Portfolio and breadth

Rebalance every six 8-hour bars (two days); otherwise hold. Sort by `(score, ASCII symbol)`. Set
`K=max(8,floor(3N/10))`; long the top `K` and short the bottom `K`. Each side receives `0.24`, each
symbol is capped at `0.03`, excess capacity stays cash, gross is at most `0.48`, and net is zero
within `1e-12`.

Every selected-fraction parameter is serialized as a reduced positive rational string
`numerator/denominator`: the center is exactly `"3/10"`, with neighbors `"1/4"` and `"7/20"`.
Implementation uses integer numerator and denominator fields, so no binary floating comparison
defines sleeve membership.

BER uses no signal-polarity gate: whenever at least 24 complete current symbols exist, both broad
sleeves are requested. Its 24-day lookback, lack of funding dependency, two-day schedule, and broad
sleeves are fixed ex ante to address active-quarter breadth. There is no regime switch, market
direction overlay, position state, drawdown input, or adaptive risk scale.

## Expected roles

- Bull: recently liquidated relative losers rebound in the long sleeve; long-bull return must be
  positive.
- Bear: recently squeezed relative winners retrace in the short sleeve; short-bear return must be
  positive.
- Chop: two-sided inventory shocks repeatedly mean-revert; combined chop return must be positive.
- Stress: the effect may intensify after forced moves, but broad sleeves, `0.48` gross, and `0.03`
  caps must contain squeeze concentration; stress return remains empirical.

## Exact falsifier

Stop BER before any parameter, neighbor, ablation, or risk study if its exact no-control reference
is insolvent or incomplete; has nonpositive annualized return, net Sharpe, or doubled-cost Sharpe;
has fewer than four profitable folds; has positive-quarter fraction below `0.55`; has nonpositive
bull, bear, or chop return; fails long-bull or short-bear attribution; has globally pooled Pearson
IC at or below zero; has positive fold IC in fewer than four of six folds; violates the pair-count,
endpoint, purge, or malformed-label rules below; produces any scheduled empty A5 record; or lacks
complete scheduled A5 score evidence. Unavailable IC or boundary evidence is a failure, not a
deferred diagnostic. Controls cannot rescue any failed core gate.

A qualifying champion must additionally pass every public Calmar, drawdown, multiplicity,
trial-adjusted probability, regime-Sharpe, sleeve-activity, PnL-concentration, and neighborhood
gate. In particular, at least seven of the center plus eight frozen neighbors must be profitable
and their median Sharpe must be at least `0.50`.

## Walk-forward diagnostic

Use the six public chronological development folds. At each aligned scheduled decision `t`, A5
persists the exact ranked dictionary passed to `score_boundary`. An empty scheduled record is an
immediate completeness failure. Aligned nonscheduled decisions return `None` and create no record.
An off-grid call fails the strategy flat and, if observed by A5, is represented by an empty record;
it is excluded from scheduled IC pairs and does not excuse a missing scheduled record.

For every finite persisted score for symbol `i` at `t`, define the label only when the organizer has
one unambiguous finite positive executable open for `i` at `t` and one at `t+48h`:

```text
y[t,i] = executable_open[t+48h,i] / executable_open[t,i] - 1
```

The symbol must be emitted in the score dictionary at `t`. Exit-fold eligibility is not required,
but the executable endpoint is; a missing or delisted exit, absent entry, duplicate executable
endpoint, nonfinite/nonpositive endpoint, wrong timestamp, nonfinite score, or nonfinite return
omits that pair with a recorded reason. There is no imputation, terminal-loss substitution, label
clipping, cost adjustment, or use of close prices.

A pair belongs to fold `k` only when both `t` and `t+48h` lie inside that fold's development
evaluation interval. Boundary-crossing pairs are purged, no pair belongs to more than one fold, and
the six fold pools are disjoint. Each fold requires at least 240 valid decision-symbol pairs from
at least ten distinct scheduled decisions; the aggregate requires at least 1,440 pairs. Failure of
any minimum makes score evidence unavailable and fails the reference.

Within each fold, compute ordinary Pearson correlation directly across all retained `(score,
simple_return)` pairs. The aggregate IC is one ordinary Pearson correlation across the union of all
six retained fold pools. Do not rank labels, demean by timestamp, average timestamp-level ICs,
weight pairs, or apply a Fisher transform. Zero variance, a nonfinite result, or malformed pair
membership is unavailable evidence and fails. Aggregate IC must be strictly positive, and at least
four of six fold ICs must be strictly positive. No label, regime, fill, cost, position, or PnL enters
strategy or score construction.
