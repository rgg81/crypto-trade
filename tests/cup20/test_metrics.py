import math

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.metrics import (
    daily_returns,
    fold_positive_pnl_shares,
    fold_sharpes,
    is_folds,
    window_metrics,
)
from crypto_trade.tournament.engine_v2 import EvaluationResult


def _result(net, *, turnover=0.0, fees=0.0, slippage=0.0, price=None, funding=0.0, events=None):
    index = pd.date_range("2021-01-01T00:00:00Z", periods=len(net), freq="8h", name="timestamp")
    price_series = np.asarray(net, dtype=float) if price is None else np.asarray(price, dtype=float)
    returns = pd.DataFrame(
        {
            "net_return": np.asarray(net, dtype=float),
            "price_pnl": price_series,
            "long_price_pnl": price_series,
            "short_price_pnl": np.zeros(len(net)),
            "funding_pnl": np.full(len(net), funding, dtype=float),
            "long_funding_pnl": np.full(len(net), funding, dtype=float),
            "short_funding_pnl": np.zeros(len(net)),
            "fees": np.full(len(net), fees, dtype=float),
            "slippage": np.full(len(net), slippage, dtype=float),
            "turnover": np.full(len(net), turnover, dtype=float),
        },
        index=index,
    )
    event_frame = (
        pd.DataFrame(events)
        if events is not None
        else pd.DataFrame({"event_type": [], "notional": []})
    )
    return EvaluationResult(returns=returns, positions=pd.DataFrame(), events=event_frame)


def test_daily_returns_compound_within_each_utc_day():
    result = _result([0.01, 0.01, 0.01, -0.02, 0.0, 0.0])
    daily = daily_returns(result)
    assert len(daily) == 2
    assert daily.iloc[0] == pytest.approx(1.01**3 - 1.0)


def test_zero_variance_returns_give_zero_sharpe_not_nan():
    metrics = window_metrics(_result([0.0] * 90))
    assert metrics.net_sharpe == 0.0
    assert math.isfinite(metrics.net_sharpe)


def test_max_drawdown_is_a_positive_magnitude():
    # One move per UTC day: +10%, -20%, +5%. Drawdown is measured on the daily curve.
    bars = [0.10, 0.0, 0.0, -0.20, 0.0, 0.0, 0.05] + [0.0] * 83
    metrics = window_metrics(_result(bars))
    assert metrics.max_drawdown == pytest.approx(0.20)
    assert metrics.max_drawdown > 0.0


def test_calmar_is_zero_when_drawdown_is_zero_and_return_is_not_positive():
    assert window_metrics(_result([0.0] * 90)).calmar == 0.0


def test_gross_edge_per_turnover_is_in_basis_points():
    result = _result([0.001] * 90, turnover=0.01, price=[0.001] * 90)
    metrics = window_metrics(result)
    expected = (0.001 * 90) / (0.01 * 90) * 10_000
    assert metrics.gross_edge_bps_per_turnover == pytest.approx(expected)


def test_cost_share_uses_only_positive_gross_bars():
    result = _result([0.001, -0.002] * 45, fees=0.0001, slippage=0.0, price=[0.001, -0.002] * 45)
    metrics = window_metrics(result)
    positive_gross = 0.001 * 45
    assert metrics.cost_share_of_positive_gross == pytest.approx(0.0001 * 90 / positive_gross)


def test_trade_count_ignores_funding_and_zero_notional_rows():
    events = {
        "event_type": ["trade", "trade", "funding", "risk_reduction"],
        "notional": [100.0, -50.0, 0.0, 25.0],
    }
    metrics = window_metrics(_result([0.0] * 90, events=events))
    assert metrics.trade_count == 3


def test_top5_day_share_is_bounded_and_correct():
    values = [0.0] * 300
    for position in range(5):
        values[position * 3] = 1.0
    metrics = window_metrics(_result(values))
    assert metrics.top5_day_share == pytest.approx(1.0)


def test_is_folds_are_four_blocks_anchored_backward_from_the_cutoff():
    folds = is_folds(pd.Timestamp("2020-08-01T00:00:00Z"), pd.Timestamp("2024-08-01T00:00:00Z"))
    assert [name for name, _, _ in folds] == ["F1", "F2", "F3", "F4"]
    assert folds[0][1] == pd.Timestamp("2020-08-01T00:00:00Z")
    assert folds[0][2] == pd.Timestamp("2021-08-01T00:00:00Z")
    assert folds[-1][2] == pd.Timestamp("2024-08-01T00:00:00Z")


def test_fold_sharpes_and_shares_cover_every_named_fold():
    # Exactly the IS window, so every scored day belongs to exactly one fold and shares sum to 1.
    index = pd.date_range(
        "2020-08-01T00:00:00Z",
        "2024-08-01T00:00:00Z",
        freq="8h",
        inclusive="left",
        name="timestamp",
    )
    rng = np.random.default_rng(2)
    values = rng.normal(0.0002, 0.004, len(index))
    returns = pd.DataFrame(
        {
            "net_return": values,
            "price_pnl": values,
            "long_price_pnl": values,
            "short_price_pnl": np.zeros(len(index)),
            "funding_pnl": np.zeros(len(index)),
            "long_funding_pnl": np.zeros(len(index)),
            "short_funding_pnl": np.zeros(len(index)),
            "fees": np.zeros(len(index)),
            "slippage": np.zeros(len(index)),
            "turnover": np.zeros(len(index)),
        },
        index=index,
    )
    result = EvaluationResult(
        returns, pd.DataFrame(), pd.DataFrame({"event_type": [], "notional": []})
    )
    folds = is_folds(pd.Timestamp("2020-08-01T00:00:00Z"), pd.Timestamp("2024-08-01T00:00:00Z"))
    sharpes = fold_sharpes(result, folds)
    shares = fold_positive_pnl_shares(result, folds)
    assert set(sharpes) == {"F1", "F2", "F3", "F4"}
    assert all(math.isfinite(value) for value in sharpes.values())
    assert sum(shares.values()) == pytest.approx(1.0)
