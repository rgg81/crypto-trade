# Team 03 confirmed-shock pivot result

Candidate: `t03-crsa-base-i3-c1-b30-v21`  
Canonical result timestamp: `2026-07-16T12:28:01.136441Z`  
Runner record SHA-256: `895396195155506c037f6a3ac772688e069c3c904562d1c1074ae6873e6b15e9`

## Development result

The run completed causally and solvently, but its return evidence is decisively negative.

| Gate | Required | Observed | Result |
| --- | ---: | ---: | --- |
| Net Sharpe | `>= 0.75` | `-1.021666` | fail |
| Annualized return | `> 0` | `-6.333241%` | fail |
| Calmar | `>= 0.40` | `-0.281910` | fail |
| Maximum drawdown | `<= 30%` | `22.465461%` | pass |
| Doubled-cost Sharpe | `>= 0.35` | `-1.537978` | fail |
| Positive-quarter fraction | `>= 0.55` | `3/14 = 0.214286` | fail |
| Positive-Sharpe regimes | `>= 3` | `0/4` | fail |
| Worst regime Sharpe | `>= -0.25` | `-1.581109` | fail |

Regime Sharpes were bear `-1.046295`, bull `-1.581109`, chop `-1.074519`, and stress
`-0.497596`. The 95% bootstrap interval for net Sharpe was `[-2.045864, -0.066356]`; even its
upper endpoint was negative. The evaluator recorded `3,341` trades without an execution or
solvency failure.

## Disposition

The preregistered base stop is noncompensatory. It states that any base failure ends Team 03 and
forbids neighbor activation, risk-control rescue, replacement cells, and a second pivot. Team 03
therefore finishes DNF. No fold, neighborhood, risk ablation, private qualifier, or OOS run is
authorized.

