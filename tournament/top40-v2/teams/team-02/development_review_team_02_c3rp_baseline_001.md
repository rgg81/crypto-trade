# Development review: team-02 C3RP baseline 001

## Disposition

**Decision: continue exactly one preregistered, no-control within-family diagnostic. Do not pivot or
declare team DNF yet.**

The next scientific reference cell is the already-declared `component-no-direction-tilt` arm. It
retains the mandatory variable persistence-versus-reversal interaction and every baseline signal,
portfolio, seed, gross, cap, schedule, and execution convention except
`maximum_side_tilt: 0.075 -> 0.0`. It is not registered or run by this review.

This is not a solvency rescue. Requested gross remains `0.90`; no brake, volatility target, stop,
turnover limit, side scale, lower cap, wider sleeve, slower schedule, or cost assumption is added.
The cell was explicitly preregistered before the baseline result to test whether directional sleeve
budgets, rather than the state-conditioned cross-sectional ranks, deliver the bull/bear roles. It
now provides one clean opportunity to obtain evidence about the mandatory core without the
directional-budget overlay.

If this reference cell is also terminal before producing complete artifacts, the initial C3RP
family stops. It may not be followed by lower gross or risk-control variants to manufacture a
submission. The subsequent choice must be a fully preregistered genuine pivot or team DNF.

## Evidence reviewed

Only team-02's own `experiments.jsonl`, preregistered research artifacts, explicit baseline config,
and QE pre-data records were reviewed. No market snapshot, external report, other team, V1,
private/final artifact, leaderboard, ballot, or organizer state was accessed.

The team ledger records:

- candidate: `team-02-c3rp-baseline-001`;
- family: `team-02-causal-crowding-residual-persistence-v1`;
- registered runtime seed: `20260801`;
- registered gross target: `0.90`;
- registered maximum side tilt: `0.075`;
- registered selected fraction per side: `1/4`;
- registered symbol precap: `0.095`;
- risk policy: `team-02-c3rp-baseline-no-control`;
- risk-config SHA-256:
  `0d893457d00453e2bdd16c0a192fbec482aff679158d3589123791498c68a310`;
- registration SHA-256:
  `163f134d130545f6d2d1de1c9821ba958e173a7eafe106749fe8c7075a703e7a`;
- result status: `failed`;
- exact failure: `ValueError: portfolio insolvent at 2022-05-13 00:00:00+00:00`;
- result timestamp: `2026-07-15T21:17:18.859175Z`;
- CPU consumed: `0.24398177153694442` hours;
- wall clock consumed: `0.24383154066916582` hours;
- result `artifact_hashes`: empty;
- result `metrics_summary`: empty.

The failed registration remains one consumed material configuration and its reported compute/time
remain consumed. This review did not read organizer counters and makes no claim about authoritative
cumulative remaining budget beyond that record.

## What the failure establishes

The following conclusions are supported directly:

1. This exact baseline, under its canonical no-control execution, did not preserve positive
   portfolio solvency through the development run.
2. The baseline trial is terminal and cannot qualify, be selected, or be retroactively repaired by
   a risk overlay.
3. Insolvency is economically material even though aggregate metrics were not serialized. A model
   that cannot finish the canonical path supplies no acceptable development evidence.
4. Synthetic unit tests and deterministic clean-process target checks did not establish economic
   survivability under the canonical path; they remain engineering evidence only.

## What is not inferable

Because no performance artifact or metric survived, this record does **not** identify:

- net or gross return, Sharpe, Calmar, maximum drawdown, tail loss, or recovery path;
- fold or quarter returns and their concentration;
- base-versus-doubled-cost sensitivity;
- bull, bear, chop, or stress behavior;
- long/short attribution, exposure, executed notional, or which sleeve contributed to insolvency;
- the state-interaction IC, trend/reversal conditional efficacy, or funding-carry diagnostic;
- turnover, participation shortfall, fill path, funding cashflow, delisting effect, or symbol-level
  contribution;
- whether insolvency arose primarily from signal economics, an adverse short move, execution
  capacity, costs/funding, data handling, or another path-dependent interaction;
- parameter-neighbor stability or trial-adjusted probability.

In particular, the exception timestamp is not permission to inspect that date, infer a symbol, or
construct a date-specific defense. No causal or performance claim is assigned to the missing path.

## Why the decision is not DNF yet

The failure produced no observation of the mandatory C3RP state-interaction falsifier. One
predeclared arm can isolate that core without weakening exposure or adding a post-loss control:
`component-no-direction-tilt`. It was specified before results, retains both behavioral legs and
variable causal `P`, and keeps both sleeves economically material at equal requested gross.

Immediate DNF would be defensible on risk conservatism, but it would leave the core causal claim
untested when a bounded preregistered diagnostic exists. Conversely, running a broad parameter
search after insolvency would be post-failure rescue. Exactly one reference cell is the narrowest
scientifically useful continuation.

## Why this is not a pivot

The reference cell remains C3RP:

- residual beta removal is unchanged;
- residual persistence and residual reversal both remain enabled;
- causal variable `P` still blends the two legs;
- realized-funding carry remains enabled at weight `0.20`;
- inverse-volatility sizing, type-7 clipping, symbol cap, daily schedule, and both sleeves remain;
- only the ancillary common-direction sleeve-budget tilt is set to its preregistered diagnostic
  value zero.

The economic mechanism and data domain therefore do not change. A genuinely different thesis is
neither needed nor justified from an artifact-free failure record.

## Exact next reference cell

Candidate placeholder: `team-02-c3rp-no-direction-tilt-002`

Status: planned, not registered, not executed

Preregistered arm: `component-no-direction-tilt`

All parameters are identical to the failed registration except the single declared delta:

| Parameter | Reference value |
| --- | ---: |
| `beta_lookback_days` | 20 |
| `direction_scale` | 1.5 |
| `fast_residual_days` | 10 |
| `fast_trend_weight` | 0.35 |
| `feature_lag_bars` | 1 |
| `funding_lookback_days` | 7 |
| `funding_statistic` | `cumulative-fsum-funding-rate` |
| `funding_weight` | 0.20 |
| `gross_target` | 0.90 |
| `maximum_side_tilt` | **0.0** |
| `minimum_cross_section` | 12 |
| `minimum_funding_symbols_for_rank` | 4 |
| `minimum_names_per_sleeve` | 4 |
| `minimum_unique_funding_events` | 2 |
| `minimum_valid_history_fraction` | `4/5` |
| `moment_ddof` | 0 |
| `persistence_breadth_threshold` | 0.30 |
| `persistence_efficiency_threshold` | 0.30 |
| `rebalance_bars` | 3 |
| `residual_reversal_days` | 2 |
| `selected_fraction_per_side` | `1/4` |
| `slow_residual_days` | 20 |
| `slow_trend_weight` | 0.65 |
| `symbol_cap` | 0.095 |
| `transition_width` | 0.15 |
| `volatility_lookback_days` | 20 |
| `volatility_quantile_method` | `hyndman-fan-type-7` |
| `volatility_quantiles` | `[0.10, 0.90]` |
| `weight_tolerance` | `1e-12` |

Frozen runtime seed remains `20260801`. Trial/search namespace remains `2026080102`. Risk policy
remains the byte-identical no-control policy; all volatility targets, drawdown brakes, position/time
stops, turnover limits, and side scales remain disabled. Pre-cap requested long and short budgets
are each exactly `0.45` because `d=0`, while total requested gross remains `0.90`.

No source/config/risk hashes are assigned here. They must be computed from the eventual explicit
QE artifacts and preregistered before execution.

## Interpretation and stop rules for the reference cell

The reference cell's primary question is: **can the mandatory state-conditioned residual
persistence/reversal core produce a complete, causal, no-control development record without the
ancillary directional-budget tilt?**

- Mere completion is not success. All original aggregate, doubled-cost, fold, quarter,
  multiplicity, concentration, regime, sleeve, notional, and neighborhood gates still apply.
- The original mechanism falsifier is unchanged: the trend-high-`P` and reversal-low-`P`
  interaction must have its preregistered sign in at least four folds, and funding must improve net
  carry in at least four folds when its paired ablation is eventually eligible.
- Long attribution must still be positive in bull, short attribution positive in bear, and the
  combined portfolio positive in chop. Equal side budgets do not waive any role.
- If the reference cell becomes insolvent or otherwise produces no complete evidence, stop C3RP.
- If it completes but fails the causal interaction or any non-compensatory economic gate, do not
  add controls or lower gross to rescue it; reject/pivot/DNF according to the preregistered rules.
- Risk-control factorial work may begin only after a no-control cell produces complete evidence and
  the signal configuration is frozen. Controls cannot rehabilitate this failed baseline.

## Trial allocation effect

- Material configuration already consumed: 1 (`team-02-c3rp-baseline-001`).
- Additional cell authorized by this review: at most 1
  (`team-02-c3rp-no-direction-tilt-002`), only after normal preregistration.
- Mechanism pivots consumed: 0.
- Private tickets consumed: 0 according to the own-namespace records reviewed.
- No other within-family cell is authorized by this review. A later choice requires a new honest
  evidence review and remains subject to the cumulative tournament budget.

## Integrity statement

This review records a negative terminal result without fabricating missing metrics. It does not
alter `strategy.py`, `frozen_config.json`, `risk_policy.json`, the registered family, the experiment
ledger, or any organizer-owned record. It runs no trial, evaluator, registration, or lifecycle
command.
