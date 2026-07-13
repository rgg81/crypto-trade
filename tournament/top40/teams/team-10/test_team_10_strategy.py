from __future__ import annotations

import dataclasses
import importlib.util
import json
import math
import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament.engine import (
    EvaluatorConfig,
    evaluate_base_and_double_cost,
    evaluate_targets,
    generate_targets,
)
from crypto_trade.tournament.protocol import (
    REBALANCE_INSTRUCTION_COLUMN,
    DecisionContext,
)
from crypto_trade.tournament.runner import source_bundle_fingerprint

sys.dont_write_bytecode = True


def _load_strategy_module() -> ModuleType:
    path = Path(__file__).with_name("strategy.py")
    spec = importlib.util.spec_from_file_location("team_10_listing_maturation", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not create the strategy module specification")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


STRATEGY = _load_strategy_module()
ListingMaturationConfig = STRATEGY.ListingMaturationConfig
PerpetualListingMaturationStrategy = STRATEGY.PerpetualListingMaturationStrategy
build_strategy = STRATEGY.build_strategy


def _utc(year: int, month: int, day: int, hour: int = 0) -> pd.Timestamp:
    return pd.Timestamp(year=year, month=month, day=day, hour=hour, tz="UTC")


def _anchor() -> pd.Timestamp:
    return _utc(2020, 2, 3)


def _snapshot_start() -> pd.Timestamp:
    return _utc(2020, 1, 1)


def _decision(cadence_days: int = 14, periods: int = 70) -> pd.Timestamp:
    return _anchor() + pd.Timedelta(days=cadence_days * periods)


def _raw_config(*, young_max_days: int = 270, cadence_days: int = 14) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "mechanism": "perpetual_listing_maturation",
        "anchor_utc": _anchor().isoformat(),
        "snapshot_start_utc": _snapshot_start().isoformat(),
        "young_min_days": 30,
        "young_max_days": young_max_days,
        "mature_min_days": 540,
        "cadence_days": cadence_days,
        "names_per_sleeve": 5,
        "weight_per_name": 0.08,
        "seed": 20260713,
        "left_censor_rule": "first_open_equals_snapshot_start",
    }


def _config(*, young_max_days: int = 270, cadence_days: int = 14) -> Any:
    return ListingMaturationConfig.from_mapping(
        _raw_config(young_max_days=young_max_days, cadence_days=cadence_days)
    )


def _empty_funding() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "funding_time": pd.Series(dtype="datetime64[ns, UTC]"),
            "symbol": pd.Series(dtype="str"),
            "funding_rate": pd.Series(dtype="float64"),
            "mark_price": pd.Series(dtype="float64"),
        }
    )


def _history(
    symbol: str,
    first_open: pd.Timestamp,
    *,
    additional_opens: tuple[Any, ...] = (),
    market_value: float = 100.0,
) -> pd.DataFrame:
    opens = (first_open, *additional_opens)
    return pd.DataFrame(
        {
            "open_time": list(opens),
            "symbol": [symbol] * len(opens),
            "open": [market_value] * len(opens),
            "close": [market_value] * len(opens),
            "quote_volume": [1_000_000.0] * len(opens),
        }
    )


def _context_from_ages(
    decision_time: pd.Timestamp,
    ages: Mapping[str, float | str],
    *,
    eligible: tuple[str, ...] | None = None,
    extra_bars: Mapping[str, pd.DataFrame] | None = None,
) -> DecisionContext:
    bars: dict[str, pd.DataFrame] = {}
    for symbol, age in ages.items():
        first = _snapshot_start() if age == "left" else decision_time - pd.Timedelta(days=age)
        bars[symbol] = _history(symbol, first)
    bars.update(extra_bars or {})
    symbols = eligible if eligible is not None else tuple(ages)
    return DecisionContext(
        decision_time=decision_time,
        bars=bars,
        funding=_empty_funding(),
        auxiliary={},
        eligible_symbols=symbols,
    )


def _complete_ages() -> dict[str, float | str]:
    ages: dict[str, float | str] = {
        "MAT_A": 700,
        "MAT_B": 710,
        "MAT_C": 720,
        "MAT_D": 730,
        "MAT_E": 740,
        "MAT_F": 750,
    }
    ages.update(
        {
            "YNG_A": 35,
            "YNG_B": 40,
            "YNG_C": 45,
            "YNG_D": 50,
            "YNG_E": 55,
            "YNG_F": 60,
        }
    )
    return ages


def _weights(strategy: Any, context: DecisionContext) -> Mapping[str, float] | None:
    return strategy.target_weights(context, seed=20260713)


@pytest.mark.parametrize("young_max", [180, 270, 360])
@pytest.mark.parametrize("cadence", [7, 14, 28])
def test_preregistered_parameter_grid_is_supported(young_max: int, cadence: int) -> None:
    config = _config(young_max_days=young_max, cadence_days=cadence)
    assert config.young_max_days == young_max
    assert config.cadence_days == cadence


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("young_min_days", 29),
        ("young_max_days", 271),
        ("mature_min_days", 539),
        ("cadence_days", 21),
        ("names_per_sleeve", 4),
        ("weight_per_name", 0.081),
        ("seed", 1),
    ],
)
def test_non_preregistered_parameters_fail_closed(field: str, value: Any) -> None:
    raw = _raw_config()
    raw[field] = value
    with pytest.raises((TypeError, ValueError)):
        ListingMaturationConfig.from_mapping(raw)


def test_factory_loads_fixed_cell_and_returns_fresh_instances() -> None:
    first = build_strategy()
    second = build_strategy()
    assert first is not second
    assert first.config.young_max_days == 270
    assert first.config.cadence_days == 14
    assert first.config.mature_min_days == 540


def test_exact_schedule_anchor_and_hold_semantics() -> None:
    strategy = PerpetualListingMaturationStrategy(_config())
    context = _context_from_ages(_anchor(), {})
    assert _weights(strategy, context) == {}

    scheduled = dataclasses.replace(context, decision_time=_anchor() + pd.Timedelta(days=14))
    assert _weights(strategy, scheduled) == {}

    for timestamp in (
        _anchor() - pd.Timedelta(hours=8),
        _anchor() + pd.Timedelta(hours=8),
        _anchor() + pd.Timedelta(days=7),
        _anchor() + pd.Timedelta(days=14, hours=8),
    ):
        assert _weights(strategy, dataclasses.replace(context, decision_time=timestamp)) is None


@pytest.mark.parametrize("cadence", [7, 14, 28])
def test_each_grid_cadence_uses_the_same_anchor(cadence: int) -> None:
    strategy = PerpetualListingMaturationStrategy(_config(cadence_days=cadence))
    empty = _context_from_ages(_anchor(), {})
    on = dataclasses.replace(empty, decision_time=_anchor() + pd.Timedelta(days=cadence))
    off = dataclasses.replace(empty, decision_time=_anchor() + pd.Timedelta(days=cadence - 1))
    assert _weights(strategy, on) == {}
    assert _weights(strategy, off) is None


def test_selection_order_signs_and_risk_contract_are_exact() -> None:
    strategy = PerpetualListingMaturationStrategy(_config())
    context = _context_from_ages(_decision(), _complete_ages())
    result = _weights(strategy, context)
    assert result is not None
    expected_long = {"MAT_B", "MAT_C", "MAT_D", "MAT_E", "MAT_F"}
    expected_short = {"YNG_A", "YNG_B", "YNG_C", "YNG_D", "YNG_E"}
    assert {symbol for symbol, value in result.items() if value > 0.0} == expected_long
    assert {symbol for symbol, value in result.items() if value < 0.0} == expected_short
    assert all(abs(value) == pytest.approx(0.08) for value in result.values())
    assert sum(abs(value) for value in result.values()) == pytest.approx(0.80)
    assert sum(result.values()) == pytest.approx(0.0, abs=1e-15)
    assert max(abs(value) for value in result.values()) < 0.10
    assert len(result) == 10


def test_age_and_symbol_ties_are_lexicographic() -> None:
    ages: dict[str, float | str] = {f"M_{letter}": 600 for letter in "GFEDCBA"}
    ages.update({f"Y_{letter}": 100 for letter in "GFEDCBA"})
    context = _context_from_ages(_decision(), ages, eligible=tuple(reversed(tuple(ages))))
    result = _weights(PerpetualListingMaturationStrategy(_config()), context)
    assert result is not None
    assert {symbol for symbol, value in result.items() if value > 0.0} == {
        "M_A",
        "M_B",
        "M_C",
        "M_D",
        "M_E",
    }
    assert {symbol for symbol, value in result.items() if value < 0.0} == {
        "Y_A",
        "Y_B",
        "Y_C",
        "Y_D",
        "Y_E",
    }


def test_pool_boundaries_are_inclusive_and_gap_names_are_excluded() -> None:
    ages: dict[str, float | str] = {
        "M_540": 540,
        "M_541": 541,
        "M_542": 542,
        "M_543": 543,
        "M_544": 544,
        "M_539": 539,
        "Y_030": 30,
        "Y_031": 31,
        "Y_032": 32,
        "Y_033": 33,
        "Y_270": 270,
        "Y_029": 29,
        "Y_271": 271,
    }
    result = _weights(
        PerpetualListingMaturationStrategy(_config()),
        _context_from_ages(_decision(), ages),
    )
    assert result is not None
    assert "M_540" in result
    assert "Y_030" in result
    assert "Y_270" in result
    assert "M_539" not in result
    assert "Y_029" not in result
    assert "Y_271" not in result


def test_left_censor_equality_is_mature_without_inferred_pre_history() -> None:
    decision_time = _anchor() + pd.Timedelta(days=14 * 20)
    ages: dict[str, float | str] = {f"LC_{index}": "left" for index in range(5)}
    after_snapshot_age = float(
        (decision_time - (_snapshot_start() + pd.Timedelta(hours=8))) / pd.Timedelta(days=1)
    )
    ages["AFTER_SNAPSHOT"] = after_snapshot_age
    ages.update({f"Y_{index}": 30 + index for index in range(5)})
    result = _weights(
        PerpetualListingMaturationStrategy(_config()),
        _context_from_ages(decision_time, ages),
    )
    assert result is not None
    assert all(result[f"LC_{index}"] > 0.0 for index in range(5))
    assert "AFTER_SNAPSHOT" not in result


def test_scheduled_call_flattens_when_either_pool_has_fewer_than_five() -> None:
    strategy = PerpetualListingMaturationStrategy(_config())
    too_few_young: dict[str, float | str] = {f"M_{index}": 600 + index for index in range(5)}
    too_few_young.update({f"Y_{index}": 40 + index for index in range(4)})
    assert _weights(strategy, _context_from_ages(_decision(), too_few_young)) == {}

    too_few_mature: dict[str, float | str] = {f"M_{index}": 600 + index for index in range(4)}
    too_few_mature.update({f"Y_{index}": 40 + index for index in range(5)})
    assert _weights(strategy, _context_from_ages(_decision(), too_few_mature)) == {}


def test_pit_fillability_uses_only_eligible_symbols() -> None:
    decision_time = _decision()
    ages = _complete_ages()
    excluded = _history("NOT_ELIGIBLE", decision_time - pd.Timedelta(days=900))
    eligible = tuple(ages)
    context = _context_from_ages(
        decision_time,
        ages,
        eligible=eligible,
        extra_bars={"NOT_ELIGIBLE": excluded},
    )
    result = _weights(PerpetualListingMaturationStrategy(_config()), context)
    assert result is not None
    assert set(result).issubset(set(eligible))
    assert "NOT_ELIGIBLE" not in result


def test_truncation_append_and_corrupt_future_invariance() -> None:
    decision_time = _decision()
    ages = _complete_ages()
    base = _context_from_ages(decision_time, ages)
    appended_bars: dict[str, pd.DataFrame] = {}
    corrupted_bars: dict[str, pd.DataFrame] = {}
    for symbol, frame in base.bars.items():
        future = _history(
            symbol,
            decision_time + pd.Timedelta(hours=8),
            additional_opens=(decision_time + pd.Timedelta(hours=16),),
            market_value=1_000_000.0,
        )
        appended_bars[symbol] = pd.concat([frame, future], ignore_index=True)
        corrupt = future.copy()
        corrupt[["open", "close", "quote_volume"]] = [[np.nan, np.inf, -np.inf]] * len(corrupt)
        corrupted_bars[symbol] = pd.concat([frame, corrupt], ignore_index=True)

    appended = dataclasses.replace(base, bars=appended_bars)
    corrupted = dataclasses.replace(base, bars=corrupted_bars)
    strategy = PerpetualListingMaturationStrategy(_config())
    expected = _weights(strategy, base)
    assert _weights(strategy, appended) == expected
    assert _weights(strategy, corrupted) == expected
    assert _weights(PerpetualListingMaturationStrategy(_config()), base) == expected


def test_prices_volume_and_funding_are_not_alpha_inputs() -> None:
    context = _context_from_ages(_decision(), _complete_ages())
    expected = _weights(PerpetualListingMaturationStrategy(_config()), context)
    corrupted_bars: dict[str, pd.DataFrame] = {}
    for symbol, frame in context.bars.items():
        corrupted = frame.copy()
        corrupted["open"] = np.nan
        corrupted["close"] = np.inf
        corrupted["quote_volume"] = -np.inf
        corrupted_bars[symbol] = corrupted
    funding = pd.DataFrame(
        {
            "funding_time": [_decision() - pd.Timedelta(hours=4)],
            "symbol": [context.eligible_symbols[0]],
            "funding_rate": [math.nan],
            "mark_price": [math.inf],
        }
    )
    corrupted_context = dataclasses.replace(context, bars=corrupted_bars, funding=funding)
    assert _weights(PerpetualListingMaturationStrategy(_config()), corrupted_context) == expected


def test_unclosed_current_bar_cannot_create_a_launch_age() -> None:
    decision_time = _decision()
    ages = _complete_ages()
    ages.pop("YNG_A")
    ages.pop("YNG_B")
    context = _context_from_ages(decision_time, ages)
    context.bars["YNG_NEW"] = _history("YNG_NEW", decision_time)
    context = dataclasses.replace(
        context,
        eligible_symbols=(*context.eligible_symbols, "YNG_NEW"),
    )
    assert _weights(PerpetualListingMaturationStrategy(_config()), context) == {}


def test_fault_semantics_are_fail_closed_and_off_schedule_is_a_hold() -> None:
    decision_time = _decision()
    strategy = PerpetualListingMaturationStrategy(_config())
    ages = _complete_ages()
    ages.pop("YNG_A")
    ages.pop("YNG_B")
    malformed = _context_from_ages(decision_time, ages)
    malformed.bars["BROKEN"] = pd.DataFrame({"open_time": [decision_time.tz_localize(None)]})
    malformed = dataclasses.replace(
        malformed,
        eligible_symbols=(*malformed.eligible_symbols, "BROKEN"),
    )
    assert _weights(strategy, malformed) == {}

    off_schedule = dataclasses.replace(
        malformed,
        decision_time=decision_time + pd.Timedelta(hours=8),
    )
    assert _weights(strategy, off_schedule) is None

    duplicate = dataclasses.replace(
        malformed,
        eligible_symbols=(*malformed.eligible_symbols, malformed.eligible_symbols[0]),
    )
    with pytest.raises(ValueError, match="duplicates"):
        _weights(strategy, duplicate)
    with pytest.raises(ValueError, match="timezone-aware"):
        naive = dataclasses.replace(malformed, decision_time=decision_time.tz_localize(None))
        _weights(strategy, naive)
    with pytest.raises(ValueError, match="runtime seed"):
        strategy.target_weights(malformed, seed=0)


def test_row_order_and_repeated_calls_are_deterministic() -> None:
    context = _context_from_ages(_decision(), _complete_ages())
    reversed_context = dataclasses.replace(
        context,
        eligible_symbols=tuple(reversed(context.eligible_symbols)),
        bars={symbol: frame.iloc[::-1] for symbol, frame in reversed(tuple(context.bars.items()))},
    )
    first = _weights(PerpetualListingMaturationStrategy(_config()), context)
    second = _weights(PerpetualListingMaturationStrategy(_config()), reversed_context)
    third = _weights(PerpetualListingMaturationStrategy(_config()), context)
    assert first == second == third


def _central_market(
    *, prior_quote_volume: float = 100_000_000.0
) -> tuple[pd.Timestamp, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    decision_time = _decision()
    mature = tuple(f"MAT_{index}" for index in range(5))
    young = tuple(f"YNG_{index}" for index in range(5))
    rows: list[dict[str, Any]] = []
    for symbol in (*mature, *young):
        first_open = (
            _snapshot_start() if symbol in mature else decision_time - pd.Timedelta(days=100)
        )
        times = (
            first_open,
            decision_time - pd.Timedelta(hours=24),
            decision_time - pd.Timedelta(hours=16),
            decision_time - pd.Timedelta(hours=8),
            decision_time,
            decision_time + pd.Timedelta(hours=8),
        )
        for timestamp in dict.fromkeys(times):
            is_next = timestamp == decision_time + pd.Timedelta(hours=8)
            next_price = 101.0 if symbol in mature else 99.0
            opening = next_price if is_next else 100.0
            closing = opening
            if timestamp == decision_time - pd.Timedelta(hours=8):
                closing = 777.0
            rows.append(
                {
                    "open_time": timestamp,
                    "symbol": symbol,
                    "open": opening,
                    "close": closing,
                    "quote_volume": prior_quote_volume,
                }
            )
    bars = pd.DataFrame(rows).sort_values(["open_time", "symbol"]).reset_index(drop=True)
    membership = pd.DataFrame(
        {
            "reconstitution_time": [decision_time] * 10,
            "symbol": [*mature, *young],
            "liquidity_rank": list(range(1, 11)),
            "trailing_quote_volume": [prior_quote_volume] * 10,
        }
    )
    funding = pd.DataFrame(
        {
            "funding_time": [decision_time + pd.Timedelta(hours=4)] * 10,
            "symbol": [*mature, *young],
            "funding_rate": [0.001] * 10,
            "mark_price": [100.0] * 10,
        }
    )
    mark_rows = [
        {
            "mark_time": timestamp,
            "symbol": symbol,
            "mark_price": 100.0,
        }
        for timestamp in (decision_time, decision_time + pd.Timedelta(hours=8))
        for symbol in (*mature, *young)
    ]
    return decision_time, bars, funding, membership, pd.DataFrame(mark_rows)


def _central_run(*, prior_quote_volume: float = 100_000_000.0) -> tuple[pd.DataFrame, Any, Any]:
    decision_time, bars, funding, membership, marks = _central_market(
        prior_quote_volume=prior_quote_volume
    )
    strategy = PerpetualListingMaturationStrategy(_config())
    targets = generate_targets(
        strategy,
        bars,
        funding,
        membership,
        [decision_time, decision_time + pd.Timedelta(hours=8)],
        seed=20260713,
    )
    base, stressed = evaluate_base_and_double_cost(
        bars,
        funding,
        membership,
        targets,
        mark_prices=marks,
        config=EvaluatorConfig(),
    )
    return targets, base, stressed


def test_common_next_open_funding_cost_and_side_accounting() -> None:
    decision_time, bars, _funding, _membership, _marks = _central_market()
    targets, base, stressed = _central_run()
    assert bool(targets.loc[decision_time, REBALANCE_INSTRUCTION_COLUMN])
    assert not bool(
        targets.loc[decision_time + pd.Timedelta(hours=8), REBALANCE_INSTRUCTION_COLUMN]
    )

    entries = base.events[
        (base.events["event_type"] == "trade") & (base.events["phase"] == "rebalance")
    ]
    assert len(entries) == 10
    assert set(pd.to_datetime(entries["timestamp"], utc=True)) == {decision_time}
    assert set(entries["price"]) == {100.0}
    producing_closes = bars.loc[bars["open_time"] == decision_time - pd.Timedelta(hours=8), "close"]
    assert set(producing_closes) == {777.0}
    assert entries["fee"].sum() > 0.0
    assert entries["slippage"].sum() > 0.0

    funding_events = base.events[base.events["event_type"] == "funding"]
    assert len(funding_events) == 10
    mature_cashflow = funding_events[funding_events["symbol"].str.startswith("MAT_")]["cashflow"]
    young_cashflow = funding_events[funding_events["symbol"].str.startswith("YNG_")]["cashflow"]
    assert (mature_cashflow < 0.0).all()
    assert (young_cashflow > 0.0).all()
    assert base.returns.iloc[0]["long_price_pnl"] > 0.0
    assert base.returns.iloc[0]["short_price_pnl"] > 0.0

    assert stressed is not base
    assert stressed.returns is not base.returns
    stressed_entries = stressed.events[
        (stressed.events["event_type"] == "trade") & (stressed.events["phase"] == "rebalance")
    ]
    assert stressed_entries["fee"].sum() == pytest.approx(2.0 * entries["fee"].sum())
    assert stressed_entries["slippage"].sum() == pytest.approx(2.0 * entries["slippage"].sum())
    assert stressed.returns["fees"].sum() > base.returns["fees"].sum()
    assert stressed.returns["slippage"].sum() > base.returns["slippage"].sum()
    assert stressed.returns["funding_pnl"].sum() == pytest.approx(base.returns["funding_pnl"].sum())


def test_common_participation_cap_carries_unfilled_target_gap() -> None:
    _targets, base, _stressed = _central_run(prior_quote_volume=1_000.0)
    assert base.returns.iloc[0]["requested_notional"] > 70_000.0
    assert base.returns.iloc[0]["unfilled_notional"] > 70_000.0
    trades = base.events[base.events["event_type"] == "trade"]
    assert trades["notional"].abs().max() <= 3.0 + 1e-12


def test_common_entry_rebalance_and_exit_each_charge_costs() -> None:
    start = _decision()
    symbol = "COST_USDT"
    times = tuple(start + pd.Timedelta(hours=offset) for offset in (-24, -16, -8, 0, 8, 16))
    bars = pd.DataFrame(
        {
            "open_time": times,
            "symbol": [symbol] * len(times),
            "open": [100.0] * len(times),
            "close": [100.0] * len(times),
            "quote_volume": [100_000_000.0] * len(times),
        }
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": [start],
            "symbol": [symbol],
            "liquidity_rank": [1],
            "trailing_quote_volume": [100_000_000.0],
        }
    )
    target_index = pd.DatetimeIndex(times[-3:])
    targets = pd.DataFrame(
        {
            REBALANCE_INSTRUCTION_COLUMN: [True, True, True],
            symbol: [0.08, -0.08, 0.0],
        },
        index=target_index,
    )
    marks = pd.DataFrame(
        {
            "mark_time": target_index,
            "symbol": [symbol] * len(target_index),
            "mark_price": [100.0] * len(target_index),
        }
    )
    result = evaluate_targets(
        bars,
        _empty_funding(),
        membership,
        targets,
        mark_prices=marks,
    )
    trades = result.events[result.events["event_type"] == "trade"].sort_values("timestamp")
    assert list(pd.to_datetime(trades["timestamp"], utc=True)) == list(target_index)
    assert trades.iloc[0]["notional"] > 0.0
    assert trades.iloc[1]["notional"] < 0.0
    assert trades.iloc[2]["notional"] > 0.0
    assert (trades["fee"] > 0.0).all()
    assert (trades["slippage"] > 0.0).all()


def test_common_delist_exit_shares_participation_and_haircuts_residual() -> None:
    start = _decision()
    disappearing = "DELIST_USDT"
    continuing = "CONTINUE_USDT"
    rows: list[dict[str, Any]] = []
    for offset in (-24, -16, -8, 0):
        rows.append(
            {
                "open_time": start + pd.Timedelta(hours=offset),
                "symbol": disappearing,
                "open": 100.0,
                "close": 100.0,
                "quote_volume": 1_000.0,
            }
        )
    for offset in (-24, -16, -8, 0, 8):
        rows.append(
            {
                "open_time": start + pd.Timedelta(hours=offset),
                "symbol": continuing,
                "open": 100.0,
                "close": 100.0,
                "quote_volume": 1_000.0,
            }
        )
    bars = pd.DataFrame(rows)
    membership = pd.DataFrame(
        {
            "reconstitution_time": [start, start],
            "symbol": [disappearing, continuing],
            "liquidity_rank": [1, 2],
            "trailing_quote_volume": [1_000.0, 1_000.0],
        }
    )
    targets = pd.DataFrame(
        {
            REBALANCE_INSTRUCTION_COLUMN: [True, False],
            disappearing: [0.08, 0.0],
        },
        index=pd.DatetimeIndex([start, start + pd.Timedelta(hours=8)]),
    )
    marks = pd.DataFrame(
        [
            {"mark_time": start, "symbol": disappearing, "mark_price": 100.0},
            {"mark_time": start, "symbol": continuing, "mark_price": 100.0},
            {
                "mark_time": start + pd.Timedelta(hours=8),
                "symbol": continuing,
                "mark_price": 100.0,
            },
        ]
    )
    result = evaluate_targets(
        bars,
        _empty_funding(),
        membership,
        targets,
        mark_prices=marks,
    )
    first = result.returns.iloc[0]
    assert first["forced_exit_requested_notional"] > 0.0
    assert first["forced_exit_unfilled_notional"] > 0.0
    assert first["conservative_settlement_notional"] > 0.0
    settlements = result.events[result.events["event_type"] == "conservative_settlement"]
    assert len(settlements) == 1
    assert settlements.iloc[0]["cashflow"] < 0.0
    entry = result.events[result.events["event_type"] == "trade"]
    assert len(entry) == 1
    assert entry.iloc[0]["fee"] > 0.0
    assert entry.iloc[0]["slippage"] > 0.0


def test_common_risk_caps_reject_oversized_symbol() -> None:
    decision_time, bars, funding, membership, marks = _central_market()
    targets = pd.DataFrame(
        {
            REBALANCE_INSTRUCTION_COLUMN: [True, False],
            "MAT_0": [0.11, 0.0],
        },
        index=pd.DatetimeIndex([decision_time, decision_time + pd.Timedelta(hours=8)]),
    )
    with pytest.raises(ValueError, match="symbol exposure"):
        evaluate_targets(
            bars,
            funding,
            membership,
            targets,
            mark_prices=marks,
        )


class _BadStrategy:
    def __init__(self, value: float):
        self.value = value

    def target_weights(self, context: DecisionContext, *, seed: int) -> Mapping[str, float] | None:
        del context, seed
        return {"NOT_ELIGIBLE": self.value}


def test_common_generator_rejects_ineligible_and_nonfinite_outputs() -> None:
    decision_time, bars, funding, membership, marks = _central_market()
    with pytest.raises(ValueError, match="non-finite"):
        generate_targets(
            _BadStrategy(math.nan),
            bars,
            funding,
            membership,
            [decision_time],
            seed=20260713,
        )

    bad_targets = generate_targets(
        _BadStrategy(0.08),
        bars,
        funding,
        membership,
        [decision_time, decision_time + pd.Timedelta(hours=8)],
        seed=20260713,
    )
    with pytest.raises(ValueError, match="ineligible target"):
        evaluate_base_and_double_cost(
            bars,
            funding,
            membership,
            bad_targets,
            mark_prices=marks,
        )


def test_common_generator_rejects_duplicate_rows_and_returns_empty_grid() -> None:
    decision_time, bars, funding, membership, _marks = _central_market()
    duplicate = pd.concat([bars, bars.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        generate_targets(
            PerpetualListingMaturationStrategy(_config()),
            duplicate,
            funding,
            membership,
            [decision_time],
            seed=20260713,
        )
    empty = generate_targets(
        PerpetualListingMaturationStrategy(_config()),
        bars,
        funding,
        membership,
        [],
        seed=20260713,
    )
    assert empty.empty


def test_source_bundle_passes_canonical_text_scan() -> None:
    root = Path(__file__).resolve().parents[4]
    fingerprint, entries = source_bundle_fingerprint(
        root,
        "team-10",
        "tournament/top40/teams/team-10/strategy.py",
    )
    assert len(fingerprint) == 64
    assert any(entry["path"] == "strategy.py" for entry in entries)
    assert any(entry["path"] == "frozen_config.json" for entry in entries)


def _clean_process_hash_probe() -> dict[str, str]:
    test_path = Path(__file__).resolve()
    root = test_path.parents[4]
    code = "\n".join(
        (
            "import hashlib, json, runpy",
            f"scope = runpy.run_path({str(test_path)!r})",
            "targets, base, stressed = scope['_central_run']()",
            "fingerprint, entries = scope['source_bundle_fingerprint'](",
            f"    {str(root)!r}, 'team-10',",
            "    'tournament/top40/teams/team-10/strategy.py',",
            ")",
            "def digest(frame):",
            "    return hashlib.sha256(frame.to_csv().encode()).hexdigest()",
            "print(json.dumps({",
            "    'targets': digest(targets),",
            "    'positions': digest(base.positions),",
            "    'returns': digest(base.returns),",
            "    'double_cost_returns': digest(stressed.returns),",
            "    'manifest': fingerprint,",
            "}, sort_keys=True))",
        )
    )
    environment = {
        "HOME": str(Path.home()),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": os.environ.get("PATH", ""),
        "PYTHONHASHSEED": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": str(root / "src"),
    }
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=root,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return json.loads(completed.stdout)


def test_clean_process_target_position_return_and_manifest_hashes_repeat() -> None:
    first = _clean_process_hash_probe()
    second = _clean_process_hash_probe()
    assert first == second
    assert set(first) == {
        "targets",
        "positions",
        "returns",
        "double_cost_returns",
        "manifest",
    }
    assert all(len(value) == 64 for value in first.values())
