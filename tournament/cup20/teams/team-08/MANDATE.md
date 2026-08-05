# Team 08 — Funding and basis term-dynamics reversion

Lane id: `funding-basis-term-dynamics-reversion`
Playbook: `tournament/cup20/TEAM-PLAYBOOK.md` (read it before you write any code)
Workspace: `tournament/cup20/teams/team-08/`
Data root: `data/cup20/is/`

## Mechanism intent

Funding and perp-spot basis are not merely levels — they are a term structure with dynamics, and the
rate of change, the persistence and the spread between a coin's current funding and its own recent
regime say things about positioning that the level alone does not. Your lane is reversion in those
dynamics: funding change, basis change, and the cross-sectional dispersion of both, as the signal.
If your candidate reduces to "short the high-funding names", you have wandered into team 07's lane
and have not done your own.

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
