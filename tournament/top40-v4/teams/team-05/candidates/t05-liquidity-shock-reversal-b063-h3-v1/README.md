# Team 05 liquidity-shock reversal baseline

This candidate uses a fixed reversal sign. It measures the latest three completed residual returns
against a sixty-three-bar causal reference distribution. Abnormal quote volume and trade count must
coincide with taker pressure in the shock direction. A continuous prior-trend discount reduces the
score when the move extends an established trend; it never switches the signal to continuation.

The portfolio uses broad, equal-gross long and short sleeves. One cohort is formed at the daily
boundary and held as one third of a three-cohort book. This preserves the alpha definition while
limiting routine replacement turnover. Missing history, inadequate breadth, or a portfolio-limit
breach requests a flat book.

All features use completed transaction bars from the supplied point-in-time eligible universe.
Targets are organizer-executed at the next executable open. No regime labels, future rows, external
data, funding forecasts, or date-specific behavior are used.

The baseline is falsified if reversal is not positive after stressed costs, if a few crash events
carry the result, or if the activity and taker confirmation adds no value over equal-turnover price
reversal.
