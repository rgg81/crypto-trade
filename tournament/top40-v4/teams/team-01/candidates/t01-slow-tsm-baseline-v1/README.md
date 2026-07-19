# Team 01 slow time-series momentum baseline

This candidate ranks every eligible coin by a volatility-normalized blend of medium and slow own-price momentum. Signals whose two horizons disagree are retained at reduced strength rather than flipped or aggressively discarded. It then holds broad, sign-respecting sleeves and only refreshes them weekly; if one side has too few valid signals, that sleeve remains cash instead of trading against the model.

The construction is deliberately transparent: completed eight-hour bars only, no fitted artifact, no calendar target, and no future execution price. The low strategy gross and central turnover limit leave room for volatility targeting and drawdown brakes to reduce exposure without forcing churn.

The first falsification questions are whether the horizon blend survives bull, bear, and chop segments, whether both sleeves contribute, and whether neighboring slow horizons retain the result.
