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

    stateful = strategy_module.build_strategy()
    duplicate_first = stateful.target_weights(context, seed=SEED)
    duplicate_second = stateful.target_weights(context, seed=SEED)
    assert duplicate_first == duplicate_second
    assert len(stateful._vintages) == 1


def test_weights_are_broad_bounded_and_short_capped() -> None:
    weights = _weights(_context())
    assert isinstance(weights, dict) and weights
    longs = [value for value in weights.values() if value > 0.0]
    shorts = [value for value in weights.values() if value < 0.0]
    assert len(longs) >= 8
    assert len(shorts) >= 8
    assert max(longs) <= 0.03 + 1e-12
    assert max(abs(value) for value in shorts) <= 0.02 + 1e-12
    assert math.fsum(abs(value) for value in weights.values()) <= 0.36 / 7.0 + 1e-12
    assert abs(math.fsum(weights.values())) <= 0.04 / 7.0 + 1e-12


def test_trial_two_admits_high_max_continuation_sign() -> None:
    context = _context()
    parameters = strategy_module.StrategyParameters()
    scores, tape_state = strategy_module._max_scores_and_tape_state(
        context,
        parameters=parameters,
    )
    cohort = strategy_module._portfolio(
        scores,
        tape_state=tape_state,
        parameters=parameters,
    )

    highest = max(scores, key=lambda symbol: (scores[symbol], symbol))
    lowest = min(scores, key=lambda symbol: (scores[symbol], symbol))
    assert scores[highest] > scores[lowest]
    assert cohort[highest] > 0.0
    assert cohort[lowest] < 0.0


def test_tape_router_assigns_bull_bear_and_chop_roles() -> None:
    parameters = strategy_module.StrategyParameters()
    assert strategy_module._routed_side_gross("bull", parameters=parameters) == (0.20, 0.16)
    assert strategy_module._routed_side_gross("bear", parameters=parameters) == (0.16, 0.20)
    assert strategy_module._routed_side_gross("neutral", parameters=parameters) == (0.18, 0.18)


def test_vintages_ramp_expire_and_drop_membership_without_renormalizing() -> None:
    first_time = DECISION_TIME - pd.Timedelta(days=6)
    full_cohort = (("AUSDT", 0.20), ("BUSDT", -0.16))
    one = (
        strategy_module.Vintage(
            decision_time=first_time,
            weights=full_cohort,
        ),
    )
    seven = tuple(
        strategy_module.Vintage(
            decision_time=first_time + pd.Timedelta(days=offset),
            weights=full_cohort,
        )
        for offset in range(7)
    )

    ramp = strategy_module._aggregate_vintages(
        one,
        eligible_symbols=frozenset({"AUSDT", "BUSDT"}),
        divisor=7,
    )
    mature = strategy_module._aggregate_vintages(
        seven,
        eligible_symbols=frozenset({"AUSDT", "BUSDT"}),
        divisor=7,
    )
    membership_exit = strategy_module._aggregate_vintages(
        seven,
        eligible_symbols=frozenset({"AUSDT"}),
        divisor=7,
    )

    assert math.isclose(sum(abs(value) for value in ramp.values()), 0.36 / 7.0)
    assert set(mature) == {"AUSDT", "BUSDT"}
    assert math.isclose(mature["AUSDT"], 0.20)
    assert math.isclose(mature["BUSDT"], -0.16)
    assert set(membership_exit) == {"AUSDT"}
    assert math.isclose(membership_exit["AUSDT"], 0.20)


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
