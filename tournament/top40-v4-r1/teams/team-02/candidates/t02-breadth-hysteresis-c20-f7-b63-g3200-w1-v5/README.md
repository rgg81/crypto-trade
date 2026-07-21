# Team 02 crypto-breadth hysteresis breakout: neighborhood center

This candidate keeps exactly one directional sleeve active but adds causal hysteresis to the
aggregate native-crypto breadth state. Breadth at or above 55% selects long fast breakouts;
breadth at or below 45% selects short fast breakouts. Inside that band the preceding weekly state
is retained. On the first valid observation inside the band, 50% breadth initializes the side.

The buffer is designed to suppress repeated side changes near the binary threshold that left the
prior candidate's 2023 fold slightly negative. The twenty-day channel, seven-day confirmation,
persistence rule, weekly Monday schedule, 0.32 gross budget, and volatility-target-only policy are
otherwise unchanged. The state uses only completed pure-crypto bars and is deterministic.

This is the preregistered center of `t02-breadth-hysteresis-weekly-neighborhood`. It is falsified
if base and doubled-cost Sharpe, the weak fold, and confidence do not improve, or if any sleeve,
regime, cost, turnover, or drawdown gate regresses. It makes no performance claim.
