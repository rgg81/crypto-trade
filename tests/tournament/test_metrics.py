from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament.metrics import (
    aggregate_daily_returns,
    classify_btc_regimes,
    compute_regime_sharpes,
    compute_window_metrics,
    sharpe_confidence_interval,
)


def test_aggregate_daily_returns_compounds_and_fills_calendar_days():
    index = pd.to_datetime(["2024-01-01 00:00", "2024-01-01 08:00", "2024-01-03 00:00"], utc=True)
    daily = aggregate_daily_returns(pd.Series([0.1, -0.05, 0.02], index=index))
    assert daily.iloc[0] == pytest.approx(1.1 * 0.95 - 1.0)
    assert daily.iloc[1] == 0.0
    assert daily.iloc[2] == pytest.approx(0.02)


def test_window_metrics_are_net_return_derived_and_bounded():
    index = pd.date_range("2024-01-01", periods=365, freq="D", tz="UTC")
    returns = pd.Series(np.tile([0.01, -0.004], 183)[:365], index=index)
    metrics = compute_window_metrics(returns)
    assert metrics.net_sharpe > 0
    assert metrics.annualized_return > 0
    assert 0 < metrics.max_drawdown < 1
    assert 0 <= metrics.positive_quarter_fraction <= 1


def test_window_metrics_include_drawdown_from_initial_nav():
    index = pd.date_range("2024-01-01", periods=2, freq="D", tz="UTC")
    metrics = compute_window_metrics(pd.Series([-0.20, 0.0], index=index))
    assert metrics.max_drawdown == pytest.approx(0.20)


def test_regime_map_is_lagged_and_sharpes_have_all_required_buckets():
    index = pd.date_range("2024-01-01", periods=200, freq="D", tz="UTC")
    btc_returns = pd.Series(0.003, index=index)
    labels = classify_btc_regimes(btc_returns)
    assert labels.iloc[:60].isna().all()
    assert labels.iloc[-1] == "bull"
    strategy = pd.Series(np.sin(np.arange(200)) / 100, index=index)
    sharpes = compute_regime_sharpes(strategy, labels)
    assert set(sharpes) == {"bear", "bull", "chop", "stress"}
    assert all(np.isfinite(value) for value in sharpes.values())


def test_block_bootstrap_sharpe_interval_is_deterministic():
    index = pd.date_range("2024-01-01", periods=200, freq="D", tz="UTC")
    returns = pd.Series(np.sin(np.arange(200)) / 100, index=index)
    first = sharpe_confidence_interval(returns, samples=200)
    second = sharpe_confidence_interval(returns, samples=200)
    assert first == second
    assert first[0] <= first[1]
