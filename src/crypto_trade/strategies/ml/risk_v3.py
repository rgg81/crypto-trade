"""v3 risk wrapper — overrides RiskV2Wrapper._build_lookups to use V3_FEATURE_COLUMNS.

iter-v3/001: V3_FEATURE_COLUMNS renames two fracdiff columns:
  fracdiff_logclose_d04  -> fracdiff_logclose_dstat
  fracdiff_logvolume_d04 -> fracdiff_logvolume_dstat

RiskV2Wrapper._build_lookups hardcodes V2_FEATURE_COLUMNS for z-score OOD.
RiskV3Wrapper overrides that single method to use V3_FEATURE_COLUMNS instead,
keeping all other gate logic identical.

Track isolation: MUST NOT import from crypto_trade.features or
crypto_trade.features_v2.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.config import OOS_CUTOFF_MS
from crypto_trade.features_v3 import V3_FEATURE_COLUMNS
from crypto_trade.strategies.ml.risk_v2 import RiskV2Wrapper, _compute_adx


class RiskV3Wrapper(RiskV2Wrapper):
    """v3 variant of RiskV2Wrapper that uses V3_FEATURE_COLUMNS for z-score OOD.

    Identical to RiskV2Wrapper in all gate logic. Only _build_lookups is
    overridden to read the v3 parquet schema (fracdiff_logclose_dstat instead
    of fracdiff_logclose_d04).
    """

    def _build_lookups(self, master: pd.DataFrame) -> None:
        """Load v3 features and compute ADX per symbol — v3 parquet schema.

        Overrides RiskV2Wrapper._build_lookups to use V3_FEATURE_COLUMNS.
        """
        import pyarrow.parquet as pq  # noqa: PLC0415

        features_dir = getattr(self.inner, "features_dir", "data/features_v3")
        interval = getattr(self.inner, "_interval", "8h")

        symbols = list(pd.unique(master["symbol"]))
        for sym in symbols:
            path = Path(features_dir) / f"{sym}_{interval}_features.parquet"
            if not path.exists():
                continue

            needed = ["open_time", "high", "low", "close", "hurst_100", *V3_FEATURE_COLUMNS]
            needed = list(dict.fromkeys(needed))  # dedup, preserve order
            table = pq.read_table(path, columns=needed).to_pandas()
            table = table.sort_values("open_time").reset_index(drop=True)

            # Training-window = IS (open_time < OOS_CUTOFF_MS)
            is_mask = table["open_time"] < OOS_CUTOFF_MS
            is_df = table.loc[is_mask, list(V3_FEATURE_COLUMNS)]

            # Snapshot feature mean/std over IS window
            self._feature_mean[sym] = is_df.mean(skipna=True)
            self._feature_std[sym] = is_df.std(skipna=True).replace(0, np.nan)

            # Hurst percentile band over IS window
            hurst_is = table.loc[is_mask, "hurst_100"].dropna().to_numpy()
            if len(hurst_is) > 10:
                self._hurst_lower[sym] = float(np.quantile(hurst_is, self.config.hurst_lower_pct))
                self._hurst_upper[sym] = float(np.quantile(hurst_is, self.config.hurst_upper_pct))
            else:
                self._hurst_lower[sym] = -np.inf
                self._hurst_upper[sym] = np.inf

            # Compute ADX for the full series (IS + OOS)
            adx_arr = _compute_adx(
                table["high"].to_numpy(),
                table["low"].to_numpy(),
                table["close"].to_numpy(),
                period=self.config.adx_period,
            )

            # Build lookup table indexed by open_time
            self._lookup[sym] = {
                "open_time": table["open_time"].to_numpy(dtype=np.int64),
                "adx": adx_arr,
                "atr_pct_rank_200": table["atr_pct_rank_200"].to_numpy(),
                "hurst_100": table["hurst_100"].to_numpy(),
                "features": table[list(V3_FEATURE_COLUMNS)].to_numpy(),
            }


__all__ = ["RiskV3Wrapper"]
