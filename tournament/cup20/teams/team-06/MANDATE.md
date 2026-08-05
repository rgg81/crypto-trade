# Team 06 — Downside-risk / low-volatility selection

Lane id: `downside-risk-low-volatility-selection`
Playbook: `tournament/cup20/TEAM-PLAYBOOK.md` (read it before you write any code)
Workspace: `tournament/cup20/teams/team-06/`
Data root: `data/cup20/is/`

## Mechanism intent

Selecting on realised volatility and selecting on downside risk are not the same selection, and in
crypto the gap between them is exactly where drawdown lives: a coin with symmetric high volatility
behaves nothing like a coin with a fat left tail. Your lane is cross-sectional selection on risk
characteristics — downside deviation, semivariance, drawdown depth and recovery time, tail asymmetry
— rather than on expected return. Note that the realised-volatility floor cuts against you
specifically: a book that cannot reach 6% annualised at full unlevered gross is disqualified, not
rewarded, so "safest" is not a strategy.

## What counts as a collision

Shared causal transforms and shared risk controls are **not** a collision. Another team computing
returns the way you do, standardising by realised volatility the way you do, or applying the same
drawdown brake, has taken nothing from you and does not need to be avoided. Twelve teams working the
same twenty coins over the same four years will inevitably reach for the same building blocks, and
pretending otherwise would only push everyone toward worse versions of the obvious thing.

**Copying another team's alpha is.** In practice this is not a temptation you can act on — you may
not read another team's directory, and the organiser's source scan enforces that boundary before any
number of yours is scored. What the rule means positively is: stay in your lane. If your candidate's
mechanism is better described by a different team's mandate than by this one, you have drifted, and
drifting into an occupied lane is the one collision that matters. The twelve lanes exist because in
crypto-cup-01 seven of ten teams independently converged on residual momentum; assignment is the
fix.
