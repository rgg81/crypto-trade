# Team 03 — Trend-quality-gated momentum

Lane id: `trend-quality-gated-momentum`
Playbook: `tournament/cup20/TEAM-PLAYBOOK.md` (read it before you write any code)
Workspace: `tournament/cup20/teams/team-03/`
Data root: `data/cup20/is/`

## Mechanism intent

Two coins can post the same trailing return by completely different paths, and the path is what
separates a trend from a random walk that happened to end up somewhere. Your lane is momentum
conditioned on trend *quality*: efficiency ratio (net displacement over path length), run length and
persistence statistics, trend-strength measures — used to decide when a directional reading deserves
size and when it is noise wearing a direction. The gate is your mechanism; an ungated momentum
signal is team 01's lane, not yours.

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
