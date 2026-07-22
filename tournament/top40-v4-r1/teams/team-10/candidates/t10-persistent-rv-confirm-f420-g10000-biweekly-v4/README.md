# Team 10 convergence confirmation: biweekly refresh

This candidate changes only the repaired model's refresh schedule. It recomputes targets every
fourteen days at Monday 00:00 UTC, anchored to 1970-01-05, while the full organizer controls remain
active between decisions. The formation, pair-stability, hedge, spread, convergence-confirmation,
and proportional risk-cap settings exactly match the weekly repair.

This is the preregistered second rebalance horizon and directly tests whether the weekly result
depends on avoidable target replacement. It uses completed IS bars only and cannot access the
sealed historical-OOS interval.
