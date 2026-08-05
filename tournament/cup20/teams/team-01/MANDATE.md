# Team 01 — Slow per-coin time-series momentum

Lane id: `slow-per-coin-time-series-momentum`
Playbook: `tournament/cup20/TEAM-PLAYBOOK.md` (read it before you write any code)
Workspace: `tournament/cup20/teams/team-01/`
Data root: `data/cup20/is/`

## Mechanism intent

Crypto perpetuals trend because flow, funding and leverage are reflexive: a move that persists pulls
in more of the flow that caused it, and a 24/7 tape gives that feedback no overnight gap in which to
reset. Your lane is the slow end of that effect — per-coin, own-history trend measured over weeks to
months, with no cross-sectional comparison anywhere in the signal. The question is not whether
momentum exists; it is whether slow own-price persistence still pays 7.5 bps a side on twenty of the
most liquid names in the market.

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
