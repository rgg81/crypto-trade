# Top40-v3 orchestrator protocol

The organizer's job is not to celebrate ten honest failures. It is to make every team exhaust a
credible research path before it is allowed to nominate a model, while preserving causal and
blind evaluation.

## Director's opening challenge

Every team is expected to produce a complete, cost-aware trading system—not merely an interesting
raw signal. A first negative lab is a diagnosis, not a submission. Teams may use causal volatility
targeting, turnover control, position and portfolio stops, drawdown brakes, cooldowns, exposure
caps, and regime routing from the start. The objective is a strong combined IS record that has
also remained positive in sealed validation and at doubled costs.

Teams should be bold about the hypothesis and ruthless about the evidence. If the sign is wrong,
test the inverse. If the horizon is wrong, move it. If market beta hides the mechanism, neutralize
it. If turnover consumes the edge, slow or buffer it. If one state causes the losses, identify a
causal state variable and reduce risk there. Do not decorate a dead signal with complexity.

## Mandatory response ladder

After each material training result, the organizer assigns a status and a concrete next action:

- **Red — net or doubled-cost Sharpe at or below zero.** The team cannot reserve validation or
  submit. It must audit lag/sign, attribute costs and regimes, test the predeclared inverse and
  simpler baseline, then either repair the mechanism or kill it.
- **Amber — positive but below a core floor.** The organizer identifies the two largest
  qualification gaps. The team runs targeted horizon, neutralization, portfolio-construction, and
  risk-control experiments rather than an undirected search.
- **Green — every public core floor met in training.** The exact bytes may consume a sealed
  validation probe. A failed probe returns the team to a targeted repair step while budget remains.
- **Nomination-ready — matching train and validation checkpoints are positive, doubled-cost
  positive, and the stitched development assessment is core-eligible.** Only this status may
  create a submission lock.

Every status, diagnosis, requested experiment, and result is appended to the organizer journal.
The organizer may challenge a team to simplify or pivot, but cannot supply another team's source,
private metrics, or future data.

Canonical result commands run one at a time. Teams may reason, review code, and prepare experiments
concurrently, but full train, validation, private, and final evaluations are serialized to keep
resource use predictable and prevent cross-run interference.

## Grandfathered incumbent lane

The organizer recognizes exactly four historical incumbents, in Teams 04, 05, 07, and 09, as
listed in [`INCUMBENT-CHALLENGER-POLICY.md`](INCUMBENT-CHALLENGER-POLICY.md). For each nested port,
the selected entrypoint and adjacent `risk_policy.json` are one hash-bound candidate unit. The
organizer must verify its V2 provenance and disclosed V3 port changes before accepting a run.

An incumbent's first V3 training request is an ordinary logged material trial. It consumes the
same team journal and, when applicable, the same opening or comeback probe budget as any
challenger. Historical performance cannot assign green, nomination-ready, public-core, private,
or final status. The exact port must independently clear the ordinary hard gates and produce
strictly positive net Sharpe, annualized return, and doubled-cost Sharpe on both training and
validation before it can be nominated. There remains only one nomination per team.

The organizer keeps the incumbent visible as the historical benchmark while challengers are
developed. It moves the preferred lane to a challenger only when standardized logged V3 evidence,
not novelty or narrative, supports replacement. This is coaching and resource discipline, not a
new hidden gate; formal eligibility and ranking remain exactly those in the charter. Collision
guards remain binding for new designs, but they do not retroactively erase the four explicitly
grandfathered incumbents or create a waiver for their descendants.

## Competition pressure

A public training leaderboard reports core eligibility, robustness score, turnover, drawdown, and
the two largest open gaps. Validation reports are limited to the owning team until the public
cohort freezes. Research novelty earns recognition but never compensates for weak performance.

One nominee per team enters the ranking. This prevents a prolific team from occupying the cohort
with correlated variants. The top four core-eligible teams advance. If fewer than three exist,
the comeback round opens automatically: unqualified teams receive a focused mechanism review and
two additional validation probes, with unchanged quality floors.

## Stop conditions

A team stops only when it locks a nomination, exhausts both opening and comeback research budgets,
or proves its mechanism is falsified. Negative training output is never promoted as a tournament
submission. An integrity, causality, solvency, or universe failure is terminal for the affected
candidate and cannot be coached around.
