"""Synthetic causal and construction tests for the Team 06 persistence pivot."""

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

DEFAULT_DECISION = pd.Timestamp(0, unit="ns", tz="UTC") + pd.Timedelta(days=20000)


def _synthetic_context(
    *,
    decision_time: pd.Timestamp = DEFAULT_DECISION,
    symbol_count: int = 28,
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
    center = (symbol_count - 1) / 2.0
    for symbol_index in range(symbol_count):
        symbol = f"C{symbol_index:02d}USDT"
        closes = [100.0]
        loading = (symbol_index - center) / max(1.0, center)
        for return_index in range(strategy.HISTORY_RETURN_BARS):
            common = 0.0015 * math.sin(return_index / 7.0)
            idiosyncratic = 0.0012 * math.sin(return_index / 4.0 + symbol_index * 0.71)
            if return_index >= strategy.BASELINE_RANK_BARS + strategy.PRIOR_RANK_BARS:
                idiosyncratic += 0.0040 * loading
            elif return_index >= strategy.BASELINE_RANK_BARS:
                idiosyncratic -= 0.0020 * loading
            closes.append(closes[-1] * math.exp(common + idiosyncratic))
        frame = pd.DataFrame({"open_time": open_times, "close": closes})
        assert isinstance(frame.index, pd.RangeIndex)
        bars[symbol] = frame
    return SimpleNamespace(
        decision_time=decision,
        bars=bars,
        funding=pd.DataFrame(columns=["timestamp", "symbol", "rate"]),
        auxiliary={},
        eligible_symbols=tuple(sorted(bars)),
    )


def _targets(context):
    result = strategy.build_strategy().target_weights(context, seed=strategy.FROZEN_SEED)
    assert result is not None
    return dict(result)


def test_deterministic_finite_broad_dollar_neutral_targets() -> None:
    context = _synthetic_context()
    first = _targets(context)
    second = _targets(context)

    assert first == second
    assert list(first) == sorted(first)
    assert sum(value > 0.0 for value in first.values()) >= 8
    assert sum(value < 0.0 for value in first.values()) >= 8
    assert all(math.isfinite(value) for value in first.values())
    assert sum(abs(value) for value in first.values()) <= 2.0 * strategy.SIDE_BUDGET + 1e-12
    assert abs(sum(first.values())) <= 1e-12
    assert max(abs(value) for value in first.values()) <= strategy.MAXIMUM_SYMBOL_EXPOSURE + 1e-12


def test_common_crypto_price_path_is_removed_by_cross_sectional_ranking() -> None:
    base = _synthetic_context()
    expected_scores = dict(
        strategy.build_strategy().preconstruction_scores(base, seed=strategy.FROZEN_SEED)
    )
    expected_targets = _targets(base)

    shifted = SimpleNamespace(**vars(base))
    shifted.bars = {}
    for symbol, frame in base.bars.items():
        changed = frame.copy()
        common_levels = [
            math.exp(0.006 * index + 0.02 * math.sin(index / 9.0)) for index in range(len(changed))
        ]
        changed["close"] = [
            float(close) * common
            for close, common in zip(changed["close"], common_levels, strict=True)
        ]
        shifted.bars[symbol] = changed

    observed_scores = dict(
        strategy.build_strategy().preconstruction_scores(shifted, seed=strategy.FROZEN_SEED)
    )
    assert observed_scores == expected_scores
    assert _targets(shifted) == expected_targets


def test_positive_relative_shift_is_followed() -> None:
    baseline = tuple(-0.4 if index % 2 else 0.4 for index in range(strategy.BASELINE_RANK_BARS))
    path = baseline + (-0.5,) * strategy.PRIOR_RANK_BARS + (0.5,) * strategy.RECENT_RANK_BARS
    feature = strategy._relative_feature(path)

    assert feature is not None
    assert feature.rank_shift > 0.0
    assert feature.coherence == 1.0
    assert feature.raw_persistence_score > 0.0


def test_persistent_relative_level_contributes_without_acceleration() -> None:
    baseline = tuple(-0.4 if index % 2 else 0.4 for index in range(strategy.BASELINE_RANK_BARS))
    path = baseline + (0.5,) * strategy.PRIOR_RANK_BARS + (0.5,) * strategy.RECENT_RANK_BARS
    feature = strategy._relative_feature(path)

    assert feature is not None
    assert feature.rank_shift == 0.0
    assert feature.raw_persistence_score > 0.0


def test_future_rows_next_open_funding_and_auxiliary_do_not_change_signal() -> None:
    base = _synthetic_context()
    expected = _targets(base)
    changed = SimpleNamespace(**vars(base))
    changed.bars = {}
    for symbol, frame in base.bars.items():
        mutated = frame.copy()
        mutated["open"] = [1.0e12 if index % 2 else 1.0e-12 for index in range(len(mutated))]
        mutated["next_open"] = 9.0e11
        future = pd.DataFrame(
            {
                "open_time": [base.decision_time, base.decision_time + pd.Timedelta(hours=8)],
                "close": [1.0e12, 1.0e-12],
                "open": [1.0e-12, 1.0e12],
                "next_open": [7.0e11, 7.0e11],
            }
        )
        changed.bars[symbol] = pd.concat([mutated, future], ignore_index=True)
    changed.funding = pd.DataFrame(
        {
            "timestamp": [base.decision_time],
            "symbol": [next(iter(base.bars))],
            "rate": [99.0],
        }
    )
    changed.auxiliary = {"unused_field": pd.DataFrame({"value": [1.0e9]})}

    assert _targets(changed) == expected


def test_exact_history_and_canonical_range_index_fail_closed() -> None:
    base = _synthetic_context()
    one_symbol = next(iter(base.bars))
    mixed_duplicate = SimpleNamespace(**vars(base))
    mixed_duplicate.bars = dict(base.bars)
    invalid_duplicate = base.bars[one_symbol].iloc[[-1]].copy()
    invalid_duplicate["close"] = -1.0
    mixed_duplicate.bars[one_symbol] = pd.concat(
        [base.bars[one_symbol], invalid_duplicate],
        ignore_index=True,
    )
    mixed_scores = dict(
        strategy.build_strategy().preconstruction_scores(
            mixed_duplicate,
            seed=strategy.FROZEN_SEED,
        )
    )
    assert one_symbol not in mixed_scores
    assert len(mixed_scores) == len(base.bars) - 1

    duplicate = SimpleNamespace(**vars(base))
    duplicate.bars = {
        symbol: pd.concat([frame, frame.iloc[[-1]]], ignore_index=True)
        for symbol, frame in base.bars.items()
    }
    assert _targets(duplicate) == {}

    noncanonical = SimpleNamespace(**vars(base))
    noncanonical.bars = {
        symbol: frame.set_index("open_time") for symbol, frame in base.bars.items()
    }
    assert _targets(noncanonical) == {}


def test_point_in_time_membership_is_the_only_candidate_set() -> None:
    context = _synthetic_context(symbol_count=32)
    context.eligible_symbols = tuple(sorted(context.bars)[:-5])
    targets = _targets(context)

    assert targets
    assert set(targets).issubset(set(context.eligible_symbols))
    assert not (set(context.bars) - set(context.eligible_symbols)) & set(targets)


def test_boundary_is_called_once_on_schedule_before_selection(monkeypatch) -> None:
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
    for offset in range(1, strategy.REBALANCE_INTERVAL_BARS):
        hold = SimpleNamespace(**vars(base))
        hold.decision_time = base.decision_time + offset * pd.Timedelta(
            hours=strategy.BAR_INTERVAL_HOURS
        )
        assert strategy.build_strategy().target_weights(hold, seed=strategy.FROZEN_SEED) is None

    off_grid = SimpleNamespace(**vars(base))
    off_grid.decision_time = base.decision_time + pd.Timedelta(hours=1)
    assert strategy.build_strategy().target_weights(off_grid, seed=strategy.FROZEN_SEED) == {}

    naive = SimpleNamespace(**vars(base))
    naive.decision_time = base.decision_time.tz_localize(None)
    assert strategy.build_strategy().target_weights(naive, seed=strategy.FROZEN_SEED) == {}

    pre_epoch = SimpleNamespace(**vars(base))
    pre_epoch.decision_time = pd.Timestamp(0, unit="ns", tz="UTC") - pd.Timedelta(hours=8)
    assert strategy.build_strategy().target_weights(pre_epoch, seed=strategy.FROZEN_SEED) == {}
    assert calls == 0


def test_boundary_returned_scores_drive_construction(monkeypatch) -> None:
    context = _synthetic_context()
    baseline = _targets(context)
    calls = 0

    def invert(scores):
        nonlocal calls
        calls += 1
        for symbol in scores:
            scores[symbol] = -scores[symbol]
        return scores

    monkeypatch.setattr(strategy, "score_boundary", invert)
    inverted = strategy.build_strategy().target_weights(context, seed=strategy.FROZEN_SEED)
    assert calls == 1
    assert inverted
    assert dict(inverted) != baseline


def test_wrong_seed_and_candidate_identity_are_rejected(monkeypatch) -> None:
    context = _synthetic_context()
    with pytest.raises(ValueError, match="frozen seed"):
        strategy.build_strategy().target_weights(context, seed=strategy.FROZEN_SEED + 1)

    monkeypatch.setattr(candidate_variant, "ACTIVE_CANDIDATE_ID", "unknown-pivot")
    with pytest.raises(ValueError, match="unknown materialized"):
        strategy.build_strategy()


def test_active_candidate_has_no_hidden_parameter_override(monkeypatch) -> None:
    monkeypatch.setattr(candidate_variant, "ACTIVE_OVERRIDES", {"selection_fraction": 0.25})
    with pytest.raises(ValueError, match="do not match"):
        strategy.build_strategy()


def test_frozen_config_matches_executable_constants() -> None:
    config = json.loads((TEAM_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    assert config["family_id"] == strategy.ACTIVE_FAMILY_ID
    assert config["candidate_id"] == strategy.ACTIVE_CANDIDATE_ID
    assert config["seed"] == strategy.FROZEN_SEED
    assert config["parameters"] == {
        "acceleration_weight": strategy.ACCELERATION_WEIGHT,
        "bar_interval_hours": strategy.BAR_INTERVAL_HOURS,
        "baseline_rank_bars": strategy.BASELINE_RANK_BARS,
        "coherence_base_weight": strategy.COHERENCE_BASE_WEIGHT,
        "level_weight": strategy.LEVEL_WEIGHT,
        "maximum_symbol_exposure": strategy.MAXIMUM_SYMBOL_EXPOSURE,
        "minimum_positions_per_side": strategy.MINIMUM_POSITIONS_PER_SIDE,
        "minimum_rank_volatility": strategy.MINIMUM_RANK_VOLATILITY,
        "minimum_valid_symbols": strategy.MINIMUM_VALID_SYMBOLS,
        "prior_rank_bars": strategy.PRIOR_RANK_BARS,
        "rebalance_interval_bars": strategy.REBALANCE_INTERVAL_BARS,
        "recent_rank_bars": strategy.RECENT_RANK_BARS,
        "selection_fraction": "1/5",
        "side_budget": strategy.SIDE_BUDGET,
    }

    risk = json.loads((TEAM_DIR / "risk_policy.json").read_text(encoding="utf-8"))
    assert risk["drawdown_brakes"] == []
    assert risk["position_stop"]["enabled"] is False
    assert risk["time_stop"]["enabled"] is False
    assert risk["turnover_limit"]["enabled"] is False
    assert risk["volatility_target"]["enabled"] is False
