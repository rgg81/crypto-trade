from __future__ import annotations

import dataclasses
import importlib.util
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

TEAM_DIR = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("team07_strategy", TEAM_DIR / "strategy.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _context(*, periods: int = 220, decision: str = "2021-04-01T00:00:00Z"):
    decision_time = pd.Timestamp(decision)
    times = pd.date_range(end=decision_time - pd.Timedelta(hours=8), periods=periods, freq="8h")
    index = np.arange(periods, dtype=float)
    leader = 0.010 * np.sin(index / 5.0) + 0.006 * np.cos(index / 13.0)
    symbols = tuple(f"C{i:02d}USDT" for i in range(20))
    bars: dict[str, pd.DataFrame] = {}
    for number, symbol in enumerate(symbols):
        lag_beta = 0.10 + 0.025 * number
        contemporaneous = 0.65 + 0.01 * (number % 4)
        idiosyncratic = 0.0025 * np.sin(index / (3.0 + number / 8.0) + number)
        log_return = contemporaneous * leader + lag_beta * np.roll(leader, 1) + idiosyncratic
        log_return[0] = idiosyncratic[0]
        close = (50.0 + number) * np.exp(np.cumsum(log_return))
        bars[symbol] = pd.DataFrame(
            {
                "open_time": times,
                "symbol": symbol,
                "open": close * 0.999,
                "high": close * 1.002,
                "low": close * 0.998,
                "close": close,
                "quote_volume": np.full(periods, 10_000_000.0 - number * 200_000.0),
            }
        )
    funding = pd.DataFrame(columns=["funding_time", "symbol", "funding_rate", "mark_price"])
    return SimpleNamespace(
        decision_time=decision_time,
        bars=bars,
        funding=funding,
        auxiliary={},
        eligible_symbols=symbols,
    )


def test_strategy_is_deterministic_finite_and_two_sided() -> None:
    context = _context()
    first = MODULE.build_strategy().target_weights(context, seed=20260801)
    second = MODULE.build_strategy().target_weights(context, seed=20260801)
    assert first == second
    assert first
    assert set(first).issubset(context.eligible_symbols)
    assert all(math.isfinite(value) for value in first.values())
    assert any(value > 0 for value in first.values())
    assert any(value < 0 for value in first.values())
    assert sum(abs(value) for value in first.values()) <= 0.80 + 1e-9
    assert abs(sum(first.values())) <= 0.16 + 1e-9
    assert max(abs(value) for value in first.values()) <= 0.09 + 1e-9


def test_inputs_are_not_mutated() -> None:
    context = _context()
    copies = {symbol: frame.copy(deep=True) for symbol, frame in context.bars.items()}
    MODULE.build_strategy().target_weights(context, seed=20260801)
    for symbol, expected in copies.items():
        pdt.assert_frame_equal(context.bars[symbol], expected)


def test_future_bar_is_rejected_fail_closed() -> None:
    context = _context()
    symbol = context.eligible_symbols[0]
    future = context.bars[symbol].iloc[[-1]].copy()
    future["open_time"] = context.decision_time
    future["close"] = 1e100
    context.bars[symbol] = pd.concat([context.bars[symbol], future], ignore_index=True)
    with pytest.raises(ValueError, match="not closed"):
        MODULE.build_strategy().target_weights(context, seed=20260801)


def test_corrupt_past_and_duplicate_timestamp_are_rejected() -> None:
    context = _context()
    symbol = context.eligible_symbols[0]
    context.bars[symbol].loc[10, "close"] = np.inf
    with pytest.raises(ValueError, match="invalid|non-finite"):
        MODULE.build_strategy().target_weights(context, seed=20260801)

    context = _context()
    symbol = context.eligible_symbols[0]
    duplicate = context.bars[symbol].iloc[[-1]].copy()
    context.bars[symbol] = pd.concat([context.bars[symbol], duplicate], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        MODULE.build_strategy().target_weights(context, seed=20260801)


def test_append_and_future_corruption_invariance_after_authorized_truncation() -> None:
    base = _context()
    reference = MODULE.build_strategy().target_weights(base, seed=20260801)
    for magnitude in (1e-100, 1e100):
        altered = _context()
        for symbol, frame in altered.bars.items():
            future = frame.iloc[[-1]].copy()
            future["open_time"] = altered.decision_time + pd.Timedelta(hours=8)
            future["close"] = magnitude
            full = pd.concat([frame, future], ignore_index=True)
            close_time = pd.to_datetime(full["open_time"], utc=True) + pd.Timedelta(hours=8)
            altered.bars[symbol] = full.loc[close_time <= altered.decision_time].copy()
        assert MODULE.build_strategy().target_weights(altered, seed=20260801) == reference


def test_insufficient_history_requests_flat() -> None:
    context = _context(periods=80)
    assert MODULE.build_strategy().target_weights(context, seed=20260801) == {}


def test_non_rebalance_boundary_holds() -> None:
    context = _context(decision="2021-04-01T08:00:00Z")
    assert MODULE.build_strategy().target_weights(context, seed=20260801) is None


def test_funding_at_or_after_boundary_is_rejected() -> None:
    context = _context()
    context.funding = pd.DataFrame(
        {
            "funding_time": [context.decision_time],
            "symbol": [context.eligible_symbols[0]],
            "funding_rate": [0.0001],
            "mark_price": [100.0],
        }
    )
    with pytest.raises(ValueError, match="unavailable"):
        MODULE.build_strategy().target_weights(context, seed=20260801)


def test_full_eligible_funding_accepts_an_underhistory_new_member() -> None:
    context = _context()
    new_symbol = "NEWUSDT"
    new_frame = context.bars[context.eligible_symbols[-1]].tail(100).copy()
    new_frame["symbol"] = new_symbol
    context.bars[new_symbol] = new_frame
    context.eligible_symbols = (*context.eligible_symbols, new_symbol)
    context.funding = pd.DataFrame(
        {
            "funding_time": [
                context.decision_time - pd.Timedelta(hours=16),
                context.decision_time - pd.Timedelta(hours=8),
            ],
            "symbol": [context.eligible_symbols[0], new_symbol],
            "funding_rate": [0.0002, -0.0003],
            "mark_price": [100.0, 10.0],
        }
    )
    targets = MODULE.build_strategy().target_weights(context, seed=20260801)
    assert targets and new_symbol not in targets
    carry = MODULE._past_funding_carry(
        context.funding,
        context.decision_time,
        set(context.eligible_symbols),
        21,
    )
    assert carry[context.eligible_symbols[0]] > 0
    assert carry[new_symbol] < 0


def test_missing_bar_does_not_compress_time_and_stale_leaders_flatten() -> None:
    context = _context()
    symbol = context.eligible_symbols[0]
    missing_time = pd.Timestamp(context.bars[symbol].iloc[101]["open_time"])
    context.bars[symbol] = context.bars[symbol].drop(index=100).reset_index(drop=True)
    returns, _liquidity = MODULE._closed_returns_and_liquidity(
        context.bars[symbol], context.decision_time, MODULE.StrategyConfig()
    )
    assert pd.isna(returns.loc[missing_time])

    stale = _context()
    for stale_symbol, frame in stale.bars.items():
        stale.bars[stale_symbol] = frame.iloc[:-1].copy()
    assert MODULE.build_strategy().target_weights(stale, seed=20260801) == {}


def test_declared_neighbors_validate_and_produce_feasible_two_sided_targets() -> None:
    neighborhood = json.loads((TEAM_DIR / "parameter_neighborhood.json").read_text())
    center = MODULE.StrategyConfig()
    context = _context(periods=260)
    for neighbor in neighborhood["neighbors"]:
        config = dataclasses.replace(center, **neighbor["changes"])
        targets = MODULE.ShockDiffusionStrategy(config).target_weights(context, seed=20260801)
        assert targets, neighbor["neighbor_id"]
        assert any(value > 0 for value in targets.values())
        assert any(value < 0 for value in targets.values())


def test_input_order_is_not_scientific_information() -> None:
    baseline = _context()
    expected = MODULE.build_strategy().target_weights(baseline, seed=20260801)
    permuted = _context()
    permuted.eligible_symbols = tuple(reversed(permuted.eligible_symbols))
    permuted.bars = dict(reversed(tuple(permuted.bars.items())))
    assert MODULE.build_strategy().target_weights(permuted, seed=20260801) == expected


def test_configuration_rejects_a_trend_window_shorter_than_required_history() -> None:
    with pytest.raises(ValueError, match="trend window"):
        MODULE.StrategyConfig(trend_bars=125).validate()


def test_seed_and_context_membership_are_bound() -> None:
    context = _context()
    with pytest.raises(ValueError, match="seed"):
        MODULE.build_strategy().target_weights(context, seed=1)
    del context.bars[context.eligible_symbols[0]]
    with pytest.raises(ValueError, match="exactly match"):
        MODULE.build_strategy().target_weights(context, seed=20260801)
