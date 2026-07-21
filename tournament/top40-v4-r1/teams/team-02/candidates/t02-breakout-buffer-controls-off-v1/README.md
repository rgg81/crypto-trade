# Team 02 buffered fast breakout: controls-off ablation

This diagnostic candidate keeps the baseline fast-breakout strategy byte-for-byte unchanged. It
scores each coin from its location in a twenty-day high-low channel and a volatility-normalized
seven-day return, attenuates unconfirmed moves, and refreshes balanced long and short sleeves every
Monday and Thursday at 00:00 UTC. Gross exposure remains 0.36.

All optional organizer controls are disabled: there is no volatility target, drawdown brake,
position stop, time stop, or turnover throttle. The baseline produced 2,042 position-stop actions,
749 time-stop actions, 1,014 blocks, and 547 drawdown-brake actions while its short sleeve and 2022
fold lost money. This preregistered ablation tests whether those interventions truncate breakout
winners or repeatedly re-enter false moves instead of protecting the raw signal.

The run is falsified if doubled-cost Sharpe and weak-fold breadth fail to improve, or if removing
the overlay creates unacceptable drawdown. It is diagnostic rather than part of the finalist
neighborhood and makes no performance claim.
