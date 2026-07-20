# Team 12 bear-only short confirmation: 240/336/84

This candidate combines exactly three transparent cross-sectional components: medium-horizon
residual momentum, short-horizon residual reversal, and downside resilience. Component weights are
fixed for bull, bear, chop, and stress states. The router derives direction and volatility from BTC
returns ending one full day before each decision, so a boundary observation cannot change
the state contemporaneously.

Stress and bear states reduce gross rather than inventing a new signal. This high-extreme point keeps
the fixed component weights and long selection, lengthens the BTC direction window to 240 bars, the
full return history to 336 bars, and momentum to 84 bars, and refreshes weekly. Residual
ranks may nominate a relative laggard whose absolute price is still rising. Shorts are therefore
permitted only in a lagged bear state, only when the coin's own 84-bar return is negative, and only
when at least four confirmed names exist. Bull, chop, and stress never force a short hedge. Short
gross is capped by both the router budget and the per-symbol limit; unused budget remains cash rather
than enlarging longs. All optional central controls remain disabled.

This is a preregistered high-extreme neighborhood point, not a performance claim. The local grid
varies BTC direction, full-history, and momentum horizons while preserving the causal lag, component
set, fixed regime weights, and bear-only short-confirmation rule.
