"""Focused synthetic tests for Team 05; no market data or evaluator is used."""

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
    name = "_top40_v3_team05_strategy_test"
    spec = importlib.util.spec_from_file_location(name, TEAM_DIR / "strategy.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


strategy_module = _load_strategy()


def _pair_symbols(pair_count: int = 6) -> tuple[str, ...]:
    return tuple(
        symbol
        for pair in range(pair_count)
        for symbol in (f"P{pair:02d}AUSDT", f"P{pair:02d}BUSDT")
    )


def _bar_frame(symbol: str, log_closes: np.ndarray, times: pd.DatetimeIndex) -> pd.DataFrame:
    closes = np.exp(log_closes)
    return pd.DataFrame(
        {
            "open_time": times,
            "symbol": symbol,
            "open": closes * 0.999,
            "high": closes * 1.001,
            "low": closes * 0.998,
            "close": closes,
            "volume": 100_000.0,
            "quote_volume": 12_000_000.0,
        }
    )


def _context(*, periods: int = 300) -> DecisionContext:
    times = pd.date_range(
        end=DECISION_TIME - pd.Timedelta(hours=8),
        periods=periods,
        freq="8h",
    )
    bars: dict[str, pd.DataFrame] = {}
    for pair in range(6):
        factor_rng = np.random.default_rng(1_000 + pair)
        residual_rng = np.random.default_rng(2_000 + pair)
        factor = 4.0 + 0.15 * pair + np.cumsum(factor_rng.normal(0.0, 0.004, periods))
        residual = np.zeros(periods, dtype=float)
        for index in range(1, periods):
            residual[index] = 0.75 * residual[index - 1] + residual_rng.normal(0.0, 0.0005)
        residual[-1] += 0.0025 if pair % 2 == 0 else -0.0025
        left = 0.2 + 1.05 * factor + residual
        right = factor
        left_symbol = f"P{pair:02d}AUSDT"
        right_symbol = f"P{pair:02d}BUSDT"
        bars[left_symbol] = _bar_frame(left_symbol, left, times)
        bars[right_symbol] = _bar_frame(right_symbol, right, times)

    symbols = _pair_symbols()
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


def test_weekly_schedule_and_flat_history_behavior() -> None:
    context = _context()
    assert isinstance(_weights(context), dict)
    off_schedule = dataclasses.replace(
        context,
        decision_time=DECISION_TIME + pd.Timedelta(hours=8),
    )
    assert _weights(off_schedule) is None
    shortened = {symbol: frame.tail(100) for symbol, frame in context.bars.items()}
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


def test_pair_signal_has_correct_convergence_sign_and_causal_beta() -> None:
    context = _context()
    parameters = strategy_module.StrategyParameters()
    left = strategy_module._log_close_history(
        context.bars["P00AUSDT"],
        decision_time=DECISION_TIME,
        parameters=parameters,
    )
    right = strategy_module._log_close_history(
        context.bars["P00BUSDT"],
        decision_time=DECISION_TIME,
        parameters=parameters,
    )
    pair_signal = strategy_module._pair_convergence_signal(
        left,
        right,
        parameters=parameters,
    )
    assert pair_signal is not None
    left_conviction, beta = pair_signal
    assert left_conviction < 0.0  # the injected final left residual is rich
    assert math.isclose(beta, 1.05, rel_tol=0.03)


def test_overlap_aggregation_preserves_beta_legs_and_clipped_conviction(
    monkeypatch,
) -> None:
    histories = {
        symbol: pd.Series([float(index)], name=symbol)
        for index, symbol in enumerate(("A", "B", "C", "D"))
    }
    fitted = {
        ("A", "B"): (-2.0, 2.0),
        ("A", "C"): (-1.0, 0.5),
        ("C", "D"): (0.5, 1.0),
    }

    def fake_pair_signal(left, right, *, parameters):
        del parameters
        return fitted[(left.name, right.name)]

    monkeypatch.setattr(strategy_module, "_pair_convergence_signal", fake_pair_signal)
    single_pair = strategy_module._aggregate_pair_signals(
        histories,
        (("A", "B"),),
        parameters=strategy_module.StrategyParameters(),
    )
    assert math.isclose(single_pair["A"], -2.0 / 3.0)
    assert math.isclose(single_pair["B"], 4.0 / 3.0)
    assert math.isclose(abs(single_pair["B"] / single_pair["A"]), 2.0)

    aggregate = strategy_module._aggregate_pair_signals(
        histories,
        tuple(fitted),
        parameters=strategy_module.StrategyParameters(),
    )
    assert math.isclose(aggregate["A"], -4.0 / 3.0)
    assert math.isclose(aggregate["B"], 4.0 / 3.0)
    assert math.isclose(aggregate["C"], 7.0 / 12.0)
    assert math.isclose(aggregate["D"], -0.25)


def test_portfolio_uses_common_scale_without_equal_weight_flattening() -> None:
    aggregate = {"A": 4.0, "B": 2.0, "C": 1.0, "D": -3.0, "E": -1.5}
    weights = strategy_module._portfolio(
        aggregate,
        parameters=strategy_module.StrategyParameters(),
    )
    assert weights
    assert math.isclose(weights["A"] / weights["B"], 2.0)
    assert math.isclose(weights["B"] / weights["C"], 2.0)
    assert math.isclose(weights["D"] / weights["E"], 2.0)
    assert max(abs(value) for value in weights.values()) <= 0.03 + 1e-12
    assert abs(math.fsum(weights.values())) <= 0.05 + 1e-12


def test_targets_respect_membership_and_exposure_bounds() -> None:
    context = _context()
    weights = _weights(context)
    assert isinstance(weights, dict) and weights
    assert set(weights).issubset(set(context.eligible_symbols))
    assert any(value > 0.0 for value in weights.values())
    assert any(value < 0.0 for value in weights.values())
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
    assert _weights(dataclasses.replace(context, bars=changed)) == baseline


def test_removing_eligible_pairs_cannot_leak_foreign_targets() -> None:
    context = _context()
    retained = _pair_symbols(4)
    restricted = dataclasses.replace(context, eligible_symbols=retained)
    result = _weights(restricted)
    assert isinstance(result, dict)
    assert set(result).issubset(set(retained))
