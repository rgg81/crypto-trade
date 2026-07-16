# Team 03 pivot research brief

Status: child-family implementation prepared; validation, registration, and evaluation not run.

## Research accounting

Parent family `t03-residual-liquidity-shock-absorption-v1` is permanently stopped after candidate
`t03-rlsa-base-h3-b30-v21-f25` ended insolvent. Its neighbors and controls were never activated.

This document preregisters Team 03's first and only planned pivot:

- Family: `t03-confirmed-residual-shock-absorption-v1`
- Parent: `t03-residual-liquidity-shock-absorption-v1`
- Candidate: `t03-crsa-base-i3-c1-b30-v21`
- Risk policy: `team-03-base` with every control disabled
- Deterministic seed: `20260801`

## Changed thesis

A high-volume move unexplained by rolling BTC beta is not assumed to reverse immediately. It is
eligible only after the next fully closed 8-hour beta residual changes sign against the impulse,
which is causal evidence that marginal forced flow may have been absorbed.

At each daily decision, the latest closed bar is the one-bar confirmation. The three bars before it
form the impulse. Beta, residual scale, and volume baselines all end before that impulse. A negative
impulse followed by a positive confirmation is long-eligible; a positive impulse followed by a
negative confirmation is short-eligible. Funding crowding and impulse volume rank confirmed names
but cannot substitute for confirmation.

This is a new alpha state and entry timing, not a risk overlay. It retains 80% target gross, the 8%
name cap, and the five-percentage-point BTC-trend sleeve tilt. It does not use P&L, equity,
drawdown, position age, stops, brakes, cooldowns, volatility scaling, or a lower gross target.

## Portfolio construction and roles

At least 20 non-BTC symbols must have valid histories. The per-side count is 25% of that valid
universe rounded down, with a floor of six. Both confirmed sides must fill their entire count or the
strategy requests flat.

- Long: buy the strongest confirmed negative impulses; expected to contribute positively in bull.
- Short: short the strongest confirmed positive impulses; expected to contribute positively in
  bear.
- Chop: symmetric repeated absorption events should contribute positively in combination.
- Stress: confirmation is hypothesized to reject continuing shocks, but solvency and drawdown are
  hard falsifiers rather than assumptions.

## Frozen stop decision

The no-control base must pass every public development, fold, cost, regime, sleeve, activity, and
concentration gate recorded in `candidate_spec.json` and `../POST_RESULT_DECISION.md`. Only a
complete base pass activates four fixed one-axis neighbors: impulse horizons 1 and 6, and BTC-beta
lookbacks 21 and 45 days. At least three of four must be profitable and the full stability gate
must pass.

Any base or neighborhood failure makes Team 03 DNF. There is no replacement neighbor, control
rescue, manual variant, or second pivot. No performance result is claimed in this brief.
