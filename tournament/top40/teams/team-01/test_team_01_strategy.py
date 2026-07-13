from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest


def _load_strategy_module():
    path = Path(__file__).with_name("strategy.py")
    spec = importlib.util.spec_from_file_location("team_01_strategy", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


STRATEGY = _load_strategy_module()
SEED = 20260713


def _decision_time() -> pd.Timestamp:
    return pd.Timestamp(year=2024, month=6, day=24, tz="UTC")


def _synthetic_context() -> SimpleNamespace:
    decision_time = _decision_time()
    closes = pd.date_range(end=decision_time, periods=317, freq="8h")
    open_times = closes - pd.Timedelta(hours=8)
    index = np.arange(len(closes), dtype=np.float64)
    btc_returns = np.zeros(len(closes), dtype=np.float64)
    btc_returns[1:] = 0.004 * np.sin(index[1:] * 0.41) + 0.002 * np.cos(index[1:] * 0.17)
    symbols = ["BTCUSDT", *(f"C{number:02d}USDT" for number in range(20))]

    bars: dict[str, pd.DataFrame] = {}
    for symbol_number, symbol in enumerate(symbols):
        if symbol == "BTCUSDT":
            returns = btc_returns
            close = 30_000.0 * np.exp(np.cumsum(returns))
        else:
            residual = np.zeros(len(closes), dtype=np.float64)
            residual[1:] = 0.006 * np.sin(
                index[1:] * (0.13 + symbol_number * 0.003) + symbol_number * 0.37
            ) + 0.003 * np.cos(index[1:] * 0.29 + symbol_number)
            returns = 0.4 * btc_returns + residual
            close = (10.0 + symbol_number) * np.exp(np.cumsum(returns))

        quote_volume = np.full(len(closes), 10_000_000.0)
        taker_buy_quote_volume = 0.5 * quote_volume
        for event_index in range(130, 311, 7):
            quote_volume[event_index] = 100_000_000.0
            imbalance = 0.8 if (event_index // 7 + symbol_number) % 2 == 0 else -0.8
            taker_buy_quote_volume[event_index] = (
                (imbalance + 1.0) * quote_volume[event_index] / 2.0
            )
        bars[symbol] = pd.DataFrame(
            {
                "open_time": open_times,
                "symbol": symbol,
                "open": close * np.exp(-returns),
                "close": close,
                "quote_volume": quote_volume,
                "taker_buy_quote_volume": taker_buy_quote_volume,
            }
        )

    funding_rows: list[dict[str, object]] = []
    for symbol_number, symbol in enumerate(symbols):
        for days_ago in range(1, 21):
            funding_rows.append(
                {
                    "funding_time": decision_time - pd.Timedelta(days=days_ago),
                    "symbol": symbol,
                    "funding_rate": (symbol_number - 10) * 1e-6 + days_ago * 1e-8,
                    "mark_price": 1.0,
                }
            )
    return SimpleNamespace(
        decision_time=decision_time,
        bars=bars,
        funding=pd.DataFrame(funding_rows),
        auxiliary={},
        eligible_symbols=tuple(symbols),
    )


@pytest.fixture(scope="module")
def context() -> SimpleNamespace:
    return _synthetic_context()


def _weights(context: SimpleNamespace) -> dict[str, float]:
    result = STRATEGY.build_strategy().target_weights(context, seed=SEED)
    assert isinstance(result, dict)
    return result


def test_factory_is_fresh_and_none_is_distinct_from_flat(context: SimpleNamespace) -> None:
    assert STRATEGY.build_strategy() is not STRATEGY.build_strategy()
    between_decisions = SimpleNamespace(**vars(context))
    between_decisions.decision_time = context.decision_time + pd.Timedelta(hours=8)
    assert STRATEGY.build_strategy().target_weights(between_decisions, seed=SEED) is None

    insufficient = SimpleNamespace(
        decision_time=context.decision_time,
        bars={},
        funding=context.funding.iloc[0:0],
        auxiliary={},
        eligible_symbols=(),
    )
    assert STRATEGY.build_strategy().target_weights(insufficient, seed=SEED) == {}


def test_valid_weekly_book_is_two_sided_capped_and_eligible(context: SimpleNamespace) -> None:
    weights = _weights(context)
    assert len(weights) == 16
    assert set(weights) <= set(context.eligible_symbols) - {"BTCUSDT"}
    assert all(math.isfinite(value) for value in weights.values())
    assert math.fsum(abs(value) for value in weights.values()) == pytest.approx(0.80, abs=1e-12)
    assert math.fsum(weights.values()) == pytest.approx(0.0, abs=1e-12)
    assert math.fsum(value for value in weights.values() if value > 0.0) == pytest.approx(
        0.40, abs=1e-12
    )
    assert math.fsum(value for value in weights.values() if value < 0.0) == pytest.approx(
        -0.40, abs=1e-12
    )
    assert max(abs(value) for value in weights.values()) <= 0.075 + 1e-12


def _with_corrupt_future(context: SimpleNamespace) -> SimpleNamespace:
    result = SimpleNamespace(**vars(context))
    result.bars = {}
    for symbol, frame in context.bars.items():
        future = pd.DataFrame(
            {
                "open_time": [context.decision_time, context.decision_time + pd.Timedelta(hours=8)],
                "symbol": [symbol, symbol],
                "open": [np.inf, -np.inf],
                "close": [np.nan, np.inf],
                "quote_volume": [np.inf, -1.0],
                "taker_buy_quote_volume": [np.nan, np.inf],
            }
        )
        result.bars[symbol] = pd.concat([frame, future], ignore_index=True)
    future_funding = pd.DataFrame(
        {
            "funding_time": [context.decision_time, context.decision_time + pd.Timedelta(days=1)],
            "symbol": ["C00USDT", "C01USDT"],
            "funding_rate": [np.inf, np.nan],
            "mark_price": [np.inf, np.nan],
        }
    )
    result.funding = pd.concat([context.funding, future_funding], ignore_index=True)
    return result


def test_append_and_corrupt_future_are_bit_identical(context: SimpleNamespace) -> None:
    baseline = _weights(context)
    assert baseline == _weights(context)
    corrupted = _weights(_with_corrupt_future(context))
    assert baseline == corrupted


def test_gap_only_invalidates_crossing_computations_and_fails_flat(
    context: SimpleNamespace,
) -> None:
    gapped = SimpleNamespace(**vars(context))
    gapped.bars = {symbol: frame.iloc[:-1].copy() for symbol, frame in context.bars.items()}
    assert STRATEGY.build_strategy().target_weights(gapped, seed=SEED) == {}


def test_duplicate_funding_timestamp_fails_closed(context: SimpleNamespace) -> None:
    duplicated = SimpleNamespace(**vars(context))
    duplicated.funding = pd.concat(
        [context.funding, context.funding.iloc[[0]]],
        ignore_index=True,
    )
    assert STRATEGY.build_strategy().target_weights(duplicated, seed=SEED) == {}


def test_historical_beta_excludes_the_current_return() -> None:
    config = STRATEGY._Config()
    btc = np.linspace(-0.02, 0.02, 130, dtype=np.float64)
    asset = 2.0 * btc
    asset[-1] = 100.0 * btc[-1]
    beta, residual, _ = STRATEGY._rolling_residuals(asset, btc, config)
    assert beta[-1] == pytest.approx(2.0, abs=1e-12)
    assert residual[-1] == pytest.approx(asset[-1] - 2.0 * btc[-1], abs=1e-12)

    btc[-50] = np.nan
    beta_after_gap, _, _ = STRATEGY._rolling_residuals(asset, btc, config)
    assert np.isnan(beta_after_gap[-1])


def test_ordinal_rank_breaks_exact_ties_by_symbol() -> None:
    assert STRATEGY._ordinal_rank({"B": 1.0, "A": 1.0, "C": 2.0}) == {
        "A": -1.0,
        "B": 0.0,
        "C": 1.0,
    }


def test_tiny_nonzero_flow_is_kept_and_side_rms_normalized() -> None:
    config = STRATEGY._Config()
    quote_volume = np.full(317, 10_000_000.0)
    residual = 0.002 * np.sin(np.arange(317, dtype=np.float64) * 0.19)

    def slopes(imbalance_magnitude: float):
        taker_buy_quote_volume = 0.5 * quote_volume
        for event_number, event_index in enumerate(range(130, 311, 7)):
            quote_volume[event_index] = 100_000_000.0
            sign = 1.0 if event_number % 2 == 0 else -1.0
            imbalance = sign * imbalance_magnitude
            taker_buy_quote_volume[event_index] = (
                (imbalance + 1.0) * quote_volume[event_index] / 2.0
            )
        return STRATEGY._event_slopes(
            quote_volume,
            taker_buy_quote_volume,
            residual,
            config,
        )

    below_old_cutoff = slopes(0.01)
    rescaled = slopes(0.02)
    assert below_old_cutoff is not None
    assert rescaled is not None
    assert below_old_cutoff == pytest.approx(rescaled, abs=1e-12)
