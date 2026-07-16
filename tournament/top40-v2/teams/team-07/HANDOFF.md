# Team07 first-trial handoff

Team07 remains prospective, unregistered, and unevaluated. The first material configuration is
`team07-shock-diffusion-center-v1` with the canonical zero-argument `strategy.py:build_strategy`,
seed `20260801`, and the no-control bytes at root `risk_policy.json`. Before computing the
registration risk hash, require root bytes to equal `risk_policies/no-control.json` exactly.

Run and read that core before registering any control. It must have positive ordinary- and
doubled-cost return/Sharpe, at least four positive folds, positive bull/bear/chop returns, positive
long-bull/short-bear/combined-chop attribution, and active long and short sleeves. Controls cannot
rescue failure; use a separately preregistered mechanism revision/pivot or DNF instead.

The frozen lifecycle imports only root `strategy.py` and root `risk_policy.json`. For a later
policy, copy the selected immutable `risk_policies/` template byte-for-byte to root
`risk_policy.json` before commit, registration, and run, and recompute all affected hashes. Use only
the active A5 superset entrypoint, which delegates through the exact A6 pure-crypto authority.

