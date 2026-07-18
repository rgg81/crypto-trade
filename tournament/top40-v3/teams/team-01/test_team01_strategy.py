"""Focused synthetic tests for Team 01; no market data or evaluator is used."""

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
    name = "_top40_v3_team01_strategy_test"
    spec = importlib.util.spec_from_file_location(name, TEAM_DIR / "strategy.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


strategy_module = _load_strategy()


def _symbols(count: int = 24) -> tuple[str, ...]:
    return tuple(f"C{index:02d}USDT" for index in range(count))


def _bar_frame(symbol: str, index: int, *, days: int = 120) -> pd.DataFrame:
    times = pd.date_range(
        start=DECISION_TIME - pd.Timedelta(days=days),
        end=DECISION_TIME - pd.Timedelta(hours=8),
        freq="8h",
    )
    midpoint = 11.5
    price = 100.0 + index
    rows: list[dict[str, object]] = []
    for step, open_time in enumerate(times):
        weekday_edge = (index - midpoint) * 0.00009 if open_time.weekday() == 0 else 0.0
        common = 0.00012 * math.sin(0.17 * step)
        idiosyncratic = 0.00001 * math.cos(0.11 * step + 0.23 * index)
        price *= math.exp(weekday_edge / 3.0 + common + idiosyncratic)
        rows.append(
            {
                "open_time": open_time,
                "symbol": symbol,
                "open": price * 0.999,
                "high": price * 1.001,
                "low": price * 0.998,
                "close": price,
                "volume": 100_000.0,
                "quote_volume": 10_000_000.0 + 1_000.0 * index,
                "trade_count": 1_000 + index,
                "taker_buy_quote_volume": 5_000_000.0,
            }
        )
    return pd.DataFrame(rows)


def _context(*, days: int = 120) -> DecisionContext:
    symbols = _symbols()
    bars = {symbol: _bar_frame(symbol, index, days=days) for index, symbol in enumerate(symbols)}
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


def test_daily_schedule_holds_off_boundary() -> None:
    scheduled = _context()
    assert isinstance(_weights(scheduled), dict)
    off_schedule = dataclasses.replace(
        scheduled,
        decision_time=DECISION_TIME + pd.Timedelta(hours=8),
    )
    assert _weights(off_schedule) is None


def test_deterministic_order_independent_targets() -> None:
    context = _context()
    first = _weights(context)
    second = _weights(context)
    reordered = dataclasses.replace(
        context,
        bars=dict(reversed(tuple(context.bars.items()))),
        eligible_symbols=tuple(reversed(context.eligible_symbols)),
    )
    assert first == second == _weights(reordered)


def test_weights_are_broad_bounded_and_neutral() -> None:
    weights = _weights(_context())
    assert isinstance(weights, dict) and weights
    longs = [value for value in weights.values() if value > 0.0]
    shorts = [value for value in weights.values() if value < 0.0]
    assert len(longs) >= 8
    assert len(shorts) >= 8
    assert max(abs(value) for value in weights.values()) <= 0.03 + 1e-12
    assert math.fsum(abs(value) for value in weights.values()) <= 0.5 + 1e-12
    assert abs(math.fsum(weights.values())) <= 0.05 + 1e-12


def test_future_rows_cannot_change_targets() -> None:
    context = _context()
    baseline = _weights(context)
    changed: dict[str, pd.DataFrame] = {}
    for symbol, frame in context.bars.items():
        future = frame.iloc[[-1]].copy(deep=True)
        future.loc[:, "open_time"] = DECISION_TIME
        future.loc[:, "close"] = np.nan
        changed[symbol] = pd.concat([frame, future], ignore_index=True)
    corrupted = dataclasses.replace(context, bars=changed)
    assert _weights(corrupted) == baseline


def test_missing_history_requests_flat_on_schedule() -> None:
    context = _context()
    shortened = {
        symbol: frame if index < 5 else frame.tail(45)
        for index, (symbol, frame) in enumerate(context.bars.items())
    }
    result = _weights(dataclasses.replace(context, bars=shortened))
    assert result == {}
