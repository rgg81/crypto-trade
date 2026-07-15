# team-02 quantitative engineering report

## Outcome

The explicit pre-data C3RP baseline is implemented. `build_strategy()` returns a fresh,
deterministic strategy and rejects every runtime seed except canonical `20260801`. It retains the
mandatory causal variable-`P` interaction between residual persistence and residual reversal,
realized funding carry, daily two-sided inverse-volatility construction, and bounded past-market
side tilt.

The implementation applies the deliberate `t-8h` feature cutoff, exact 8-hour grids, current
eligibility only, population moments, complete displacement horizons, exact average ranks,
valid-only ranks of negative cumulative realized `funding_rate`, type-7 volatility quantiles, and
the frozen 9.5% cap water-filling algorithm. Funding uses the official worker fields without cadence
scaling, ignores `mark_price`, and neutralizes duplicates, non-finite rates, and insufficient
history exactly as frozen. It returns `None` only at valid unscheduled boundaries and `{}` for
invalid or insufficient scheduled construction. It contains no fill, position, PnL, cost,
risk-state, or execution logic.

The initial `risk_policy.json` is a valid no-control policy. Preregistered future control values
are present but disabled; position/time stops and side scaling remain disabled, and
same-boundary reentry remains false.

## Verification

The narrow synthetic suite passes `11/11` tests. It covers append/corrupt/truncate invariance,
the exact extra-lag boundary, strict cumulative-funding availability, sign, duplicate/non-finite
neutralization, point-in-time membership, canonical-seed rejection, the state-interaction sign,
deterministic ranks and set ties, fresh-instance/input-order determinism, both sleeves and exposure
bounds, invalid data, scheduling actions, read-only context, and risk/config validation.

Two separate clean Python processes produced identical target bytes:

- strategy source SHA-256:
  `d8f577a8c9cedc63a2b743b3ca5ecea2e24f30e93c5a667eff01582ea3b09d0f`
- synthetic target SHA-256:
  `b9a3cb9751e3265030a8ef710661765b35f595141fc86f476636c720e0a12599`
- synthetic target: five longs, five shorts, gross `0.8514132319270987`, net
  `0.09858676807290127`

Ruff lint and format checks pass. JSON parsing and the neutral declarative risk-policy parser pass.
The detailed hashes and coverage record are in `test_evidence.json`.

## Scope and remaining evidence

QE-authored files are `strategy.py`, `frozen_config.json`, `risk_policy.json`,
`test_strategy.py`, `test_evidence.json`, and this report. The QR's pre-data numerical
clarification resolved every implementation ambiguity before code or results; no ambiguity
remains.

No snapshot byte, market observation, evaluator, trial registration, lifecycle mutation, private
window, or final window was accessed. Accordingly, next-open fills, actual central funding
cashflows, base/doubled costs, fold and regime results, long/short realized attribution, and future
risk-control action semantics remain organizer-evaluator evidence. This report makes no performance
claim and does not register a candidate.
