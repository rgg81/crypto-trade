# Team 04 — Market-residual cross-sectional momentum

Lane id: `market-residual-cross-sectional-momentum`
Playbook: `tournament/cup20/TEAM-PLAYBOOK.md` (read it before you write any code)
Workspace: `tournament/cup20/teams/team-04/`
Data root: `data/cup20/is/`

## Mechanism intent

Almost all of a crypto book's variance is one factor with BTC's name on it, so a cross-sectional
ranking that ignores it is largely a ranking of beta. Your lane is momentum on the **residual** —
coin returns after removing a market component estimated causally from past rows only — expressed as
a long/short cross-section inside the top twenty. A twenty-name universe has materially less
dispersion than forty, so you will be working in thirds rather than quintiles; that handicap is
deliberate, accepted, and stated up front in the charter.

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
