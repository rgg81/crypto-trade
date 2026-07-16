# Team08 first-trial handoff

Team08 remains prospective, unregistered, and unevaluated. The first material configuration is
`vdr-core-candidate-001` with the canonical zero-argument `strategy.py:build_strategy`, seed
`20260801`, and the no-control bytes at root `risk_policy.json`. Before computing the registration
risk hash, require root bytes to equal `risk_policies/no-control.json` exactly.

Materialize and independently review the candidate-specific A5 files before registration. Their
schedule and open-to-open label horizon are both 24 hours. Run and read the no-control core before
registering any control; every gate in `control-activation.template.json` must pass. Controls cannot
rescue failure; use a separately preregistered mechanism revision/pivot or DNF instead.

The frozen lifecycle imports only root `strategy.py` and root `risk_policy.json`. For a later
policy, copy the selected immutable `risk_policies/` template byte-for-byte to root
`risk_policy.json` before commit, registration, and run, and recompute all affected hashes. Replace
the family and trial timestamp placeholders only at their actual registration events. Use only the
active A7 runtime-preload entrypoint, which preserves A5 and delegates through the exact A6
pure-crypto authority.
