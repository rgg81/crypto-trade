# Team 10 — Volatility-regime risk-on / risk-off timing

Lane id: `volatility-regime-risk-on-risk-off-timing`
Playbook: `tournament/cup20/TEAM-PLAYBOOK.md` (read it before you write any code)
Workspace: `tournament/cup20/teams/team-10/`
Data root: `data/cup20/is/`

## Mechanism intent

Crypto volatility clusters hard, and the regime it clusters into changes the sign of nearly every
other mechanism: trend pays in one regime and gets shredded in the other. Your lane is the timing
layer itself — identify the regime causally from past rows (realised volatility level and term
structure, cross-sectional dispersion, correlation to BTC) and express it as exposure: risk-on,
risk-off, or the direction of a simple base book. You are being asked whether regime timing adds
anything a static book does not already have, and "no" is a publishable answer here.

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
