# team-01 QE implementation report

Status: **rdf-core-h21-k1-g05 implemented and synthetically verified; not registered or evaluated**

The implementation is a faithful, stateless translation of the preregistered
`t01-residual-drift-funding-v1` mechanism. `build_strategy()` returns a fresh strategy fixed to
the QR's frozen next core cell: `H=21d`, `K=1d`, `gamma=0.5`, `q=0.25`, `delta=0.075`, runtime
seed `20260801`, base costs, and no enabled organizer risk controls. The sole change from rejected
reference `rdf-ref-001` is the already-registered skip choice from three days to one. The family
remains parameterized in `StrategyParameters`; any other material cell still requires its own
registration before execution.

## Implementation boundary

- Strategy inputs are limited to `decision_time`, past-closed 8h closes, actual funding rows with
  `funding_time < decision_time`, and the current organizer-delivered eligible symbols.
- BTC is only the common factor and direction input. It is never ranked or replaced.
- The implementation recomputes the rolling beta, residual path statistic, funding cross-section,
  robust ranks, and sleeve targets at each scheduled boundary. It contains no learned full-window
  state, target table, position/PnL state, filesystem access, network access, or subprocess call.
- It returns `None` away from 00:00 UTC, `{}` when scheduled construction is invalid, and a finite
  two-sided eligible-only mapping otherwise. Gross is 0.80, absolute net is at most 0.15 for this
  frozen tilt, and each symbol is capped at 0.09.
- Funding is pre-sliced and grouped once per boundary before per-symbol transforms. This is a
  computational optimization only; it does not alter the registered formula or availability rule.

## Evidence

The evaluator-free synthetic suite passed twice in separate Python processes: **12 passed, 0
failed**. Both processes reproduced canonical synthetic target SHA-256
`89013d78cea4a81462a17528a7c48d4d6c7857b2a9825d9d8bb66032d934bc12`.

Coverage includes future truncation/append/corruption invariance, ignored future opens, strict
funding cutoff, membership removal, funding sign, deterministic score ties, daily hold behavior,
runtime seed enforcement, missing/duplicate/NaN/Inf rejection, two-sided flat fallback, and
gross/net/symbol bounds. `risk_policy.json` parses through the neutral V2 risk-policy interface and
has every optional control disabled. Static V2 team-source text validation also passed.

Exact commands, dependency versions, source hashes, and the complete check list are recorded in
`test_evidence.json`.

## Deliberately pending organizer evidence

No snapshot bytes, tournament evaluator, lifecycle command, trial registration, development
metric, private window, or final window was accessed. Consequently base/doubled-cost returns,
folds, regime/sleeve attribution, turnover, actual funding cashflows, next-open fills,
participation, delisting behavior, and risk-action ordering are not claimed here. Those are
central-engine properties and material tournament evidence; they remain pending preregistration
and organizer execution. The no-control core cell does not exercise stop, brake, cooldown, or
same-boundary reentry events. Planned risk controls remain separate registered ablations.

No implementation ambiguity remains after the QR's frozen `rdf-ref-001` development review and
one-factor next-cell decision.
