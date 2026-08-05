# Team 09 — Taker-flow / price-volume pressure

Lane id: `taker-flow-price-volume-pressure`
Playbook: `tournament/cup20/TEAM-PLAYBOOK.md` (read it before you write any code)
Workspace: `tournament/cup20/teams/team-09/`
Data root: `data/cup20/is/`

## Mechanism intent

Every bar in this snapshot carries taker-buy volume and trade count alongside price, so aggressive
order flow is directly observable here rather than inferred. Your lane is the pressure that flow
exerts on price: taker-buy imbalance, flow relative to its own recent scale, the interaction between
where volume arrived and where price went, and the divergence when the two disagree. Microstructure
aggregated to 8h is a coarse instrument — establishing that anything survives that aggregation is
part of the work, not an obstacle to route around.

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
