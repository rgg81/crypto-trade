# team-01 provenance

Recorded at `2026-07-15T19:33:29Z` for family
`t01-residual-drift-funding-v1`.

## Independent origin

This design was formed independently for Top-40 V2 from first principles: gradual cross-sectional
repricing motivates medium-horizon residual continuation; removal of the common BTC component
separates relative rotation from broad beta; recent actual funding is a causal measure of carry
crowding; and bounded side tilt plus organizer-owned tail controls assign distinct bull, bear,
chop, and stress roles. No historical portfolio implementation, prior tournament strategy,
leaderboard, result, ballot, private record, final-OOS observation, or other V2 team mechanism was
used.

No empirical claim appears in the preregistration. Words such as "should" and "expected" denote a
hypothesis to be falsified. No snapshot, evaluator, `run-window`, `register-trial`, private worker,
or final worker was invoked during formation.

## Authorized material consulted

The following clean-room inputs were read and are bound here by SHA-256:

| SHA-256 | Path | Use |
|---|---|---|
| `3b8e18f110bd28ccb1c64322d8449f0f769e3d495085d77abb643dd87f014d14` | `TOURNAMENT-CHARTER-TOP40-V2.md` | objective, windows, execution, gates, sleeves, risk discipline |
| `bd0e4f70bcf335b2ac4e44ec049b89b8e8eaf4c6ac6502574d0accf12d9d9947` | `tournament/top40-v2/config.toml` | frozen machine-readable values and budgets |
| `3122ec61487207f866cb21caaa82fbc8ef27e30f0538f5c06da9ec283ac28223` | `tournament/top40-v2/METHODOLOGY-DISTILLATION.md` | causal features, chronological evidence, ablations |
| `3bcd90b08fcf2d0935f443689f68249c7d58741eb1cf90cd329eda8470634ee1` | `tournament/top40-v2/TEAM-PLAYBOOK.md` | team lifecycle and required artifacts |
| `c94614e9a9871b84985b1da74173693f65736186b2e55b8c32fc8f3cb472abcc` | `tournament/top40-v2/PHASE0-POLICY.md` | data boundary, accounting, risk ordering |
| `f239ca3fb549dace905a2079b58c51cf60d4de2b1a45daf68503c8defdc33cbc` | `.claude/agents/top40-v2-quant-researcher.md` | QR scope and clean-room obligations |
| `1a740d839cf8cdbef2322da0db17634384e9a8bb7b5e8fbb5a071e34c4ef2f7a` | `src/crypto_trade/tournament/protocol.py` | neutral decision/target interface |
| `94ea2c377c80890df299217a487eae0ac9e0365635f67d387e8b23eb68119b8e` | `src/crypto_trade/tournament/risk_policy.py` | neutral declarative control schema and boundary semantics |
| `fff67076592e337adb721b72c4c77326c3e40e396ba57217c387a8b5f58f2b5d` | `src/crypto_trade/tournament/_strategy_worker_v2.py` | neutral worker availability checks only |
| `d4fc1c381f9e69c0dbdd5b7c6e5d273e43b39c5df16a082a99af1b4ef7310ec2` | `src/crypto_trade/tournament/runner_v2.py` | neutral required-field and past-only streaming interface fragments only |
| `ea0f4659ded846978c9e5e4727594727c04a00b894365d4caccf46bc08ce950f` | `src/crypto_trade/tournament/engine_v2.py` | neutral next-open/funding/risk ordering interface fragments only |
| `bddb6a85ec7f62bf432fbaa744905b92b779941b8983d3552dde01de0a2b3fab` | `scripts/top40_v2_tournament.py` | neutral `register-family` input schema and command only |

Inside the team namespace, only `BOOTSTRAP.md`, the empty `families.jsonl` and
`experiments.jsonl`, and the organizer-provided disabled `risk_policy.json` were inspected before
writing this package.

## Mechanism identity

- Semantic fingerprint: `RDF-1|BTC30|H14-21-28|K1-3|E0.5-1|F7x0.35|Q20-25-30|G80|T5-10|D1`
- Family registration bytes SHA-256: `c48a7b54b80236f97081dec2d8f2fac26b14b7329efd9f8c63af330ce6566149`
- Fingerprint rule: SHA-256 of the exact UTF-8 bytes, including final newline, of
  `family_registration_t01_residual_drift_funding_v1.json`.
- The organizer-owned compact `families.jsonl` encoding can have a different byte hash while
  representing the exact same validated registration object.

## Reproducibility declarations

- Canonical runtime strategy seed: `20260801`, frozen by `config.toml`. This is the only seed passed
  to the worker and the only seed permitted to produce a production target.
- Team trial/search/placebo namespace: `2026080101`. It is never the worker seed and never changes
  a production target.
- Erratum: the already-registered family input's parameter label
  `strategy_seed: 2026080101` means the team trial/search/placebo namespace. It does **not**
  override the frozen config runtime seed `20260801`. The registration input and organizer family
  ledger remain byte-for-byte unchanged.
- Cross-sectional tie break: ascending symbol after score ordering.
- Randomness is absent from the strategy. The team namespace is used only to identify the
  preregistered deterministic permutation placebo and must not change a production target.
- No prefitted coefficients, serialized historical state, timestamp-to-target table, or opaque
  object is permitted.
- Candidate selection is deterministic under the formula and tie breaks in `research_brief.md`.
- Every material signal, construction, neighbor, cost, component, and risk cell will be registered
  before its result is read. The family cap is 39 of the cumulative 80 configurations.
- The private qualifier receives one frozen ticket only after a complete development pass. Final
  OOS remains inaccessible as a research view.

## Pre-data reference-cell clarification

At `2026-07-15T19:53:41Z`, before any team-01 trial, data view, evaluator call, or result, the QR
resolved the registered-domain tie for the initial implementation/test cell as `rdf-ref-001`:
`H=21d`, `K=3d`, `gamma=0.5`, `q=0.25`, and `delta=0.075`, with every other baseline constant
listed normatively in section 6.1 of `research_brief.md`. The cell uses frozen base costs, no
enabled organizer risk controls, and runtime seed `20260801`.

The choice is structural rather than empirical. `H=21` and `q=0.25` are registered central values;
`delta=0.075` was already the registered core reference; `K=3` separates medium-horizon
continuation from recent bounce/liquidation noise; and concave `gamma=0.5` rewards path coherence
without aggressively collapsing breadth. This clarification changes neither the family thesis nor
its registered parameter domain, registration input, or organizer family ledger. It does not make
the reference cell a champion and does not authorize an unregistered trial.

## Organizer collision-control guardrail

Family identity is frozen as **BTC-factor residual, path-efficient, medium-horizon continuation**.
This family may not introduce a persistence/reversal state switch, route observations into a
reversal state, or select short-horizon reversal without a formal mechanism pivot registered
before any material trial. This condition discloses no other team's mechanism and does not alter
the original registration bytes.

## Assumptions disclosed at registration

1. `BTCUSDT` remains available with sufficient causal history to serve as the common factor; the
   strategy requests flat rather than choosing a substitute after the fact.
2. Canonical funding rows are actual completed events and preserve the venue sign convention.
3. A just-closed 8h close may inform a decision, but the resulting target receives only the next
   executable open and ordinary costs.
4. The authoritative current eligible set is the only membership source; current-member history
   does not authorize a historical-membership reconstruction.
5. Flat periods caused by insufficient history are genuine outputs, not missing observations to
   be dropped from evaluation.

## Artifact ownership

The QR owns `research_brief.md`, `feature_lineage.json`, `ablations.json`, this provenance record,
and the family-registration input. Organizer-owned `families.jsonl` and run state may change only
through the single authorized registration command. `experiments.jsonl` is not edited.
