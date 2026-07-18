# Top40 V3 Amendment 0001 implementation review

Review type: independent static scope, lifecycle, and scientific-semantics review

Decision: representation correction approved; activation conditional on every integration control
below passing in the fresh freeze

## Confirmed

- The parent runner remains byte-identical to its Phase-0 hash
  `b4704dce1f2bfb7f624feea16bf1ec0bbc9ce345995856741551bb6d57c2ecc3`.
- Explicit UTC bounds preserve the intended inclusive daily slice.
- Date-only scored-window labels match the frozen coaching schema.
- The correction does not alter returns, execution, costs, risk, data, thresholds, or strategy
  bytes.
- Amendment implementation names are deliberately separate from the frozen parent implementation.

## Required activation controls

The integration freeze must prove all of the following:

1. A Phase-0-discovered activation sentinel invalidates the historical Phase-0 command path, while
   an exact hard tombstone independently makes the historical organizer entrypoint fail before it
   can append a new request.
2. The amended entrypoint independently verifies the canonical parent record against every one of
   its historical scope paths and authorizes only the exact frozen amendment delta.
3. The evaluator identity composes the parent evaluator, adapter, integration module, and
   integration-freeze hashes without a circular self-hash.
4. Runtime substitution is private, serialized, temporary, and restored after success or any
   `BaseException`; pre-import or concurrent replacement fails closed.
5. Regression evidence covers every authorized stage, the complete metric result (including
   stressed Sharpe, regimes, and both confidence intervals), and a metrics-to-coaching train
   canary.
6. At freeze time, the live laboratory journal is the exact two-record incident prefix, has no
   pending request, and projects Team 04 run/trial count 1 with all other counts zero. After
   activation, append-only extensions—including one normal pending request—remain valid.
7. The incident source archive, original Phase-0 record/test output, config, data authority, and A6
   zero-violation report remain exact.
8. The new command surface is closed; the freeze remains provisional until it is uniquely committed
   as the only delta directly after the implementation commit; activation itself emits no lab
   event. Team 04's next normal invocation becomes run sequence 2 and material trial 2.

Until those assertions are tested and bound into `integration-freeze.json`, Amendment 0001 is not
an active tournament authority and no market evaluation may run through it.
