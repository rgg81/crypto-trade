# Team10 first-trial handoff

Team10 remains prospective, unregistered, and unevaluated. The first material configuration is
`t10-rtre-core-v1` with canonical `strategy.py:build_strategy`, seed `20260801`, and the no-control
bytes at root `risk_policy.json`. Before computing the registration risk hash, require root bytes to
equal `risk_policies/no-control.json` exactly.

Run and read that core before registering any control. It must have base return >0 and Sharpe >=0.75,
doubled return >0 and Sharpe >=0.35, at least four of six positive folds, positive bull/bear/chop returns, positive
long-bull/short-bear/combined-chop attribution, and active long and short sleeves. Controls cannot
rescue any failed numeric threshold in `qualification_thresholds.json`; use a separately
preregistered mechanism revision/pivot or DNF instead.

The lifecycle imports only root `strategy.py` and root `risk_policy.json`. For a later policy, copy
the selected immutable `risk_policies/` template byte-for-byte to root before commit, registration,
and run, and recompute all affected hashes. Replace family/trial timestamp and hash placeholders only
at the actual lifecycle events. Use the active A7 runtime-preload entrypoint; it delegates the frozen
A5 score protocol and A6 authority. Never invoke the direct A5 script for a result-bearing command.

Non-core mechanism and neighbor JSON files are declarations only. Before any such registration,
materialize the declared override into separately hash-bound executable strategy/config bytes and
prove the canonical zero-argument builder exposes it. Freeze all 12 definitions before the center
result, register all 12 materialized neighbors before reading the first neighbor result, and withhold
qualification until complete aggregation passes `neighbor_staging_plan.json`.
