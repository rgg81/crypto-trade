# Team 04 pivot 02 research brief: Path-Adaptive Relative Dynamics

## Identity and evidence boundary

- Family: `team-04-path-adaptive-relative-dynamics-v1` (`PARD`).
- Exact reference: `team-04-pard-reference-001`.
- Parent: stopped `team-04-broad-exhaustion-reversal-v1`.
- Runtime seed: `20260801`; rebalance interval: 48 hours.
- Status: statically promoted to the canonical root as a byte-identical package; not serially
  validated, independently reviewed, rebound to A7, registered, or evaluated.

Visible IS showed BER made zero trades across 3,732 decisions. PARD therefore prioritizes an
explicit availability proof and continuous two-sided exposure after warmup. It does not interpret
BER's zero return as reversal evidence, tune BER's shock parameters, or use another team's result.

## Economic mechanism

Crypto relative returns arise from two different microeconomic states. Persistent paths can reflect
slow information diffusion, collateral migration, and durable token-specific repricing. A sharp
two-day displacement against a path that has not been persistent is more consistent with temporary
liquidity pressure and should mean-revert. PARD combines these roles with one fixed per-symbol path
coherence statistic; it never switches on an organizer regime or a common-market direction.

At scheduled decision `t`, use completed closes no later than `t-8h`. For each current pure-crypto
symbol, normalize organizer-aware, timezone-naive, or epoch timestamp encodings to UTC; select the
latest 70 unique positive closes; require their 69 intervals to be contiguous eight-hour bars; and
require the newest close to be no more than 16 hours behind the cutoff. There is no fill,
interpolation, or substitution.

The first 63 returns are the established 21-day path. Its final 21 returns are a seven-day
confirmation window. The final six independent returns are the recent two-day displacement. Let
`sigma` be population volatility of the established path and require `sigma>=1e-6`:

```text
L = sum(established 63) / (sigma * sqrt(63))
M = sum(last 21 of established) / (sigma * sqrt(21))
D = sum(recent 6) / (sigma * sqrt(6))
```

Split the established path into seven nonoverlapping three-day blocks. Let `a` be the fraction of
block sums with the same nonzero sign as the whole established path, and set
`C=clip(2a-1,0,1)`; use `C=0` when the absolute established sum is at most `1e-12`.
Across complete current symbols,
average-rank `L`, `M`, and `D` independently to `[-1,1]`. Define:

```text
trend = 0.60 * rank(L) + 0.40 * rank(M)
trend_blend = 0.35 + 0.65 * C
raw = trend_blend * trend - (1 - trend_blend) * rank(D)
score = average_rank(raw) mapped to [-1,1]
```

Thus a coherent established path favors continuation, while an incoherent path assigns more weight
to reversal of the independent recent displacement. The `0.35` trend floor prevents a noisy
single displacement from becoming the entire model. Every weight and horizon is fixed before the
PARD outcome is observed.

## Portfolio and regime roles

Require at least 20 complete current names. Long the top and short the bottom
`max(6,floor(N/4))` final scores. Each side requests `0.25`; every symbol is capped at `0.03`;
unallocatable capacity remains cash; gross is at most `0.50`; net is zero within `1e-12`. There is
no position state, stop, volatility target, drawdown brake, directional overlay, or same-boundary
reentry. Every selected long score must be strictly positive and every selected short score must
be strictly negative; otherwise the scheduled target is flat rather than an ASCII-selected
zero-signal book.

- Bull: coherent token-specific leaders continue in the long sleeve; relative laggards remain the
  short sleeve, so the book does not require positive market beta.
- Bear: coherent relative laggards continue in the short sleeve while resilient tokens occupy the
  long sleeve.
- Chop: low path coherence shifts weight toward two-day displacement reversal on both sides.
- Stress: the mechanism stays two-sided and broad; `0.50` gross and `0.03` caps limit single-token
  squeezes, but stress performance remains empirical.

## Falsifier and search discipline

The exact no-control center is the only first-stage observation. Stop PARD before every neighbor,
ablation, or risk-control arm unless that center has trades and a nonempty A5 score row at every
manifest-scheduled timestamp after warmup; is complete and solvent; and clears all of these frozen
numeric floors:

- annualized return strictly above `0.00`, net Sharpe at least `0.75`, Calmar at least `0.40`,
  maximum drawdown at most `0.30`, and doubled-cost Sharpe at least `0.35`;
- at least four of six profitable folds, positive-quarter fraction at least `0.55`, and
  trial-adjusted positive probability at least `0.90`;
- bull, bear, and chop returns each strictly above zero; at least three strictly positive regime
  Sharpes across bull, bear, chop, and stress; worst-regime Sharpe at least `-0.25`; and long-bull,
  short-bear, and combined-chop returns each strictly above zero;
- for each sleeve, exposure at least `0.01`, active-bar fraction at least `0.10`, mean exposure at
  least `0.01`, and executed notional at least `1000` USDT; and maximum positive-PnL concentration
  at most `0.40`; and
- pooled 48-hour score IC strictly above zero, at least four of six fold score ICs strictly above
  zero, at least 240 pairs and ten scheduled decisions per fold, at least 1,440 aggregate pairs,
  complete causal scheduled-score coverage, and independent semantic-coupling approval.

Unavailable evidence is failure. Controls cannot rescue a failed core. Only after every core and
A5 pre-neighbor gate passes may the frozen center plus eight one-axis neighbors be observed. At
least seven of nine cells (and therefore a profitable fraction of at least `0.70`) must be
profitable and neighborhood median Sharpe must be at least `0.50`. Only after that neighborhood
gate passes may the preregistered risk factorial be observed. There is no separately invented tail
threshold; tail behavior is governed by the declared drawdown, regime, sleeve, solvency, and
positive-PnL-concentration gates.

## A5, A6, and A7 authority

At every 48-hour scheduled decision, PARD passes the exact final ranked dictionary to the direct
organizer-owned A5 identity hook after all feature transforms and before sleeve selection, caps, or
risk. A scheduled failed feature state passes `{}` exactly once. Nonscheduled decisions hold and do
not call the hook. Scores use no labels.

A6's certified universe is transitively mandatory: only native crypto instruments are eligible;
stablecoins, metals, commodities, indexes, equities, and other TradFi proxies are excluded even if
listed as Binance perpetuals. PARD does not inspect symbol names to reintroduce excluded assets.

Team 04's current A7 binding names BER and is not authority for PARD. A governed candidate-specific
A7 rebind, canonical promotion, fresh A5 manifests/review, pivot-family registration, and final
post-pivot source hash are hard preconditions to any trial registration or run.
