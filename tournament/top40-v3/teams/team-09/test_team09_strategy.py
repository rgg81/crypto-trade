"""Focused synthetic tests for Team 09; no market data or evaluator is used."""

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
    name = "_top40_v3_team09_strategy_test"
    spec = importlib.util.spec_from_file_location(name, TEAM_DIR / "strategy.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


strategy_module = _load_strategy()


def _symbols(count: int = 24) -> tuple[str, ...]:
    return tuple(f"F{index:02d}USDT" for index in range(count))


def _bars(symbol: str, index: int, *, periods: int = 40) -> pd.DataFrame:
    times = pd.date_range(
        end=DECISION_TIME - pd.Timedelta(hours=8),
        periods=periods,
        freq="8h",
    )
    price = 100.0 + index
    if index < 8:
        residual_drift = 0.0004
    elif index >= 16:
        residual_drift = -0.0010
    else:
        residual_drift = 0.0
    rows: list[dict[str, object]] = []
    for step, open_time in enumerate(times):
        common = 0.0001 * math.sin(0.23 * step)
        price *= math.exp(common + residual_drift)
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


def _funding(symbols: tuple[str, ...]) -> pd.DataFrame:
    times = pd.date_range(
        start=DECISION_TIME - pd.Timedelta(days=30),
        end=DECISION_TIME - pd.Timedelta(hours=8),
        freq="8h",
    )
    midpoint = (len(symbols) - 1) / 2.0
    rows: list[dict[str, object]] = []
    for index, symbol in enumerate(symbols):
        rate = (index - midpoint) * 2.0e-6
        for timestamp in times:
            rows.append(
                {
                    "funding_time": timestamp,
                    "symbol": symbol,
                    "funding_rate": rate,
                    "mark_price": 100.0 + index,
                }
            )
    return pd.DataFrame(rows)


def _context() -> DecisionContext:
    symbols = _symbols()
    return DecisionContext(
        decision_time=DECISION_TIME,
        bars={symbol: _bars(symbol, index) for index, symbol in enumerate(symbols)},
        funding=_funding(symbols),
        auxiliary={},
        eligible_symbols=tuple(reversed(symbols)),
    )


def _weights(context: DecisionContext) -> dict[str, float] | None:
    return strategy_module.build_strategy().target_weights(context, seed=SEED)


def test_daily_schedule_and_stale_history_flat_behavior() -> None:
    context = _context()
    assert isinstance(_weights(context), dict)
    off_schedule = dataclasses.replace(
        context,
        decision_time=DECISION_TIME + pd.Timedelta(hours=8),
    )
    assert _weights(off_schedule) is None
    stale = context.funding.loc[
        pd.to_datetime(context.funding["funding_time"], utc=True)
        < DECISION_TIME - pd.Timedelta(hours=12)
    ]
    assert _weights(dataclasses.replace(context, funding=stale)) == {}


def test_deterministic_under_input_reordering() -> None:
    context = _context()
    first = _weights(context)
    reordered = dataclasses.replace(
        context,
        bars=dict(reversed(tuple(context.bars.items()))),
        funding=context.funding.iloc[::-1].reset_index(drop=True),
        eligible_symbols=tuple(reversed(context.eligible_symbols)),
    )
    assert first == _weights(context) == _weights(reordered)


def test_targets_are_bounded_and_have_positive_expected_carry() -> None:
    context = _context()
    weights = _weights(context)
    assert isinstance(weights, dict) and weights
    features = strategy_module._funding_features(
        context.funding,
        eligible_symbols=tuple(sorted(context.eligible_symbols)),
        decision_time=DECISION_TIME,
        parameters=strategy_module._REFERENCE,
    )
    expected_carry = math.fsum(
        -weight * features[symbol].expected_rate_per_day
        for symbol, weight in weights.items()
    )
    assert expected_carry > 0.0
    assert set(weights).issubset(set(context.eligible_symbols))
    assert max(abs(value) for value in weights.values()) <= 0.03 + 1e-12
    assert math.fsum(abs(value) for value in weights.values()) <= 0.5 + 1e-12
    assert abs(math.fsum(weights.values())) <= 0.05 + 1e-12


def test_price_weakness_sizes_carry_but_cannot_veto_the_book() -> None:
    context = _context()
    features = strategy_module._funding_features(
        context.funding,
        eligible_symbols=tuple(sorted(context.eligible_symbols)),
        decision_time=DECISION_TIME,
        parameters=strategy_module._REFERENCE,
    )
    quiet_price = {
        symbol: strategy_module.PriceState(
            residual_three_bar=0.01,
            residual_nine_bar=0.02,
        )
        for symbol in features
    }
    baseline = strategy_module._portfolio(
        features,
        quiet_price,
        parameters=strategy_module._REFERENCE,
    )
    assert baseline

    most_crowded = max(
        (symbol for symbol in baseline if baseline[symbol] < 0.0),
        key=lambda symbol: features[symbol].expected_rate_per_day,
    )
    weak_price = dict(quiet_price)
    weak_price[most_crowded] = strategy_module.PriceState(
        residual_three_bar=-0.04,
        residual_nine_bar=-0.08,
    )
    tilted = strategy_module._portfolio(
        features,
        weak_price,
        parameters=strategy_module._REFERENCE,
    )
    assert tilted
    assert tilted.keys() == baseline.keys()
    assert all(
        math.copysign(1.0, tilted[symbol])
        == math.copysign(1.0, baseline[symbol])
        for symbol in baseline
    )
    assert abs(tilted[most_crowded]) > abs(baseline[most_crowded])


def test_delayed_settlement_is_not_backfilled() -> None:
    context = _context()
    symbol = _symbols()[0]
    delayed = context.funding.copy(deep=True)
    symbol_rows = delayed.index[delayed["symbol"].eq(symbol)]
    latest_index = symbol_rows[-1]
    delayed.loc[latest_index, "funding_time"] = DECISION_TIME
    features = strategy_module._funding_features(
        delayed,
        eligible_symbols=tuple(sorted(context.eligible_symbols)),
        decision_time=DECISION_TIME,
        parameters=strategy_module._REFERENCE,
    )
    assert symbol not in features


def test_future_rows_cannot_change_targets() -> None:
    context = _context()
    baseline = _weights(context)
    bars: dict[str, pd.DataFrame] = {}
    for symbol, frame in context.bars.items():
        future = frame.iloc[[-1]].copy(deep=True)
        future.loc[:, "open_time"] = DECISION_TIME
        future.loc[:, "close"] = np.nan
        bars[symbol] = pd.concat([frame, future], ignore_index=True)
    future_funding = pd.DataFrame(
        [
            {
                "funding_time": DECISION_TIME,
                "symbol": symbol,
                "funding_rate": np.nan,
                "mark_price": 1.0,
            }
            for symbol in context.eligible_symbols
        ]
    )
    funding = pd.concat([context.funding, future_funding], ignore_index=True)
    assert _weights(dataclasses.replace(context, bars=bars, funding=funding)) == baseline
