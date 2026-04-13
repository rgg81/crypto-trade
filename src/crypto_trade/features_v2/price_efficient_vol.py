"""v2 efficient OHLC volatility estimators — iter-v2/001 will implement.

Planned features:

- ``parkinson_vol_20`` / ``parkinson_vol_50`` — Parkinson estimator (high/low range)
- ``garman_klass_vol_20`` — Garman-Klass estimator (OHLC)
- ``rogers_satchell_vol_20`` — Rogers-Satchell estimator (drift-adjusted)
- ``parkinson_gk_ratio_20`` — Ratio between Parkinson and Garman-Klass
"""

from __future__ import annotations

import pandas as pd


def add_price_efficient_vol_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add v2 efficient OHLC vol features to *df*. Implemented in iter-v2/001."""
    raise NotImplementedError(
        "v2 efficient vol features are implemented in iter-v2/001; scaffold stub"
    )
