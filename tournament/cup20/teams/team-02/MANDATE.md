# Team 02 — Breakout / channel-position

Lane id: `breakout-channel-position`
Playbook: `tournament/cup20/TEAM-PLAYBOOK.md` (read it before you write any code)
Workspace: `tournament/cup20/teams/team-02/`
Data root: `data/cup20/is/`

## Mechanism intent

Where a coin sits inside its own recent range is a different statement from how fast it has been
moving: a breach of a multi-week extreme is the market clearing a level, and levels are where stops,
liquidations and resting orders cluster. Your lane is position-in-channel and range breach as the
signal itself — rolling extremes, distance to a trailing high or low, normalised location within a
band — not as a filter bolted onto a trend signal. Expect false breaks to be the entire problem;
what distinguishes a break that carries from one that snaps back is the research question.

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
