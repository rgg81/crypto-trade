# Team 11 stopped dual-horizon upper-history neighbor

This candidate tests whether asset-specific crypto returns recur over the Monday-to-Monday week.
For every eligible coin and each of the Monday 00:00, 08:00, and 16:00 UTC anchors, it forms up to
seventy-eight completed weekly open-to-open returns using only bars available at the decision.
Each weekly cross-section is residualized against its contemporaneous median before robust clipping,
which removes common crypto-market direction from the estimated calendar effect.

The Monday 08:00 estimate and the average of its two adjacent Monday anchors each receive fifty
percent weight. The strongest relative forecasts enter the long sleeve using seventy-eight weeks
of history; the weakest relative forecasts enter the short sleeve only after one hundred seventeen weeks
of history. This role-specific formation rule addresses the trial-3 attribution: shorter short-side
histories confused temporary winners with persistent laggards, while the seventy-eight-week long
ranking remained economically positive. Both sleeves receive equal symmetric weights at 0.58 total
gross. Each sleeve selects thirty percent of the valid cross-section, subject to the eight-name
minimum, to diversify the eight-name trial-4 portfolio without increasing rebalance frequency. The
portfolio is held continuously until the next Monday 08:00 UTC decision. A symmetric position stop
exits a name after a close-confirmed six-percent loss and blocks reentry for three bars. Volatility
scaling, drawdown brakes, time stops, and turnover clipping remain disabled.

The preregistered local neighborhood keeps the long history at seventy-eight weeks and anchor
weight at 0.50. Its center is short-history 104 weeks and sleeve fraction 0.30, bracketed by
short histories 91/117 weeks and sleeve fractions 0.25/0.35. The six-percent position stop and
three-bar cooldown remain fixed at every point. Era, sleeve, edge, and stressed-cost failures
falsify the candidate.

This is the preregistered upper short-history coordinate `(117 weeks, 0.30 fraction)`.
