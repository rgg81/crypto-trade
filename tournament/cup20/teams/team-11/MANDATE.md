# Team 11 — Calendar and settlement-clock seasonality

Lane id: `calendar-settlement-clock-seasonality`
Playbook: `tournament/cup20/TEAM-PLAYBOOK.md` (read it before you write any code)
Workspace: `tournament/cup20/teams/team-11/`
Data root: `data/cup20/is/`

## Mechanism intent

The 8h decision grid is not arbitrary — it is the funding settlement clock, and around it sit
predictable flows: positioning into settlement, unwinding after, plus weekday and time-of-day
patterns that persist because the participants creating them keep human schedules. Your lane is that
seasonality: intra-day slot effects, day-of-week effects, settlement-boundary effects, and their
interactions. Seasonality is the easiest place in this tournament to fit noise, which makes the
phase-offset sweep and the declared neighbourhood load-bearing for you in a way they are not for
anyone else.

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
