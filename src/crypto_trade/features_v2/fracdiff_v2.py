"""v2 fractional differentiation features — iter-v2/001 will implement.

Planned features (AFML Ch. 5):

- ``fracdiff_logclose_d04`` — Fractionally differentiated log close, fixed window=100
- ``fracdiff_logvolume_d04`` — Fractionally differentiated log volume

Differencing order ``d`` is selected per symbol via the minimum ``d`` that gives
ADF p-value < 0.05, preserving long-run memory while achieving stationarity.
v1 tested this in iter 100 and results were inconclusive due to a confounding
parquet regeneration; v2 revisits with a cleaner harness.
"""

from __future__ import annotations

import pandas as pd


def add_fracdiff_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add v2 fracdiff features to *df*. Implemented in iter-v2/001."""
    raise NotImplementedError(
        "v2 fracdiff features are implemented in iter-v2/001; scaffold stub"
    )
