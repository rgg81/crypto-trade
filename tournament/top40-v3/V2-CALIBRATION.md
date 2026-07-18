# Top40 V3 qualification calibration against V2 development results

This document calibrates the public V3 policy against committed Top40-v2 visible-development
runner records. It does not reclassify the V2 tournament or use private/OOS evidence.

## Policy separation

Public eligibility requires all four immutable integrity facts—reproducible, causal, solvent, and
universe-compliant—and these core floors:

| Metric | V3 public floor |
|---|---:|
| Net Sharpe | `>= 0.75` |
| Annualized return | `> 0` |
| Maximum drawdown | `<= 0.30` |
| Doubled-cost Sharpe | `>= 0.35` |
| Positive-quarter fraction | `>= 0.50` |
| Trade count | `>= 1000` |
| Positive regime Sharpes | `>= 2/4` |
| Worst regime Sharpe | `>= -0.75` |

Robustness orders eligible candidates but never creates another eligibility gate. With
`C(x) = min(1, max(0, x))`:

```text
R =
25*C((Sharpe - 0.75)/0.75)
+ 15*C(annual_return/0.30)
+ 15*C((0.30-drawdown)/0.20)
+ 15*C((double_cost_sharpe-0.35)/0.65)
+ 15*C((positive_quarters-0.50)/0.25)
+ 10*(positive_regime_count/4)
+ 5*C((worst_regime_sharpe+0.75)/1.50)
```

The assessment API returns every eligible candidate in descending `R`. A separately frozen
finalist-count cap may take the first `N`; there is no `R >= 50` rule.

## One-nominee-per-team V2 calibration

Using one representative nominee per team and V3's frozen four-finalist cap gives:

| Rank | Candidate | Team | Eligible | R | Calibration outcome |
|---:|---|---|---|---:|---|
| 1 | `team-04-utc-reference-001` | 04 | yes | `77.0193492586806` | advances |
| 2 | `t07-two-tape-rank-durability-v1-base` | 07 | yes | `67.44919300281242` | advances |
| 3 | `team05-crtr-ab-dd` | 05 | yes | `63.759621761910715` | advances |
| 4 | `team09-drp-pivot02-v1` | 09 | yes | `46.14891896646174` | advances |

Team09 is intentionally eligible and advances even though its score is below 50. This demonstrates
that `R` ranks strong core passers without becoming another arbitrary all-or-nothing gate.

## Core-floor veto calibration

`team-02-fir-reference-001` remains ineligible despite strong aggregate metrics because bear
Sharpe is `-1.0155758613712025`, below the `-0.75` catastrophic-regime floor.

`t10-fpu-core-v1` remains ineligible for the same reason: bear Sharpe is
`-1.3505783247443206`.

`rdf-core-h14-k3-g05-r1` remains ineligible independently for the recorded Team01 integrity
failure, maximum drawdown `0.43890174643882895`, and bear Sharpe
`-1.4234211206019132`.

These are narrow core vetoes. V3 does not require every V2 fold, role, score-IC, trial-adjusted
confidence, neighborhood, or PnL-concentration diagnostic to pass independently.

## Private assessment

Private eligibility rechecks the four integrity facts and requires net Sharpe `> 0`, annualized
return `> 0`, doubled-cost Sharpe `> 0`, and maximum drawdown `<= 0.35`. It has no per-regime veto;
private evidence is intended to test generalization rather than repeat public regime selection.

## V2 evidence paths

- `reports-top40-v2/team-04/qualification-attempts/team-04-utc-reference-001.runner-record.json`
- `reports-top40-v2/team-07/qualification-attempts/t07-two-tape-rank-durability-v1-base.runner-record.json`
- `reports-top40-v2/team-05/qualification-attempts/team05-crtr-ab-dd.runner-record.json`
- `reports-top40-v2/team-09/qualification-attempts/team09-drp-pivot02-v1.runner-record.json`
- `reports-top40-v2/team-02/qualification-attempts/team-02-fir-reference-001.runner-record.json`
- `reports-top40-v2/team-10/qualification-attempts/t10-fpu-core-v1.runner-record.json`
- `reports-top40-v2/team-01/qualification-attempts/rdf-core-h14-k3-g05-r1.runner-record.json`
