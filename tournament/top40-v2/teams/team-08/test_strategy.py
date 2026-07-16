"""Synthetic causal and construction tests for Team 08's first mechanism pivot."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from crypto_trade.tournament.score_adapter_protocol_v5 import (
    score_boundary as public_score_boundary,
)

TEAM_DIR = Path(__file__).resolve().parent
if str(TEAM_DIR) not in sys.path:
    sys.path.insert(0, str(TEAM_DIR))

import candidate_variant  # noqa: E402
import strategy  # noqa: E402

DEFAULT_DECISION = pd.Timestamp(0, unit="ns", tz="UTC") + pd.Timedelta(
    hours=strategy.BAR_INTERVAL_HOURS * strategy.REBALANCE_INTERVAL_BARS * 3000
)


def _synthetic_context(
    *,
    decision_time: pd.Timestamp = DEFAULT_DECISION,
    symbol_count: int = 28,
    common_drift: float = 0.0,
):
    decision = pd.Timestamp(decision_time)
    periods = strategy.HISTORY_RETURN_BARS + 1
    open_times = pd.date_range(
        end=decision - pd.Timedelta(hours=strategy.BAR_INTERVAL_HOURS),
        periods=periods,
        freq="8h",
        tz="UTC",
    )
    bars: dict[str, pd.DataFrame] = {}
    compression_start = (
        strategy.HISTORY_RETURN_BARS
        - strategy.COMPRESSION_VOLATILITY_BARS
        - strategy.SHOCK_BARS
    )
    shock_start = strategy.HISTORY_RETURN_BARS - strategy.SHOCK_BARS
    for symbol_index in range(symbol_count):
        symbol = f"C{symbol_index:02d}USDT"
        pair = symbol_index // 2
        direction = 1.0 if symbol_index % 2 == 0 else -1.0
        returns: list[float] = []
        for return_index in range(strategy.HISTORY_RETURN_BARS):
            if return_index >= shock_start:
                idiosyncratic = direction * (0.010 + pair * 0.00012)
            elif return_index >= compression_start:
                idiosyncratic = direction * 0.00030 * math.sin(
                    return_index * 1.17 + pair * 0.13
                )
            else:
                idiosyncratic = direction * 0.0040 * math.sin(
                    return_index * 0.71 + pair * 0.19
                )
            common = common_drift + 0.0015 * math.sin(return_index * 0.37)
            returns.append(common + idiosyncratic)
        closes = [100.0 + symbol_index]
        for value in returns:
            closes.append(closes[-1] * math.exp(value))
        bars[symbol] = pd.DataFrame(
            {
                "open_time": open_times,
                "close": closes,
                "quote_volume": [10_000_000.0 - symbol_index * 10_000.0] * periods,
            }
        )
    return SimpleNamespace(
        decision_time=decision,
        bars=bars,
        funding=pd.DataFrame(columns=["funding_time", "symbol", "funding_rate"]),
        auxiliary={},
        eligible_symbols=tuple(sorted(bars)),
    )


def _targets(context):
    result = strategy.build_strategy().target_weights(context, seed=strategy.FROZEN_SEED)
    assert result is not None
    return dict(result)


def _feature_path(shock: tuple[float, float, float], *, compressed: bool = True):
    unused = [0.003 * math.sin(index * 0.41) for index in range(18)]
    baseline = [0.004 * math.sin(index * 0.83) for index in range(84)]
    amplitude = 0.00035 if compressed else 0.006
    compression = [amplitude * math.sin(index * 1.11) for index in range(21)]
    return tuple(unused + baseline + compression + list(shock))


def test_deterministic_finite_broad_exactly_neutral_targets() -> None:
    context = _synthetic_context()
    first = _targets(context)
    second = _targets(context)

    assert first == second
    assert first
    assert list(first) == sorted(first)
    assert sum(value > 0.0 for value in first.values()) >= 8
    assert sum(value < 0.0 for value in first.values()) >= 8
    assert all(math.isfinite(value) for value in first.values())
    assert abs(sum(abs(value) for value in first.values()) - strategy.GROSS_TARGET) <= 1e-10
    assert abs(sum(first.values())) <= 1e-10
    assert max(abs(value) for value in first.values()) <= strategy.MAXIMUM_SYMBOL_EXPOSURE


def test_positive_and_negative_shocks_are_traded_for_recoil() -> None:
    targets = _targets(_synthetic_context())
    positive_shock = {f"C{index:02d}USDT" for index in range(0, 28, 2)}
    negative_shock = {f"C{index:02d}USDT" for index in range(1, 28, 2)}

    assert {symbol for symbol, value in targets.items() if value < 0.0}.issubset(positive_shock)
    assert {symbol for symbol, value in targets.items() if value > 0.0}.issubset(negative_shock)


def test_common_bull_and_bear_drifts_do_not_change_the_relative_book() -> None:
    neutral = _targets(_synthetic_context())
    bull = _targets(_synthetic_context(common_drift=0.0010))
    bear = _targets(_synthetic_context(common_drift=-0.0010))

    assert bull == neutral
    assert bear == neutral
    assert abs(sum(bull.values())) <= 1e-10
    assert abs(sum(bear.values())) <= 1e-10


def test_compression_and_recoil_direction_are_part_of_the_new_mechanism() -> None:
    compressed = strategy._recoil_feature(_feature_path((0.009, 0.011, 0.010)))
    uncompressed = strategy._recoil_feature(
        _feature_path((0.009, 0.011, 0.010), compressed=False)
    )
    negative_shock = strategy._recoil_feature(_feature_path((-0.009, -0.011, -0.010)))

    assert compressed is not None and uncompressed is not None and negative_shock is not None
    assert compressed.compression_ratio < uncompressed.compression_ratio
    assert compressed.raw_recoil_score < 0.0
    assert uncompressed.raw_recoil_score == 0.0
    assert negative_shock.raw_recoil_score > 0.0


def test_multibar_durability_penalizes_a_rough_shock_path() -> None:
    persistent = strategy._recoil_feature(_feature_path((0.007, 0.007, 0.007)))
    rough = strategy._recoil_feature(_feature_path((0.020, -0.018, 0.019)))

    assert persistent is not None and rough is not None
    assert persistent.direction_agreement > rough.direction_agreement
    assert persistent.path_roughness < rough.path_roughness
    assert abs(persistent.raw_recoil_score) > abs(rough.raw_recoil_score)


def test_boundary_is_called_once_after_final_transform_and_before_construction(monkeypatch) -> None:
    context = _synthetic_context()
    assert strategy.score_boundary is public_score_boundary
    snapshot = strategy.build_strategy().preconstruction_snapshot(
        context,
        seed=strategy.FROZEN_SEED,
    )
    assert snapshot is not None
    expected = snapshot.score_map()
    observed: list[dict[str, float]] = []

    def capture(scores):
        observed.append(dict(scores))
        return scores

    monkeypatch.setattr(strategy, "score_boundary", capture)
    targets = strategy.build_strategy().target_weights(context, seed=strategy.FROZEN_SEED)

    assert targets
    assert observed == [expected]


def test_boundary_returned_values_drive_both_sleeves(monkeypatch) -> None:
    context = _synthetic_context()
    baseline = _targets(context)
    baseline_longs = {symbol for symbol, value in baseline.items() if value > 0.0}
    baseline_shorts = {symbol for symbol, value in baseline.items() if value < 0.0}

    def invert(scores):
        for symbol in scores:
            scores[symbol] = -scores[symbol]
        return scores

    monkeypatch.setattr(strategy, "score_boundary", invert)
    inverted = strategy.build_strategy().target_weights(context, seed=strategy.FROZEN_SEED)

    assert inverted
    assert {symbol for symbol, value in inverted.items() if value > 0.0} == baseline_shorts
    assert {symbol for symbol, value in inverted.items() if value < 0.0} == baseline_longs


def test_public_boundary_rejects_a_replacement_dictionary(monkeypatch) -> None:
    monkeypatch.setattr(strategy, "score_boundary", lambda scores: dict(scores))
    with pytest.raises(ValueError, match="exact input dictionary"):
        strategy.build_strategy().target_weights(_synthetic_context(), seed=strategy.FROZEN_SEED)


def test_scheduled_failure_captures_one_empty_dictionary(monkeypatch) -> None:
    context = _synthetic_context(symbol_count=strategy.MINIMUM_VALID_SYMBOLS - 1)
    observed = []

    def capture(scores):
        observed.append(scores)
        return scores

    monkeypatch.setattr(strategy, "score_boundary", capture)
    assert _targets(context) == {}
    assert observed == [{}]


def test_hold_and_off_grid_decisions_do_not_call_boundary(monkeypatch) -> None:
    base = _synthetic_context()
    calls = 0

    def capture(scores):
        nonlocal calls
        calls += 1
        return scores

    monkeypatch.setattr(strategy, "score_boundary", capture)
    hold = SimpleNamespace(**vars(base))
    hold.decision_time = base.decision_time + pd.Timedelta(hours=8)
    assert strategy.build_strategy().target_weights(hold, seed=strategy.FROZEN_SEED) is None

    off_grid = SimpleNamespace(**vars(base))
    off_grid.decision_time = base.decision_time + pd.Timedelta(hours=1)
    assert strategy.build_strategy().target_weights(off_grid, seed=strategy.FROZEN_SEED) == {}
    assert calls == 0


def test_future_rows_and_unused_fields_do_not_change_targets() -> None:
    base = _synthetic_context()
    expected = _targets(base)
    changed = SimpleNamespace(**vars(base))
    changed.bars = {}
    for symbol, frame in base.bars.items():
        mutated = frame.copy()
        mutated["open"] = [1.0e12 if index % 2 else 1.0e-12 for index in range(len(mutated))]
        future = pd.DataFrame(
            {
                "open_time": [base.decision_time, base.decision_time + pd.Timedelta(hours=8)],
                "close": [1.0e12, 1.0e-12],
                "open": [1.0e-12, 1.0e12],
            }
        )
        changed.bars[symbol] = pd.concat([mutated, future], ignore_index=True)
    changed.funding = pd.DataFrame({"funding_rate": [float("inf")]})
    changed.auxiliary = {"unused": pd.DataFrame({"value": [1.0e12]})}

    assert _targets(changed) == expected


def test_missing_or_physically_duplicated_required_history_flattens() -> None:
    missing = _synthetic_context()
    missing.bars = {symbol: frame.iloc[:-1].copy() for symbol, frame in missing.bars.items()}
    assert _targets(missing) == {}

    duplicate = _synthetic_context()
    duplicate.bars = {
        symbol: pd.concat([frame, frame.iloc[[-1]]], ignore_index=True)
        for symbol, frame in duplicate.bars.items()
    }
    assert _targets(duplicate) == {}

    mixed = _synthetic_context()
    mixed.bars = {
        symbol: pd.concat(
            [
                frame,
                pd.DataFrame(
                    {"open_time": [frame.iloc[-1]["open_time"]], "close": [float("nan")]}
                ),
            ],
            ignore_index=True,
        )
        for symbol, frame in mixed.bars.items()
    }
    assert _targets(mixed) == {}


def test_point_in_time_membership_is_the_only_candidate_set() -> None:
    context = _synthetic_context(symbol_count=32)
    excluded = set(sorted(context.bars)[-4:])
    context.eligible_symbols = tuple(sorted(set(context.bars) - excluded))
    targets = _targets(context)

    assert targets
    assert set(targets).issubset(set(context.eligible_symbols))
    assert not excluded & set(targets)


def test_wrong_seed_and_candidate_identity_are_rejected(monkeypatch) -> None:
    context = _synthetic_context()
    with pytest.raises(ValueError, match="frozen seed"):
        strategy.build_strategy().target_weights(context, seed=strategy.FROZEN_SEED + 1)

    monkeypatch.setattr(candidate_variant, "ACTIVE_CANDIDATE_ID", "unknown-pivot")
    with pytest.raises(ValueError, match="unknown materialized"):
        strategy.build_strategy()


def test_active_candidate_has_no_hidden_parameter_override(monkeypatch) -> None:
    monkeypatch.setattr(candidate_variant, "ACTIVE_OVERRIDES", {"gross_target": 0.40})
    with pytest.raises(ValueError, match="do not match"):
        strategy.build_strategy()


def test_frozen_config_matches_executable_constants_and_no_control() -> None:
    config = json.loads((TEAM_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    assert config["family_id"] == strategy.ACTIVE_FAMILY_ID
    assert config["candidate_id"] == strategy.ACTIVE_CANDIDATE_ID
    assert config["seed"] == strategy.FROZEN_SEED
    assert config["parameters"] == {
        "bar_interval_hours": strategy.BAR_INTERVAL_HOURS,
        "baseline_volatility_bars": strategy.BASELINE_VOLATILITY_BARS,
        "compression_ratio_ceiling": strategy.COMPRESSION_RATIO_CEILING,
        "compression_ratio_floor": strategy.COMPRESSION_RATIO_FLOOR,
        "compression_volatility_bars": strategy.COMPRESSION_VOLATILITY_BARS,
        "gross_target": strategy.GROSS_TARGET,
        "history_return_bars": strategy.HISTORY_RETURN_BARS,
        "maximum_symbol_exposure": strategy.MAXIMUM_SYMBOL_EXPOSURE,
        "minimum_direction_agreement": "2/3",
        "minimum_positions_per_side": strategy.MINIMUM_POSITIONS_PER_SIDE,
        "minimum_valid_symbols": strategy.MINIMUM_VALID_SYMBOLS,
        "rebalance_interval_bars": strategy.REBALANCE_INTERVAL_BARS,
        "selected_fraction_per_side": "1/5",
        "shock_bars": strategy.SHOCK_BARS,
        "shock_saturation_z": strategy.SHOCK_SATURATION_Z,
    }

    risk = json.loads((TEAM_DIR / "risk_policy.json").read_text(encoding="utf-8"))
    assert risk["drawdown_brakes"] == []
    assert risk["position_stop"]["enabled"] is False
    assert risk["time_stop"]["enabled"] is False
    assert risk["turnover_limit"]["enabled"] is False
    assert risk["volatility_target"]["enabled"] is False
