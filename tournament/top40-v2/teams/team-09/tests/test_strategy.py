from __future__ import annotations

import dataclasses
import importlib.util
import itertools
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

TEAM_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "team09_strategy_under_test", TEAM_DIR / "strategy.py"
)
assert SPEC is not None and SPEC.loader is not None
STRATEGY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = STRATEGY
SPEC.loader.exec_module(STRATEGY)


def _context(*, confirmed: bool = True) -> SimpleNamespace:
    decision = pd.Timestamp(year=2023, month=1, day=2, tz="UTC")
    symbols = tuple(f"T{index:02d}USDT" for index in range(16))
    funding_levels = np.linspace(-0.0008, 0.0008, len(symbols))
    bar_times = pd.date_range(end=decision - pd.Timedelta(hours=8), periods=90, freq="8h")
    funding_times = pd.date_range(end=decision - pd.Timedelta(hours=8), periods=21, freq="8h")
    bars: dict[str, pd.DataFrame] = {}
    funding_rows: list[dict[str, object]] = []
    for symbol, level in zip(symbols, funding_levels, strict=True):
        desired = -1.0 if level > 0 else 1.0
        price_direction = desired if confirmed else -desired
        closes = 100.0 * np.exp(price_direction * 0.002 * np.arange(len(bar_times)))
        bars[symbol] = pd.DataFrame(
            {
                "open_time": bar_times,
                "symbol": symbol,
                "open": closes / math.exp(price_direction * 0.001),
                "close": closes,
                "quote_volume": 1_000_000.0,
            }
        )
        funding_rows.extend(
            {
                "funding_time": timestamp,
                "symbol": symbol,
                "funding_rate": float(level),
                "mark_price": 100.0,
                "settlement_time": timestamp,
            }
            for timestamp in funding_times
        )
    return SimpleNamespace(
        decision_time=decision,
        eligible_symbols=symbols,
        bars=bars,
        funding=pd.DataFrame(funding_rows),
        auxiliary={},
    )


def _weights(context: SimpleNamespace) -> dict[str, float]:
    result = STRATEGY.build_strategy().target_weights(context, seed=20260801)
    assert isinstance(result, dict)
    return result


def test_center_creates_balanced_material_long_and_short_sleeves() -> None:
    context = _context()
    weights = _weights(context)
    longs = {symbol: weight for symbol, weight in weights.items() if weight > 0}
    shorts = {symbol: weight for symbol, weight in weights.items() if weight < 0}

    assert len(longs) >= 4
    assert len(shorts) >= 4
    assert sum(longs.values()) == pytest.approx(-sum(shorts.values()))
    assert sum(abs(weight) for weight in weights.values()) <= 1.0
    assert abs(sum(weights.values())) <= 0.25
    assert max(abs(weight) for weight in weights.values()) <= 0.10
    assert set(weights).issubset(context.eligible_symbols)


def test_synthetic_positions_have_correct_relative_funding_carry_direction() -> None:
    context = _context()
    weights = _weights(context)
    mean_rates = context.funding.groupby("symbol")["funding_rate"].mean()
    # The central evaluator uses cashflow = -position * mark * funding_rate.
    relative_carry = sum(-weight * float(mean_rates[symbol]) for symbol, weight in weights.items())
    assert relative_carry > 0


def test_price_confirmation_is_required() -> None:
    assert _weights(_context(confirmed=False)) == {}


def test_equal_funding_pressure_requests_flat() -> None:
    context = _context()
    context.funding.loc[:, "funding_rate"] = 0.0001
    assert _weights(context) == {}


@pytest.mark.parametrize("stale", [False, True])
def test_missing_gap_or_stale_latest_bar_is_not_time_compressed(stale: bool) -> None:
    context = _context()
    affected = context.eligible_symbols[0]
    if stale:
        context.bars[affected] = context.bars[affected].iloc[:-1].copy()
    else:
        context.bars[affected] = context.bars[affected].drop(context.bars[affected].index[-10])
    weights = _weights(context)
    assert affected not in weights
    assert any(weight > 0 for weight in weights.values())
    assert any(weight < 0 for weight in weights.values())


def test_under_history_new_member_with_funding_does_not_abort_cross_section() -> None:
    context = _context()
    symbol = "NEWUSDT"
    context.eligible_symbols = (*context.eligible_symbols, symbol)
    context.bars[symbol] = next(iter(context.bars.values())).iloc[-10:].assign(symbol=symbol)
    extra = context.funding[context.funding["symbol"] == context.eligible_symbols[0]].copy()
    extra.loc[:, "symbol"] = symbol
    context.funding = pd.concat([context.funding, extra], ignore_index=True)

    weights = _weights(context)
    assert symbol not in weights
    assert weights


@pytest.mark.parametrize("funding_history", ["none", "insufficient", "stale"])
def test_member_without_usable_funding_is_excluded_without_aborting(
    funding_history: str,
) -> None:
    context = _context()
    symbol = "NEWUSDT"
    context.eligible_symbols = (*context.eligible_symbols, symbol)
    context.bars[symbol] = next(iter(context.bars.values())).assign(symbol=symbol)
    if funding_history != "none":
        extra = context.funding[context.funding["symbol"] == context.eligible_symbols[0]].copy()
        extra.loc[:, "symbol"] = symbol
        if funding_history == "insufficient":
            extra = extra.tail(STRATEGY.StrategyConfig().minimum_funding_events - 1)
        else:
            extra.loc[:, "funding_time"] -= pd.Timedelta(hours=24)
        context.funding = pd.concat([context.funding, extra], ignore_index=True)

    weights = _weights(context)
    assert symbol not in weights
    assert any(weight > 0 for weight in weights.values())
    assert any(weight < 0 for weight in weights.values())


def test_input_order_does_not_change_targets() -> None:
    context = _context()
    expected = _weights(context)
    context.eligible_symbols = tuple(reversed(context.eligible_symbols))
    context.bars = {
        symbol: context.bars[symbol].iloc[::-1].reset_index(drop=True)
        for symbol in context.eligible_symbols
    }
    context.funding = context.funding.iloc[::-1].reset_index(drop=True)
    assert _weights(context) == expected


def test_clean_instances_are_deterministic() -> None:
    context = _context()
    first = _weights(context)
    second = _weights(_context())
    assert first == second


def test_future_bar_and_funding_rows_fail_closed() -> None:
    bar_context = _context()
    symbol = bar_context.eligible_symbols[0]
    future = bar_context.bars[symbol].iloc[[-1]].copy()
    future.loc[:, "open_time"] = bar_context.decision_time
    bar_context.bars[symbol] = pd.concat([bar_context.bars[symbol], future], ignore_index=True)
    with pytest.raises(ValueError, match="unavailable"):
        _weights(bar_context)

    funding_context = _context()
    future_funding = funding_context.funding.iloc[[0]].copy()
    future_funding.loc[:, "funding_time"] = funding_context.decision_time
    funding_context.funding = pd.concat(
        [funding_context.funding, future_funding], ignore_index=True
    )
    with pytest.raises(ValueError, match="non-past"):
        _weights(funding_context)


@pytest.mark.parametrize(
    ("fault", "message"),
    [
        ("duplicate", "duplicate"),
        ("timestamp", "invalid"),
        ("rate", "invalid"),
        ("ineligible", "ineligible"),
    ],
)
def test_malformed_funding_fails_closed(fault: str, message: str) -> None:
    context = _context()
    if fault == "duplicate":
        context.funding = pd.concat([context.funding, context.funding.iloc[[0]]], ignore_index=True)
    elif fault == "timestamp":
        context.funding.loc[0, "funding_time"] = pd.NaT
    elif fault == "rate":
        context.funding.loc[0, "funding_rate"] = np.inf
    else:
        context.funding.loc[0, "symbol"] = "OUTSIDEUSDT"
    with pytest.raises(ValueError, match=message):
        _weights(context)


def test_non_rebalance_boundary_holds_and_wrong_seed_fails() -> None:
    context = _context()
    context.decision_time += pd.Timedelta(hours=8)
    assert STRATEGY.build_strategy().target_weights(context, seed=20260801) is None
    with pytest.raises(ValueError, match="seed"):
        STRATEGY.build_strategy().target_weights(_context(), seed=7)
    with pytest.raises(ValueError, match="seed"):
        STRATEGY.build_strategy().target_weights(_context(), seed=20260801.0)


def test_frozen_config_and_trial_template_cover_every_strategy_parameter() -> None:
    frozen = json.loads((TEAM_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    trial = json.loads((TEAM_DIR / "trial_registration_template.json").read_text(encoding="utf-8"))
    expected = dataclasses.asdict(STRATEGY.StrategyConfig())
    assert frozen["parameters"] == expected
    assert trial["parameters"] == expected
    assert frozen["seed"] == expected["expected_seed"]


def test_every_declared_neighbor_is_feasible_and_one_axis_from_center() -> None:
    manifest = json.loads((TEAM_DIR / "parameter_neighborhood.json").read_text(encoding="utf-8"))
    center = STRATEGY.StrategyConfig()
    assert len(manifest["neighbors"]) == 10
    assert len({item["neighbor_id"] for item in manifest["neighbors"]}) == 10
    axes: dict[str, list[float]] = {}
    for item in manifest["neighbors"]:
        assert len(item["changes"]) == 1
        neighbor = dataclasses.replace(center, **item["changes"])
        neighbor.validate()
        assert neighbor != center
        field, value = next(iter(item["changes"].items()))
        axes.setdefault(field, []).append(value)
    assert len(axes) == 5
    for field, values in axes.items():
        assert len(values) == 2
        assert min(values) < getattr(center, field) < max(values)


def test_complete_family_cartesian_domain_is_declared_and_feasible() -> None:
    family = json.loads(
        (TEAM_DIR / "family_registration_template.json").read_text(encoding="utf-8")
    )
    domains = family["parameter_ranges"]
    fields = [field.name for field in dataclasses.fields(STRATEGY.StrategyConfig)]
    center = STRATEGY.StrategyConfig()
    assert set(domains) == set(fields)
    assert all(getattr(center, field) in domains[field] for field in fields)
    combinations = 0
    for values in itertools.product(*(domains[field] for field in fields)):
        dataclasses.replace(center, **dict(zip(fields, values, strict=True))).validate()
        combinations += 1
    assert combinations == 3**5


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"interval_hours": 8.0}, "integers"),
        ({"confirmation_bars": 9.5}, "integers"),
        ({"expected_seed": 20260801.0}, "integers"),
        ({"funding_half_life_hours": math.inf}, "finite"),
        ({"funding_lookback_hours": 170}, "complete funding intervals"),
        (
            {"funding_lookback_hours": 80, "minimum_funding_events": 12},
            "available slots",
        ),
        (
            {
                "funding_lookback_hours": 16,
                "minimum_funding_events": 2,
                "maximum_funding_age_hours": 24,
            },
            "cannot exceed",
        ),
        (
            {
                "maximum_symbols_per_side": 5,
                "maximum_symbol_weight": 0.08,
                "target_side_gross": 0.5,
            },
            "cannot fund",
        ),
    ],
)
def test_invalid_configuration_domain_fails_closed(
    changes: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        dataclasses.replace(STRATEGY.StrategyConfig(), **changes).validate()
