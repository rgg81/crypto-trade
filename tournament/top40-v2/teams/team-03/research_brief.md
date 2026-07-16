# Team 03 research brief

Status: preregistration candidate prepared; not registered and not evaluated.

## Candidate

- Family: `t03-residual-liquidity-shock-absorption-v1`
- Candidate: `t03-rlsa-base-h3-b30-v21-f25`
- Risk policy: `team-03-base` (no controls enabled)
- Deterministic seed: `20260801`

## Thesis and mechanism

High-volume price moves that are not explained by rolling BTC beta, and that agree with crowded
perpetual funding, may contain temporary forced-flow impact. Once per day, the candidate estimates
BTC beta and residual volatility from history ending before the latest three closed 8-hour bars.
It then ranks the three-bar residual shock, amplifies unusually high-volume shocks, and applies a
funding-crowding adjustment. The strongest negative exhaustion tail is bought and the strongest
positive exhaustion tail is shorted. BTC is an untraded anchor.

The base book requires at least 20 valid non-BTC contracts, selects 25% per side with at least five
names per sleeve, targets 80% gross, caps each name at 8%, and uses a 60-day BTC trend only to move
five percentage points of gross between sleeves. Expected gross is 45%/35% in bull conditions,
35%/45% in bear conditions, and 40%/40% in chop.

## Economic roles

- Long: provide liquidity after unusually negative idiosyncratic shocks; expected to contribute
  during bull pullbacks.
- Short: fade unusually positive idiosyncratic shocks; expected to contribute during bear relief
  rallies.
- Chop: symmetric repeated overshoots are the primary expected source of return.
- Stress: falling-knife and squeeze risk remain explicit. Controls may be tested only after the
  no-control mechanism passes its screen.

## Preregistered falsifier

Reject immediately for causal-test failure, nondeterminism, invalid execution, or insolvency.
Reject the no-control iteration for nonpositive stitched OOF Sharpe, fewer than four positive
folds, nonpositive bull/bear/chop return, nonpositive long-bull or short-bear attribution,
nonpositive doubled-cost Sharpe, or drawdown above 40%. Risk controls cannot rescue a failed base
mechanism.

No return, Sharpe, drawdown, regime, sleeve, cost, or neighborhood result is claimed in this brief.
