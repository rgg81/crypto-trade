"""v2 tail-risk features — iter-v2/001 will implement.

Planned features:

- ``ret_skew_50`` / ``ret_skew_100`` / ``ret_skew_200`` — Rolling skewness of log returns
- ``ret_kurt_50`` / ``ret_kurt_200`` — Rolling kurtosis (black-swan proximity)
- ``range_realized_vol_50`` — Realized vol from high-low range
- ``max_dd_window_50`` — Rolling window max drawdown of close
"""

from __future__ import annotations

import pandas as pd


def add_tail_risk_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add v2 tail-risk features to *df*. Implemented in iter-v2/001."""
    raise NotImplementedError(
        "v2 tail-risk features are implemented in iter-v2/001; scaffold stub"
    )
