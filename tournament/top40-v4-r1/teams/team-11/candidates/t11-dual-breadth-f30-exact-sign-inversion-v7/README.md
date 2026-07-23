# Team 11 exact sign inversion

This candidate tests whether asset-specific crypto returns recur over the Monday-to-Monday week.
For every eligible coin and each of the Monday 00:00, 08:00, and 16:00 UTC anchors, it forms up to
seventy-eight completed weekly open-to-open returns using only bars available at the decision.
Each weekly cross-section is residualized against its contemporaneous median before robust clipping,
which removes common crypto-market direction from the estimated calendar effect.

The Monday 08:00 estimate and the average of its two adjacent Monday anchors each receive fifty
percent weight. The strongest relative forecasts enter the long sleeve using seventy-eight weeks
of history; the weakest relative forecasts enter the short sleeve only after one hundred four weeks
of history. This role-specific formation rule addresses the trial-3 attribution: shorter short-side
histories confused temporary winners with persistent laggards, while the seventy-eight-week long
ranking remained economically positive. Both sleeves receive equal symmetric weights at 0.58 total
gross. Each sleeve selects thirty percent of the valid cross-section, subject to the eight-name
minimum, to diversify the eight-name trial-4 portfolio without increasing rebalance frequency. The
portfolio is held continuously until the next Monday 08:00 UTC decision. Immediately after that
portfolio is formed, every target weight is multiplied by exactly negative one. Stops, volatility
scaling, drawdown brakes, time stops, and turnover clipping remain disabled.

This candidate changes no feature, formation window, selection count, schedule, gross budget, or
risk control from the trial-5 breadth center. It is the exact sign falsifier required by the research
matrix; comparable positive performance would invalidate the original interpretation.
