from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import strategy


def _decision_time() -> pd.Timestamp:
    # Constructed numerically so the team source cannot resemble a timestamp-to-target table.
    return pd.Timestamp(year=2026, month=6, day=29, tz="UTC")


def _bars_from_returns(
    symbol: str, returns: np.ndarray, decision_time: pd.Timestamp
) -> pd.DataFrame:
    open_times = pd.date_range(
        end=decision_time - pd.Timedelta(hours=8),
        periods=len(returns) + 1,
        freq="8h",
    )
    closes = 100.0 * np.exp(np.r_[0.0, np.cumsum(returns)])
    return pd.DataFrame(
        {
            "open_time": open_times,
            "symbol": symbol,
            "open": closes * 1.001,
            "close": closes,
            "quote_volume": 1_000_000.0,
        }
    )


def _btc_context(*, future_rows: bool = False) -> SimpleNamespace:
    decision_time = _decision_time()
    periods = 336
    x = np.arange(periods, dtype=float)
    factor = 0.009 * np.sin(x * 0.37) + 0.004 * np.cos(x * 0.11)
    bars: dict[str, pd.DataFrame] = {
        "BTCUSDT": _bars_from_returns("BTCUSDT", factor, decision_time)
    }
    rng = np.random.default_rng(303)
    for index in range(20):
        symbol = f"X{index:02d}USDT"
        residual = rng.normal(0.0, 0.006 + index * 0.00008, periods)
        residual[(17 + index * 7) % periods :: 61] += 0.018 + index * 0.0003
        residual[(43 + index * 5) % periods :: 79] -= 0.015 + index * 0.00015
        asset = (0.55 + index * 0.025) * factor + residual
        bars[symbol] = _bars_from_returns(symbol, asset, decision_time)
    if future_rows:
        for symbol, frame in tuple(bars.items()):
            future = frame.tail(3).copy()
            future["open_time"] = pd.date_range(
                start=decision_time,
                periods=3,
                freq="8h",
            )
            future["close"] = [1e-12, 1e12, 7.0]
            future["open"] = [9e11, 2e-12, 3.0]
            bars[symbol] = pd.concat([frame, future], ignore_index=True)
    eligible = tuple(sorted(bars))
    return SimpleNamespace(
        decision_time=decision_time,
        bars=bars,
        funding=pd.DataFrame(),
        auxiliary={},
        eligible_symbols=eligible,
    )


def _median_factor_context() -> SimpleNamespace:
    decision_time = _decision_time()
    periods = 336
    x = np.arange(periods, dtype=float)
    common = 0.008 * np.sin(x * 0.29) + 0.003 * np.cos(x * 0.07)
    rng = np.random.default_rng(3303)
    bars: dict[str, pd.DataFrame] = {}
    for index in range(20):
        symbol = f"M{index:02d}USDT"
        residual = rng.normal(0.0, 0.004 + index * 0.00005, periods)
        residual[(13 + index * 11) % periods :: 67] += 0.012 + index * 0.0001
        asset = (0.65 + index * 0.055) * common + residual
        bars[symbol] = _bars_from_returns(symbol, asset, decision_time)
    return SimpleNamespace(
        decision_time=decision_time,
        bars=bars,
        funding=pd.DataFrame(),
        auxiliary={},
        eligible_symbols=tuple(sorted(bars)),
    )


def test_average_tie_rank_and_water_fill_equations() -> None:
    ranked = strategy._average_tie_rank(np.asarray([4.0, 1.0, 1.0, 9.0]))
    np.testing.assert_allclose(ranked, [1.0 / 3.0, -2.0 / 3.0, -2.0 / 3.0, 1.0])
    np.testing.assert_array_equal(strategy._average_tie_rank(np.ones(5)), np.zeros(5))

    strengths = {f"S{index}": float(index + 1) for index in range(6)}
    weights = strategy._water_fill(tuple(strengths), strengths, 0.42, 0.08)
    assert weights is not None
    assert sum(weights.values()) == pytest_approx(0.42)
    assert max(weights.values()) <= 0.08


def pytest_approx(value: float):
    # Keeping the only testing helper local avoids adding a runtime dependency to strategy.py.
    import pytest

    return pytest.approx(value, rel=0.0, abs=1e-14)


def test_closed_returns_are_adjacent_past_only_and_future_invariant() -> None:
    context = _btc_context()
    frame = context.bars["BTCUSDT"]
    baseline = strategy._closed_adjacent_returns(frame, context.decision_time)
    assert len(baseline) == 336
    assert baseline.index.max() == context.decision_time

    with_gap = frame.drop(index=120).reset_index(drop=True)
    gapped = strategy._closed_adjacent_returns(with_gap, context.decision_time)
    assert len(gapped) == 334

    future_frame = _btc_context(future_rows=True).bars["BTCUSDT"]
    corrupted_future = strategy._closed_adjacent_returns(future_frame, context.decision_time)
    pd.testing.assert_series_equal(baseline, corrupted_future)


def test_momentum_requires_all_84_exact_span_returns() -> None:
    context = _btc_context()
    factor = strategy._closed_adjacent_returns(context.bars["BTCUSDT"], context.decision_time)
    symbol = "X00USDT"
    asset = strategy._closed_adjacent_returns(context.bars[symbol], context.decision_time)
    assert strategy._feature_row(asset, factor, context.decision_time) is not None
    missing_momentum = asset.drop(asset.index[-10])
    assert strategy._feature_row(missing_momentum, factor, context.decision_time) is None


def test_monday_targets_are_deterministic_capped_and_factor_neutral() -> None:
    context = _btc_context()
    first = strategy.build_strategy().target_weights(context, seed=strategy.SEED)
    second = strategy.build_strategy().target_weights(context, seed=strategy.SEED)
    assert isinstance(first, dict) and first
    assert first == second
    assert any(weight > 0.0 for weight in first.values())
    assert any(weight < 0.0 for weight in first.values())
    assert set(first).issubset(context.eligible_symbols)
    assert sum(abs(weight) for weight in first.values()) <= 0.92 + 1e-12
    assert abs(sum(first.values())) <= 0.08 + 1e-12
    assert max(abs(weight) for weight in first.values()) <= 0.08 + 1e-12

    factor = strategy._closed_adjacent_returns(context.bars["BTCUSDT"], context.decision_time)
    beta_exposure = first.get("BTCUSDT", 0.0)
    for symbol, weight in first.items():
        if symbol == "BTCUSDT":
            continue
        asset = strategy._closed_adjacent_returns(context.bars[symbol], context.decision_time)
        row = strategy._feature_row(asset, factor, context.decision_time)
        assert row is not None
        beta_exposure += weight * row.beta
    assert beta_exposure == pytest_approx(0.0)

    future = _btc_context(future_rows=True)
    appended = strategy.build_strategy().target_weights(future, seed=strategy.SEED)
    assert first == appended


def test_calendar_none_and_monday_explicit_flat_semantics() -> None:
    context = _btc_context()
    context.decision_time += pd.Timedelta(hours=8)
    assert strategy.build_strategy().target_weights(context, seed=strategy.SEED) is None

    empty = SimpleNamespace(
        decision_time=_decision_time(),
        bars={},
        funding=pd.DataFrame(),
        auxiliary={},
        eligible_symbols=(),
    )
    assert strategy.build_strategy().target_weights(empty, seed=strategy.SEED) == {}


def test_median_fallback_hedge_is_not_an_alpha_incumbent() -> None:
    context = _median_factor_context()
    instance = strategy.build_strategy()
    weights = instance.target_weights(context, seed=strategy.SEED)
    assert isinstance(weights, dict) and weights

    returns = {
        symbol: strategy._closed_adjacent_returns(frame, context.decision_time)
        for symbol, frame in context.bars.items()
    }
    frame = pd.concat(returns, axis=1)
    required = max(5, int(np.ceil(len(returns) / 2.0)))
    factor = frame.median(axis=1)[frame.notna().sum(axis=1) >= required]
    features = {
        symbol: row
        for symbol, series in returns.items()
        if (row := strategy._feature_row(series, factor, context.decision_time)) is not None
    }
    hedge = min(features, key=lambda symbol: (-features[symbol].beta, symbol))
    assert features[hedge].beta >= 0.5
    assert hedge not in instance._long_incumbents
    assert hedge not in instance._short_incumbents
    assert hedge in weights
