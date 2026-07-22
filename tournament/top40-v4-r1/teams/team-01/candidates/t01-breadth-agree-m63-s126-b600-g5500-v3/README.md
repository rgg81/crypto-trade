# Team 01 breadth-aware dual-horizon trend: center

The accepted baseline made money in every organizer regime, but its sleeves repeatedly fought the
broad market: shorts lost in 2020, 2021, and 2023, while longs lost in 2022. This repair requires
the 63-day and 126-day volatility-normalized signals to have the same sign before a coin can enter.

It then measures causal sign breadth across the confirmed coins. Above 60% positive breadth, 72%
of target gross is reserved for longs and 28% for shorts; below 40%, those budgets reverse; between
the thresholds, the book is balanced. Missing sleeves are capped at 0.242 gross so net exposure
never breaches the tournament's 0.25 limit. The rule therefore remains two-sided and per-coin, but
does not mechanically spend half its risk fighting a broad trend.

The total cap rises from 0.44 to 0.55 because the baseline passed return, turnover, cost, regime,
and drawdown gates while realizing only 0.157 average gross. The full five-point neighborhood is
frozen before evaluation at `(medium_days, slow_days, breadth_threshold)` values
`(49,112,.55)`, `(56,119,.575)`, `(63,126,.60)`, `(70,140,.625)`, and `(77,154,.65)`.

The candidate uses completed bars and next-open execution only. It makes no performance claim and
cannot access the sealed historical-OOS interval.
