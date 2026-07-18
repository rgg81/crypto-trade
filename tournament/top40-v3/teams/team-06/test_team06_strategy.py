"""Focused synthetic tests for Team 06; no market data or evaluator is used."""

from __future__ import annotations

import dataclasses
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext


TEAM_DIR = Path(__file__).resolve().parent
DECISION_TIME = pd.Timestamp("2023-06-26T00:00:00Z")
SEED = 20260718


def _load_strategy():
    name = "_top40_v3_team06_strategy_test"
    spec = importlib.util.spec_from_file_location(name, TEAM_DIR / "strategy.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


strategy_module = _load_strategy()


def _symbols(count: int = 16) -> tuple[str, ...]:
    return tuple(f"T{index:02d}USDT" for index in range(count))


def _bar_frame(symbol: str, index: int, *, periods: int = 100) -> pd.DataFrame:
    times = pd.date_range(
        end=DECISION_TIME - pd.Timedelta(hours=8),
        periods=periods,
        freq="8h",
    )
    direction = 1.0 if index < 8 else -1.0
    price = 100.0 + index
    rows: list[dict[str, object]] = []
    for step, open_time in enumerate(times):
        amplitude = 0.00025 + 0.00002 * (index % 4)
        log_return = direction * 0.0009 + amplitude * math.sin(0.31 * step + 0.17 * index)
        price *= math.exp(log_return)
        rows.append(
            {
                "open_time": open_time,
                "symbol": symbol,
                "open": price * 0.999,
                "high": price * 1.001,
                "low": price * 0.998,
                "close": price,
                "volume": 100_000.0,
                "quote_volume": 10_000_000.0,
            }
        )
    return pd.DataFrame(rows)


def _context(*, periods: int = 100) -> DecisionContext:
    symbols = _symbols()
    bars = {
        symbol: _bar_frame(symbol, index, periods=periods)
        for index, symbol in enumerate(symbols)
    }
    return DecisionContext(
        decision_time=DECISION_TIME,
        bars=bars,
        funding=pd.DataFrame(
            columns=["funding_time", "symbol", "funding_rate", "mark_price"]
        ),
        auxiliary={},
        eligible_symbols=tuple(reversed(symbols)),
    )


def _weights(context: DecisionContext) -> dict[str, float] | None:
    return strategy_module.build_strategy().target_weights(context, seed=SEED)


def test_daily_schedule_and_flat_history_behavior() -> None:
    context = _context()
    assert isinstance(_weights(context), dict)
    off_schedule = dataclasses.replace(
        context,
        decision_time=DECISION_TIME + pd.Timedelta(hours=8),
    )
    assert _weights(off_schedule) is None
    shortened = {symbol: frame.tail(40) for symbol, frame in context.bars.items()}
    assert _weights(dataclasses.replace(context, bars=shortened)) == {}


def test_deterministic_under_input_reordering() -> None:
    context = _context()
    first = _weights(context)
    reordered = dataclasses.replace(
        context,
        bars=dict(reversed(tuple(context.bars.items()))),
        eligible_symbols=tuple(reversed(context.eligible_symbols)),
    )
    assert first == _weights(context) == _weights(reordered)


def test_targets_respect_membership_and_exposure_bounds() -> None:
    context = _context()
    weights = _weights(context)
    assert isinstance(weights, dict) and weights
    assert set(weights).issubset(set(context.eligible_symbols))
    assert any(value > 0.0 for value in weights.values())
    assert any(value < 0.0 for value in weights.values())
    assert max(abs(value) for value in weights.values()) <= 0.03 + 1e-12
    assert math.fsum(abs(value) for value in weights.values()) <= 0.5 + 1e-12
    assert abs(math.fsum(weights.values())) <= 0.20 + 1e-12


def test_future_rows_cannot_change_targets() -> None:
    context = _context()
    baseline = _weights(context)
    changed: dict[str, pd.DataFrame] = {}
    for symbol, frame in context.bars.items():
        future = frame.iloc[[-1]].copy(deep=True)
        future.loc[:, "open_time"] = DECISION_TIME
        future.loc[:, "close"] = np.nan
        changed[symbol] = pd.concat([frame, future], ignore_index=True)
    assert _weights(dataclasses.replace(context, bars=changed)) == baseline


def test_each_direction_comes_from_own_history() -> None:
    context = _context()
    weights = _weights(context)
    assert isinstance(weights, dict) and weights
    for index, symbol in enumerate(_symbols()):
        assert math.copysign(1.0, weights[symbol]) == (1.0 if index < 8 else -1.0)
