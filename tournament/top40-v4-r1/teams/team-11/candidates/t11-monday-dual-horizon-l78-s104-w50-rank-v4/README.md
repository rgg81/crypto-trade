# Team 11 role-specific Monday weekly seasonality

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
gross, and the portfolio is held continuously until the next Monday 08:00 UTC decision. Stops,
volatility scaling, drawdown brakes, and turnover clipping remain disabled.

The preregistered local neighborhood keeps the long history fixed at seventy-eight weeks and tests
the center at short-history 104 weeks and center-anchor weight 0.50, plus one-axis neighbors at short
histories 91 and 117 weeks and center-anchor weights 0.25 and 0.75. Era, sleeve, adjacent-cell, and
stressed-cost failures falsify the candidate.
