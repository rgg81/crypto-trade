# Strategy API and trial workflow

This is the complete neutral interface available to every lane. It describes mechanics only and
does not prescribe or hint at a strategy.

## Candidate directory

Each trial entrypoint is
`tournament/top40-v4-r2/teams/team-NN/candidates/<candidate-id>/strategy.py`. The directory must
contain these UTF-8 text files:

- `candidate.json`, copied from the template and completed with exact preregistration metadata;
- `strategy.py`, defining callable `build_strategy()`;
- `risk_policy.json`, copied from the complete declarative template;
- `README.md`, documenting provenance, causal timing, parameters, and the prospective falsifier;
- `cleanroom-attestation.json`, copied from its template with exact identity values.

Candidate identifiers use lowercase letters, digits, dots, underscores, or hyphens and begin with
a letter or digit. The tree may contain only text source/configuration—no symlinks, generated
caches, fitted objects, data, timestamp-keyed targets, returns, scores, fills, or positions.
Every `neighborhood_coordinates` key must also exist in `material_parameters` with exactly the same
finite non-boolean numeric value. Use `{}` for controls and role checks that are not neighborhood
points. The organizer score-blind preflights the entire batch before accepting its first request;
a deterministic admission failure retires the lane without opening scores or consuming a trial.

## Entrypoint contract

The candidate has exactly one executable file, `strategy.py`. `build_strategy()` contains only a
zero-argument construction of one direct module-level class. That class contains exactly:

```python
def target_weights(self, context, *, seed):
    ...
```

The method returns either a finite `dict[str, float]`, `None`, or `{}`. A mapping requests an
explicit rebalance; `{}` requests a flat book; `None` keeps quantities until the next decision
while the central engine may still enforce exits and risk reductions. Symbols must come from
`context.eligible_symbols`. Submitted targets must satisfy gross `sum(abs(w)) <= 1.0`, absolute
net `abs(sum(w)) <= 0.25`, and `abs(w) <= 0.10` per symbol. The evaluator owns fills, fees,
slippage, participation limits, funding, and risk-policy actions.

`target_weights` is a pure stateless decision function with the exact signature shown: no
decorators/defaults, `self` access, persistent module/class/iterator state, helper delegation,
decision-time ordinal branching, top-level control flow, dynamic/dunder/file calls, RNG APIs,
packing arithmetic, arbitrary strings, nonempty literal containers, or high-capacity literals.
Calls inside the method use the frozen positive
allowlist of transparent Python/NumPy/pandas operations. The fixed `seed` argument is reserved but
random APIs are not admitted in this edition. Candidate code has no network, subprocess,
credential, repository, or host-write access during an official run.

The sanitized team kit now includes an accepted `templates/strategy.py`, the exact prose contract
in `ADMISSION-CHECKER.md`, and machine-readable `admission-call-allowlist.json`; activation tests
require the JSON call sets to equal the organizer checker. A complete unaccepted batch may receive
up to three uniform score-blind repair sessions before terminal rejection.

## Past-only context

At a decision boundary, `context.decision_time` is a timezone-aware UTC pandas timestamp.
`context.eligible_symbols` is the point-in-time weekly Top-40 membership intersected with symbols
that have an executable next open; that future open is hidden.

`context.bars` maps each eligible symbol to a read-only pandas frame containing only completed 8h
bars at or before the decision. Columns are `open_time`, `symbol`, `open`, `high`, `low`, `close`,
`volume`, `close_time`, `quote_volume`, `trade_count`, `taker_buy_volume`, and
`taker_buy_quote_volume`. Frames may have unequal history lengths; code must tolerate recent
listings and missing non-executable intervals.

`context.funding` is a read-only frame for currently eligible symbols. Its columns are
`funding_time`, `symbol`, `funding_rate`, `mark_price`, and `settlement_time`; all observations are
strictly earlier than the decision. `context.auxiliary` is empty. A strategy must not mutate any
context frame.

The first accepted candidate establishes the stable mechanism-family label. Parented
`control-ablation` and `role-check` candidates may use more specific descriptive mechanism prose;
all other within-family variants normally repeat the family label. A genuine family change uses
`mechanism-pivot`, is allowed once, and starts a new parent epoch. No-op and second pivots fail
before acceptance.

## Accepted trials and certificates

The organizer accepts a trial into the append-only journal before market access; a runtime failure
still consumes the slot. The sequential broker is the sole trial ingress: it launches the isolated
research phase, binds exact source receipts, consumes the outbox, and only then invokes evaluation.
Operators run one complete lane with:

```bash
CRYPTO_TRADE_TOP40_V4_EDITION=r2 PYTHONPATH=src \
  .venv/bin/python scripts/top40_v4_r2_team_broker.py run-team team-NN
```

Keep each returned `request_record_sha256`. At acceptance, the organizer also writes a score-free
receipt under `reports-top40-v4-r2/is/team-NN/receipts/`; this preserves the request hash even when
execution fails or is interrupted. The research certificate has exactly the seven keys shown in
`templates/research-certificate.json`; each value is a nonempty list of unique request hashes whose
candidate tags include that key, and their union must cover every accepted trial.
One trial may cover multiple preregistered cells. Nomination or evidence-backed retirement requires
at least eight accepted trials. Nomination additionally requires three distinct formation
horizons, two rebalance horizons, three control profiles, and five successful, distinct local
neighborhood points that bracket every nominee coordinate. See `config.toml` for the frozen pass
fraction, median 2x-cost Sharpe, IS floors, and the twelve-trial cap.

An exact sign-inversion candidate sets `parent_candidate_id` to a cited baseline, keeps the same
mechanism, formation horizon, rebalance horizon, control profile, and risk policy, and returns the
negative of every baseline target while preserving its explicit-rebalance/hold decisions. The
organizer verifies this equality directly from the two immutable target artifacts at nomination;
a label alone is not evidence.

The team writes its completed certificate only to `work/research-certificate.json` and references
it from `outbox/decision.json`. The broker validates and copies exact bytes into the organizer-only
certificate namespace before nomination. No lane is obliged to nominate a candidate that fails the
frozen gates.

An individual IS summary is intentionally provisional: its `neighborhood_stability` gate remains
false because the organizer can validate the multi-trial certificate only at nomination. Assess
the other frozen gates using the lane's final accepted-trial count; a valid nomination recomputes
the complete selection with the certified neighborhood enabled.
