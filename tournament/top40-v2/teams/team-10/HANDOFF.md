# Team10 first-trial handoff

Team10 remains prospective, unregistered, and unevaluated. The first material configuration is
`t10-rtre-core-v1` with canonical `strategy.py:build_strategy`, seed `20260801`, and the no-control
bytes at root `risk_policy.json`. Before computing the registration risk hash, require root bytes to
equal `risk_policies/no-control.json` exactly.

Run and read that core before registering any control. It must have positive ordinary- and
doubled-cost return/Sharpe, at least four positive folds, positive bull/bear/chop returns, positive
long-bull/short-bear/combined-chop attribution, and active long and short sleeves. Controls cannot
rescue failure; use a separately preregistered mechanism revision/pivot or DNF instead.

The lifecycle imports only root `strategy.py` and root `risk_policy.json`. For a later policy, copy
the selected immutable `risk_policies/` template byte-for-byte to root before commit, registration,
and run, and recompute all affected hashes. Replace family/trial timestamp and hash placeholders only
at the actual lifecycle events. Use the active A5 superset entrypoint and delegated A6 authority.

Non-core mechanism and neighbor JSON files are declarations only. Before any such registration,
materialize the declared override into separately hash-bound executable strategy/config bytes and
prove the canonical zero-argument builder exposes it.
