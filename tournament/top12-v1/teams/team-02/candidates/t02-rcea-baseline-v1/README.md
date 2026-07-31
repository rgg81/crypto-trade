# Team 02 baseline: asymmetric compression release

## Thesis

Markets sometimes leave a sustained, coin-specific range-compression state with an informative
one-bar expansion. This candidate treats that *change of state* as the event, rather than trading
an unconditional price breakout or scaling an existing signal by volatility.

For each symbol, normalized true ranges over the prior 12 days must be materially compressed
relative to the earlier portion of a 42-day formation window. A completed 8-hour bar then has to
expand relative to that compressed range distribution. Upside releases receive a continuation
signal when the bar closes high in its range with adequate directional efficiency. Downside
releases must pass stricter expansion, close-location, and efficiency thresholds. Long releases
remain eligible for four days, whereas the stricter short release remains eligible for two days.
This encodes the preregistered directional asymmetry directly in the alpha.

The strategy examines only bars for which `open_time + 8h <= decision_time`. It requests a new
portfolio no more often than every 48 hours. When both sides are present, each side receives a
separate score-weighted budget; when only one side is present, its budget is capped at 0.20.
Final targets are finite and hard-limited to 0.08 per symbol, 0.80 gross, and 0.20 absolute net.

## Falsifier

Falsify the mechanism if compression-release events have symmetric direction-conditioned
payoffs, if the stricter downside response and longer upside persistence are unstable across the
formation/rebalance grid or market roles, or if next-open costs consume the post-transition edge.

## Declared baseline parameters

- Formation history: 126 completed 8-hour bars (42 days).
- Compression state: 36 completed 8-hour bars (12 days).
- Compression median ratio: at most 0.68 of the earlier reference median.
- Compression upper-quartile ratio: at most 0.82 of the earlier reference median.
- Upside expansion multiple: 1.75; close location at least 0.72; body efficiency at least 0.42.
- Downside expansion multiple: 2.10; close location at most 0.18; body efficiency at least 0.55.
- Long/short signal lives: 12/6 bars.
- Rebalance interval: 6 bars (48 hours).
