"""Cross-asset features: BTC indicators as features for all symbols.

This is a post-processing step that runs AFTER standard feature generation.
It loads BTC's kline data, computes BTC-derived features, and merges them
into all symbols' parquet files by open_time.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pandas_ta as ta
import pyarrow as pa
import pyarrow.parquet as pq

from crypto_trade.kline_array import load_kline_array
from crypto_trade.storage import csv_path


def _compute_btc_features(btc_df: pd.DataFrame) -> pd.DataFrame:
    """Compute BTC-derived features from BTC OHLCV data."""
    close = btc_df["close"]
    high = btc_df["high"]
    low = btc_df["low"]
    cols: dict[str, pd.Series] = {}

    # BTC returns (lagged: previous candle's return, avoids lookahead)
    cols["xbtc_return_1"] = close.pct_change(1) * 100
    cols["xbtc_return_3"] = close.pct_change(3) * 100
    cols["xbtc_return_8"] = close.pct_change(8) * 100

    # BTC volatility regime
    atr_14 = ta.atr(high, low, close, length=14)
    if atr_14 is not None:
        cols["xbtc_natr_14"] = atr_14 / close * 100
    atr_21 = ta.atr(high, low, close, length=21)
    if atr_21 is not None:
        cols["xbtc_natr_21"] = atr_21 / close * 100

    # BTC momentum
    cols["xbtc_rsi_14"] = ta.rsi(close, length=14)

    # BTC trend
    adx_df = ta.adx(high, low, close, length=14)
    if adx_df is not None:
        cols["xbtc_adx_14"] = adx_df.iloc[:, 0]

    result = pd.DataFrame(cols, index=btc_df.index)
    result["open_time"] = btc_df["open_time"]
    return result


def add_cross_asset_features(
    features_dir: str,
    data_dir: str,
    interval: str,
) -> int:
    """Add BTC cross-asset features to all parquet files in features_dir.

    Returns the number of files updated.
    """
    features_path = Path(features_dir)
    parquet_files = list(features_path.glob(f"*_{interval}_features.parquet"))
    if not parquet_files:
        print(f"No parquet files found in {features_dir} for interval {interval}")
        return 0

    # Load BTC kline data
    btc_csv = csv_path(Path(data_dir), "BTCUSDT", interval)
    if not btc_csv.exists():
        print(f"BTC kline data not found: {btc_csv}")
        return 0

    btc_ka = load_kline_array(btc_csv)
    btc_df = btc_ka.df.copy().reset_index(drop=True)
    btc_features = _compute_btc_features(btc_df).reset_index(drop=True)

    xbtc_cols = [c for c in btc_features.columns if c.startswith("xbtc_")]
    print(f"Computed {len(xbtc_cols)} BTC cross-asset features: {xbtc_cols}")

    updated = 0
    for pf in parquet_files:
        table = pq.read_table(pf)
        existing_cols = set(table.column_names)

        # Skip if cross-asset features already present
        if all(c in existing_cols for c in xbtc_cols):
            continue

        df = table.to_pandas()
        df = df.reset_index(drop=True)

        # Merge BTC features by open_time
        merged = df.merge(
            btc_features[["open_time"] + xbtc_cols],
            on="open_time",
            how="left",
        )

        # Write back
        new_table = pa.Table.from_pandas(merged, preserve_index=False)
        pq.write_table(new_table, pf, compression="zstd")

        symbol = pf.stem.replace(f"_{interval}_features", "")
        n_matched = merged[xbtc_cols[0]].notna().sum()
        print(
            f"  {symbol}: added {len(xbtc_cols)} xbtc features ({n_matched}/{len(merged)} matched)"
        )
        updated += 1

    return updated
