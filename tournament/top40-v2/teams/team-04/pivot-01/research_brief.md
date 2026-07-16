# Team 04 pivot 01 research brief: Broad Exhaustion Reversal

## Identity

- Family: `team-04-broad-exhaustion-reversal-v1` (`BER`).
- Exact reference: `team-04-ber-reference-001`.
- Parent: stopped `team-04-uncrowded-trend-carry-v1`.
- Status: implemented, promoted, and synthetic-validation passed; not registered or evaluated.
  A5/A6 are active, while immutable review/hash binding remains pending.
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

On every manifest-scheduled decision, `strategy.py` calls the organizer-owned A5 identity hook
exactly once. A valid ranked cross section is passed immediately after ranking and before sleeve
selection; a scheduled fail-closed decision passes the exact built-in empty dictionary `{}`. The
call is exactly
`from crypto_trade.tournament.score_adapter_protocol_v5 import score_boundary` followed by
`scores = score_boundary(scores)`. A5 must return the exact input dictionary object and persist its
finite nonempty ranked contents as replay score rows without labels. Aligned nonscheduled,
off-grid, and pre-anchor calls never invoke the hook. A5 is active through
`scripts/top40_v2_tournament_score_diagnostics_v5.py`; registration is blocked until the canonical
executable-source manifest, independent semantic review, score manifest, and exact opt-in are
first-added in A5's required order.

`organizer_score_adapter.py` is retained only as a noncanonical audit aid for the pre-A5 design. It
is not promoted, is not an A5 adapter, is not an official score source, and must never be executed
by the organizer diagnostic. The A5 boundary is the sole canonical score source.

All future tournament commands use the active A5 dispatcher (SHA-256
`0dc9228f3b9c6fe41b2655055f766fc92f323a289a050e6bdf4e48a30b0105f4`). Its delegated A6 audit
restricts every development replay to the certified pure-crypto-only universe; Binance-listed
stablecoins, direct TradFi, equities, indexes, metals, and commodities are ineligible.

## Portfolio and breadth

The literal UTC timestamp `1970-01-01T00:00:00Z` is the immutable schedule anchor, not a placeholder.
Rebalance every six 8-hour bars from that anchor (two days); otherwise hold. Sort by `(score, ASCII symbol)`. Set
`K=max(8,floor(3N/10))`; long the top `K` and short the bottom `K`. Each side receives `0.24`, each
symbol is capped at `0.03`, excess capacity stays cash, gross is at most `0.48`, and net is zero
within `1e-12`.

Every selected-fraction parameter is serialized as a reduced positive rational string
`numerator/denominator`: the center is exactly `"3/10"`, with neighbors `"1/4"` and `"7/20"`.
Implementation uses integer numerator and denominator fields, so no binary floating comparison
defines sleeve membership.

The family registration also declares both fixed reference parameters that appear in the trial
(`minimum_baseline_volatility=[1e-6]` and `minimum_names_per_sleeve=[8]`) and the two material
causal-ablation values (`shock_days=1` and `coherence_base_weight=1.0`). No planned material scalar
lies outside the registered range.

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
endpoint, purge, or malformed-label rules below; or lacks complete scheduled A5 score-row
coverage. A5 itself accepts an empty scheduled capture; Team 04's separately audited schedule
coverage gate treats any scheduled timestamp with no replay score rows as failure. Unavailable IC
or boundary evidence is a failure, not a deferred diagnostic. Controls cannot rescue any failed
core gate.

A qualifying champion must additionally pass every public Calmar, drawdown, multiplicity,
trial-adjusted probability, regime-Sharpe, sleeve-activity, PnL-concentration, and neighborhood
gate. In particular, at least seven of the center plus eight frozen neighbors must be profitable
and their median Sharpe must be at least `0.50`.

## Walk-forward diagnostic

Use the six public chronological development folds. At each decision selected by the manifest's
literal `1970-01-01T00:00:00Z` anchor and 48-hour interval, A5 captures the exact dictionary passed
to `score_boundary`. A nonempty dictionary becomes replay score rows. A scheduled `{}` capture is
valid under frozen A5 and proves the required call occurred, but it creates no replay score rows;
Team 04 therefore compares replay timestamps with the canonical schedule and fails the reference
if any scheduled timestamp has no score row. This is a preregistered Team 04 research gate, not an
automatic A5 qualification gate. Aligned nonscheduled decisions return `None`; off-grid and
pre-anchor calls return `{}`. All three nonscheduled cases make no hook call and create no A5 score
artifact row.

For every finite persisted score for symbol `i` at `t`, define the label only when the organizer has
one unambiguous finite positive executable open for `i` at `t` and one at `t+48h`:

```text
y[t,i] = executable_open[t+48h,i] / executable_open[t,i] - 1
```

The symbol must be emitted in the score dictionary at `t`. Exit-fold eligibility is not required,
but both executable endpoints are. Frozen A5 rejects any duplicate `(open_time,symbol)` in the
executable-open panel by aborting the entire diagnostic before label pairing. A missing or delisted
exit, absent entry, wrong-timestamp endpoint, or nonfinite/nonpositive endpoint omits that pair and
increments the aggregate `unavailable_symbol_label_count`; A5 does not persist a per-pair reason.
Nonfinite scores are rejected before score-artifact creation, and nonfinite Pearson inputs abort
the diagnostic. There is no imputation, terminal-loss substitution, label clipping, cost
adjustment, or use of close prices.

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
