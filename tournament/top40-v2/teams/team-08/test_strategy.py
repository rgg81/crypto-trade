from __future__ import annotations

import dataclasses
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

TEAM_DIR = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "team08_strategy_under_test", TEAM_DIR / "strategy.py"
)
assert SPEC is not None and SPEC.loader is not None
strategy_module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = strategy_module
SPEC.loader.exec_module(strategy_module)

DEFAULT_DECISION = pd.Timestamp(year=2022, month=6, day=1, tz="UTC")


def _symbols(count: int = 20) -> tuple[str, ...]:
    return tuple(f"C{index:02d}USDT" for index in range(count))


def _bar_frame(
    symbol: str,
    *,
    decision_time: pd.Timestamp,
    symbol_index: int,
    bars: int = 80,
    mode: str = "expansion",
) -> pd.DataFrame:
    open_time = pd.date_range(
        end=decision_time - pd.Timedelta(hours=8),
        periods=bars,
        freq="8h",
        tz="UTC",
    )
    return_count = bars - 1
    axis = np.arange(return_count, dtype=float)
    phase = symbol_index * 0.37
    returns = 0.006 * np.sin(axis * 0.71 + phase) + 0.0025 * np.cos(axis * 0.23 - phase)
    returns[-10:-1] = 0.00025 * np.sin(axis[-10:-1] * 1.31 + phase)
    sign = 1.0 if symbol_index % 2 == 0 else -1.0
    if mode == "expansion":
        returns[-1] = sign * (0.016 + 0.0004 * symbol_index)
    elif mode == "failed-release":
        returns[-1] = sign * (0.00038 + 0.000008 * symbol_index)
    else:
        raise ValueError(mode)
    close = 100.0 * np.exp(np.r_[0.0, np.cumsum(returns)])
    return pd.DataFrame(
        {
            "open_time": open_time,
            "symbol": symbol,
            "open": close,
            "close": close,
            "quote_volume": np.full(bars, 2_000_000.0 + symbol_index),
        }
    )


def _context(
    *,
    mode: str = "expansion",
    decision_time: pd.Timestamp | None = None,
    symbols: tuple[str, ...] | None = None,
    bars: int = 80,
) -> SimpleNamespace:
    if decision_time is None:
        decision_time = DEFAULT_DECISION
    if symbols is None:
        symbols = _symbols()
    frames = {
        symbol: _bar_frame(
            symbol,
            decision_time=decision_time,
            symbol_index=int(symbol[1:3]),
            bars=bars,
            mode=mode,
        )
        for symbol in symbols
    }
    return SimpleNamespace(
        decision_time=decision_time,
        bars=frames,
        funding=pd.DataFrame(),
        auxiliary={},
        eligible_symbols=symbols,
    )


def _compression_mask_matrix() -> tuple[pd.DataFrame, set[str], set[str]]:
    """Create paired residual returns with exactly zero cross-sectional medians."""

    prior_axis = np.arange(63, dtype=float)
    compressed: dict[str, np.ndarray] = {}
    uncompressed: dict[str, np.ndarray] = {}
    for pair in range(6):
        prior = 0.006 * np.where((prior_axis.astype(int) + pair) % 2 == 0, 1.0, -1.0)
        prior[-9:] = 0.0002 * np.where((prior_axis[-9:].astype(int) + pair) % 2 == 0, 1.0, -1.0)
        release = 0.020 + 0.0002 * pair
        vector = np.r_[prior, release]
        compressed[f"A{pair * 2:02d}USDT"] = vector
        compressed[f"A{pair * 2 + 1:02d}USDT"] = -vector
    for pair in range(4):
        prior = 0.006 * np.where((prior_axis.astype(int) + pair) % 2 == 0, 1.0, -1.0)
        release = 0.050 + 0.0005 * pair
        vector = np.r_[prior, release]
        uncompressed[f"U{pair * 2:02d}USDT"] = vector
        uncompressed[f"U{pair * 2 + 1:02d}USDT"] = -vector
    all_series = {**compressed, **uncompressed}
    return (
        pd.DataFrame(all_series, index=pd.RangeIndex(64)),
        set(compressed),
        set(uncompressed),
    )


def test_default_config_matches_authored_frozen_config() -> None:
    authored = json.loads((TEAM_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    assert dataclasses.asdict(strategy_module.DEFAULT_CONFIG) == authored["strategy_parameters"]


def test_parameter_neighbors_are_valid_distinct_and_inside_declared_domains() -> None:
    frozen = json.loads((TEAM_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    family = json.loads((TEAM_DIR / "family_registration.draft.json").read_text(encoding="utf-8"))
    neighborhood = json.loads(
        (TEAM_DIR / "parameter_neighborhood.json").read_text(encoding="utf-8")
    )
    center = frozen["strategy_parameters"]
    domains = family["parameter_ranges"]
    config_fields = {field.name for field in dataclasses.fields(strategy_module.StrategyConfig)}
    assert len(config_fields) == 17
    assert set(center) == config_fields
    assert set(domains) == config_fields
    assert all(center[name] in domains[name] for name in config_fields)

    materialized: list[dict[str, object]] = []
    for neighbor in neighborhood["neighbors"]:
        parameters = dict(center)
        parameters.update(neighbor["overrides"])
        validated = strategy_module.StrategyConfig(**parameters)
        canonical = dataclasses.asdict(validated)
        assert canonical == parameters
        assert all(canonical[name] in domains[name] for name in config_fields)
        materialized.append(canonical)

    assert len(materialized) == 8
    encodings = [json.dumps(parameters, sort_keys=True) for parameters in materialized]
    assert len(set(encodings)) == len(encodings)
    assert json.dumps(center, sort_keys=True) not in set(encodings)


def test_uncompressed_names_are_removed_before_centering_and_selection() -> None:
    matrix, compressed, uncompressed = _compression_mask_matrix()
    scores = strategy_module._raw_scores(matrix, strategy_module.DEFAULT_CONFIG)
    assert set(scores.index) == compressed
    assert set(scores.index).isdisjoint(uncompressed)
    weights = strategy_module._portfolio(scores, strategy_module.DEFAULT_CONFIG)
    assert weights
    assert set(weights).issubset(compressed)
    assert set(weights).isdisjoint(uncompressed)


def test_expansion_builds_balanced_material_sleeves() -> None:
    context = _context(mode="expansion")
    weights = strategy_module.build_strategy().target_weights(context, seed=20260801)
    assert weights
    longs = {symbol: weight for symbol, weight in weights.items() if weight > 0}
    shorts = {symbol: weight for symbol, weight in weights.items() if weight < 0}
    assert len(longs) >= 5
    assert len(shorts) >= 5
    assert sum(abs(weight) for weight in weights.values()) == pytest.approx(0.8)
    assert sum(weights.values()) == pytest.approx(0.0, abs=1e-12)
    assert max(abs(weight) for weight in weights.values()) <= 0.09 + 1e-12
    assert set(weights).issubset(context.eligible_symbols)


def test_failed_release_convergence_reverses_isolated_direction() -> None:
    context = _context(mode="failed-release")
    weights = strategy_module.build_strategy().target_weights(context, seed=20260801)
    assert weights
    positive_release = {
        symbol for index, symbol in enumerate(context.eligible_symbols) if index % 2 == 0
    }
    negative_release = set(context.eligible_symbols) - positive_release
    assert {symbol for symbol, weight in weights.items() if weight > 0}.issubset(negative_release)
    assert {symbol for symbol, weight in weights.items() if weight < 0}.issubset(positive_release)


def test_symbol_order_and_seed_do_not_change_targets() -> None:
    first = _context()
    reversed_symbols = tuple(reversed(first.eligible_symbols))
    second = SimpleNamespace(
        decision_time=first.decision_time,
        bars={symbol: first.bars[symbol] for symbol in reversed_symbols},
        funding=first.funding.copy(),
        auxiliary={},
        eligible_symbols=reversed_symbols,
    )
    first_weights = strategy_module.build_strategy().target_weights(first, seed=1)
    second_weights = strategy_module.build_strategy().target_weights(second, seed=999999)
    assert first_weights == second_weights


def test_older_past_prefix_does_not_change_current_target() -> None:
    longer = _context(bars=96)
    shorter = SimpleNamespace(
        decision_time=longer.decision_time,
        bars={
            symbol: frame.iloc[16:].reset_index(drop=True) for symbol, frame in longer.bars.items()
        },
        funding=pd.DataFrame(),
        auxiliary={},
        eligible_symbols=longer.eligible_symbols,
    )
    assert strategy_module.build_strategy().target_weights(
        longer, seed=20260801
    ) == strategy_module.build_strategy().target_weights(shorter, seed=20260801)


def test_point_in_time_membership_removal_cannot_leave_old_targets() -> None:
    full = _context()
    reduced_symbols = full.eligible_symbols[:-2]
    reduced = SimpleNamespace(
        decision_time=full.decision_time,
        bars={symbol: full.bars[symbol] for symbol in reduced_symbols},
        funding=pd.DataFrame(),
        auxiliary={},
        eligible_symbols=reduced_symbols,
    )
    weights = strategy_module.build_strategy().target_weights(reduced, seed=20260801)
    assert weights is not None
    assert set(weights).issubset(reduced_symbols)


def test_non_rebalance_boundary_returns_none_after_validation() -> None:
    context = _context(decision_time=DEFAULT_DECISION + pd.Timedelta(hours=8))
    assert strategy_module.build_strategy().target_weights(context, seed=20260801) is None
    first_symbol = context.eligible_symbols[0]
    bad = context.bars[first_symbol].copy()
    bad.loc[bad.index[-1], "close"] = np.nan
    context.bars[first_symbol] = bad
    with pytest.raises(ValueError, match="finite and positive"):
        strategy_module.build_strategy().target_weights(context, seed=20260801)


def test_insufficient_or_recently_gapped_history_requests_flat() -> None:
    short = _context(bars=40)
    assert strategy_module.build_strategy().target_weights(short, seed=20260801) == {}

    gapped = _context()
    for symbol, frame in tuple(gapped.bars.items()):
        gapped.bars[symbol] = frame.drop(frame.index[-20]).reset_index(drop=True)
    assert strategy_module.build_strategy().target_weights(gapped, seed=20260801) == {}


def test_future_or_incomplete_bar_fails_closed() -> None:
    context = _context()
    symbol = context.eligible_symbols[0]
    future = context.bars[symbol].iloc[[-1]].copy()
    future["open_time"] = context.decision_time
    future["close"] = 1e12
    context.bars[symbol] = pd.concat([context.bars[symbol], future], ignore_index=True)
    with pytest.raises(ValueError, match="unclosed or future"):
        strategy_module.build_strategy().target_weights(context, seed=20260801)


@pytest.mark.parametrize("fault", ["duplicate", "unordered", "symbol", "naive-time"])
def test_malformed_bar_history_fails_closed(fault: str) -> None:
    context = _context()
    symbol = context.eligible_symbols[0]
    frame = context.bars[symbol].copy()
    if fault == "duplicate":
        frame.loc[frame.index[-1], "open_time"] = frame.loc[frame.index[-2], "open_time"]
    elif fault == "unordered":
        frame.loc[frame.index[-2], "open_time"], frame.loc[frame.index[-1], "open_time"] = (
            frame.loc[frame.index[-1], "open_time"],
            frame.loc[frame.index[-2], "open_time"],
        )
    elif fault == "symbol":
        frame.loc[frame.index[-1], "symbol"] = "WRONGUSDT"
    elif fault == "naive-time":
        frame["open_time"] = pd.DatetimeIndex(frame["open_time"]).tz_localize(None)
    context.bars[symbol] = frame
    with pytest.raises(ValueError):
        strategy_module.build_strategy().target_weights(context, seed=20260801)


def test_nonpast_funding_and_unexpected_auxiliary_fail_closed() -> None:
    context = _context()
    context.funding = pd.DataFrame(
        {
            "funding_time": [context.decision_time],
            "symbol": [context.eligible_symbols[0]],
        }
    )
    with pytest.raises(ValueError, match="strictly past"):
        strategy_module.build_strategy().target_weights(context, seed=20260801)

    context = _context()
    context.auxiliary = {"unapproved": pd.DataFrame()}
    with pytest.raises(ValueError, match="auxiliary"):
        strategy_module.build_strategy().target_weights(context, seed=20260801)


def test_invalid_seed_and_membership_contract_fail_closed() -> None:
    context = _context()
    with pytest.raises(ValueError, match="seed"):
        strategy_module.build_strategy().target_weights(context, seed=-1)

    context.eligible_symbols = context.eligible_symbols + (context.eligible_symbols[0],)
    with pytest.raises(ValueError, match="duplicates"):
        strategy_module.build_strategy().target_weights(context, seed=20260801)
