# Team 09 repaired flow pressure: volatility-target-only

This individual-control candidate keeps the repaired 168/18/2600 weekly market-neutral signal exactly unchanged. It combines
cross-sectionally residualized taker-buy imbalance, residual price pressure, and quote-volume plus
trade-count activity normalized against each coin's own history. Price/flow disagreement is treated
as exhaustion and dampens conviction rather than reversing the economic hypothesis. Relative to
the parent, an unconfirmed positive score is scaled to 10% while an unconfirmed negative score
retains the parent's 35% scale. This directly targets the losing long sleeve observed in the weak
folds without changing the short-pressure rule.

The portfolio selects balanced long and short sleeves, retains names inside a wider rank buffer,
and targets 0.26 gross. It uses 168 completed bars for normalization and an 18-bar pressure window.
The only optional organizer control is a no-leverage 22% annualized volatility target with a
30-day trailing window. There is no drawdown brake, position stop, time stop, or turnover throttle.
This isolates the gentlest member of the original stack after the controls-off trial showed that the
raw repaired targets possess five-fold breadth. Missing, incomplete, or insufficient histories
request a flat book. The implementation is deterministic and uses only rows completed by the
decision.

This is a preregistered individual-control role check and makes no performance claim. Its signal
coordinates sit at the already bracketed neighborhood center; the five distinct surrounding points,
not this duplicate center coordinate, supply the local-neighborhood evidence.
