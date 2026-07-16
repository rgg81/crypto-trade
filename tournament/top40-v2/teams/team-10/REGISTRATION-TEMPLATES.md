# Team 10 registration-template instructions

All adjacent `*.template.json` files are prospective drafts. A 64-character zero value is a
sentinel, not a real hash, and each `REPLACE_WITH_ACTUAL_REGISTRATION_TIMESTAMP_Z` value is an
intentionally invalid timestamp placeholder. These files must never be passed to a lifecycle
command unchanged.

After independent static review, the organizer must materialize and hash the complete executable
source set, exact config, exact strategy, and exact risk policy. It must replace every sentinel and
register the family before registering the first material trial through
`scripts/top40_v2_tournament_score_diagnostics_v5.py`.

The first trial is exclusively the reference signal with no-control bytes at root
`risk_policy.json`. Verify exact equality with `risk_policies/no-control.json` before computing the
risk hash. Do not register a control unless the completed core has passed every broad positive
activation minimum. For any later policy, first copy its immutable template byte-for-byte to root,
commit, and recompute every risk/source binding; the lifecycle never selects a side path.

The walk-forward and parameter-neighborhood manifest templates may be materialized only from
centrally produced artifacts after the exact candidate is frozen. Template paths do not claim that
those artifacts exist. `families.jsonl` and `experiments.jsonl` are organizer projections and must
never be hand edited.
