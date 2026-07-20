# Team 12 repaired center: dual absolute-trend confirmation

This candidate combines exactly three transparent cross-sectional components: medium-horizon
residual momentum, short-horizon residual reversal, and downside resilience. Component weights are
fixed for bull, bear, chop, and stress states. The router derives direction and volatility from BTC
returns ending one full day before each weekly decision, so a boundary observation cannot change
the state contemporaneously.

The repaired center uses a 180-bar BTC direction window, 252-bar full history, and 63-bar momentum.
Longs must also have a positive 21-bar own-price return, and shorts are permitted only in a lagged
bear state with a negative 63-bar own-price return. Each sleeve requires at least four confirmed
names. When a sleeve lacks breadth, its budget remains cash rather than being forced into a weak
relative rank.
The only optional central control is a no-leverage 20% annualized volatility target using a 30-day
trailing window. There is no drawdown brake, position stop, time stop, or turnover throttle. The
target does not enlarge exposure and otherwise leaves the repaired signal unchanged.

This is a preregistered individual-control role check, not a performance claim. Its signal
coordinates sit at the center bracketed by the five distinct neighborhood points; those points, not
this duplicate center coordinate, supply the local-neighborhood evidence.
