# Team 12 fixed regime ensemble: controls-off ablation

This candidate combines exactly three transparent cross-sectional components: medium-horizon
residual momentum, short-horizon residual reversal, and downside resilience. Component weights are
fixed for bull, bear, chop, and stress states. The router derives direction and volatility from BTC
returns ending one full day before each weekly decision, so a boundary observation cannot change
the state contemporaneously.

Stress and bear states reduce gross rather than inventing a new signal. The portfolio remains
balanced long/short, retains names inside a wider rank band, and never changes the component set or
weights during evaluation. This diagnostic keeps the router, component weights, signal horizons,
sleeve construction, and router-level gross budgets unchanged. All optional central controls are
disabled: no volatility target, drawdown brake, position stop, time stop, or turnover throttle. That
isolates whether the baseline's weak bear fold and losing short sleeve belong to the ensemble or to
the overlay.

This is a preregistered control ablation, not a performance claim. Its coordinates remain at the
neighborhood center, but it is excluded from the five-point neighborhood evidence because the
original baseline already occupies the same coordinate vector.
