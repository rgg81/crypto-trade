"""Focused synthetic tests for Team 10; no market data or evaluator is used."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext


MODULE_PATH = Path(__file__).with_name("strategy.py")
SPEC = importlib.util.spec_from_file_location("top40_v3_team_10", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

SEED = 20260718


def _synthetic_context(
    decision_time: pd.Timestamp | None = None,
    periods: int = 600,
    symbols: int = 24,
    latest_cross_section_scale: float = 0.0012,
) -> DecisionContext:
    decision = decision_time or pd.Timestamp("2026-07-13 00:00:00", tz="UTC")
    times = pd.date_range(
        end=decision - pd.Timedelta(hours=8),
        periods=periods,
        freq="8h",
        tz="UTC",
    )
    common = 0.00012 * np.sin(np.arange(periods, dtype=float) / 13.0)
    bars: dict[str, pd.DataFrame] = {}
    eligible: list[str] = []

    for symbol_number in range(symbols):
        symbol = f"COIN{symbol_number:02d}USDT"
        eligible.append(symbol)
        generator = np.random.default_rng(3_000 + symbol_number)
        innovation = np.zeros(periods, dtype=float)
        target_slope = 0.25 + 0.014 * symbol_number
        for row in range(1, periods):
            response_slot = times[row].hour
            slope = target_slope if response_slot == 0 else -0.10
            innovation[row] = (
                slope * innovation[row - 1] + generator.normal(0.0, 0.00055)
            )

        # A deterministic final cross-section makes the forecast direction
        # observable without changing any fitted response pair.
        innovation[-1] = (
            symbol_number - (symbols - 1) / 2.0
        ) * latest_cross_section_scale
        log_close = 4.0 + 0.025 * symbol_number + np.cumsum(common + innovation)
        bars[symbol] = pd.DataFrame(
            {
                "open_time": times,
                "close": np.exp(log_close),
            }
        )

    return DecisionContext(
        decision_time=decision,
        bars=bars,
        funding=pd.DataFrame(),
        auxiliary={},
        eligible_symbols=tuple(eligible),
    )


def test_schedule_and_missing_or_stale_history_are_flat() -> None:
    strategy = MODULE.build_strategy()
    context = _synthetic_context()
    assert strategy.target_weights(context, seed=SEED)

    off_schedule = DecisionContext(
        decision_time=context.decision_time + pd.Timedelta(hours=1),
        eligible_symbols=context.eligible_symbols,
        bars=context.bars,
        funding=context.funding,
        auxiliary=context.auxiliary,
    )
    assert strategy.target_weights(off_schedule, seed=SEED) is None

    stale_bars = {
        symbol: frame.iloc[:-100].copy() for symbol, frame in context.bars.items()
    }
    stale = DecisionContext(
        decision_time=context.decision_time,
        eligible_symbols=context.eligible_symbols,
        bars=stale_bars,
        funding=context.funding,
        auxiliary=context.auxiliary,
    )
    assert strategy.target_weights(stale, seed=SEED) == {}


def test_deterministic_under_symbol_and_row_reordering() -> None:
    strategy = MODULE.build_strategy()
    context = _synthetic_context()
    expected = strategy.target_weights(context, seed=SEED)

    reordered = DecisionContext(
        decision_time=context.decision_time,
        eligible_symbols=tuple(reversed(context.eligible_symbols)),
        bars={
            symbol: context.bars[symbol].sample(frac=1.0, random_state=91).reset_index(drop=True)
            for symbol in reversed(context.eligible_symbols)
        },
        funding=context.funding,
        auxiliary=context.auxiliary,
    )
    assert strategy.target_weights(reordered, seed=SEED) == expected


def test_exact_membership_and_portfolio_limits() -> None:
    strategy = MODULE.build_strategy()
    context = _synthetic_context()
    target = strategy.target_weights(context, seed=SEED)
    assert target
    assert set(target).issubset(set(context.eligible_symbols))
    assert all(abs(weight) <= 0.03 + 1.0e-12 for weight in target.values())
    assert sum(abs(weight) for weight in target.values()) <= 0.50 + 1.0e-12
    assert abs(sum(target.values())) <= 0.05 + 1.0e-12
    assert any(weight > 0.0 for weight in target.values())
    assert any(weight < 0.0 for weight in target.values())


def test_future_rows_do_not_change_the_decision() -> None:
    strategy = MODULE.build_strategy()
    context = _synthetic_context()
    expected = strategy.target_weights(context, seed=SEED)

    future_bars: dict[str, pd.DataFrame] = {}
    for number, symbol in enumerate(context.eligible_symbols):
        future = pd.DataFrame(
            {
                "open_time": [context.decision_time],
                "close": [10_000.0 + number],
            }
        )
        future_bars[symbol] = pd.concat(
            [context.bars[symbol], future], ignore_index=True
        )
    amended = DecisionContext(
        decision_time=context.decision_time,
        eligible_symbols=context.eligible_symbols,
        bars=future_bars,
        funding=context.funding,
        auxiliary=context.auxiliary,
    )
    assert strategy.target_weights(amended, seed=SEED) == expected


def test_target_cell_slope_is_not_a_shifted_slot_placebo() -> None:
    context = _synthetic_context()
    decision = pd.Timestamp(context.decision_time)
    residual = MODULE._residual_return_frame(context, decision)
    assert not residual.empty

    symbol = context.eligible_symbols[-1]
    target_slot = MODULE._shrunk_response_slope(
        residual[symbol], target_slot=0, decision_time=decision
    )
    shifted_placebo = MODULE._shrunk_response_slope(
        residual[symbol], target_slot=8, decision_time=decision
    )
    assert target_slot is not None and shifted_placebo is not None
    assert target_slot > shifted_placebo + 0.10


def test_slot_estimate_uses_the_predeclared_cross_coin_prior() -> None:
    context = _synthetic_context()
    decision = pd.Timestamp(context.decision_time)
    residual = MODULE._residual_return_frame(context, decision)
    prior = MODULE._robust_cross_coin_slot_prior(residual, 0, decision)
    assert prior is not None

    series = residual[context.eligible_symbols[-1]]
    components = MODULE._response_slope_components(series, 0, decision)
    assert components is not None
    asset_pooled, slot, observations = components
    shrunk = MODULE._shrunk_response_slope(
        series,
        0,
        decision,
        cross_coin_slot_prior=prior,
    )
    assert shrunk is not None
    blended_prior = (
        MODULE.PARAMETERS.asset_pooled_prior_weight * asset_pooled
        + (1.0 - MODULE.PARAMETERS.asset_pooled_prior_weight) * prior
    )
    slot_weight = observations / (
        observations + MODULE.PARAMETERS.shrinkage_prior_observations
    )
    expected = slot_weight * slot + (1.0 - slot_weight) * blended_prior
    assert np.isclose(shrunk, expected)


def test_forecasts_must_clear_the_declared_round_trip_cost() -> None:
    symbols = [f"COIN{index:02d}USDT" for index in range(24)]
    below_hurdle = {
        symbol: (-0.00149 if index < 12 else 0.00149)
        for index, symbol in enumerate(symbols)
    }
    assert MODULE._neutral_portfolio(below_hurdle) == {}

    above_hurdle = {
        symbol: (-0.0017 if index < 12 else 0.0017)
        for index, symbol in enumerate(symbols)
    }
    assert MODULE._neutral_portfolio(above_hurdle)
