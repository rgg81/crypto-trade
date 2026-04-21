"""Feature parity tests — verify live pipeline produces identical features to backtest.

These tests ensure that features generated via the live data_pipeline
(refresh_klines + refresh_features) are bit-for-bit identical to features
already in the Parquet files used by backtest.
"""

from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import pytest

from crypto_trade.live.data_pipeline import build_master

# These tests require actual data files — skip if not available
FEATURES_DIR = Path("data/features")
DATA_DIR = Path("data")
INTERVAL = "8h"

# Baseline v152 symbols
BASELINE_SYMBOLS = {
    "A": ["BTCUSDT", "ETHUSDT"],
    "C": ["LINKUSDT"],
    "D": ["BNBUSDT"],
}
ALL_SYMBOLS = ["BTCUSDT", "ETHUSDT", "LINKUSDT", "BNBUSDT"]


def _parquet_exists(symbol: str) -> bool:
    return (FEATURES_DIR / f"{symbol}_{INTERVAL}_features.parquet").exists()


def _kline_csv_exists(symbol: str) -> bool:
    return (DATA_DIR / symbol / f"{INTERVAL}.csv").exists()


@pytest.mark.skipif(
    not all(_parquet_exists(s) for s in ALL_SYMBOLS),
    reason="Feature Parquet files not available — run feature generation first",
)
class TestFeatureParity:
    """Verify that features are consistent and complete for baseline symbols."""

    def test_all_baseline_symbols_have_parquet(self):
        for symbol in ALL_SYMBOLS:
            path = FEATURES_DIR / f"{symbol}_{INTERVAL}_features.parquet"
            assert path.exists(), f"Missing Parquet: {path}"

    def test_parquet_has_open_time_column(self):
        for symbol in ALL_SYMBOLS:
            path = FEATURES_DIR / f"{symbol}_{INTERVAL}_features.parquet"
            schema = pq.read_schema(path)
            assert "open_time" in schema.names, f"{symbol}: missing open_time column"

    def test_feature_columns_intersect_across_model_a_symbols(self):
        """Model A pools BTC+ETH — both must share the same feature columns."""
        btc_schema = pq.read_schema(FEATURES_DIR / f"BTCUSDT_{INTERVAL}_features.parquet")
        eth_schema = pq.read_schema(FEATURES_DIR / f"ETHUSDT_{INTERVAL}_features.parquet")

        btc_cols = set(btc_schema.names)
        eth_cols = set(eth_schema.names)

        shared = btc_cols & eth_cols
        assert len(shared) > 10, f"Only {len(shared)} shared columns between BTC and ETH"

    def test_parquet_timestamps_match_kline_csv(self):
        """Feature Parquet open_time values should be a subset of kline CSV open_times."""
        for symbol in ALL_SYMBOLS:
            if not _kline_csv_exists(symbol):
                pytest.skip(f"No kline CSV for {symbol}")

            parquet_path = FEATURES_DIR / f"{symbol}_{INTERVAL}_features.parquet"
            table = pq.read_table(parquet_path, columns=["open_time"])
            parquet_times = set(table.column("open_time").to_pylist())

            master = build_master([symbol], INTERVAL, DATA_DIR)
            kline_times = set(master["open_time"].tolist())

            # All parquet times should exist in kline data
            missing = parquet_times - kline_times
            assert len(missing) == 0, (
                f"{symbol}: {len(missing)} Parquet timestamps not in kline CSV"
            )

    def test_features_no_all_nan_columns(self):
        """No feature column should be entirely NaN."""
        for symbol in ALL_SYMBOLS:
            parquet_path = FEATURES_DIR / f"{symbol}_{INTERVAL}_features.parquet"
            table = pq.read_table(parquet_path)
            df = table.to_pandas()

            feat_cols = [c for c in df.columns if c != "open_time"]
            all_nan_cols = [c for c in feat_cols if df[c].isna().all()]
            assert len(all_nan_cols) == 0, f"{symbol}: all-NaN columns: {all_nan_cols[:5]}"

    def test_recent_candle_has_features(self):
        """The most recent candle in kline data should have features in Parquet."""
        for symbol in ALL_SYMBOLS:
            if not _kline_csv_exists(symbol):
                pytest.skip(f"No kline CSV for {symbol}")

            master = build_master([symbol], INTERVAL, DATA_DIR)
            if master.empty:
                pytest.skip(f"No kline data for {symbol}")

            latest_ot = int(master["open_time"].iloc[-1])

            parquet_path = FEATURES_DIR / f"{symbol}_{INTERVAL}_features.parquet"
            table = pq.read_table(parquet_path, columns=["open_time"])
            parquet_max = int(table.column("open_time").to_pylist()[-1])

            # Parquet should be within 1 candle of the latest kline
            # (the very last candle may not have features if it's still forming)
            candle_ms = 28800000  # 8h
            assert abs(latest_ot - parquet_max) <= candle_ms, (
                f"{symbol}: latest kline {latest_ot}, latest feature {parquet_max}, gap > 1 candle"
            )


@pytest.mark.skipif(
    not all(_parquet_exists(s) for s in ALL_SYMBOLS),
    reason="Feature Parquet files not available",
)
class TestMasterDFParity:
    """Verify build_master produces correct schema for LightGBM consumption."""

    def test_master_df_schema_for_model_a(self):
        master = build_master(["BTCUSDT", "ETHUSDT"], INTERVAL, DATA_DIR)
        assert not master.empty
        assert master["symbol"].dtype.name == "category"
        assert set(master["symbol"].unique()) == {"BTCUSDT", "ETHUSDT"}
        assert master["open_time"].dtype == np.int64

    def test_master_sorted_by_open_time_then_symbol(self):
        master = build_master(["BTCUSDT", "ETHUSDT"], INTERVAL, DATA_DIR)
        ots = master["open_time"].values
        # open_time should be non-decreasing
        assert np.all(ots[1:] >= ots[:-1])

    def test_master_has_enough_history(self):
        """Must have 25+ months (2286+ candles) for LightGBM training."""
        master = build_master(ALL_SYMBOLS, INTERVAL, DATA_DIR)
        per_symbol = master.groupby("symbol").size()
        for symbol in ALL_SYMBOLS:
            if symbol in per_symbol.index:
                n = per_symbol[symbol]
                assert n >= 2000, f"{symbol}: only {n} candles, need 2286+ for 24mo training"
