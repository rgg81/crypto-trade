"""Focused synthetic tests for Team 02; no market data or evaluator is used."""

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
    name = "_top40_v3_team02_strategy_test"
    spec = importlib.util.spec_from_file_location(name, TEAM_DIR / "strategy.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


strategy_module = _load_strategy()


def _symbols(count: int = 24) -> tuple[str, ...]:
    return tuple(f"M{index:02d}USDT" for index in range(count))


def _bar_frame(symbol: str, index: int, *, days: int = 40) -> pd.DataFrame:
    times = pd.date_range(
        start=DECISION_TIME - pd.Timedelta(days=days),
        end=DECISION_TIME - pd.Timedelta(hours=8),
        freq="8h",
    )
    price = 50.0 + index
    lottery_day = (DECISION_TIME - pd.Timedelta(days=3)).floor("D")
    rows: list[dict[str, object]] = []
    for step, open_time in enumerate(times):
        common = 0.00008 * math.sin(0.19 * step)
        idiosyncratic = 0.00001 * math.cos(0.13 * step + 0.29 * index)
        lottery = (
            index * 0.00045
            if open_time.floor("D") == lottery_day and open_time.hour == 16
            else 0.0
        )
        price *= math.exp(common + idiosyncratic + lottery)
        rows.append(
            {
                "open_time": open_time,
                "symbol": symbol,
                "open": price * 0.999,
                "high": price * 1.001,
                "low": price * 0.998,
                "close": price,
                "volume": 100_000.0,
                "quote_volume": 8_000_000.0 + 100_000.0 * index,
                "trade_count": 1_000 + index,
                "taker_buy_quote_volume": 4_000_000.0,
            }
        )
    return pd.DataFrame(rows)


def _context(*, days: int = 40) -> DecisionContext:
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


def test_weights_are_broad_bounded_and_short_capped() -> None:
    weights = _weights(_context())
    assert isinstance(weights, dict) and weights
    longs = [value for value in weights.values() if value > 0.0]
    shorts = [value for value in weights.values() if value < 0.0]
    assert len(longs) >= 8
    assert len(shorts) >= 8
    assert max(longs) <= 0.03 + 1e-12
    assert max(abs(value) for value in shorts) <= 0.02 + 1e-12
    assert math.fsum(abs(value) for value in weights.values()) <= 0.5 + 1e-12
    assert abs(math.fsum(weights.values())) <= 0.05 + 1e-12
    assert math.fsum(abs(value) for value in shorts) <= 0.16 + 1e-12


def test_future_rows_cannot_change_targets() -> None:
    context = _context()
    baseline = _weights(context)
    changed: dict[str, pd.DataFrame] = {}
    for symbol, frame in context.bars.items():
        future = frame.iloc[[-1]].copy(deep=True)
        future.loc[:, "open_time"] = DECISION_TIME
        future.loc[:, "close"] = np.nan
        future.loc[:, "quote_volume"] = np.inf
        changed[symbol] = pd.concat([frame, future], ignore_index=True)
    assert _weights(dataclasses.replace(context, bars=changed)) == baseline


def test_missing_history_or_liquidity_requests_flat() -> None:
    context = _context()
    shortened = {
        symbol: frame if index < 5 else frame.tail(60)
        for index, (symbol, frame) in enumerate(context.bars.items())
    }
    assert _weights(dataclasses.replace(context, bars=shortened)) == {}

    illiquid = {
        symbol: frame.assign(quote_volume=0.0) if index >= 5 else frame
        for index, (symbol, frame) in enumerate(context.bars.items())
    }
    assert _weights(dataclasses.replace(context, bars=illiquid)) == {}
