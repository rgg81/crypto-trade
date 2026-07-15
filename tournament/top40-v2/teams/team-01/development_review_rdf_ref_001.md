# Development review: `rdf-ref-001`

Review timestamp: `2026-07-15`

Family: `t01-residual-drift-funding-v1`

Disposition: **continue the declared 12-cell core grid; do not apply risk overlays**

## Conclusion

The no-control reference is not a development qualifier and is not a causal success. It passes the
point gates for aggregate net Sharpe, annualized return, Calmar, and doubled-cost Sharpe, but fails
maximum drawdown, positive folds, positive quarters, bear behavior, and worst-regime Sharpe. Its
aggregate result is concentrated in 2020-2021: the final three frozen folds and the last six
quarters are all negative, the November 2021 equity peak is never recovered, and the short sleeve
loses money even before shared trading costs.

One of twelve registered core cells is insufficient to reject the whole family. The correct next
research action is a one-factor test of the registered skip choice: `rdf-core-h21-k1-g05`, changing
only `skip_days` from 3 to 1. This asks whether a more current medium-horizon continuation signal
can repair the bear/late-period failure. It is not a reversal switch. The candidate must be
registered before any future run; this review runs or registers nothing.

## Evidence boundary and method

Only team-01's own completed visible-development evidence was read:

- `tournament/top40-v2/teams/team-01/experiments.jsonl`;
- `reports-top40-v2/team-01/qualification-attempts/rdf-ref-001.runner-record.json`; and
- `reports-top40-v2/team-01/development-runs/rdf-ref-001/` canonical artifacts.

Runner-record point estimates and confidence intervals are reported as canonical. Fold, quarter,
tail, exposure, contribution, turnover, and concentration diagnostics were recomputed read-only
from the candidate's daily/bar returns, targets, positions, and event rows. Daily Sharpe uses the
sample standard deviation and `sqrt(365)`; returns are compounded. Executed sleeve notional is
reconstructed by carrying each symbol quantity and splitting a sign-crossing trade between the
side it closes and the side it opens. Shared bar cost contributions are allocated by the same
timestamp's reconstructed long/short USD fees and slippage; this allocation is diagnostic, not an
organizer-owned sleeve metric.

No market snapshot, evaluator, lifecycle command, other team, private/final artifact, strategy
change, risk-policy change, or frozen-config change was used. The six rows below are slices at the
preregistered fold boundaries. Formal OOF qualification still requires six hash-bound manifests,
independent cutoff-safe replay evidence, the trial-adjusted probability, and parameter neighbors.

## Aggregate and cost evidence

| Metric | Base costs | Doubled costs | V2 interpretation |
|---|---:|---:|---|
| Total compounded return | 131.7629% | 71.7747% | Positive, but temporally concentrated |
| Annualized return | 27.9696% | 17.2031% | Base annual-return gate passes |
| Net Sharpe | 1.123931 | 0.766779 | Base `>=0.75` and doubled-cost `>=0.35` point gates pass |
| Sharpe 95% interval | `[-0.003884, 2.193983]` | `[-0.377007, 1.853200]` | Both lower bounds include nonpositive values |
| Annualized volatility | 24.6314% | 24.6403% | Similar market risk; cost drag drives the difference |
| Maximum drawdown | 45.5647% | 53.8809% | Base 30% limit fails by 15.56 points |
| Calmar | 0.613845 | 0.319280 | Base `>=0.40` passes; doubled-cost diagnostic does not |
| Worst day | -6.0950% | -6.1087% | Material daily tail |
| 1% expected shortfall | -4.1899% | -4.2179% | Doubled costs slightly worsen the tail |
| Positive quarters | 5/14 (35.7143%) | 5/14 (35.7143%) | Required 55% fails |
| Positive frozen folds | 3/6 | 3/6 | Required four fails |

The base equity peak is `2021-11-22`, the drawdown trough is `2023-05-11`, and end-of-development
drawdown remains 45.4087%. There is no recovery to the old peak. Aggregate Sharpe therefore masks
a durable post-peak failure rather than a brief isolated loss.

## Six frozen folds

| Fold | Window `[start,end)` | Base return | Base Sharpe | Base max DD | Double return | Double Sharpe |
|---|---|---:|---:|---:|---:|---:|
| F1 | 2020-02-03 to 2020-09-01 | 1.8375% | 0.3008 | 9.4803% | 0.3372% | 0.1098 |
| F2 | 2020-09-01 to 2021-04-01 | 167.6600% | 4.8891 | 11.8648% | 154.1924% | 4.6408 |
| F3 | 2021-04-01 to 2021-11-01 | 47.7451% | 2.3926 | 10.8115% | 39.3312% | 2.0537 |
| F4 | 2021-11-01 to 2022-06-01 | -18.9702% | -1.4870 | 23.1349% | -23.7408% | -1.9468 |
| F5 | 2022-06-01 to 2023-01-01 | -13.2559% | -1.2157 | 21.2206% | -18.4108% | -1.7794 |
| F6 | 2023-01-01 to 2023-07-01 | -18.1244% | -2.2635 | 22.4070% | -22.3107% | -2.8763 |

Only F1-F3 are positive. The best positive fold supplies 56.4020% of total positive fold dollar
PnL, above the configured 40% concentration ceiling under this transparent diagnostic definition.
Because the formal concentration field and fold manifests are not present, this is a diagnostic
failure rather than a claim that the organizer has assessed the gate.

F1 is also weak evidence: 72.04% of its daily observations are zero because the first nonzero target
does not occur until `2020-07-04`. That flat warmup is causal and must remain in the evidence; it is
not removed to improve fold or quarter counts.

## Quarters

| Quarter | Base return | Doubled-cost return | Sign |
|---|---:|---:|---|
| 2020Q1 | 0.0000% | 0.0000% | flat / nonpositive |
| 2020Q2 | 0.0000% | 0.0000% | flat / nonpositive |
| 2020Q3 | 4.9164% | 2.7689% | positive |
| 2020Q4 | 36.6800% | 33.3501% | positive |
| 2021Q1 | 90.0828% | 86.1098% | positive |
| 2021Q2 | 25.6302% | 22.6533% | positive |
| 2021Q3 | -1.2357% | -3.8257% | negative |
| 2021Q4 | 13.0555% | 10.1484% | positive |
| 2022Q1 | -2.1622% | -4.5875% | negative |
| 2022Q2 | -11.9811% | -14.2021% | negative |
| 2022Q3 | -11.4834% | -14.0043% | negative |
| 2022Q4 | -2.8807% | -5.2240% | negative |
| 2023Q1 | -11.6509% | -13.8680% | negative |
| 2023Q2 | -7.3272% | -9.8020% | negative |

The required positive-quarter fraction fails at 35.7143%. The largest positive quarter supplies
45.0735% of positive quarter dollar PnL under the same diagnostic concentration definition, also
above 40%. More importantly, every quarter after 2021Q4 is negative at both cost levels.

## Common regimes

Only regime Sharpe is present in the runner record; exact regime compounded returns and
sleeve-by-regime attribution are absent.

| Regime | Net Sharpe | Available gate implication |
|---|---:|---|
| Bull | 1.072263 | Positive Sharpe; exact bull compounded return and long attribution unavailable |
| Bear | -1.264131 | Worst regime; fails the `>=-0.25` floor and cannot meet the required positive bear-return condition |
| Chop | 2.214132 | Positive Sharpe; exact combined chop return unavailable |
| Stress | 2.462946 | Positive Sharpe; stress-specific drawdown and tail unavailable |

Exactly three of four reported regime Sharpes are positive, satisfying that count in isolation.
The overall regime gate nevertheless fails because bear is deeply negative and the worst-regime
floor is breached by 1.0141 Sharpe units. Positive bull/chop Sharpes are not substituted for the
missing exact return and sleeve-role fields.

## Sleeves, exposure, and executed notional

| Diagnostic | Long | Short | Interpretation |
|---|---:|---:|---|
| Mean realized exposure, all bars | 35.6598% | 33.9798% | Both exceed the 1% mean floor |
| Mean realized exposure, active bars | 40.9989% | 39.0674% | Close to intended two-sided 0.80 gross |
| Active-bar fraction at `>=1%` | 86.9775% | 86.9775% | Both exceed the 10% floor |
| Reconstructed executed notional | $45.495M | $64.478M | Both exceed the $1,000 floor by orders of magnitude |
| Price return contribution sum | 1.544525 | -0.441659 | Short price selection loses materially |
| Funding return contribution sum | -0.080240 | 0.211012 | Longs pay; shorts receive as hypothesized |
| Gross contribution before shared costs | 1.464285 | -0.230646 | The short sleeve is negative before trading costs |
| Diagnostic net after allocated shared costs | 1.337300 | -0.402839 | Not an organizer-owned role metric |

Both sleeves are unquestionably material in exposure and notional, but the economic outcome is
one-sided. The short sleeve loses 0.230646 in summed return contribution even after favorable
funding and before shared fees/slippage. This does not prove the mandatory short-in-bear role fails,
because sleeve-by-regime attribution is absent, but it is strong adverse evidence. Long-in-bull,
short-in-bear, and combined-in-chop gates remain formally unavailable.

Funding behaves in the intended accounting direction: long funding contributes `-0.080240`, short
funding `+0.211012`, and net funding `+0.130773`. That supports the carry-sign premise but not the
causal ranking claim; the registered `lambda_funding=0` ablation has not been run.

## Drawdown, tail, turnover, fills, and controls

- Mean gross exposure is 69.6397% over all bars and 80.0663% when active. Maximum gross is
  1.000000000001 from central enforcement; maximum absolute net exposure is 23.1048%, below 25%.
- Annualized one-way turnover is approximately `117.042x`; summed turnover is `398.905x`.
  There are 22,733 executed trade rows and approximately $109.973M of reconstructed two-sided
  executed notional.
- Base fees total $56,176 and slippage $28,088 in event dollars. In summed return-contribution
  units, fees are 0.199452 and slippage 0.099726; doubled-cost units are 0.398987 and 0.199493.
- Requested notional is $112.480M and unfilled notional $0.128M, for a 99.8862% diagnostic fill
  fraction. Participation is not the principal failure.
- Worst 8h bar return is -4.4119%; worst daily return is -6.0950%; daily 1% expected shortfall is
  -4.1899%.
- `team-01-base` has no declarative volatility target, drawdown brake, position/time stop, turnover
  limit, or side scaling. The event rows show 171 membership exits and 54 common exposure-cap
  reductions, not evidence of a selected risk overlay. Risk controls therefore did not create the
  reference result and may not be used to rescue its causal fold failure.
- Of 1,244 scheduled daily rebalances, 1,082 have nonzero targets and 162 are flat. Across all
  daily returns, 12.4598% are zero.

## V2 gate ledger from available evidence

| Gate | Threshold | Observed | Status |
|---|---:|---:|---|
| Net Sharpe | `>=0.75` | 1.123931 | **PASS (point estimate)** |
| Annualized return | `>0` | 27.9696% | **PASS** |
| Calmar | `>=0.40` | 0.613845 | **PASS** |
| Maximum drawdown | `<=30%` | 45.5647% | **FAIL** |
| Doubled-cost Sharpe | `>=0.35` | 0.766779 | **PASS (point estimate)** |
| Positive folds | `>=4/6` | 3/6 | **FAIL** |
| Positive-quarter fraction | `>=55%` | 35.7143% | **FAIL** |
| Trial-adjusted probability positive | `>=90%` | Not emitted | **UNAVAILABLE** |
| Bull/bear/chop positive return | all three | Bear Sharpe -1.264131; exact other returns absent | **FAIL (bear)** |
| Positive-Sharpe regimes | `>=3` | 3 | **PASS in isolation** |
| Worst-regime Sharpe | `>=-0.25` | -1.264131 | **FAIL** |
| Long positive in bull | `>0` | Sleeve-by-regime field absent | **UNAVAILABLE** |
| Short positive in bear | `>0` | Sleeve-by-regime field absent; short overall negative | **UNAVAILABLE / adverse** |
| Combined positive in chop | `>0` | Exact chop return absent | **UNAVAILABLE** |
| Side exposure | `>=1%` | Active means 40.999% / 39.067% | **PASS diagnostically** |
| Side active fraction | `>=10%` | 86.978% / 86.978% | **PASS diagnostically** |
| Mean side exposure | `>=1%` | 35.660% / 33.980% | **PASS diagnostically** |
| Side executed notional | `>=$1,000` | $45.495M / $64.478M | **PASS diagnostically** |
| Positive-PnL concentration | `<=40%` | Fold 56.402%; quarter 45.074% | **FAIL diagnostically; canonical field absent** |
| Profitable neighbor fraction | `>=70%` | No neighbors | **UNAVAILABLE** |
| Neighbor median Sharpe | `>=0.50` | No neighbors | **UNAVAILABLE** |
| Six fold/model manifests | required | Not present in reviewed evidence | **UNAVAILABLE** |

These failures are non-compensatory. The aggregate winners do not establish formal qualification,
and this review does not request a private ticket.

## Preregistered causal and falsifier implications

The reference satisfies only one of the four primary causal minima: aggregate no-control Sharpe is
positive. It fails the required four positive folds with only three. Pooled next-day score IC,
positive-IC fold count, and the raw-momentum comparison are not present, so those falsifiers remain
unresolved. Funding cashflow has the predicted sign, but its ranking benefit remains untested.

The time pattern is economically coherent adverse evidence: strong long-led gains in 2020-2021,
then three negative folds, six consecutive negative quarters, a losing short sleeve, and a large
unrecovered drawdown. Risk overlays cannot establish the missing continuation IC or turn three
positive folds into causal breadth. The reference cell is rejected and receives no risk overlay.

The family itself is not yet rejected because eleven preregistered `H x K x gamma` cells remain.
The current evidence points first to signal staleness: a three-day skip may omit information needed
for the short sleeve to adapt during a broad decline.

## Frozen next-research decision and stop rules

Decision: **continue the declared 12-cell core grid; do not pivot yet and do not start risk
ablations.**

Exact next material cell, in order after the completed reference:

- planned candidate ID: `rdf-core-h21-k1-g05`;
- `residual_lookback_days=21`;
- `skip_days=1`;
- `path_efficiency_exponent=0.5`;
- `rank_tail_fraction=0.25`;
- `direction_tilt_delta=0.075`; and
- every other source, seed (`20260801`), funding, beta, weighting, execution, base-cost, and
  no-control parameter identical to `rdf-ref-001`.

This is a clean one-factor contrast against the reference. It remains medium-horizon BTC-residual
continuation and explicitly does not introduce a persistence/reversal state switch.

Stop rules, frozen before seeing the next cell:

1. A core cell is dead and receives no construction or risk overlay if aggregate no-control net
   Sharpe is nonpositive, fewer than four folds have positive net return, pooled next-day score IC
   is nonpositive, or fewer than four folds have positive score IC once IC evidence is emitted.
2. For `rdf-core-h21-k1-g05`, failure to clear the causal minima stops the `H=21, K=1,
   gamma=0.5` branch immediately; it does not justify a risk overlay. The remaining registered
   core cells may still be tested in their declared family budget.
3. If none of the full 12-cell core grid clears all four causal minima, stop this family and pivot
   or record DNF. Do not expand the parameter domain and do not use a risk policy as rescue.
4. Even a causal-minimum passer cannot advance as champion until all non-compensatory V2 gates,
   six manifests, raw-momentum and funding component checks, trial adjustment, and the declared
   parameter neighborhood are complete. No private or final evidence may influence this decision.
