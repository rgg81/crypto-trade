# Team 07 confirmed-carry volatility-only ablation

The +0.25 price-confirmed strategy and every target parameter are unchanged. Only the causal,
no-leverage volatility target remains enabled; stops, cooldowns, drawdown brakes, time stops and
the turnover throttle are disabled. This isolates the individual scaling control while removing
exit-driven target interference.
