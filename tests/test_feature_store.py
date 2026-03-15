"""Tests for feature_store: CSV-to-Parquet conversion and lookup."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from crypto_trade.feature_store import (
    convert_all_features,
    convert_features_to_parquet,
    lookup_features,
    write_parquet,
)


def _make_feature_csv(path: Path, n: int = 200, symbol: str = "TEST") -> pd.DataFrame:
    """Create a small feature CSV and return the DataFrame."""
    rng = np.random.default_rng(42)
    open_time = np.arange(n, dtype=np.int64) * 300_000
    df = pd.DataFrame(
        {
            "open_time": open_time,
            "open": 100.0 + rng.normal(0, 1, n),
            "high": 101.0 + rng.normal(0, 1, n),
            "low": 99.0 + rng.normal(0, 1, n),
            "close": 100.0 + rng.normal(0, 1, n),
            "volume": rng.uniform(100, 10000, n),
            "feat_a": rng.normal(0, 1, n),
            "feat_b": rng.normal(0, 1, n),
            "feat_c": rng.normal(0, 1, n),
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return df


class TestConvertCsvToParquet:
    def test_basic_conversion(self, tmp_path: Path):
        csv_path = tmp_path / "TEST_5m_features.csv"
        df = _make_feature_csv(csv_path, n=150)

        parquet_path = csv_path.with_suffix(".parquet")
        n_rows = convert_features_to_parquet(csv_path, parquet_path)

        assert n_rows == 150
        assert parquet_path.exists()

        # Verify schema matches
        table = pq.read_table(parquet_path)
        result = table.to_pandas()
        assert list(result.columns) == list(df.columns)
        assert len(result) == 150

    def test_row_groups(self, tmp_path: Path):
        csv_path = tmp_path / "TEST_5m_features.csv"
        _make_feature_csv(csv_path, n=150)

        parquet_path = csv_path.with_suffix(".parquet")
        convert_features_to_parquet(csv_path, parquet_path, row_group_size=50)

        pf = pq.ParquetFile(parquet_path)
        assert pf.metadata.num_row_groups == 3  # 150 / 50

    def test_statistics_present(self, tmp_path: Path):
        csv_path = tmp_path / "TEST_5m_features.csv"
        _make_feature_csv(csv_path, n=100)

        parquet_path = csv_path.with_suffix(".parquet")
        convert_features_to_parquet(csv_path, parquet_path, row_group_size=50)

        pf = pq.ParquetFile(parquet_path)
        # open_time column should have min/max stats
        rg0 = pf.metadata.row_group(0)
        col_idx = next(
            i for i in range(rg0.num_columns) if rg0.column(i).path_in_schema == "open_time"
        )
        stats = rg0.column(col_idx).statistics
        assert stats is not None
        assert stats.has_min_max


class TestConvertDeletesCsv:
    def test_csv_deleted(self, tmp_path: Path):
        csv_path = tmp_path / "TEST_5m_features.csv"
        _make_feature_csv(csv_path, n=50)

        results = convert_all_features(tmp_path, "5m", workers=1, delete_csv=True)

        assert len(results) == 1
        assert not csv_path.exists()
        assert csv_path.with_suffix(".parquet").exists()

    def test_keep_csv(self, tmp_path: Path):
        csv_path = tmp_path / "TEST_5m_features.csv"
        _make_feature_csv(csv_path, n=50)

        results = convert_all_features(tmp_path, "5m", workers=1, delete_csv=False)

        assert len(results) == 1
        assert csv_path.exists()
        assert csv_path.with_suffix(".parquet").exists()


class TestConvertSkipsUpToDate:
    def test_skips_existing(self, tmp_path: Path):
        csv_path = tmp_path / "TEST_5m_features.csv"
        _make_feature_csv(csv_path, n=50)

        # First conversion
        convert_all_features(tmp_path, "5m", workers=1, delete_csv=False)
        parquet_path = csv_path.with_suffix(".parquet")
        assert parquet_path.exists()

        # Second run should skip (parquet is newer)
        results = convert_all_features(tmp_path, "5m", workers=1, delete_csv=False)
        assert len(results) == 0


class TestLookupParquet:
    def test_basic_lookup(self, tmp_path: Path):
        csv_path = tmp_path / "TEST_5m_features.csv"
        _make_feature_csv(csv_path, n=200)
        convert_all_features(tmp_path, "5m", workers=1, delete_csv=False)

        # Look up specific timestamps
        ts = [0, 300_000, 600_000]  # first three rows
        result = lookup_features(
            [(s, t) for s in ["TEST"] for t in ts],
            features_dir=tmp_path,
            interval="5m",
        )

        assert len(result) == 3
        assert list(result["open_time"]) == ts
        assert "symbol" in result.columns

    def test_missing_timestamps(self, tmp_path: Path):
        csv_path = tmp_path / "TEST_5m_features.csv"
        _make_feature_csv(csv_path, n=100)
        convert_all_features(tmp_path, "5m", workers=1, delete_csv=False)

        # Mix of real and fake timestamps
        lookups = [("TEST", 0), ("TEST", 999_999_999)]
        result = lookup_features(lookups, features_dir=tmp_path, interval="5m")

        assert len(result) == 1
        assert result.iloc[0]["open_time"] == 0

    def test_missing_symbol(self, tmp_path: Path):
        # No parquet file at all
        result = lookup_features(
            [("NOSYMBOL", 0)],
            features_dir=tmp_path,
            interval="5m",
        )
        assert len(result) == 0

    def test_multiple_symbols(self, tmp_path: Path):
        for sym in ["AAA", "BBB"]:
            csv_path = tmp_path / f"{sym}_5m_features.csv"
            _make_feature_csv(csv_path, n=50)

        convert_all_features(tmp_path, "5m", workers=1, delete_csv=False)

        lookups = [("AAA", 0), ("AAA", 300_000), ("BBB", 0)]
        result = lookup_features(lookups, features_dir=tmp_path, interval="5m")

        assert len(result) == 3
        assert set(result["symbol"]) == {"AAA", "BBB"}
        # Sorted by (symbol, open_time)
        assert list(result["symbol"]) == ["AAA", "AAA", "BBB"]

    def test_column_pruning(self, tmp_path: Path):
        csv_path = tmp_path / "TEST_5m_features.csv"
        _make_feature_csv(csv_path, n=100)
        convert_all_features(tmp_path, "5m", workers=1, delete_csv=False)

        result = lookup_features(
            [("TEST", 0)],
            features_dir=tmp_path,
            interval="5m",
            columns=["feat_a", "feat_b"],
        )

        assert len(result) == 1
        # Should have open_time (auto-included), feat_a, feat_b, symbol
        assert "feat_a" in result.columns
        assert "feat_b" in result.columns
        assert "open_time" in result.columns
        assert "symbol" in result.columns
        # Should NOT have feat_c or other columns
        assert "feat_c" not in result.columns
        assert "close" not in result.columns


class TestWriteParquet:
    def test_write_and_read_back(self, tmp_path: Path):
        rng = np.random.default_rng(42)
        df = pd.DataFrame(
            {
                "open_time": np.arange(100, dtype=np.int64) * 300_000,
                "value": rng.normal(0, 1, 100),
            }
        )
        path = tmp_path / "test.parquet"
        write_parquet(df, path)

        result = pq.read_table(path).to_pandas()
        assert len(result) == 100
        pd.testing.assert_frame_equal(result, df)
