from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# Column schema: name → dtype
_COLUMNS = {
    "open_time": np.int64,
    "open": np.float64,
    "high": np.float64,
    "low": np.float64,
    "close": np.float64,
    "volume": np.float64,
    "close_time": np.int64,
    "quote_volume": np.float64,
    "trades": np.int64,
    "taker_buy_volume": np.float64,
    "taker_buy_quote_volume": np.float64,
}


class KlineArray:
    """Columnar kline storage backed by a pandas DataFrame with DatetimeIndex.

    Properties (.open, .close, etc.) return numpy arrays so all existing
    strategy/indicator code works unchanged.  Use .df for pandas operations.
    """

    __slots__ = ("_df",)

    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df

    # -- alternate constructors ------------------------------------------------

    @classmethod
    def from_arrays(
        cls,
        *,
        open_time: np.ndarray,
        open: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        volume: np.ndarray,
        close_time: np.ndarray,
        quote_volume: np.ndarray,
        trades: np.ndarray,
        taker_buy_volume: np.ndarray,
        taker_buy_quote_volume: np.ndarray,
    ) -> KlineArray:
        """Build a KlineArray from 11 numpy arrays (backward-compat constructor)."""
        df = pd.DataFrame(
            {
                "open_time": open_time,
                "open": open,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
                "close_time": close_time,
                "quote_volume": quote_volume,
                "trades": trades,
                "taker_buy_volume": taker_buy_volume,
                "taker_buy_quote_volume": taker_buy_quote_volume,
            }
        )
        df.index = pd.to_datetime(df["open_time"], unit="ms", utc=True)
        return cls(df)

    @classmethod
    def empty(cls) -> KlineArray:
        """Return an empty KlineArray with the correct schema."""
        df = pd.DataFrame({col: pd.array([], dtype=dtype) for col, dtype in _COLUMNS.items()})
        df.index = pd.DatetimeIndex([], tz="UTC")
        return cls(df)

    # -- properties returning numpy arrays ------------------------------------

    @property
    def open_time(self) -> np.ndarray:
        return self._df["open_time"].values

    @property
    def open(self) -> np.ndarray:
        return self._df["open"].values

    @property
    def high(self) -> np.ndarray:
        return self._df["high"].values

    @property
    def low(self) -> np.ndarray:
        return self._df["low"].values

    @property
    def close(self) -> np.ndarray:
        return self._df["close"].values

    @property
    def volume(self) -> np.ndarray:
        return self._df["volume"].values

    @property
    def close_time(self) -> np.ndarray:
        return self._df["close_time"].values

    @property
    def quote_volume(self) -> np.ndarray:
        return self._df["quote_volume"].values

    @property
    def trades(self) -> np.ndarray:
        return self._df["trades"].values

    @property
    def taker_buy_volume(self) -> np.ndarray:
        return self._df["taker_buy_volume"].values

    @property
    def taker_buy_quote_volume(self) -> np.ndarray:
        return self._df["taker_buy_quote_volume"].values

    # -- symbol column (present after merge) -----------------------------------

    @property
    def symbols(self) -> np.ndarray | None:
        if "symbol" in self._df.columns:
            return self._df["symbol"].values
        return None

    @classmethod
    def merge(cls, symbol_arrays: dict[str, KlineArray]) -> KlineArray:
        """Merge per-symbol KlineArrays into one time-sorted KlineArray."""
        dfs = []
        for sym, arr in symbol_arrays.items():
            df = arr.df.reset_index(drop=True).copy()
            df["symbol"] = sym
            dfs.append(df)
        merged = pd.concat(dfs, ignore_index=True).sort_values(
            "open_time", kind="mergesort", ignore_index=True
        )
        merged.index = pd.to_datetime(merged["open_time"], unit="ms", utc=True)
        return cls(merged)

    # -- DataFrame access ------------------------------------------------------

    @property
    def df(self) -> pd.DataFrame:
        return self._df

    # -- slicing ---------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._df)

    def slice(self, start: int, end: int) -> KlineArray:
        """Return a view of rows [start:end] via iloc."""
        return KlineArray(self._df.iloc[start:end])

    def time_slice(self, start_ms: int | None = None, end_ms: int | None = None) -> KlineArray:
        """Slice by epoch-ms timestamps using the DatetimeIndex."""
        start_ts = pd.Timestamp(start_ms, unit="ms", tz="UTC") if start_ms is not None else None
        end_ts = pd.Timestamp(end_ms, unit="ms", tz="UTC") if end_ms is not None else None
        return KlineArray(self._df.loc[start_ts:end_ts])


def load_kline_array(path: Path) -> KlineArray:
    """Load a CSV file into a DataFrame-backed KlineArray."""
    if not path.exists():
        return KlineArray.empty()

    df = pd.read_csv(
        path,
        dtype={
            "open_time": np.int64,
            "open": np.float64,
            "high": np.float64,
            "low": np.float64,
            "close": np.float64,
            "volume": np.float64,
            "close_time": np.int64,
            "quote_volume": np.float64,
            "trades": np.int64,
            "taker_buy_volume": np.float64,
            "taker_buy_quote_volume": np.float64,
        },
    )

    if df.empty:
        return KlineArray.empty()

    df.index = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    return KlineArray(df)
