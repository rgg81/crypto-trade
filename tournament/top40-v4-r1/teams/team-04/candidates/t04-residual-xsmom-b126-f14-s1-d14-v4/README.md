# Team 04 fourteen-day residual momentum: slower-rebalance check

This candidate keeps the strongest frozen 14-day residual formation, causal 126-day beta estimate,
one-day skip, balanced sleeves, 0.44 gross target, and original full protective controls. Its only
signal-level change is to refresh ranks every fourteen days at 00:00 UTC, anchored to the Monday
Unix epoch week, instead of every Monday.

The slower schedule tests whether weekly rank churn is disrupting continuation and worsening the
chop and short roles. It is falsified if it fails to improve those roles, worst-fold Sharpe, and
aggregate Sharpe, or if it sacrifices four-fold base and doubled-cost breadth. This is a diagnostic
rebalance-grid point outside the frozen formation neighborhood and makes no performance claim.

All decisions use completed pure-crypto bars, execute at the next eligible open, and never access
the sealed OOS interval.
