"""Focused synthetic tests for Team 07; no market data or evaluator is used."""

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
    name = "_top40_v3_team07_strategy_test"
    spec = importlib.util.spec_from_file_location(name, TEAM_DIR / "strategy.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


strategy_module = _load_strategy()


def _symbols(count: int = 32) -> tuple[str, ...]:
    return tuple(f"R{index:02d}USDT" for index in range(count))


def _bar_frame(symbol: str, index: int, *, days: int = 30) -> pd.DataFrame:
    times = pd.date_range(
        start=DECISION_TIME - pd.Timedelta(days=days),
        end=DECISION_TIME - pd.Timedelta(hours=8),
        freq="8h",
    )
    deep_liquidity = index % 2 == 0
    direction = (index - 15.5) / 15.5
    price = 70.0 + index
    rows: list[dict[str, object]] = []
    for step, open_time in enumerate(times):
        is_recent = step >= len(times) - 3
        common = 0.00045 * math.sin(0.13 * step)
        residual_move = 0.0012 * direction if is_recent else 0.00003 * math.sin(
            0.27 * step + index
        )
        log_return = common + residual_move
        price *= math.exp(log_return)
        baseline_quote = 5_000_000.0 * (1.0 + 0.03 * math.sin(0.11 * step))
        baseline_trades = 1_000.0 * (1.0 + 0.03 * math.cos(0.09 * step))
        if is_recent and deep_liquidity:
            quote_volume = baseline_quote * 3.0
            trade_count = baseline_trades * 3.0
            range_fraction = 0.0007
            taker_share = 0.72 if direction > 0.0 else 0.28
        elif is_recent:
            quote_volume = baseline_quote * 0.25
            trade_count = baseline_trades * 0.30
            range_fraction = 0.015
            taker_share = 0.28 if direction > 0.0 else 0.72
        else:
            quote_volume = baseline_quote
            trade_count = baseline_trades
            range_fraction = 0.002
            taker_share = 0.50
        rows.append(
            {
                "open_time": open_time,
                "symbol": symbol,
                "open": price * math.exp(-0.5 * log_return),
                "high": price * math.exp(0.5 * range_fraction),
                "low": price * math.exp(-0.5 * range_fraction),
                "close": price,
                "volume": 100_000.0,
                "quote_volume": quote_volume,
                "trade_count": trade_count,
                "taker_buy_quote_volume": quote_volume * taker_share,
            }
        )
    return pd.DataFrame(rows)


def _context(*, days: int = 30) -> DecisionContext:
    symbols = _symbols()
    bars = {symbol: _bar_frame(symbol, index, days=days) for index, symbol in enumerate(symbols)}
    bars["FORBIDDENUSDT"] = _bar_frame("FORBIDDENUSDT", 30, days=days)
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


def test_weights_are_broad_bounded_neutral_and_eligible_only() -> None:
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
    assert math.fsum(abs(value) for value in weights.values()) <= 0.5 + 1e-12
    assert abs(math.fsum(weights.values())) <= 0.05 + 1e-12


def test_liquidity_state_routes_the_same_move_to_opposite_branches() -> None:
    continuation = strategy_module._smooth_router(
        quote_volume_state=0.8,
        trade_breadth_state=0.8,
        price_impact_state=-0.8,
        flow_confirmation=0.5,
    )
    reversal = strategy_module._smooth_router(
        quote_volume_state=-0.8,
        trade_breadth_state=-0.8,
        price_impact_state=0.8,
        flow_confirmation=-0.5,
    )
    assert continuation > 0.0 > reversal
    assert 0.01 * continuation > 0.0 > 0.01 * reversal

    features = strategy_module._router_features(_context())
    deep = features["R30USDT"]
    displaced = features["R31USDT"]
    assert deep.recent_residual_move > 0.0
    assert displaced.recent_residual_move > 0.0
    assert deep.liquidity_router > 0.0 > displaced.liquidity_router
    assert deep.routed_expected_return > 0.0 > displaced.routed_expected_return


def test_future_rows_and_noneligible_data_cannot_change_targets() -> None:
    context = _context()
    baseline = _weights(context)
    changed: dict[str, pd.DataFrame] = {}
    for symbol, frame in context.bars.items():
        future = frame.iloc[[-1]].copy(deep=True)
        future.loc[:, "open_time"] = DECISION_TIME
        future.loc[:, "close"] = np.inf
        future.loc[:, "quote_volume"] = 0.0
        changed[symbol] = pd.concat([frame, future], ignore_index=True)
    changed["FORBIDDENUSDT"] = changed["FORBIDDENUSDT"].assign(close=1e30)

    assert _weights(dataclasses.replace(context, bars=changed)) == baseline


def test_missing_zero_volume_or_gapped_history_requests_flat() -> None:
    context = _context()
    shortened = {
        symbol: frame if index < 5 else frame.tail(50)
        for index, (symbol, frame) in enumerate(context.bars.items())
    }
    assert _weights(dataclasses.replace(context, bars=shortened)) == {}

    zero_volume = {
        symbol: frame.assign(quote_volume=0.0) if symbol in context.eligible_symbols else frame
        for symbol, frame in context.bars.items()
    }
    assert _weights(dataclasses.replace(context, bars=zero_volume)) == {}

    gapped = {
        symbol: frame.drop(frame.index[-10]) if symbol in context.eligible_symbols else frame
        for symbol, frame in context.bars.items()
    }
    assert _weights(dataclasses.replace(context, bars=gapped)) == {}
