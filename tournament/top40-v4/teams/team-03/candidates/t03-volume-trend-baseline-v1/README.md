# Team 03 volume-confirmed trend baseline

This candidate starts with each coin's own medium-horizon price trend. It then asks whether recent quote volume was concentrated on returns in the trend direction and whether recent participation is healthy relative to its own lagged baseline. Weak confirmation attenuates the trend; it never mechanically reverses it.

Only completed eight-hour bars enter the calculation. The strategy refreshes broad sign-respecting sleeves weekly at modest gross exposure; a side without enough valid signals remains cash. Central volatility targeting, drawdown brakes, position and time stops, and a turnover cap address liquidity bursts and trend failures.

The key control is the same price-trend construction without the volume multiplier. Nearby formation and confirmation windows should be tested only after this baseline establishes whether the mechanism adds value.
