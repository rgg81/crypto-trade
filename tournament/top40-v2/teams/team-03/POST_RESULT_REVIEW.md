# Team 03 falsifier review

Decision: stop and falsify `t03-residual-liquidity-shock-absorption-v1`. Do not run its declared
neighbors or risk-control ablations.

## Registered falsifier application

| Preregistered condition | Available evidence | Determination |
| --- | --- | --- |
| Reject immediately for causal failure or nondeterminism | Five synthetic checks passed before registration | Prerequisite passed; not qualification evidence |
| Reject immediately for invalid execution or insolvency | Evaluator reported portfolio insolvency at `2022-05-13 00:00:00+00:00` | Hard fail; family iteration stops |
| No-control OOF Sharpe must be positive | No metrics were promoted | Unevaluable; cannot be credited |
| At least four folds must be positive | No fold artifacts were promoted | Unevaluable; cannot be credited |
| Bull, bear, and chop returns must each be positive | No regime artifacts were promoted | Unevaluable; cannot be credited |
| Long-bull and short-bear roles must be positive | No sleeve artifacts were promoted | Unevaluable; cannot be credited |
| Doubled-cost Sharpe must be positive | No cost artifact was promoted | Unevaluable; cannot be credited |
| Drawdown must not exceed 40% | Insolvency occurred before a metric report was promoted | Hard fail already dominates |
| Risk controls cannot rescue a failed base mechanism | Base ended insolvent | All old-family control variants remain unauthorized |

The terminal insolvency alone is sufficient. Missing downstream evidence does not soften the
decision and must not be converted into estimated values.

## Public-rule application

The public playbook says a failed hypothesis is research evidence rather than a submission, every
failed material attempt consumes budget, and a team may continue with a documented mechanism
pivot or finish DNF. The Phase-0 policy permits at most two pivots and does not reset the cumulative
80-configuration, 12-CPU-hour, or 18-wall-clock-hour budgets.

Team 03 has one recorded material configuration, approximately 0.196 CPU hour, approximately
0.196 wall-clock hour, and no earlier pivot. Budget therefore permits a child family, but budget
availability is not evidence that the old signal works.

## Family disposition

- Scientific state: `STOPPED_FALSIFIED_INSOLVENCY`.
- Candidate disposition: terminal failure; never eligible for qualification.
- Old parameter neighborhood: cancelled before activation.
- Old volatility, drawdown, turnover, and combined controls: cancelled before activation.
- Old source and registration: retained unchanged for audit; no corrected rerun.
- Promoted development evidence: none.

The only permissible continuation is a preregistered child mechanism that changes when alpha is
believed to exist. Lower gross, volatility targeting, drawdown brakes, position stops, time stops,
or cooldowns applied to the failed immediate-reversal signal would be a prohibited rescue.
