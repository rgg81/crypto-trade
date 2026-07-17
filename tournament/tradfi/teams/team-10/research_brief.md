# team-10 research brief — t10-ts-trend-v1 (plain per-name time-series trend)

Status: PRE-REGISTERED 2026-07-17 (Section 9 FROZEN SPEC completed after the experiment
program; everything in Sections 1-8 was written BEFORE any experiment result was read).

## 1. Mechanism

Per-name, own-history time-series trend: each name goes long (short) when its own trailing
vol-normalized return is positive (negative), sized inversely to its own volatility. No
cross-sectional ranking of any kind, no bear/market gating (RESERVED family), no VIX regime
switching (team-06). Every quantity used for name i is computed from name i's own price
series alone.

Signal core, per name i, per day t (all from `close`):

- `logp = ln(close)`
- momentum window K days, optional skip s days:
  `mom_{i,K,s}(t) = logp_i(t-s) - logp_i(t-K)`  (implemented as `logp.shift(s) - logp.shift(K)`)
- per-name vol: `sigma_i(t) = EWMstd(span=63, min_periods=42)` of daily simple returns
  (`close.pct_change(fill_method=None)`), floored at 0.004/day (~6.3%/yr) to bound
  inverse-vol sizing.
- standardized trend: `z_{i,K,s}(t) = mom_{i,K,s}(t) / (sigma_i(t) * sqrt(K - s))`
- transform T: one of `sign(z)`, `clip(z, -2, 2)`, `tanh(z)`
- raw weight: `w_i(t) = T(z_i(t)) / sigma_i(t)`, optionally EMA-smoothed over span m
  (`fillna(0)` before smoothing; names with insufficient history stay NaN/0 = flat).

Multi-horizon variant (still per-name, own-history): `z_blend = mean(z_63, z_126, z_252)`
then transform and size identically. NO gate of any form on top.

The engine owns everything downstream (gross=1, |w_i|<=0.10, |net|<=0.25, shift(1),
6 bps/side on |dw|, 15% vol-target). We emit raw signed weights only; same-bar decisions.

## 2. Economic rationale

Investor underreaction and slow capital reallocation produce autocorrelation in individual
names' risk-adjusted returns at the 1-12 month horizon; this is the single most replicated
per-asset anomaly (TSMOM) and it does not require relative comparisons across names to
exist. This universe (Binance TradFi single-stock perps) is a retail-favorite, high-attention
set where trend-chasing flows and slow institutional rebalancing coexist — per-name
persistence should be at least as strong as in broad equity panels. Inverse-vol sizing turns
heterogeneous names into comparable risk units without any cross-sectional operation, and
the low natural decay of 3-12-month signals keeps turnover compatible with 6 bps/side.

## 3. Expected regime behavior

- Sustained trends (bull or bear): positive; a mostly-long book in bulls, mostly-short in
  bears. The engine's |net|<=0.25 trim converts one-sided phases into a smaller spread book
  that the vol-target re-levers — expect the raw directional edge to be partially converted
  into (weaker) per-name relative persistence in those phases.
- Sharp reversals / V-bottoms (2011, 2018-Q4->2019, 2020-03->04, 2022->2023 turn): the known
  weak regime — trend is late on both exits and entries; drawdowns concentrate here.
- Chop: roughly flat gross, small cost drag (slow signals, EMA smoothing).

## 4. Falsifier (kill criteria, pre-registered)

The family is DEAD (documented pivot to a then-free family, or DNF) if, over the Stage-A/B/C
plateau (all configs sharing the selected transform, K within a factor of 2 of the selected
horizon):

- plateau-median net IS Sharpe @1x < 0.30, or
- positive Sharpe exists only at an isolated (K, transform) peak — i.e. neighbors within one
  grid step drop below 50% of the peak Sharpe, or
- the breadth floor (median >= 5 names/side) cannot be met by any config satisfying the
  Sharpe criteria, or
- 2x-cost Sharpe <= 0 for the selected config (cost fragility).

## 5. Parameter plan (pre-registered grid + rationale)

Fixed throughout (not tuned): sigma = EWMstd(span=63, min_periods=42) of daily simple
returns, floor 0.004/day; inverse-vol sizing; NaN = flat; no forward-fill anywhere;
`aux['seed']` unused (fully deterministic strategy).

| Stage | Axis | Grid | Rationale |
|---|---|---|---|
| A | horizon K, transform=sign, m=0, s=0 | K in {21, 63, 126, 252} | locate the horizon plateau; 1-12 months is the documented TSMOM band |
| B | transform | {clip2, tanh} at the two best-plateau K from A | continuous transforms damp sign-flip churn and weak-trend exposure |
| C | multi-horizon blend | mean(z_63, z_126, z_252) with best transform (+ sign for reference) | blends are the canonical plateau-over-peak TSMOM construction |
| D | weight smoothing m | EMA span {5, 10, 21} on best of A/B/C | turnover control at 6 bps/side; expect Sharpe-neutral-or-better net |
| E | skip s | s=5 on best-so-far | short-term reversal contamination check |
| F | plateau confirmation | +/-1 grid step around the final pick (only cells not already run) | selection-rule integrity |

Budget: ~16 experiment lines (hard cap 40 incl. registrations; 2 registration lines already
used). One `experiments.jsonl` line per evaluated config, appended BEFORE reading its
result; the paired 2x-cost number of the same config is a published sensitivity of that same
experiment, not a separate line.

## 6. Selection rule (pre-registered)

Among configs meeting: median names/side >= 5, 2x Sharpe > 0 — prefer the SIMPLEST config
(fewer active axes: blend counts as one axis; smoothing preferred over none only if it
changes Sharpe by > -0.05 while cutting turnover materially) within 0.05 net IS Sharpe @1x
of the best such config. Ties: higher 2x Sharpe, then less-negative maxDD. No config may be
selected whose one-step grid neighbors average < 90% of its Sharpe (peak-only ban).

## 7. Breadth risk & contingency (pre-registered)

IS 2010-2024 is bull-heavy: a sign-based TS book will be long-heavy and `median_names_short`
is the binding constraint. Continuous transforms do not change side counts (sign of weight =
sign of z). If the floor fails across the grid, the pre-registered contingency — still
strictly per-name, own-history — is per-name time-series recentring: replace z with
`z - EWMmean(span=756, min_periods=252)(z)` (each name's trend measured against its own
long-run typical trend). This will be logged as its own experiment stage (G) if and only if
Stage A-F configs fail the floor. It is NOT cross-sectional demeaning: no other name's data
enters name i's signal.

## 8. Data, tools, discipline

- Data: ONLY `tournament.engine.load_is_panels()` / `team_view` inside this team dir;
  numbers reported come ONLY from `te.run_is` Metrics (and later the QE's `team-run`).
- `pn['ret_fwd']` is never touched in signal construction (scratch scripts consume
  `team_view(pn)` only and pass full `pn` solely into `te.run_is`).
- Both cost tiers recorded for every experiment (cost_mult=1.0 and 2.0).
- Append-only `experiments.jsonl`, line BEFORE result, monotone timestamps.

## 9. FROZEN SPEC for the QE

FROZEN 2026-07-17 after the exp-003..exp-023 program (21 material experiments; see
is_report.md and out/exp_results.json). Selected config = **exp-016**, chosen mechanically
by the Section-6 rule: the two higher-Sharpe cells (exp-021 K=315 at 0.893, exp-022 m=10 at
0.892) are BANNED by the peak-only rule (one-step neighbor averages 0.678 / 0.745 vs
required 0.804 / 0.803); exp-016 passes (0.746 >= 0.738) and no other passing config is
within 0.05 of it.

### 9.1 Exact computation — `build_raw_weights(pn, aux)`

```python
import numpy as np

def build_raw_weights(pn, aux):
    close = pn["close"]                                   # dates x tickers, ragged starts
    ret = close.pct_change(fill_method=None)              # simple daily returns, no padding
    logp = np.log(close)
    sigma = ret.ewm(span=63, min_periods=42).std().clip(lower=0.004)
    mom = logp.shift(5) - logp.shift(252)                 # 12m momentum, 1w skip
    z = mom / (sigma * np.sqrt(247.0))                    # 247 = 252 - 5
    w = np.sign(z) / sigma                                # sign transform, inverse-vol size
    w = w.fillna(0.0).ewm(span=21, min_periods=1).mean()  # EMA-21 weight smoothing
    return w
```

Constants (ALL fixed, nothing left to the QE): momentum lookback K=252, skip s=5,
sqrt-normalizer sqrt(247), vol = EWM std (span=63, min_periods=42) of
`close.pct_change(fill_method=None)`, vol floor 0.004/day, transform = sign, sizing =
1/sigma, weight smoothing = EMA span 21 with min_periods=1 applied AFTER `fillna(0.0)`,
no re-masking after the EMA (pre-history zeros decay in and contribute flat; the engine
treats 0 as flat). Output on `pn['close']`'s own index/columns; the engine's `conform_raw`
re-aligns defensively.

Determinism & interface notes: pure function of `pn['close']`; `aux` (vix, sector_map,
seed) intentionally unused — no randomness anywhere; derive tickers from panel columns
(never hard-code); same-bar decisions (engine applies the shift(1)); NO gating, NO
cross-sectional operation, NO use of any other name's data in name i's weight.

Missing data: NaN close -> NaN z -> 0 after the fillna; a name enters only once it has
252d of log-price history AND >= 42 return observations for sigma; names that halt or
delist decay to flat over ~21d via the EMA (deterministic, engine-safe).

### 9.2 Reference IS numbers (evaluator `te.run_is`, out/exp_results.json exp-016) —
the QE must reproduce these via `cli.py team-run`:

| metric | 1x cost | 2x cost |
|---|---|---|
| net IS Sharpe | 0.8201 | 0.7653 |
| maxDD | -23.15% | -23.57% |
| ann. turnover | 6.40x | 6.40x |
| total return | +424.1% | +363.1% |
| median names long/short | 37 / 11 | 37 / 11 |
| mean gross / mean net | 0.970 / +0.195 | 0.970 / +0.195 |
| n_months | 174 | 174 |
| regime Sharpe (bull/bear/chop) | +1.19 / -1.13 / +0.64 | +1.13 / -1.17 / +0.58 |
