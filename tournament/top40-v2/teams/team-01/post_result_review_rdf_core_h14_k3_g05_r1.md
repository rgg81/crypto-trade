# Post-result review: `rdf-core-h14-k3-g05-r1`

Prepared: `2026-07-16`  
Family: `t01-residual-drift-funding-v1`  
Disposition: **stop this family; no risk rescue and no additional old-family core cell**  
Next action: **authorize specification of one formal mechanism pivot, not registration or execution**

## Decision

The H14 replacement is the strongest aggregate result in the family, but it does not repair the
family's defining failure. Net Sharpe is `1.230012`, annualized return `31.1593%`, Calmar `0.709937`,
and doubled-cost Sharpe `0.818887`. Those point gates pass, and the net-Sharpe bootstrap interval is
fully positive. Maximum drawdown remains `43.8902%`, only `7/14` quarters are positive, bear Sharpe
is `-1.423421`, and the exact fold sequence is still three positive early folds followed by three
negative late folds. The candidate therefore fails mandatory development, chronology, and regime
gates despite its attractive aggregate result.

More decisively, the exact preregistration rejects this cell if fewer than four folds are positive
or if pooled/fold score IC is unavailable. It has only `3/6` positive folds and no candidate-specific
score diagnostic. Both are independent stop-rule failures. Risk controls cannot rescue either one.
The residual-drift/funding family must stop.

## Evidence boundary

This review uses only Team 01's registration, experiment ledger, canonical runner record, and its
archived H14 base/double-cost daily and bar-return artifacts, plus the public V2 rules. No evaluator,
analysis script, strategy process, lifecycle command, other team, V1 result, private qualifier, or
final-OOS material was accessed. Fold signs and approximate returns were read from the canonical
boundary equities; no formal organizer assessment is claimed.

## Visible development gates

| Gate | Required | H14 evidence | Status |
|---|---:|---:|---|
| Net Sharpe | `>=0.75` | `1.230012` | **PASS** |
| Annualized return | `>0` | `31.1593%` | **PASS** |
| Calmar | `>=0.40` | `0.709937` | **PASS** |
| Maximum drawdown | `<=30%` | `43.8902%` | **FAIL** |
| Doubled-cost Sharpe | `>=0.35` | `0.818887` | **PASS** |
| Positive folds | `>=4/6` | `3/6` | **FAIL** |
| Positive quarters | `>=55%` | `50%` (`7/14`) | **FAIL** |
| Trial-adjusted probability positive | `>=90%` | not emitted | **UNAVAILABLE** |
| Bull/bear/chop positive return | all three | bear Sharpe `-1.423421` | **FAIL — bear** |
| Positive-Sharpe regimes | `>=3` | bull, chop, stress = `3` | **PASS** |
| Worst-regime Sharpe | `>=-0.25` | `-1.423421` | **FAIL** |
| Long positive in bull | `>0` | no regime-by-sleeve field | **UNAVAILABLE** |
| Short positive in bear | `>0` | no regime-by-sleeve field | **UNAVAILABLE** |
| Combined positive in chop | `>0` | no exact role-return field | **UNAVAILABLE** |
| Side exposure/activity/notional | frozen minima | raw artifacts only; no formal summary | **UNAVAILABLE** |
| Profitable-neighbor fraction | `>=70%` | no neighborhood | **UNAVAILABLE** |
| Neighbor median Sharpe | `>=0.50` | no neighborhood | **UNAVAILABLE** |
| Positive-PnL concentration | `<=40%` | approximate largest positive-fold share `62.75%` | **DIAGNOSTIC FAIL** |

Positive bull and chop Sharpes do not substitute for the missing exact compounded returns or sleeve
roles. The negative bear Sharpe is sufficient adverse evidence for the required positive-bear
condition, and the worst-regime floor fails by more than `1.17` Sharpe units.

## Six chronological folds

The boundary-equity derivation gives the following approximate compounded returns. Signs and the
positive-fold count are exact.

| Fold | Window `[start,end)` | Base return | Doubled-cost return | Sign |
|---|---|---:|---:|---|
| F1 | 2020-02-03 to 2020-09-01 | `+3.5483%` | `+1.8125%` | positive |
| F2 | 2020-09-01 to 2021-04-01 | `+160.3756%` | `+144.0866%` | positive |
| F3 | 2021-04-01 to 2021-11-01 | `+35.2512%` | `+26.4333%` | positive |
| F4 | 2021-11-01 to 2022-06-01 | `-11.0879%` | `-16.9727%` | negative |
| F5 | 2022-06-01 to 2023-01-01 | `-9.9522%` | `-15.7374%` | negative |
| F6 | 2023-01-01 to 2023-07-01 | `-13.6693%` | `-18.5883%` | negative |

H14 improves positive-quarter breadth from the earlier cells' `5/14` to `7/14`, and its aggregate
and doubled-cost Sharpes are stronger. It nevertheless leaves the exact early/late fold sign split
unchanged. The largest positive fold contributes approximately `62.75%` of positive fold-dollar
PnL, above the public `40%` stability ceiling under this transparent diagnostic definition.

## Preregistered causal falsifier

| Causal minimum | Required | Evidence | Result |
|---|---:|---:|---|
| Complete canonical record | yes | complete | pass |
| Aggregate no-control Sharpe | `>0` | `1.230012` | pass |
| Positive folds | `>=4/6` | `3/6` | **fail** |
| Pooled next-day score IC | `>0` | unavailable | **fail** |
| Positive score-IC folds | `>=4/6` | unavailable | **fail** |

One failure is sufficient. There are three. The registration explicitly requires the family to
stop and either pivot formally or record DNF. No volatility target, drawdown brake, stop, side
scale, construction search, or additional old-family coordinate is authorized.

## Why one formal pivot is justified

Immediate DNF would be honest and scientifically valid. One bounded pivot is nevertheless justified
because the completed solvent cells repeatedly show real aggregate, bull, chop, and cost-stressed
strength while failing in the same late/bear direction. H14 improves Sharpe, quarters, and drawdown
without changing the late-fold signs. That motivates, but does not prove, one falsifiable diagnosis:
unconditional BTC residualization may remove common downside information that the short sleeve needs
in bear markets.

The pivot is `t01-regime-conditional-trend-carry-v2`, reference candidate
`rctc-pivot-ref-001`. It is a new state-dependent mechanism and must be registered as a formal pivot
before implementation or measurement.

### Exact reference mechanism

- At `00:00 UTC`, use only closed 8h bars and funding rows strictly before the decision.
- Classify direction from BTC data ending at `t-1 day`: bull when its trailing 60-day log return is
  at least `+0.10`, bear when at most `-0.10`, otherwise chop.
- In bull and chop, retain the H14/K3/gamma0.5 path-efficient BTC-residual continuation score.
- In bear, replace only the ranking input with path-efficient standardized 14-day raw asset trend,
  also ending three days before the decision. Long relative survivors; short the strongest absolute
  downside trends.
- In every state subtract `0.35 * robust_z(seven-day realized funding)`.
- Keep `q=0.25`, at least 24 valid symbols and six names per side, 0.09 symbol caps, inverse-volatility
  capped-simplex sleeves, total gross 0.80, and runtime seed `20260801`. Compute the clipped sleeve
  tilt from the same lagged BTC direction value with scale `0.20` and delta `0.075`.
- The reference has no risk controls. It changes one economic branch, not risk and signal together.

### Pivot stop rule

Reject `rctc-pivot-ref-001` with no risk rescue if it is incomplete/insolvent, aggregate Sharpe is
nonpositive, fewer than four folds are positive, any of bull/bear/chop net return is nonpositive,
long-bull/short-bear/combined-chop attribution is nonpositive, fewer than three regime Sharpes are
positive, or worst-regime Sharpe is below `-0.25`. Its bear return and short-bear attribution must be
positive against the completed all-residual H14 comparator. Failure requires DNF or a separately
registered second and final pivot; it authorizes no parameter search.

If the no-control reference clears those causal and role gates, a fresh review may preregister—not
silently apply—a risk matrix with a 20% annualized volatility target and the existing 10%/18%/25%
drawdown brakes at base and doubled costs. Formal qualification still requires every aggregate,
drawdown, quarter, multiplicity, fold-manifest, concentration, sleeve, and neighborhood gate.

## Accounting

The infrastructure-failed H14 attempt and its replacement both remain counted. Team 01 has consumed
`5/80` material registrations, approximately `0.791591` CPU hours and `0.790933` wall-clock hours.
This decision consumes the first of at most two mechanism pivots only when its family registration
is actually recorded; it does not itself register, implement, or run the pivot.
