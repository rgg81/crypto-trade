# Team 04 market-residual cross-sectional momentum baseline

This candidate builds a robust market return from the cross-sectional median of completed coin returns, estimates each coin's lagged market beta, and ranks cumulative beta-residual momentum. The most recent week is skipped to reduce short-term reversal contamination.

The portfolio holds broad long and short sleeves and mildly adjusts their gross budgets toward beta balance, within narrow bounds. It refreshes weekly and starts at modest gross exposure. Central volatility targeting, drawdown brakes, stops, and a tight turnover limit provide a second risk layer.

The primary control is the same formation and skip construction applied to raw returns. Beta-window and formation-window neighbors should follow only after residualization demonstrates a stable contribution across market regimes.
