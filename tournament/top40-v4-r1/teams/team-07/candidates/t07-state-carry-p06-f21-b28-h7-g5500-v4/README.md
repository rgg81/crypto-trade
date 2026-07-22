# Team 07 2-day residual-trend protection

This is one point in a five-candidate protection-horizon neighborhood frozen before any point is
evaluated. Funding windows, BTC state, gross and net budgets, seven-day cohort averaging,
protection strength, and organizer controls are identical across all five points.

The only executable coordinate is the adverse idiosyncratic trend accumulated over 6
completed 8-hour residual returns (2 days). Residual volatility is estimated from the same
fixed twenty-one-return history at every point. Adverse moves reduce actual exposure without
renormalizing the sleeve, and each emitted cohort must retain strictly positive expected carry.

The neighborhood is falsified if positive-trend shorts or negative-trend longs remain dominant,
if slower protection creates excessive lag, or if profitability and doubled-cost Sharpe do not form
a broad plateau around the three-day center.
