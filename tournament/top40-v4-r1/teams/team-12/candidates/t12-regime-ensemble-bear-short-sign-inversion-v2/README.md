# Team 12 repaired-center exact sign inversion

This candidate combines exactly three transparent cross-sectional components: medium-horizon
residual momentum, short-horizon residual reversal, and downside resilience. Component weights are
fixed for bull, bear, chop, and stress states. The router derives direction and volatility from BTC
returns ending one full day before each weekly decision, so a boundary observation cannot change
the state contemporaneously.

The repaired center uses a 180-bar BTC direction window, 252-bar full history, and 63-bar momentum.
Shorts are permitted only in a lagged bear state, only when the coin's own 63-bar return is negative,
and only when at least four confirmed names exist. Bull, chop, and stress never force a short hedge.
After the complete target is constructed, this diagnostic negates every weight exactly. It does not
re-rank names, swap component definitions, change gross budgets, or add controls.

This is a preregistered sign-inversion diagnostic, not a performance claim. It is intentionally
outside the local-neighborhood evidence and all optional central controls are disabled.
