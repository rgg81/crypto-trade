# Top-40 V2 Amendment 0008 — Team 05 infrastructure-only replacement

Status: **DRAFT — INDEPENDENT REVIEW AND IMMUTABLE FREEZE REQUIRED**

## Incident and decision

Team 05 preregistered `team05-crtr-core-v2` under the already accepted
`team05-causal-residual-trend-reversal-v1` family. Its development run reached the frozen strategy
worker but terminated before strategy initialization with:

```text
StrategyExecutionError: ModuleNotFoundError: No module named
'crypto_trade.tournament.score_adapter_protocol_v5'
```

The terminal result contains no model metrics and no artifacts. Amendment 0007 subsequently fixed
that exact frozen-worker protocol-availability defect, but explicitly did not authorize a retry.
The immutable journal also forbids replaying a candidate that already has a terminal result.

This amendment authorizes exactly one administrative replacement identity:

- team: `team-05`;
- existing family: `team05-causal-residual-trend-reversal-v1`;
- failed historical candidate: `team05-crtr-core-v2`;
- replacement candidate: `team05-crtr-core-v2-infra-r1`;
- stage: visible development only;
- active command authority: Amendment 0007.

The replacement is not a new mechanism family, a mechanism pivot, a control activation, a model
revision, or a budget refund. The failed v2 registration, reservation, result, accounting, and
journal records remain immutable and charged. The replacement becomes ordinary material trial 2.

## Exact incident authority

The authorization is conditional on all of these existing bytes and journal facts remaining exact:

| Authority | SHA-256 or identity |
| --- | --- |
| v2 registration input | `a1d3535e033f656e0f8dd3e62046f8b4b6488688d79ecbd97c9770f89282e08c` |
| v2 registration event | `c4727f39271d9cde42935de53d34a0d1ce5f4e7cfeca2db9b282d9a8bc0488c9` |
| v2 reservation | `94ad47e6899207eaa5e245720555eeb204858320f6866177304feca5a49b0ea7` |
| v2 terminal-result event | `4fe7e3d84b41899b84513d67f17db215d6b59c165cbd379bd598fc2f3f21d5a2` |
| organizer registration record | sequence 25, `5d4b00663128fe0aec307ef0a6a532c052b7a84a5d53fae2c685b7f974444701` |
| organizer result record | sequence 26, `15e4d3453ee1fdaae0a4f1439f8a5bf57c4cf16c99fa73ff9992c29fa64aa09f` |
| recorded metrics/artifacts | both empty objects |
| recorded CPU / wall time | `0.0004992790838888888` / `0.0003490867155616999` hours |

The current organizer journal is an immutable extension of those two records. At this draft's
boundary it contains 61 records (sequences 0 through 60) and has head
`fd0bc861a74c6c895f796bccebec44b913dba0814550f97215fdbadeb98ae6fd`.
Later lawful appends may extend that prefix; they may not alter or remove the incident records.

## Scientific immutability

The replacement must preserve the complete CRTR scientific candidate:

- the same registered family and economic thesis;
- the same strategy math, feature horizons, score transform, score direction, schedule, label,
  seed, parameters, portfolio construction, risk policy, and falsifier;
- the same no-control root risk bytes;
- no performance-derived threshold, sign, weight, eligibility, or feature change;
- no optional control, neighbor, ablation, or private observation before the replacement core earns
  it under the existing gates.

Only the minimum administrative bytes required to introduce the new identity are permitted:

- candidate identity/whitelist declarations;
- identity assertions and documentary bindings in tests and templates;
- the new Amendment 0008 binding;
- fresh candidate-bound A5 manifests, review, and trial registration.

Any change to signal logic, model parameters, risk bytes, score schedule/label, or economic thesis
voids this authorization and requires ordinary family/pivot governance instead.

## Fresh A5 and registration ancestry

The v2 A5 files cannot be renamed or reused as the replacement's controls. The replacement must
first-add, in strict commit order:

1. `team05-crtr-core-v2-infra-r1.executable-source-manifest.json`, covering the complete final
   executable dependency set;
2. an independent
   `team05-crtr-core-v2-infra-r1.semantic-coupling-review.json` approving the exact immutable
   strategy and executable manifest;
3. `team05-crtr-core-v2-infra-r1.json`, binding the approved semantic review and unchanged 72-hour
   score schedule/label; and
4. a new trial registration with the exact score-manifest opt-in, current source bundle, A7 active
   authority, and frozen Amendment 0008 authority.

All ordinary A5 candidate/source/history checks remain active. The replacement registration is a
normal journal append and consumes material trial 2. Exactly one A7 `run-window development` is
authorized for the replacement. A terminal replacement result cannot be replayed under this
amendment.

## A6 pure-crypto authority

Amendment 0006 remains mandatory before and after every delegated command. Eligibility remains
native crypto only. Stablecoin bases, leveraged tokens, tokenized or synthetic TradFi securities,
metals, commodities, equities, ETFs, indexes, FX, premarket products, and other direct TradFi
exposures remain excluded even when Binance lists a perpetual. Team 05 may consume only the exact
organizer-provided eligible set and may not locally expand or reclassify it.

## Why no new dispatcher is needed

Amendment 0007 already provides the reviewed runtime repair and mechanically accepts a newly
preregistered candidate under an existing family. What A7 withholds is the *authority* to treat an
administrative replacement as eligible. Amendment 0008 supplies only that explicit, exact-byte,
one-shot authority. It changes no command implementation and therefore requires no replacement
dispatcher or integration patch.

Activation occurs only when an independent reviewer approves the exact draft bytes and a later
immutable freeze binds the draft commit, review commit, parent authorities, incident records,
candidate identity, and one-shot invariants. Before that freeze, no replacement source edit,
manifest, registration, or run is authorized.

## Required review and freeze checks

Independent review must confirm:

1. the failure was infrastructure-only and produced no model metric or artifact;
2. the v2 terminal history remains immutable and charged;
3. the replacement uses the same family and is not a pivot;
4. no scientific, risk, score, universe, budget, or gate change is authorized;
5. the new candidate must complete fresh A5 first-add ancestry;
6. the replacement is material trial 2 and receives exactly one run;
7. A7 and A6 remain exact active parents; and
8. the freeze itself, not this draft, is the activation boundary.

