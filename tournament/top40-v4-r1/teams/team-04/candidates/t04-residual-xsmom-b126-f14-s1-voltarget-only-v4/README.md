# Team 04 fourteen-day residual momentum: volatility-target-only ablation

This individual-control candidate keeps the frozen 14-day residual-momentum signal, causal 126-day
beta estimate, one-day skip, balanced sleeves, weekly schedule, and 0.44 gross target unchanged.
The only active optional organizer control is the existing no-leverage 22% annualized volatility
target with a 42-day trailing window. Drawdown brakes, position stops, time stops, and the turnover
throttle are disabled.

The full-control 14-day parent was Team 4's strongest frozen formation point, but it still lost on
the short sleeve and in chop. This run tests whether the gentlest isolated control preserves its
four profitable folds and cost resilience while avoiding interactions that truncate relative
winners and losers. It is falsified if Sharpe and role breadth do not improve, or if drawdown,
turnover, costs, or edge density become unacceptable.

This is a diagnostic control ablation outside the formation neighborhood and makes no performance
claim. It uses completed pure-crypto bars only and never accesses the sealed OOS interval.
