# Team 02 dual-trend weekly breakout: neighborhood center

This candidate retains the validated fast-breakout direction while adding a causal, per-coin slow
trend gate. A positive twenty-day channel/seven-day confirmation score may enter the long sleeve
only when the coin's completed sixty-three-day log return is positive; a negative score may enter
the short sleeve only when that return is negative. This targets the observed counter-regime
failure without using a hindsight calendar label or a common TradFi proxy.

Targets refresh once per week, Monday at 00:00 UTC, instead of twice weekly. This is intended to
reduce the controls-off parent's 31.1x annual turnover while allowing confirmed breakouts to run.
The only enabled organizer overlay is the 22% volatility target; drawdown brakes, position stops,
time stops, and the turnover throttle remain off because the baseline ablation showed frequent
interventions truncating fold breadth.

This is the preregistered center of `t02-dual-trend-weekly-neighborhood`. It is falsified if both
sleeves do not produce positive gross PnL, annual turnover remains uneconomic, chop Sharpe stays
negative, or doubled-cost robustness does not materially improve. It makes no performance claim.
