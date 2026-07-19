# Team 12 fixed regime-ensemble baseline

This candidate combines exactly three transparent cross-sectional components: medium-horizon
residual momentum, short-horizon residual reversal, and downside resilience. Component weights are
fixed for bull, bear, chop, and stress states. The router derives direction and volatility from BTC
returns ending one full day before each weekly decision, so a boundary observation cannot change
the state contemporaneously.

Stress and bear states reduce gross rather than inventing a new signal. The portfolio remains
balanced long/short, retains names inside a wider rank band, and never changes the component set or
weights during evaluation. Candidate-local controls add another volatility target, drawdown brakes,
position cooldowns, and a one-way turnover cap.

This is a preregistered baseline, not a performance claim. Its neighborhood changes formation and
component horizons while preserving the fixed router and lag convention.
