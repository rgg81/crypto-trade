# Team 11 three-slot Monday weekly seasonality

This candidate tests whether asset-specific crypto returns recur over the Monday-to-Monday week.
For every eligible coin and each of the Monday 00:00, 08:00, and 16:00 UTC anchors, it forms up to
seventy-eight completed weekly open-to-open returns using only bars available at the decision.
Each weekly cross-section is residualized against its contemporaneous median before robust clipping,
which removes common crypto-market direction from the estimated calendar effect.

The Monday 08:00 estimate receives seventy-five percent weight and the average of its two adjacent
Monday anchors receives twenty-five percent. Forecasts must have the correct sign to enter the
corresponding sleeve. The strongest positive and negative forecasts receive equal symmetric weights
at 0.58 total gross, and the resulting portfolio is held continuously until the next Monday 08:00
UTC decision. Stops, volatility scaling, drawdown brakes, and turnover clipping are disabled so the
trial measures the calendar hypothesis directly.

The adjacent-slot shrinkage is the causal robustness control suggested by the first failed one-bar
baseline. The local neighborhood varies only the seventy-eight-week history and the seventy-five
percent center weight; era, sleeve, adjacent-cell, and stressed-cost failures falsify the candidate.
