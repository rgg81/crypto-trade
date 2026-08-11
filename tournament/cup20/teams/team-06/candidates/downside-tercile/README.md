# downside-tercile

Cross-sectional selection on downside risk inside the point-in-time top-20 crypto perpetual
universe. Long the six names with the lowest downside-risk composite, short the six highest,
rebalanced weekly on the 8h grid.

**The composite** is the equal-weight sum of the cross-sectional z-scores of four characteristics,
each measured on the trailing `FORMATION_BARS` 8h bars: left-tail CVaR at 5%, downside
semideviation about the window mean, maximum peak-to-trough drawdown of the close path, and the
fraction of the window spent below its running maximum. Equal weights because nothing in the
research justified unequal ones; the four are the facets of downside risk the lane names.

**Why this should pay in crypto and not merely in a backtest.** Leverage is universally available
and liquidation is automatic, so a coin's left tail is largely a record of how much crowded
leveraged length has been forced out of it. That length is also what makes the coin expensive.
Symmetric volatility counts the up-moves and the down-moves alike and so cannot separate a coin
whose width is two-sided market-making churn from one whose width is repeated one-sided
deleveraging. This book selects on the second.

**The one control** is a leg-weight tilt: the two sleeves take unequal shares of gross so that
their trailing market betas offset. Selecting on risk always produces sleeves of unequal beta, and
without the tilt the book is a short-beta position rather than a cross-sectional one. Ablated in
the certificate.

Not in the book, deliberately: no expected-return signal, no momentum, no funding or basis input,
no fitted model, no state carried between decisions. `target_weights` is a pure function of the
past-only bars the context streams in.

Files: `strategy.py` (`build_strategy()`), `risk_policy.json` (flat; `volatility_target.enabled`
is `false`), `neighbourhood.json` (three swept coordinates, seven points).
