# Team 05 final LDM pivot-02 provenance

Status: prospective, unregistered, and without LDM development evidence.

The original `team05-causal-residual-trend-reversal-v1` family and seven completed material trials
remain immutable in `families.jsonl`, `experiments.jsonl`, canonical `score-adapters/team05-crtr-*`
files, organizer runner records, and reports. Its fixed combined candidate failed quarter, fold,
trial-adjusted-confidence, chop, worst-regime, and concentration gates.

Pivot-01 `team05-up-down-capture-convexity-v1` then registered and ran one exact no-control core,
`team05-udcc-pivot01-core-v1`, as material trial 8. It produced net Sharpe 0.558394, annualized
return 0.058688, Calmar 0.513252, drawdown 0.114344, doubled-cost Sharpe 0.476160, and positive
quarter fraction 0.714286. It nevertheless failed noncompensatory central gates: Sharpe was below
0.75, only two regimes had positive Sharpe, and worst-regime Sharpe was -0.408613. Its failure audit
is commit `8f9fc0b2`; controls, neighbors, and same-family replacements were forbidden.

LDM is the separately documented final mechanism pivot. It replaces conditional price capture with
temporal migration in unsigned range per contemporaneous quote-volume share. It does not reuse or
invert CRTR or UDCC scores.

The active authority chain is:

- Amendment 0005: direct declared A5 score boundary and diagnostic manifest;
- Amendment 0006: certified point-in-time native-crypto-only membership;
- Amendment 0007: pinned runtime preload at SHA
  `8a4ada10176d2606df3f358fc188e21b45153ad9a7270f36908736f03322a3a9`.

Amendment 0008 is fully consumed historical authority for the scientifically identical CRTR
infrastructure replacement. It must not appear in LDM registration.

LDM lifecycle order is complete materialization commit, executable-source manifest first-add,
independent semantic review first-add, score manifest first-add, A7 `pivot-team`, final source
fingerprint, A7 `register-trial`, then one A7 development run. No private or OOS data may be read
before formal development qualification. A failed final core makes Team 05 DNF.
