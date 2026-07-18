"""Focused synthetic tests for Team 08; no market data or evaluator is used."""

from __future__ import annotations

import dataclasses
import importlib.util
import json
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
    name = "_top40_v3_team08_strategy_test"
    spec = importlib.util.spec_from_file_location(name, TEAM_DIR / "strategy.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


strategy_module = _load_strategy()


def _symbols(count: int = 32) -> tuple[str, ...]:
    return tuple(f"H{index:02d}USDT" for index in range(count))


def _bar_frame(symbol: str, index: int, *, days: int = 60) -> pd.DataFrame:
    times = pd.date_range(
        start=DECISION_TIME - pd.Timedelta(days=days),
        end=DECISION_TIME - pd.Timedelta(hours=8),
        freq="8h",
    )
    relative_trend = (index - 15.5) * 0.000018
    price = 90.0 + index
    rows: list[dict[str, object]] = []
    for step, open_time in enumerate(times):
        common = 0.00055 * math.sin(0.11 * step) + 0.00018 * math.cos(0.03 * step)
        idiosyncratic = 0.00006 * math.sin(0.23 * step + 0.19 * index)
        price *= math.exp(common + relative_trend + idiosyncratic)
        rows.append(
            {
                "open_time": open_time,
                "symbol": symbol,
                "open": price * 0.999,
                "high": price * 1.002,
                "low": price * 0.998,
                "close": price,
                "volume": 100_000.0,
                "quote_volume": 7_000_000.0 + 80_000.0 * index,
                "trade_count": 1_000 + index,
                "taker_buy_quote_volume": 3_500_000.0,
            }
        )
    return pd.DataFrame(rows)


def _context(*, days: int = 60) -> DecisionContext:
    symbols = _symbols()
    bars = {symbol: _bar_frame(symbol, index, days=days) for index, symbol in enumerate(symbols)}
    bars["FORBIDDENUSDT"] = _bar_frame("FORBIDDENUSDT", 31, days=days)
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


def test_daily_schedule_and_frozen_seed() -> None:
    context = _context()
    assert isinstance(_weights(context), dict)
    off_schedule = dataclasses.replace(
        context,
        decision_time=DECISION_TIME + pd.Timedelta(hours=8),
    )
    assert _weights(off_schedule) is None
    config = json.loads((TEAM_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    assert config["seed"] == SEED


def test_deterministic_order_independent_targets_and_ties() -> None:
    context = _context()
    first = _weights(context)
    second = _weights(context)
    reordered = dataclasses.replace(
        context,
        bars=dict(reversed(tuple(context.bars.items()))),
        eligible_symbols=tuple(reversed(context.eligible_symbols)),
    )
    assert first == second == _weights(reordered)
    tied = strategy_module._portfolio(
        {symbol: 1.0 for symbol in _symbols(24)},
        parameters=strategy_module.StrategyParameters(),
    )
    assert list(tied) == sorted(tied)

    stateful = strategy_module.build_strategy()
    duplicate_first = stateful.target_weights(context, seed=SEED)
    duplicate_second = stateful.target_weights(context, seed=SEED)
    assert duplicate_first == duplicate_second
    assert len(stateful._vintages) == 1


def test_weights_are_broad_bounded_exactly_neutral_and_eligible_only() -> None:
    context = _context()
    weights = _weights(context)

    assert isinstance(weights, dict) and weights
    assert set(weights).issubset(context.eligible_symbols)
    assert "FORBIDDENUSDT" not in weights
    longs = [value for value in weights.values() if value > 0.0]
    shorts = [value for value in weights.values() if value < 0.0]
    assert len(longs) >= 8
    assert len(shorts) >= 8
    assert max(abs(value) for value in weights.values()) <= 0.03 + 1e-12
    assert math.fsum(abs(value) for value in weights.values()) <= 0.44 / 3.0 + 1e-12
    assert abs(math.fsum(weights.values())) <= 1e-12


def test_three_daily_vintages_ramp_and_membership_exits_only_reduce_risk() -> None:
    parameters = strategy_module.StrategyParameters()
    longs = tuple((f"L{index}USDT", 0.0275) for index in range(8))
    shorts = tuple((f"S{index}USDT", -0.0275) for index in range(8))
    cohort = tuple(sorted((*longs, *shorts)))
    eligible = frozenset(symbol for symbol, _ in cohort)
    start = DECISION_TIME - pd.Timedelta(days=2)
    full_vintages = tuple(
        strategy_module.Vintage(
            decision_time=start + pd.Timedelta(days=offset),
            weights=cohort,
        )
        for offset in range(3)
    )

    ramp = strategy_module._aggregate_vintages(
        full_vintages[:1],
        eligible_symbols=eligible,
        parameters=parameters,
    )
    mature = strategy_module._aggregate_vintages(
        full_vintages,
        eligible_symbols=eligible,
        parameters=parameters,
    )
    one_short_exit = strategy_module._aggregate_vintages(
        full_vintages,
        eligible_symbols=eligible - {"S0USDT"},
        parameters=parameters,
    )
    excessive_short_exits = strategy_module._aggregate_vintages(
        full_vintages,
        eligible_symbols=frozenset(symbol for symbol, _ in longs),
        parameters=parameters,
    )

    assert math.isclose(math.fsum(abs(value) for value in ramp.values()), 0.44 / 3.0)
    assert math.isclose(math.fsum(abs(value) for value in mature.values()), 0.44)
    assert "S0USDT" not in one_short_exit
    assert all(
        math.isclose(one_short_exit[symbol], mature[symbol])
        for symbol in one_short_exit
    )
    assert excessive_short_exits == {}


def test_invalid_current_signal_clears_all_stored_vintages() -> None:
    context = _context()
    stateful = strategy_module.build_strategy()
    assert stateful.target_weights(context, seed=SEED)
    assert len(stateful._vintages) == 1

    invalid_next_day = dataclasses.replace(
        context,
        decision_time=DECISION_TIME + pd.Timedelta(days=1),
        bars={symbol: frame.tail(100) for symbol, frame in context.bars.items()},
    )
    assert stateful.target_weights(invalid_next_day, seed=SEED) == {}
    assert len(stateful._vintages) == 0


def test_three_horizons_agree_on_relative_leaders_and_laggards() -> None:
    context = _context()
    features = strategy_module._momentum_features(context)
    scores = strategy_module._momentum_scores(context)
    weights = _weights(context)

    assert len(features) >= 24
    assert features["H31USDT"].fast_scaled_momentum > 0.0
    assert features["H31USDT"].medium_scaled_momentum > 0.0
    assert features["H31USDT"].slow_scaled_momentum > 0.0
    assert features["H31USDT"].sign_consensus == 1.0
    assert features["H00USDT"].sign_consensus == -1.0
    assert scores["H31USDT"] > scores["H00USDT"]
    assert isinstance(weights, dict)
    assert weights["H31USDT"] > 0.0 > weights["H00USDT"]


def test_liquidity_can_filter_but_cannot_route_or_change_signal_sign() -> None:
    context = _context()
    baseline_features = strategy_module._momentum_features(context)
    baseline_weights = _weights(context)
    changed = {
        symbol: frame.assign(
            quote_volume=2_000_000.0
            + np.arange(len(frame), dtype=float) * (index + 1) * 10_000.0
        )
        if symbol in context.eligible_symbols
        else frame
        for index, (symbol, frame) in enumerate(context.bars.items())
    }
    changed_context = dataclasses.replace(context, bars=changed)

    assert strategy_module._momentum_features(changed_context) == baseline_features
    assert _weights(changed_context) == baseline_weights
    assert not hasattr(strategy_module, "_smooth_router")


def test_future_rows_and_noneligible_data_cannot_change_targets() -> None:
    context = _context()
    baseline = _weights(context)
    changed: dict[str, pd.DataFrame] = {}
    for symbol, frame in context.bars.items():
        future = frame.iloc[[-1]].copy(deep=True)
        future.loc[:, "open_time"] = DECISION_TIME
        future.loc[:, "close"] = np.inf
        future.loc[:, "quote_volume"] = np.inf
        changed[symbol] = pd.concat([frame, future], ignore_index=True)
    changed["FORBIDDENUSDT"] = changed["FORBIDDENUSDT"].assign(close=1e30)

    assert _weights(dataclasses.replace(context, bars=changed)) == baseline


def test_missing_illiquid_or_gapped_history_requests_flat() -> None:
    context = _context()
    shortened = {
        symbol: frame if index < 5 else frame.tail(100)
        for index, (symbol, frame) in enumerate(context.bars.items())
    }
    assert _weights(dataclasses.replace(context, bars=shortened)) == {}

    illiquid = {
        symbol: frame.assign(quote_volume=0.0) if symbol in context.eligible_symbols else frame
        for symbol, frame in context.bars.items()
    }
    assert _weights(dataclasses.replace(context, bars=illiquid)) == {}

    gapped = {
        symbol: frame.drop(frame.index[-20]) if symbol in context.eligible_symbols else frame
        for symbol, frame in context.bars.items()
    }
    assert _weights(dataclasses.replace(context, bars=gapped)) == {}
