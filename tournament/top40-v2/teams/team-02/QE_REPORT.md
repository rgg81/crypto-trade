# Team 02 FIR engineering report

## Implemented reference

`team-02-fir-reference-001` implements the exact no-control reference for proposed final-pivot
family `team-02-funding-inventory-relaxation-v1`. It has not been registered, run, or measured.

The strategy uses only realized funding strictly before each decision, exact closed 8-hour prices
through `t-8h` for a risk filter, and current organizer eligibility. It computes 21-day funding per
day and recent-three-day versus prior-eighteen-day relaxation, excludes the highest-volatility
fifth, and applies the fixed score `-0.75*rank(level)+0.25*rank(relaxation)`. Price returns never
enter the score.

At every fixed three-day rebalance it requires 30 features before and 24 after filtering, selects
the top/bottom quarter with at least six names per side, and requests equal 0.20 side budgets under
a 0.03 name cap. Gross is at most 0.40; capacity that cannot be allocated remains cash. It refuses
a portfolio whose selected short funding level does not exceed selected long funding level.

`risk_policy.json` is fully disabled and identified as `team-02-fir-reference-no-control`. The
lower gross, cap, breadth, volatility exclusion, and schedule are preregistered construction—not an
organizer risk overlay or a post-result rescue.

## Verification status

The organizer ran the synthetic suite twice, serially, after formatting: **11 passed in 2.02
seconds**, then **11 passed in 1.97 seconds**. Ruff check also passes. The suite covers exact funding
windows and calendar-day normalization, relaxation sign, price-risk window, rank ties, volatility
filtering, sleeve carry ordering, future append/corrupt/truncate invariance,
stale/duplicate/invalid funding, missing/duplicate/corrupt prices, membership, input order,
allocation, clock, seed, context immutability, frozen config, and no-control policy.

Exact commands, timings, and final team-file hashes are recorded in `test_evidence.json`. No
performance claim is made by implementation or synthetic tests.

## Scope

Only Team 02-local source, documentation, JSON, and tests were changed. Existing organizer-owned
family/experiment ledgers, reports, shared state, public infrastructure, and every prohibited data
domain were left untouched. No tournament evaluator or backtest has run for this candidate.
