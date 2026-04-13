"""v2 volume microstructure features — iter-v2/001 will implement.

Planned features:

- ``vwap_dev_20`` / ``vwap_dev_50`` — VWAP deviation normalized by ATR
- ``volume_mom_ratio_20`` — Volume momentum ratio (short/long volume mean)
- ``volume_cv_50`` — Volume coefficient of variation (activity consistency)
- ``obv_slope_50`` — Linear regression slope of OBV, normalized
- ``hl_range_ratio_20`` — High-low range relative to rolling mean
- ``close_pos_in_range_20`` / ``close_pos_in_range_50`` — Close position within bar range
"""

from __future__ import annotations

import pandas as pd


def add_volume_micro_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add v2 volume-microstructure features to *df*. Implemented in iter-v2/001."""
    raise NotImplementedError(
        "v2 volume-micro features are implemented in iter-v2/001; scaffold stub"
    )
