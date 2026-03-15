"""Tests for the feature engineering pipeline."""

from __future__ import annotations

import numpy as np
import pandas as pd

from crypto_trade.features import GROUP_REGISTRY, generate_features, list_groups
from crypto_trade.features.mean_reversion import add_mean_reversion_features
from crypto_trade.features.momentum import add_momentum_features
from crypto_trade.features.statistical import add_statistical_features
from crypto_trade.features.trend import add_trend_features
from crypto_trade.features.volatility import add_volatility_features
from crypto_trade.features.volume import add_volume_features


def _make_ohlcv_df(n: int = 500) -> pd.DataFrame:
    """Create a realistic OHLCV DataFrame with n rows."""
    rng = np.random.default_rng(42)
    # Random walk for close prices
    close = 100.0 + np.cumsum(rng.normal(0, 0.5, n))
    close = np.maximum(close, 1.0)  # keep positive

    high = close + rng.uniform(0.1, 2.0, n)
    low = close - rng.uniform(0.1, 2.0, n)
    low = np.maximum(low, 0.01)
    open_ = low + rng.uniform(0, 1, n) * (high - low)

    volume = rng.uniform(100, 10000, n)
    taker_buy_volume = volume * rng.uniform(0.3, 0.7, n)

    open_time = np.arange(n, dtype=np.int64) * 300_000  # 5m intervals in ms

    df = pd.DataFrame(
        {
            "open_time": open_time,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "close_time": open_time + 299_999,
            "quote_volume": volume * close,
            "trades": rng.integers(10, 1000, n),
            "taker_buy_volume": taker_buy_volume,
            "taker_buy_quote_volume": taker_buy_volume * close,
        }
    )
    df.index = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    return df


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------


def test_list_groups():
    groups = list_groups()
    assert len(groups) == 6
    expected = {"momentum", "volatility", "trend", "volume", "mean_reversion", "statistical"}
    assert set(groups) == expected


def test_registry_has_all_groups():
    assert len(GROUP_REGISTRY) == 6


# ---------------------------------------------------------------------------
# Per-group tests
# ---------------------------------------------------------------------------


class TestStatistical:
    def test_adds_columns(self):
        df = _make_ohlcv_df(200)
        original_cols = set(df.columns)
        result = add_statistical_features(df)
        new_cols = [c for c in result.columns if c not in original_cols]
        assert len(new_cols) >= 20
        assert all(c.startswith("stat_") for c in new_cols)

    def test_return_columns(self):
        df = _make_ohlcv_df(100)
        result = add_statistical_features(df)
        assert "stat_return_1" in result.columns
        assert "stat_log_return_1" in result.columns


class TestMomentum:
    def test_adds_columns(self):
        df = _make_ohlcv_df(200)
        original_cols = set(df.columns)
        result = add_momentum_features(df)
        new_cols = [c for c in result.columns if c not in original_cols]
        assert len(new_cols) >= 25
        assert all(c.startswith("mom_") for c in new_cols)

    def test_rsi_range(self):
        df = _make_ohlcv_df(200)
        result = add_momentum_features(df)
        rsi = result["mom_rsi_14"].dropna()
        assert rsi.min() >= 0
        assert rsi.max() <= 100


class TestVolatility:
    def test_adds_columns(self):
        df = _make_ohlcv_df(200)
        original_cols = set(df.columns)
        result = add_volatility_features(df)
        new_cols = [c for c in result.columns if c not in original_cols]
        assert len(new_cols) >= 25
        assert all(c.startswith("vol_") for c in new_cols)

    def test_range_spike_present(self):
        df = _make_ohlcv_df(200)
        result = add_volatility_features(df)
        assert "vol_range_spike_48" in result.columns


class TestTrend:
    def test_adds_columns(self):
        df = _make_ohlcv_df(200)
        original_cols = set(df.columns)
        result = add_trend_features(df)
        new_cols = [c for c in result.columns if c not in original_cols]
        assert len(new_cols) >= 20
        assert all(c.startswith("trend_") for c in new_cols)


class TestVolume:
    def test_adds_columns(self):
        df = _make_ohlcv_df(200)
        original_cols = set(df.columns)
        result = add_volume_features(df)
        new_cols = [c for c in result.columns if c not in original_cols]
        assert len(new_cols) >= 20
        assert all(c.startswith("vol_") for c in new_cols)

    def test_taker_buy_ratio(self):
        df = _make_ohlcv_df(200)
        result = add_volume_features(df)
        assert "vol_taker_buy_ratio" in result.columns
        ratio = result["vol_taker_buy_ratio"].dropna()
        assert ratio.min() >= 0
        assert ratio.max() <= 1


class TestMeanReversion:
    def test_adds_columns(self):
        df = _make_ohlcv_df(200)
        original_cols = set(df.columns)
        result = add_mean_reversion_features(df)
        new_cols = [c for c in result.columns if c not in original_cols]
        assert len(new_cols) >= 20
        assert all(c.startswith("mr_") for c in new_cols)


# ---------------------------------------------------------------------------
# Integration test: generate all features
# ---------------------------------------------------------------------------


class TestGenerateAll:
    def test_all_groups(self):
        df = _make_ohlcv_df(300)
        original_cols = set(df.columns)
        result = generate_features(df, list_groups())
        new_cols = [c for c in result.columns if c not in original_cols]
        # Should have ~165 features across all groups
        assert len(new_cols) >= 100
        assert len(result) == 300  # row count unchanged

    def test_single_group(self):
        df = _make_ohlcv_df(200)
        result = generate_features(df, ["statistical"])
        assert "stat_return_1" in result.columns
        # Should not have momentum features
        assert not any(c.startswith("mom_") for c in result.columns)

    def test_no_rows_lost(self):
        df = _make_ohlcv_df(500)
        n = len(df)
        result = generate_features(df, list_groups())
        assert len(result) == n
