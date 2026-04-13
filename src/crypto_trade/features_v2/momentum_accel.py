"""v2 momentum-acceleration features — iter-v2/001 will implement.

Planned features:

- ``mom_accel_5_20`` / ``mom_accel_20_100`` — Multi-horizon momentum acceleration
- ``ema_spread_atr_20`` — EMA spread normalized by ATR (trend strength in vol units)
- ``ret_autocorr_lag1_50`` / ``ret_autocorr_lag5_50`` — Return autocorrelation (regime signature)
"""

from __future__ import annotations

import pandas as pd


def add_momentum_accel_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add v2 momentum-acceleration features to *df*. Implemented in iter-v2/001."""
    raise NotImplementedError(
        "v2 momentum-accel features are implemented in iter-v2/001; scaffold stub"
    )
