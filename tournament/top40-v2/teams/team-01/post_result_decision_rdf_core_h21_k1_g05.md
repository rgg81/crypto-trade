# Post-result core-grid decision after `rdf-core-h21-k1-g05`

Decision timestamp: `2026-07-15T23:01:11Z`  
Family: `t01-residual-drift-funding-v1`  
Decision: **reject the tested K=1 cell without risk rescue; authorize at most one next no-control
core cell, `rdf-core-h21-k3-g10`**

## Evidence boundary

This decision uses only Team 01's frozen family/preregistration documents and the two recorded
development outcomes in its own experiment ledger. It does not inspect market data, raw
return/trade/position/target artifacts, another team, private/final evidence, or external research.
No strategy, config, risk policy, test, registration input, family/experiment ledger, lifecycle
state, or report is changed.

The available outcomes are:

1. `rdf-ref-001` (`H=21`, `K=3`, `gamma=0.5`) completed. Its recorded net Sharpe was
   `1.123931`, doubled-cost Sharpe `0.766779`, maximum drawdown `45.5647%`, positive-quarter
   fraction `35.7143%`, and bear Sharpe `-1.264131`. The frozen review records only three of six
   positive folds and negative late folds. It is solvent and informative but fails mandatory
   drawdown, quarter, bear, fold, and worst-regime evidence.
2. `rdf-core-h21-k1-g05` changed only `K: 3 -> 1` at the same `H=21` and `gamma=0.5`. It failed
   with `ValueError: portfolio insolvent at 2022-05-13 00:00:00+00:00`. Its result record contains
   no completed metric summary.

No more granular causal story is inferred from the insolvency. In particular, this decision does
not claim that every untested K=1 combination would be insolvent. It rejects the observed K=1 cell
and declines to allocate the next trial to the K=1 branch.

## Why K=1 is rejected and cannot receive risk rescue

The K=1 trial is terminal rather than merely below a point threshold:

- insolvency prevents a complete development return series, six-fold assessment, doubled-cost
  assessment, regime/role evidence, and score-IC falsifier evidence;
- therefore the cell cannot demonstrate positive aggregate no-control Sharpe, four positive
  folds, positive pooled next-day score IC, or positive score IC in four folds;
- the registered family explicitly requires the no-control core to clear those causal minima
  before risk selection; and
- a volatility target or drawdown brake applied after seeing insolvency would test whether an
  overlay can suppress a failed core, not whether K=1 continuation is viable. That is the exact
  rescue prohibited by the family falsifier.

Consequently `rdf-core-h21-k1-g05` is rejected permanently. It receives no rerun, risk overlay,
construction adjustment, or post-hoc parameter. This decision authorizes no further K=1 cell.

## One exact next diagnostic cell

The only proposed next material candidate is:

`rdf-core-h21-k3-g10`

It is a one-coordinate contrast against `rdf-ref-001`, the only completed solvent baseline:

`path_efficiency_exponent: 0.5 -> 1.0`

All other parameters remain identical to `rdf-ref-001`. Relative to the immediately preceding
terminal K=1 run, the candidate returns to the solvent reference's `K=3`; attribution is therefore
made against `rdf-ref-001`, not against an incomplete insolvent record.

### Complete proposed parameter binding

| Field | Exact value | Relation to `rdf-ref-001` |
|---|---:|---|
| `beta_clip` | `[-1, 3]` | unchanged |
| `beta_lookback_days` | `30` | unchanged |
| `btc_symbol` | `BTCUSDT` | unchanged |
| `btc_variance_floor` | `1e-12` | unchanged |
| `direction_lookback_days` | `60` | unchanged |
| `direction_return_scale` | `0.20` | unchanged |
| `direction_tilt_delta` | `0.075` | unchanged |
| `funding_lookback_days` | `7` | unchanged |
| `funding_penalty` | `0.35` | unchanged |
| `minimum_funding_events` | `14` | unchanged |
| `minimum_names_per_side` | `6` | unchanged |
| `minimum_paired_returns` | `72` | unchanged |
| `minimum_valid_symbols` | `24` | unchanged |
| `path_efficiency_exponent` | **`1.0`** | **only delta, from `0.5`** |
| `per_symbol_target_cap` | `0.09` | unchanged |
| `rank_tail_fraction` | `0.25` | unchanged |
| `rebalance_boundary_utc` | `00:00` | unchanged |
| `residual_denominator_floor` | `1e-8` | unchanged |
| `residual_lookback_days` | `21` | unchanged |
| `risk_policy_id` | `team-01-base` | unchanged; no controls enabled |
| `skip_days` | `3` | unchanged |
| `total_gross` | `0.80` | unchanged |
| runtime strategy seed | `20260801` | unchanged |
| execution cost multiplier | `1.0` | base-cost no-control cell |

The candidate uses no drawdown brake, volatility target, stop, cooldown, turnover overlay, or side
scaling. It remains BTC-factor residual, path-efficient medium-horizon continuation and introduces
no persistence/reversal switch.

## Pre-result rationale

This choice is diagnostic rather than a forecast of improvement:

- The solvent reference provides evidence that the fixed `H=21, K=3` frame can complete and can
  produce positive aggregate and doubled-cost Sharpe, although its chronology and risk fail.
- Reducing the skip to K=1 destroyed operational viability in the otherwise identical cell. The
  next test should not retain that failed coordinate or change several signal dimensions at once.
- `gamma=1.0` is the only other preregistered path-efficiency value. Compared with the reference's
  concave square-root weight, it places relatively less score weight on low-coherence paths. This
  directly tests the registered claim that coherent residual drift, rather than terminal
  displacement alone, is persistent.
- Holding H, K, funding, construction, gross, costs, and seed fixed makes any difference maximally
  attributable to the path-efficiency coordinate. Changing H now would answer a separate horizon
  question and is not authorized by this decision.

No new value or threshold is invented from the outcomes. Both gamma values and every fixed
constant were registered before the results.

## Exact stop rule

`rdf-core-h21-k3-g10` is a single no-control trial. It stops and is rejected, with no construction
or risk rescue, if any of the following occurs:

1. the run is terminal, insolvent, interrupted, or lacks a complete canonical development record;
2. aggregate no-control net Sharpe is nonpositive;
3. fewer than four of six chronological folds have positive net return;
4. pooled next-day score information coefficient is nonpositive or unavailable at the decision
   point; or
5. fewer than four folds have positive score information coefficient, or that count is unavailable
   at the decision point.

These are the preregistered causal minima, not post-hoc qualification values. If all are satisfied,
the cell is only eligible for a fresh QR review. It does not automatically authorize risk controls,
construction search, a private ticket, or another core trial. Formal advancement still requires
every non-compensatory V2 aggregate, doubled-cost, drawdown, quarter, regime, sleeve, concentration,
trial-adjustment, manifest, and neighbor gate.

If the cell fails, this document authorizes no automatic successor. The family remains governed by
the original 12-cell falsifier; a subsequent QR decision must explicitly stop, continue another
registered core coordinate, pivot, or record DNF. Risk controls may never turn a causal-minimum
failure into a core pass.

## Trial and resource accounting

The failed K=1 run counts fully.

| Budget | Consumed now | Remaining now | If the proposed cell is later registered/run |
|---|---:|---:|---:|
| Tournament material configurations | 2 / 80 | 78 | 3 / 80 consumed; 77 remain |
| Registered core factorial allocation | 2 / 12 | 10 | 3 / 12 consumed; 9 remain |
| Initial-family allocation | 2 / 39 | 37 | 3 / 39 consumed; 36 remain |
| CPU | 0.381261 / 12 h | 11.618739 h | Proposed run will add its actual usage |
| Wall clock | 0.380973 / 18 h | 17.619027 h | Proposed run will add its actual usage |
| Mechanism pivots | 0 / 2 | 2 | unchanged |

This document is a research decision only. `rdf-core-h21-k3-g10` remains
`planned_not_registered_not_run`.

