# team-01 QE implementation report

Status: **rdf-core-h14-k3-g05 implemented and synthetically verified once; not registered or evaluated**

The implementation remains a faithful, stateless translation of the preregistered
`t01-residual-drift-funding-v1` mechanism. `build_strategy()` now returns the exact next core cell
authorized after the third material result: `H=14d`, `K=3d`, `gamma=0.5`, `q=0.25`,
`delta=0.075`, runtime seed `20260801`, base costs, and no enabled organizer risk controls.
Relative to solvent baseline `rdf-ref-001`, the sole material coordinate change is the already
registered horizon value `H: 21d -> 14d`. Every other signal, construction, execution, risk, and
seed coordinate matches that baseline. Any other material cell still requires a fresh research
decision and preregistration.

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

## Synthetic verification

The organizer ran the evaluator-free suite twice, serially: **14 passed in 2.68 seconds**, then
**14 passed in 2.66 seconds** after pinning the exact target hash. Each suite launched the official
namespaced V2 strategy worker twice on synthetic data; all four worker outputs matched direct
targets. The exact canonical synthetic target SHA-256 was
`ebf2cce8ba380674f001cd852dcdb7cc6decbaaeed40ab07bd8ebb677e12977f`.

Coverage retains the causal and worker-contract checks of the preceding implementation and now
reconstructs both the exact 14-day residual window and the otherwise identical 21-day solvent
baseline. Those signal values match their respective formulas and differ in the synthetic fixture.
The suite also binds `frozen_config.json` to the one-coordinate H14 change and the byte-identical
no-control risk policy.

Candidate-specific evidence and final team-file hashes are recorded in `test_evidence.json`.

## Deliberately pending organizer evidence

No snapshot bytes, tournament evaluator, lifecycle command, trial registration, development
metric, private window, or final window was accessed. Consequently base/doubled-cost returns,
folds, regime/sleeve attribution, turnover, actual funding cashflows, next-open fills,
participation, delisting behavior, and risk-action ordering are not claimed here. Those are
central-engine properties and material tournament evidence; they remain pending preregistration
and organizer execution. The no-control core cell does not exercise stop, brake, cooldown, or
same-boundary reentry events. Planned risk controls remain separate registered ablations.

The organizer-private Amendment 0001 score diagnostic remains required after a completed run:
Team 01's own falsifier treats missing pooled or per-fold score IC as failure. No implementation
ambiguity remains after the frozen post-result decision authorizing
`rdf-core-h14-k3-g05` as the sole next cell.
