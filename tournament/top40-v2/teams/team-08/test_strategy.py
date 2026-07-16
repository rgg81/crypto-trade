"""Synthetic causal and construction tests for Team 08's second/final mechanism pivot."""

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
    center = (symbol_count - 1) / 2.0
    for symbol_index in range(symbol_count):
        symbol = f"C{symbol_index:02d}USDT"
        loading = (symbol_index - center) / max(center, 1.0)
        closes = [100.0 + symbol_index]
        for return_index in range(strategy.HISTORY_RETURN_BARS):
            common = common_drift + 0.0018 * math.sin(return_index * 0.37)
            persistent = 0.00055 * loading
            idiosyncratic = 0.00022 * math.sin(
                return_index * 0.71 + symbol_index * 0.13
            )
            closes.append(closes[-1] * math.exp(common + persistent + idiosyncratic))
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


def _persistent_path(*, direction: float = 1.0, recent_amplitude: float = 0.0003):
    result = []
    for index in range(strategy.HISTORY_RETURN_BARS):
        amplitude = recent_amplitude if index >= strategy.BASELINE_VOLATILITY_BARS else 0.0003
        result.append(direction * 0.00045 + amplitude * math.sin(index * 0.83))
    return tuple(result)


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


def test_persistent_relative_leaders_and_laggards_occupy_opposite_sleeves() -> None:
    context = _synthetic_context()
    model = strategy.build_strategy()
    snapshot = model.preconstruction_snapshot(context, seed=strategy.FROZEN_SEED)
    assert snapshot is not None
    scores = snapshot.score_map()
    targets = _targets(context)
    side_count = sum(value > 0.0 for value in targets.values())
    expected_shorts = set(sorted(scores, key=lambda symbol: (scores[symbol], symbol))[:side_count])
    expected_longs = set(sorted(scores, key=lambda symbol: (scores[symbol], symbol))[-side_count:])

    assert {symbol for symbol, value in targets.items() if value < 0.0} == expected_shorts
    assert {symbol for symbol, value in targets.items() if value > 0.0} == expected_longs


def test_inactive_zero_scores_remain_zero_and_cannot_enter_either_sleeve(monkeypatch) -> None:
    context = _synthetic_context()
    symbols = tuple(sorted(context.eligible_symbols))
    zero_snapshot = strategy.PreconstructionSnapshot(
        decision_time=context.decision_time,
        scores=tuple((symbol, 0.0) for symbol in symbols),
    )
    model = strategy.build_strategy()
    monkeypatch.setattr(model, "preconstruction_snapshot", lambda *args, **kwargs: zero_snapshot)

    assert strategy._signed_magnitude_ranks({symbol: 0.0 for symbol in symbols}) == {
        symbol: 0.0 for symbol in symbols
    }
    assert model.target_weights(context, seed=strategy.FROZEN_SEED) == {}


def test_asymmetric_zero_scores_remain_inactive_when_both_active_sides_are_broad(
    monkeypatch,
) -> None:
    context = _synthetic_context()
    symbols = tuple(sorted(context.eligible_symbols))
    raw = {
        symbol: (
            -float(index + 1)
            if index < 9
            else float(index - 18)
            if index >= 19
            else 0.0
        )
        for index, symbol in enumerate(symbols)
    }
    ranked = strategy._signed_magnitude_ranks(raw)
    assert ranked is not None
    inactive = {symbol for symbol, value in raw.items() if value == 0.0}
    assert inactive
    assert all(ranked[symbol] == 0.0 for symbol in inactive)
    snapshot = strategy.PreconstructionSnapshot(
        decision_time=context.decision_time,
        scores=tuple((symbol, ranked[symbol]) for symbol in symbols),
    )
    model = strategy.build_strategy()
    monkeypatch.setattr(model, "preconstruction_snapshot", lambda *args, **kwargs: snapshot)
    targets = model.target_weights(context, seed=strategy.FROZEN_SEED)

    assert targets
    assert inactive.isdisjoint(targets)


def test_sparse_active_side_flattens_instead_of_recruiting_zero_scores(monkeypatch) -> None:
    context = _synthetic_context()
    symbols = tuple(sorted(context.eligible_symbols))
    raw = {
        symbol: (
            -float(index + 1)
            if index < 7
            else float(index - 17)
            if index >= 18
            else 0.0
        )
        for index, symbol in enumerate(symbols)
    }
    ranked = strategy._signed_magnitude_ranks(raw)
    assert ranked is not None
    snapshot = strategy.PreconstructionSnapshot(
        decision_time=context.decision_time,
        scores=tuple((symbol, ranked[symbol]) for symbol in symbols),
    )
    model = strategy.build_strategy()
    monkeypatch.setattr(model, "preconstruction_snapshot", lambda *args, **kwargs: snapshot)

    assert model.target_weights(context, seed=strategy.FROZEN_SEED) == {}


def test_common_bull_and_bear_drifts_do_not_change_the_relative_book() -> None:
    neutral = _targets(_synthetic_context())
    bull = _targets(_synthetic_context(common_drift=0.0010))
    bear = _targets(_synthetic_context(common_drift=-0.0010))

    assert bull == neutral
    assert bear == neutral
    assert abs(sum(bull.values())) <= 1e-10
    assert abs(sum(bear.values())) <= 1e-10


def test_three_horizon_continuation_is_not_recoil_sign_inversion() -> None:
    positive = strategy._persistence_feature(_persistent_path(direction=1.0))
    negative = strategy._persistence_feature(_persistent_path(direction=-1.0))

    assert positive is not None and negative is not None
    assert positive.raw_persistence_score > 0.0
    assert negative.raw_persistence_score < 0.0
    assert positive.horizon_agreement == 1.0
    assert negative.horizon_agreement == 1.0
    assert all(value > 0.0 for value in positive.horizon_components)
    assert all(value < 0.0 for value in negative.horizon_components)


def test_horizon_disagreement_is_required_and_shrunk() -> None:
    persistent = strategy._persistence_feature(_persistent_path())
    mixed_path = tuple(
        0.0010 + 0.0002 * math.sin(index * 0.67)
        if index < 63
        else (
            -0.0015 + 0.0002 * math.sin(index * 0.67)
            if index < 105
            else 0.0015 + 0.0002 * math.sin(index * 0.67)
        )
        for index in range(strategy.HISTORY_RETURN_BARS)
    )
    mixed = strategy._persistence_feature(mixed_path)

    assert persistent is not None and mixed is not None
    assert persistent.horizon_agreement == 1.0
    assert mixed.horizon_agreement == pytest.approx(2.0 / 3.0)
    assert abs(mixed.raw_persistence_score) < abs(persistent.raw_persistence_score)


def test_excess_recent_volatility_only_shrinks_signal() -> None:
    ordinary = strategy._persistence_feature(_persistent_path(recent_amplitude=0.0003))
    volatile = strategy._persistence_feature(_persistent_path(recent_amplitude=0.0040))

    assert ordinary is not None and volatile is not None
    assert ordinary.volatility_shrink == 1.0
    assert volatile.recent_to_baseline_volatility > 1.0
    assert 0.0 < volatile.volatility_shrink < 1.0


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
        "disagreement_power": strategy.DISAGREEMENT_POWER,
        "gross_target": strategy.GROSS_TARGET,
        "history_return_bars": strategy.HISTORY_RETURN_BARS,
        "horizon_saturation_z": strategy.HORIZON_SATURATION_Z,
        "maximum_symbol_exposure": strategy.MAXIMUM_SYMBOL_EXPOSURE,
        "medium_horizon_bars": strategy.MEDIUM_HORIZON_BARS,
        "medium_horizon_weight": strategy.MEDIUM_HORIZON_WEIGHT,
        "minimum_agreeing_horizons": strategy.MINIMUM_AGREEING_HORIZONS,
        "minimum_positions_per_side": strategy.MINIMUM_POSITIONS_PER_SIDE,
        "minimum_valid_symbols": strategy.MINIMUM_VALID_SYMBOLS,
        "rebalance_interval_bars": strategy.REBALANCE_INTERVAL_BARS,
        "recent_volatility_bars": strategy.RECENT_VOLATILITY_BARS,
        "selected_fraction_per_side": "1/5",
        "short_horizon_bars": strategy.SHORT_HORIZON_BARS,
        "short_horizon_weight": strategy.SHORT_HORIZON_WEIGHT,
        "slow_horizon_bars": strategy.SLOW_HORIZON_BARS,
        "slow_horizon_weight": strategy.SLOW_HORIZON_WEIGHT,
    }

    risk = json.loads((TEAM_DIR / "risk_policy.json").read_text(encoding="utf-8"))
    assert risk["drawdown_brakes"] == []
    assert risk["position_stop"]["enabled"] is False
    assert risk["time_stop"]["enabled"] is False
    assert risk["turnover_limit"]["enabled"] is False
    assert risk["volatility_target"]["enabled"] is False
