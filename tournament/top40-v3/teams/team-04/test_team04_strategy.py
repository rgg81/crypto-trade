"""Focused synthetic tests for Team 04; no market data or evaluator is used."""

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
TEAM03_DIR = TEAM_DIR.parent / "team-03"
DECISION_TIME = pd.Timestamp("2023-06-26T00:00:00Z")
SEED = 20260718


def _load_strategy(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


strategy_module = _load_strategy(
    TEAM_DIR / "strategy.py",
    "_top40_v3_team04_strategy_test",
)
team03_module = _load_strategy(
    TEAM03_DIR / "strategy.py",
    "_top40_v3_team03_distinctness_test",
)


def _symbols(count: int = 32) -> tuple[str, ...]:
    return tuple(f"D{index:02d}USDT" for index in range(count))


def _bar_frame(symbol: str, index: int, *, days: int = 60) -> pd.DataFrame:
    times = pd.date_range(
        start=DECISION_TIME - pd.Timedelta(days=days),
        end=DECISION_TIME - pd.Timedelta(hours=8),
        freq="8h",
    )
    downside_intensity = index / 31.0
    lottery_intensity = 1.0 - downside_intensity
    price = 80.0 + index
    rows: list[dict[str, object]] = []
    for step, open_time in enumerate(times):
        common = 0.00055 * math.sin(0.13 * step) + 0.00020 * math.cos(0.05 * step)
        downside = -0.0040 * downside_intensity if step % 19 in {0, 1} else 0.0
        lottery = 0.0040 * lottery_intensity if step % 23 in {0, 1} else 0.0
        idiosyncratic = 0.00004 * math.sin(0.29 * step + 0.17 * index)
        price *= math.exp(common + downside + lottery + idiosyncratic)
        rows.append(
            {
                "open_time": open_time,
                "symbol": symbol,
                "open": price * 0.999,
                "high": price * 1.002,
                "low": price * 0.998,
                "close": price,
                "volume": 100_000.0,
                "quote_volume": 9_000_000.0 + 50_000.0 * index,
                "trade_count": 1_000 + index,
                "taker_buy_quote_volume": 4_500_000.0,
            }
        )
    return pd.DataFrame(rows)


def _context(*, days: int = 60) -> DecisionContext:
    symbols = _symbols()
    bars = {symbol: _bar_frame(symbol, index, days=days) for index, symbol in enumerate(symbols)}
    bars["FORBIDDENUSDT"] = _bar_frame("FORBIDDENUSDT", 0, days=days)
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


def test_weekly_schedule_and_frozen_seed() -> None:
    context = _context()
    assert isinstance(_weights(context), dict)
    off_schedule = dataclasses.replace(
        context,
        decision_time=DECISION_TIME + pd.Timedelta(days=1),
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


def test_missing_or_noncontiguous_history_requests_flat() -> None:
    context = _context()
    shortened = {
        symbol: frame if index < 5 else frame.tail(100)
        for index, (symbol, frame) in enumerate(context.bars.items())
    }
    assert _weights(dataclasses.replace(context, bars=shortened)) == {}

    gapped = {
        symbol: frame.drop(frame.index[-20]) if symbol in context.eligible_symbols else frame
        for symbol, frame in context.bars.items()
    }
    assert _weights(dataclasses.replace(context, bars=gapped)) == {}


def test_downside_and_lottery_components_have_separate_preregistered_signs() -> None:
    context = _context()
    features = strategy_module._risk_decomposition_components(context)
    scores = strategy_module._risk_decomposition_scores(context)

    assert len(features) >= 24
    assert features["D31USDT"].downside_semivariance > features["D00USDT"].downside_semivariance
    assert features["D00USDT"].positive_jump_variance > features["D31USDT"].positive_jump_variance
    assert scores["D31USDT"] > scores["D00USDT"]


def test_team03_and_team04_features_are_genuinely_distinct() -> None:
    context = _context()
    team03_features = team03_module._anti_euphoria_components(context)
    team04_features = strategy_module._risk_decomposition_components(context)
    team03_scores = team03_module._anti_euphoria_scores(context)
    team04_scores = strategy_module._risk_decomposition_scores(context)

    assert team03_features and team04_features
    assert {field.name for field in dataclasses.fields(team03_module.AntiEuphoriaFeature)} == {
        "positive_jump_variance",
        "positive_tail_share",
        "residual_skew",
        "positive_tail_breadth",
    }
    assert {field.name for field in dataclasses.fields(strategy_module.RiskDecompositionFeature)} == {
        "downside_semivariance",
        "positive_jump_variance",
        "total_residual_variance",
        "market_beta",
    }
    assert team03_scores != team04_scores
