# Team 11 shrunk calendar baseline

This candidate estimates one preregistered weekly calendar cell from completed open-to-open bars.
Every return is first residualized against the contemporaneous cross-coin median. The target-cell
mean is then shrunk toward separate weekday, UTC-slot, and unconditional priors, so a sparse noisy
cell cannot dominate the forecast.

The strategy enters only at Monday 00:00 UTC, admits positive forecasts to the long sleeve and
negative forecasts to the short sleeve, and explicitly returns to cash at the next eight-hour
boundary. A one-bar central time stop independently enforces that exact forecast horizon. Total
gross is 0.24, with volatility scaling, position cooldowns, drawdown brakes, and a turnover cap.

This is a preregistered baseline and makes no performance claim. The local neighborhood varies the
history length and shrinkage strength without changing the calendar cell after results are known.
