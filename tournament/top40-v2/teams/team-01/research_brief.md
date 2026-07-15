# team-01 research brief: residual drift with funding de-crowding

Status: **preregistered research design; no experiment has been run**

Family ID: `t01-residual-drift-funding-v1`
Design timestamp: `2026-07-15T19:33:29Z`

## 1. Falsifiable economic thesis

Capital rotates through large crypto futures gradually rather than instantaneously. After removing
the common BTC move, assets with a persistent, path-efficient medium-horizon residual drift should
continue to outperform assets with persistent negative residual drift over the next daily holding
interval. The effect should be stronger net of costs when the portfolio avoids paying the crowded
side of funding: expensive positive funding lowers a long score and improves a short score, while
negative funding does the converse.

This is not an absolute directional forecast. The cross-sectional residual signal supplies both
sleeves. A small, bounded, causal BTC-trend tilt gives the long sleeve more gross in broad advances
and the short sleeve more gross in broad declines. The book remains two-sided at every active
rebalance. Organizer-owned volatility scaling and drawdown brakes are tested only as tail controls;
they are not allowed to rescue an unprofitable core signal.

The family is rejected before risk-overlay selection if none of the 12 preregistered core cells has
all of: positive no-control aggregate net Sharpe, positive no-control net return in at least four of
six chronological folds, positive pooled next-day score information coefficient, and positive
score information coefficient in at least four folds. A positive backtest produced only by a risk
overlay does not satisfy the thesis. The family is also rejected or formally pivoted if the
beta-residualized signal cannot beat the otherwise identical raw-momentum ablation on the declared
selection metric; residualization may not be silently removed.

Mechanism-identity guardrail: this family is and remains **BTC-factor residual,
path-efficient, medium-horizon continuation**. It may not add a persistence/reversal state switch,
route observations into a reversal state, or select a short-horizon reversal signal. Any such
change is a different causal mechanism and requires a formal pivot before a material trial. This
organizer collision-control condition changes no registered parameter or family bytes.

## 2. Decision and execution clock

- All times are UTC. The strategy receives only organizer-authorized `DecisionContext` data.
- It makes a strategy request only at `00:00`; at `08:00` and `16:00` it returns `None` to hold.
- At decision time `t`, a price row with `open_time = t - 8h` is usable because its close is known
  at `t`. A funding row is usable only when `funding_time < t`.
- A target decided at `t` fills at the next executable open under central costs, participation,
  membership, and delisting rules. The open used for the fill is never an input to the decision.
- Membership is the authoritative point-in-time weekly Top-40 eligible set delivered at `t`.
  Current eligibility is never reconstructed from future or full-sample volume.
- Non-daily boundaries, missing BTC, fewer than 24 valid symbols, a non-finite transform, or an
  infeasible capped allocation produce `None` (hold) at non-rebalance times and `{}` (flat request)
  at a scheduled rebalance. There is no one-sided fallback.

## 3. Signal definition

Let `C_i,u` be the last closed 8h close for symbol `i` and `r_i,u = log(C_i,u/C_i,u-1)`.
All windows below end no later than `t`; bars are never forward-filled.

### 3.1 Common-factor residual

For each eligible non-BTC symbol with at least 72 paired returns in the last 90 8h intervals
(30 days), estimate

`beta_i(t) = clip(cov(r_i, r_BTC) / var(r_BTC), -1, 3)`.

The intercept is not removed because persistent asset-specific drift is the object of the signal.
If BTC variance is at most `1e-12`, BTC is missing, or coverage fails, the symbol is invalid. Define
past-only residuals `e_i,u = r_i,u - beta_i(t) * r_BTC,u`.

### 3.2 Drift and path efficiency

For drift horizon `H` days and skip `K` days, use the `3H` residual returns ending `3K` bars before
`t`:

- `M_i = sum(e_i,u)`;
- `sigma_i` = sample standard deviation of those residuals;
- `T_i = M_i / max(sigma_i * sqrt(3H), 1e-8)`;
- `E_i = abs(M_i) / max(sum(abs(e_i,u)), 1e-8)`; and
- `U_i = T_i * E_i^gamma`.

The skip prevents the last one to three days of bounce or liquidation noise from defining the
medium-horizon direction. `E_i` penalizes a terminal displacement assembled from a violently
alternating path.

### 3.3 Funding de-crowding

For each symbol, sum actual `funding_rate` observations with `t - 7d <= funding_time < t`.
At least 14 finite events are required; there is no imputation. Call this sum `F_i`. Positive
`F_i` represents a recently expensive long / remunerated short; negative `F_i` represents the
opposite.

For a contemporaneous valid cross-section, define

`robust_z(x_i) = clip((x_i - median(x)) / (1.4826 * MAD(x)), -3, 3)`.

If cross-sectional MAD is at most `1e-12`, the scheduled request is flat. The final score is

`S_i = robust_z(U_i) - lambda_funding * robust_z(F_i)`.

Thus funding changes ranking but cannot create a price-drift direction by itself.

### 3.4 Sleeve construction

1. Sort by `(S_i, symbol)` deterministically. Select `k = max(6, floor(q * N_valid))` from each
   tail. Require `S > 0` for every long and `S < 0` for every short; otherwise request flat.
2. Within each sleeve use inverse residual-volatility notionals. Winsorize `1/sigma_i` at the
   contemporaneous 20th and 80th percentiles, normalize, and project deterministically onto the
   simplex with a per-symbol target cap of `0.09`.
3. Let `R_BTC,60d = log(C_BTC,t / C_BTC,t-60d)` when 60 days are available; otherwise set its
   directional value to zero. Set `m_t = clip(R_BTC,60d / 0.20, -1, 1)`.
4. Before organizer risk scaling, assign long gross `0.40 + delta*m_t` and short magnitude
   `0.40 - delta*m_t`. Gross is exactly `0.80`, net is bounded by `2*delta <= 0.20`, and at the
   widest registered tilt both sleeves retain at least `0.30` gross.
5. Return finite signed targets only for current eligible symbols. Do not rescale a missing or
   capacity-constrained side into the other sleeve.

BTC may be ranked as an asset only if the implementation can construct its residual without a
self-factor degeneracy. The initial specification excludes BTC from the ranked assets but uses it
as the common factor; it remains in the eligible-set count only for coverage diagnostics.

## 4. Expected regime and sleeve roles

| Regime / sleeve | Ex ante role | Failure interpretation |
|---|---|---|
| Bull | Persistent positive residual leaders plus bounded positive BTC tilt should make the long sleeve positive. Shorts are smaller and seek laggards, not a broad-market short. | Nonpositive long attribution in bull fails the mandatory role gate. |
| Bear | Persistent negative residual laggards plus bounded negative BTC tilt should make short attribution positive. Longs are smaller and hold relative survivors. | Nonpositive short attribution in bear fails the mandatory role gate. |
| Chop | Near-zero BTC tilt leaves an approximately balanced dispersion book; continuation across relative winners and losers should make the combined book positive. | Nonpositive combined chop return falsifies the all-regime use case even if aggregate Sharpe is high. |
| Stress | Residualization and funding de-crowding should limit common beta and squeeze exposure; volatility scaling and brakes should reduce tail loss. Flat stress return is acceptable, not a fitted target. | Breaching the common drawdown/tail gates or concentration in stress rejects the candidate. |
| Long sleeve | Monetize gradual positive idiosyncratic repricing and avoid expensive positive funding. | Insufficient exposure/notional or bull loss rejects the candidate. |
| Short sleeve | Monetize gradual negative idiosyncratic repricing and prefer positive funding receipts. | Insufficient exposure/notional or bear loss rejects the candidate. |

These are hypotheses, not promised results. Every organizer regime-by-sleeve attribution cell is
reported, including unfavorable cells.

## 5. Chronological evidence and selection

The forecasting rule has no supervised model, full-period scaler, feature selector, or learned
coefficient. Rolling beta and every rank are recomputed from the past-only context at each
boundary. Therefore each fixed parameter cell can be replayed independently in each fold without
training on that fold. Hyperparameter comparison across visible development is nevertheless
selection-touched: every cell counts as a trial and the organizer's trial adjustment is binding.

The six outer folds are contiguous and end-exclusive:

1. `[2020-02-03, 2020-09-01)`
2. `[2020-09-01, 2021-04-01)`
3. `[2021-04-01, 2021-11-01)`
4. `[2021-11-01, 2022-06-01)`
5. `[2022-06-01, 2023-01-01)`
6. `[2023-01-01, 2023-07-01)`

Each fold is generated by a separate cutoff-safe replay from authorized warmup, with a hash-bound
source, parameter object, seed, fold boundary, target series, and return series. It is not a slice
from one fitted full-period object. Stateful rolling buffers may warm on earlier authorized rows,
but no earlier return outcome changes a parameter.

The diagnostic label is the next daily executable-open to following daily executable-open return;
it begins strictly after the decision. Labels crossing a fold boundary are purged, and one daily
holding interval is embargoed for any diagnostic that compares a training prefix with the next
fold. These diagnostic omissions do not remove canonical portfolio returns from the fold.

Among candidates that clear every frozen development, regime, sleeve, concentration,
multiplicity, doubled-cost, and neighborhood gate, select the highest

`J = percentile_25(six fold net Sharpes) + 0.25 * doubled_cost_OOF_Sharpe`.

Tie breaks, in order, are lower maximum drawdown, lower annualized one-way turnover, then the
lexicographically smallest canonical parameter JSON. No private or final information enters this
rule. If no candidate clears every gate, there is no champion.

## 6. Registered parameter domain

| Parameter | Values / rule |
|---|---|
| Beta lookback | fixed 30 days; minimum 72 paired 8h returns; beta clipped `[-1, 3]` |
| Residual drift `H` | core search `{14, 21, 28}` days; declared neighbor step `7` days within `[7, 35]` |
| Skip `K` | `{1, 3}` days |
| Path exponent `gamma` | `{0.5, 1.0}` |
| Funding lookback / minimum events | fixed 7 days / 14 events |
| Funding penalty `lambda_funding` | fixed `0.35`; zero is an ablation only and cannot be selected silently |
| Tail fraction `q` | construction search `{0.20, 0.25, 0.30}`; neighbor step `0.05` within `[0.15, 0.35]` |
| Direction lookback / scale | fixed 60 days / `0.20` log return |
| Direction tilt `delta` | core reference `0.075`; construction search `{0.05, 0.10}` |
| Gross / symbol cap | fixed `0.80` / `0.09` |
| Rebalance | daily at `00:00 UTC` |
| Validity | at least 24 valid symbols and at least six per side |
| Canonical runtime strategy seed | `20260801`, frozen by `config.toml`; this is the only worker/production target seed |
| Team trial/search/placebo namespace | `2026080101`; never passed as the worker seed and never used to alter a production target |

The parameter neighborhood is a nine-cell Cartesian cross around the selected `(H, q)`:
`H + {-7,0,+7}` days by `q + {-0.05,0,+0.05}`, clipped only to the preregistered bounds. The
center may reuse its already registered result; the eight distinct neighbors are separately
registered before execution. All other selected parameters remain frozen.

## 7. Risk policy and ablation decision

Only two organizer-owned controls are proposed:

- Volatility target: 30 trailing days, annualized target `0.35`, scale clipped to `[0.25, 1.00]`.
- Drawdown brakes: gross scale `0.75` at 10% drawdown, `0.40` at 18%, and `0.00` at 25%.

Position stop, time stop, turnover limit, and side scaling remain disabled. Same-boundary reentry
is false. Funding is charged first; a boundary-confirmed risk reduction acts at the next open,
pays ordinary costs, and shares participation capacity.

The exact no-control, individual, combined, and doubled-cost matrix is in `ablations.json`. A
control is retained only if its targeted metric improves without causing a mandatory gate to fail.
The combined policy must reduce both maximum drawdown and 1% daily expected shortfall versus no
control, improve expected shortfall by at least 10%, retain at least 70% of annualized return, and
not reduce base- or doubled-cost Sharpe by more than 0.05. If it fails, select the least complex
passing individual policy or no control under the same frozen selection tie breaks.

## 8. Trial allocation

The initial family has a hard cap of 39 material configurations, leaving 41 of the tournament's 80
for a possible documented pivot. Stop early when a falsifier fires.

| Block | Maximum trials | Purpose |
|---|---:|---|
| A: core signal factorial | 12 | `H x K x gamma` with reference construction |
| B: construction | 6 | `q x delta` on the selected core signal |
| N: local neighborhood | 8 | eight byte-distinct neighbors around the already-run center |
| R: risk/cost matrix | 8 | none, volatility, brakes, combined at base and doubled costs |
| F: component/placebo falsifiers | 5 | raw momentum, no funding, no path efficiency, no direction tilt, sign inversion |
| **Total initial-family cap** | **39** | every cell registered before its result is read |

An exact duplicate already present in the organizer journal is reused rather than rerun; the 39 is
a conservative ceiling, not permission to omit accounting. Tests that only check deterministic
invariance and do not alter a material candidate are not performance trials.

## 9. QE handoff and mandatory tests

Implementation must be a deterministic `build_strategy()` with `target_weights(context,
seed=...)`; the runtime `seed` must be the frozen config value `20260801`. It must not access files,
network, evaluator state, future opens, or auxiliary data.
The formulas, invalid-data behavior, tie breaks, capped projection, and daily hold behavior above
are normative. Any ambiguity is returned to the QR before implementation rather than chosen by the
QE.

Before a material run, tests must demonstrate:

- truncation, corrupt-future, append, and future-membership invariance;
- latest usable close is `t` and every funding row is strictly before `t`;
- no full-window scaler, imputer, beta, rank, or target table exists;
- daily-only requests, `None` hold semantics, deterministic symbol tie breaks, finite targets;
- gross/net/symbol limits, two-sided construction, flat behavior on inadequate coverage;
- funding sign: positive recent funding lowers a long score and favors a short score;
- next-open execution, participation, delisting, funding, and risk action ordering remain central;
- no same-boundary reopening after a central control action; and
- clean-process and repeated-runtime-seed (`20260801`) target hashes match exactly; the
  `2026080101` trial/search/placebo namespace is never a production target seed.

## 10. Assumptions and known failure modes

- `BTCUSDT` is expected to remain eligible with continuous 8h history. If it is absent, the
  strategy requests flat rather than substituting a retrospectively chosen market proxy.
- The funding feature assumes canonical rows represent actual completed funding events and their
  published sign; it makes no claim about an unobserved scheduled rate.
- Cross-sectional continuation can reverse during liquidations, listings, or narrative rotations.
  The skip, path efficiency, funding term, and risk controls mitigate but cannot remove this risk.
- A bounded BTC tilt creates residual market exposure and can lose when the 60-day trend reverses.
- Inverse-volatility allocation can overweight apparently quiet contracts before a jump. The
  per-symbol cap and central participation limit are essential.
- Early or sparse history can cause flat periods. Coverage is never repaired with future data or
  cross-sectional imputation.
- Development is selection-touched and not untouched evidence. Private qualification remains one
  blind pass/fail ticket; final OOS is not a research round.
