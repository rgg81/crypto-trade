# Team 10 convergence confirmation: volatility-target-only ablation

This candidate freezes the repaired weekly targets exactly and retains only the causal 20% annual
volatility target, capped at a scale of one. Drawdown brakes, position and time stops, and the
turnover throttle are disabled. It is the required individual-control comparison against the
previous controls-off trial and the full-control repair.

The result tests control dependence; it does not authorize a post-result parameter change. It uses
completed IS bars only and cannot access the sealed historical-OOS interval.
