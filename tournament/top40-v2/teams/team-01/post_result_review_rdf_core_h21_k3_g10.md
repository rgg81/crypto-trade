# Post-result review: `rdf-core-h21-k3-g10`

Evidence commit: `f763818e6f5f382644bca7779981c8fe9e34ee96`  
Review timestamp: `2026-07-15T23:34:48Z`  
Family: `t01-residual-drift-funding-v1`  
Disposition: **reject without risk rescue**  
Next decision: **authorize at most one diagnostic no-control cell,
`rdf-core-h14-k3-g05`; failure stops this family or requires a formal pivot**

## Evidence boundary and integrity

The candidate development-run directory and runner record have no byte differences from commit
`f763818e`. This review uses only Team 01's frozen preregistration/decision documents, its runner
record and experiment outcome, and the committed artifacts under
`reports-top40-v2/team-01/development-runs/rdf-core-h21-k3-g10/`.

No snapshot, other team, private/final evidence, external research, or uncommitted performance
source was inspected. No executable, config, risk policy, test, ledger, lifecycle state, report,
registration input, or evidence artifact was modified.

Runner metrics and confidence intervals are canonical. Fold, quarter, concentration, tail,
exposure, sleeve, cost, and fill diagnostics were recomputed serially from the committed candidate
artifacts. Daily returns are compounded; Sharpe uses sample daily standard deviation and
`sqrt(365)`. The six fold boundaries are the exact preregistered end-exclusive intervals.

## Decision in one paragraph

Increasing the path-efficiency exponent from `0.5` to `1.0` does not repair the solvent reference.
The candidate completes and retains positive aggregate and doubled-cost Sharpe, but has only three
positive folds, the same 5/14 positive quarters, 46.24% drawdown, bear Sharpe `-1.527`, a losing
short sleeve, and greater positive-fold concentration. More decisively, a valid cross-sectional
next-day score IC cannot be reconstructed from the committed artifacts. The exact pre-result rule
rejects the cell when positive folds are fewer than four or when pooled/fold IC is unavailable.
Risk controls may not rescue either failure.

## Aggregate and doubled-cost evidence

| Metric | Base costs | Doubled costs | Interpretation |
|---|---:|---:|---|
| Total compounded return | 95.5525% | 44.0658% | Positive but concentrated early |
| Annualized return | 21.7472% | 11.3072% | Positive-return point gate passes |
| Net Sharpe | 0.932417 | 0.562459 | Base `>=0.75` and doubled `>=0.35` point gates pass |
| Sharpe 95% interval | `[-0.206273, 2.049109]` | `[-0.589676, 1.704868]` | Both include nonpositive values |
| Annualized volatility | 24.2519% | 24.2644% | Similar risk; costs reduce return |
| Maximum drawdown | 46.2448% | 55.2937% | Base 30% limit fails |
| Calmar | 0.470264 | 0.204493 | Base `>=0.40` passes; double diagnostic is weak |
| Worst day | -5.7976% | -5.8219% | Material tail |
| 1% expected shortfall | -4.2638% | -4.2952% | Cost stress worsens tail slightly |
| Positive folds | 3/6 | 3/6 | Required four; causal minimum fails |
| Positive quarters | 5/14 (35.7143%) | 5/14 (35.7143%) | Required 55% fails |

The base equity peak remains `2021-11-22`, the trough is `2023-05-11`, and the peak is not
recovered. End-of-development drawdown is 46.0737%.

## Exact six chronological folds

| Fold | Window `[start,end)` | Base return | Base Sharpe | Base max DD | Double return | Double Sharpe |
|---|---|---:|---:|---:|---:|---:|
| F1 | 2020-02-03 to 2020-09-01 | 2.5561% | 0.3861 | 8.9974% | 0.9697% | 0.1896 |
| F2 | 2020-09-01 to 2021-04-01 | 158.0284% | 4.9623 | 12.2922% | 144.6418% | 4.6915 |
| F3 | 2021-04-01 to 2021-11-01 | 29.1890% | 1.6434 | 16.5052% | 21.5724% | 1.2872 |
| F4 | 2021-11-01 to 2022-06-01 | -20.4860% | -1.5657 | 25.0390% | -25.2985% | -2.0210 |
| F5 | 2022-06-01 to 2023-01-01 | -13.2615% | -1.1986 | 20.9252% | -18.4975% | -1.7632 |
| F6 | 2023-01-01 to 2023-07-01 | -17.0621% | -2.0570 | 20.5968% | -21.2041% | -2.6411 |

F1-F3 are positive and F4-F6 negative at both cost levels. This is the same chronological sign
pattern as `rdf-ref-001`, so stronger path weighting does not create the required fourth positive
fold. The largest positive fold contributes 67.0076% of all positive fold dollar PnL under the
transparent diagnostic definition, versus 56.4020% for the reference and above the configured
40% ceiling. Formal concentration assessment still belongs to the organizer, but the diagnostic
evidence is adverse.

F1 contains 72.04% zero days because the first nonzero target is `2020-07-04`; the causal warmup is
retained rather than removed.

## Quarters

| Quarter | Base return | Doubled-cost return | Sign |
|---|---:|---:|---|
| 2020Q1 | 0.0000% | 0.0000% | flat / nonpositive |
| 2020Q2 | 0.0000% | 0.0000% | flat / nonpositive |
| 2020Q3 | 7.9213% | 5.6054% | positive |
| 2020Q4 | 39.4663% | 36.1361% | positive |
| 2021Q1 | 75.8137% | 71.8156% | positive |
| 2021Q2 | 21.1267% | 18.0119% | positive |
| 2021Q3 | -8.7605% | -11.1712% | negative |
| 2021Q4 | 11.7604% | 8.9524% | positive |
| 2022Q1 | -1.6213% | -4.1762% | negative |
| 2022Q2 | -13.2091% | -15.5404% | negative |
| 2022Q3 | -10.8557% | -13.3555% | negative |
| 2022Q4 | -5.2233% | -7.5821% | negative |
| 2023Q1 | -10.9307% | -13.1065% | negative |
| 2023Q2 | -6.8839% | -9.3189% | negative |

The candidate has no positive quarter after 2021Q4. The largest positive quarter supplies 44.7625%
of positive quarter dollar PnL, above 40%. Stronger gamma therefore changes magnitudes but not the
failed quarter breadth.

## Regimes and sleeve roles

| Regime | Candidate Sharpe | Reference Sharpe | Delta | Gate implication |
|---|---:|---:|---:|---|
| Bull | 1.048657 | 1.072263 | -0.023606 | Positive Sharpe; exact long-bull attribution absent |
| Bear | -1.527082 | -1.264131 | -0.262951 | Fails positive-bear role and `>=-0.25` worst-regime floor |
| Chop | 1.499451 | 2.214132 | -0.714681 | Positive Sharpe; exact combined-chop return absent |
| Stress | 2.385344 | 2.462946 | -0.077602 | Positive Sharpe; stress-specific tail absent |

Three regime Sharpes are positive, but the regime gate fails because bear deteriorates and is the
worst regime. The committed artifacts do not contain common regime labels joined to sleeve
contributions, so long-bull, short-bear, and combined-chop attribution cannot be reconstructed
formally.

Overall sleeve evidence is nevertheless adverse:

| Diagnostic | Long | Short |
|---|---:|---:|
| Mean exposure, all bars | 35.6729% | 33.9913% |
| Mean exposure, active bars | 41.0140% | 39.0806% |
| Active-bar fraction at `>=1%` | 86.9775% | 86.9775% |
| Reconstructed executed notional | $42.377M | $57.121M |
| Price contribution sum | 1.467624 | -0.515940 |
| Funding contribution sum | -0.087065 | 0.205410 |
| Gross contribution before shared costs | 1.380560 | -0.310530 |
| Diagnostic net after allocated shared costs | 1.247647 | -0.483359 |

Both sleeves are material, so the failure is not inactivity. The short sleeve loses before shared
costs despite receiving positive funding. Its gross contribution is worse than the reference's
`-0.230646`, providing no support for the required bear role.

## Costs, turnover, fills, and exposure

- Annualized one-way turnover is `119.6097x`, versus `117.0420x` for the reference. Summed turnover
  is `407.6560x`.
- There are 22,803 executed trade rows. Event-dollar fees are $50,757.50 and slippage is
  $25,378.75. Base return-contribution costs sum to 0.305742; doubled-cost contributions sum to
  0.611603.
- Requested notional is $101.641M and unfilled notional $0.126M, a 99.8763% diagnostic fill
  fraction. Participation is not the primary failure.
- Active gross averages 80.0946%; maximum gross is 1.000000000001 and maximum absolute net is
  22.9840%, within common exposure limits after central enforcement.
- Worst 8h return is -4.1751%. No declarative risk-policy reason appears; the candidate is the
  required no-control core.

## Comparison with `rdf-ref-001`

The only strategy coordinate changed is `gamma: 0.5 -> 1.0`. Every principal reported comparison
is unchanged or worse:

| Metric | Candidate | Reference | Candidate minus reference |
|---|---:|---:|---:|
| Annualized return | 21.7472% | 27.9696% | -6.2224 points |
| Net Sharpe | 0.932417 | 1.123931 | -0.191514 |
| Doubled-cost Sharpe | 0.562459 | 0.766779 | -0.204320 |
| Maximum drawdown | 46.2448% | 45.5647% | +0.6801 points |
| Positive quarters | 35.7143% | 35.7143% | unchanged |
| Positive folds | 3/6 | 3/6 | unchanged |
| Bear Sharpe | -1.527082 | -1.264131 | -0.262951 |
| Short gross contribution | -0.310530 | -0.230646 | -0.079883 |
| Positive-fold concentration | 67.0076% | 56.4020% | +10.6056 points |

The preregistered linear path-efficiency weighting is rejected. It neither stabilizes the time
series nor improves the short/bear mechanism.

## Next-day score IC audit

Pooled and per-fold next-day score IC are **not causally reconstructable** from the committed
artifacts:

- `targets.parquet` contains final weights and rebalance metadata, not the pre-construction score;
- final weights mix rank selection, inverse-volatility weighting, symbol caps, sleeve budgets, and
  the BTC tilt, so treating weight as score would change the preregistered diagnostic;
- event rows contain selected executions/funding only, not a full eligible-symbol next-open return
  panel;
- positions are quantities without a cross-sectional price/return panel; and
- bar-return artifacts are portfolio and sleeve aggregates.

Computing IC would require the forbidden snapshot or a separately emitted causal score/forward-
return panel. A selection-conditioned IC from traded symbols would be optimistic and invalid.
Accordingly:

- pooled next-day score IC: `unavailable`;
- positive score-IC folds: `unavailable`; and
- both count as failures under the exact pre-result stop rule.

## Frozen stop-rule application

| Causal condition | Required | Evidence | Result |
|---|---:|---:|---|
| Complete canonical development record | yes | complete | pass |
| Aggregate no-control net Sharpe | `>0` | 0.932417 | pass |
| Positive net-return folds | `>=4/6` | 3/6 | **fail** |
| Pooled next-day score IC | `>0` | unavailable | **fail** |
| Positive score-IC folds | `>=4/6` | unavailable | **fail** |

One failure is sufficient. `rdf-core-h21-k3-g10` is rejected, its gamma=1 branch stops, and it
receives no construction search or risk overlay. Aggregate Sharpe cannot compensate.

## At most one next preregistered core cell

The evidence supports one final diagnostic coordinate before stopping or pivoting:

`rdf-core-h14-k3-g05`

This is a one-coordinate contrast against the solvent reference:

`residual_lookback_days: 21 -> 14`

Rationale:

- both registered gamma values at `H=21, K=3` have the same 3-positive/3-negative fold split and
  failed bear/quarter/drawdown behavior;
- K=1 at `H=21, gamma=0.5` is terminally insolvent and remains rejected;
- the remaining orthogonal core question is whether the preregistered shorter medium horizon can
  respond to late/bear weakness while retaining the three-day skip that excludes the recent
  bounce/liquidation interval; and
- `H=14` is preferred over `H=28` for this single diagnostic because making an already late-failing
  signal slower does not isolate the response-lag hypothesis. This is a structural choice among
  preregistered values, not a fitted new value.

### Complete proposed binding

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
| `path_efficiency_exponent` | `0.5` | unchanged |
| `per_symbol_target_cap` | `0.09` | unchanged |
| `rank_tail_fraction` | `0.25` | unchanged |
| `rebalance_boundary_utc` | `00:00` | unchanged |
| `residual_denominator_floor` | `1e-8` | unchanged |
| `residual_lookback_days` | **`14`** | **only delta, from `21`** |
| `risk_policy_id` | `team-01-base` | unchanged; no controls enabled |
| `skip_days` | `3` | unchanged |
| `total_gross` | `0.80` | unchanged |
| runtime strategy seed | `20260801` | unchanged |
| execution cost multiplier | `1.0` | base costs |

The cell remains BTC-factor residual, path-efficient medium-horizon continuation. It adds no state
switch, reversal feature, construction change, or risk policy.

### Pre-result stop rule for `rdf-core-h14-k3-g05`

Reject the cell with no risk rescue if it is terminal/incomplete, aggregate no-control Sharpe is
nonpositive, positive folds are fewer than four, pooled next-day score IC is nonpositive or
unavailable, or positive score-IC folds are fewer than four or unavailable. Missing IC is failure,
not neutral evidence.

If any causal minimum fails, stop this family and either make a formal mechanism pivot or record
DNF; no further core cell is automatically authorized. If all causal minima pass, require a fresh
QR review before any construction, risk, private, or additional trial decision. Formal advancement
still requires every V2 gate and manifest/neighbor requirement.

## Trial and resource accounting

The insolvent K1 and rejected gamma=1 cells both consume full material trials.

| Budget | Consumed now | Remaining now | If the proposed cell is later registered/run |
|---|---:|---:|---:|
| Tournament material configurations | 3 / 80 | 77 | 4 / 80 consumed; 76 remain |
| Core factorial allocation | 3 / 12 | 9 | 4 / 12 consumed; 8 remain |
| Initial-family allocation | 3 / 39 | 36 | 4 / 39 consumed; 35 remain |
| CPU | 0.589317 / 12 h | 11.410683 h | Add actual proposed-run usage |
| Wall clock | 0.588817 / 18 h | 17.411183 h | Add actual proposed-run usage |
| Mechanism pivots | 0 / 2 | 2 | unchanged |

This review does not register or run `rdf-core-h14-k3-g05`. Its status is
`planned_not_registered_not_run`.
