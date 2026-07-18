# Top40 V3 Amendment 0001: UTC metric-bound integration

Amendment ID: `top40-v3-amendment-0001-utc-metric-bounds`

Status: prospective; inactive until the integration freeze verifies and is committed

## Decision

Adopt one additive evaluator adapter and a new organizer entrypoint. The immutable parent runner,
Phase-0 record, configuration, journal, and state schemas remain unchanged. Replace the original
organizer entrypoint with an exact fail-closed tombstone so it cannot be re-enabled by deleting the
activation sentinel; its historical bytes remain bound in the evidence commit.

The adapter performs exactly two representation corrections:

1. Convert both metric-slice boundaries to explicit UTC timestamps before delegating to the frozen
   metric implementation.
2. Publish the scored-window start and end as date-only ISO values required by the frozen coaching
   schema.

The amended evaluator authority hashes the parent evaluator, adapter, integration module, and
active integration-freeze bytes. Every later journal request and result is therefore distinguishable
from the defective parent evaluator.

## Unchanged tournament semantics

This amendment does not change:

- the pure-crypto universe or A6 audit;
- any input row, split, warm-up, membership, contract, seed, or causality boundary;
- strategy source, parameters, candidate identity, or risk policy;
- fees, slippage, funding, execution, exposure limits, or solvency rules;
- metric formulas, bootstrap settings, regimes, core floors, ranking, or tie-breaks;
- trial, validation-probe, nomination, private, or final-OOS budgets;
- the rule that every training invocation consumes a material trial; or
- any sealed-data or disclosure rule.

## Parent and activation boundary

The integration must verify the original Phase-0 authority and the first two journal records as an
exact prefix. Activation is permitted only from journal sequence 2 with head
`1737d4431198669b1d5d64962e6d04052620a6e69175eb8f20b029f89b539d64`, Team 04 run/trial count 1,
all other team counts zero, no pending request, and the incident source archive intact.

Future journal records may extend that prefix—including a normal accepted request that is pending
while its runner executes—but cannot replace it. The old entrypoint is a fixed tombstone; the
amendment entrypoint is the sole prospective organizer authority.

## Freeze requirements

Activation requires, in order:

1. preserved historical evidence;
2. exact implementation-file hashes and a unique implementation commit directly following the
   evidence commit;
3. an independent scope and semantics review;
4. a serialized rerun of the complete parent targeted suite;
5. additive amendment regression and metrics-to-coaching tests;
6. a fresh zero-violation A6 pure-crypto audit;
7. stable parent Phase-0 scope before and after testing; and
8. an exactly-once canonical integration-freeze record binding all evidence above;
9. a unique commit containing only that integration freeze and directly following the
   implementation commit.

The freeze command produces only a provisional record. Activation begins only after requirement 9
is independently verified. Any mismatch fails closed. Amendment activation itself appends no
laboratory event and releases no metric.
