"""v2 regime features — iter-v2/001 will implement.

Planned features (see quant-iteration-v2 skill, v2 Feature Catalog):

- ``hurst_100`` / ``hurst_200`` — Rolling Hurst exponent (R/S method)
- ``hurst_diff_100_50`` — Regime-transition detector
- ``atr_pct_rank_200`` / ``atr_pct_rank_500`` / ``atr_pct_rank_1000`` — ATR percentile rank
- ``bb_width_pct_rank_100`` — Bollinger Band width percentile (squeeze detector)
- ``cusum_reset_count_200`` — Number of CUSUM structural-break resets in last 200 candles
- ``adx_v2_14`` — ADX only if v1's ``trend.py`` does not already ship it
"""

from __future__ import annotations

import pandas as pd


def add_regime_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add v2 regime features to *df*. Implemented in iter-v2/001."""
    raise NotImplementedError(
        "v2 regime features are implemented in iter-v2/001; scaffold stub"
    )
