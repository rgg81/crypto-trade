"""Synthetic causal and construction tests for the Team 07 mechanism pivot."""

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

DEFAULT_DECISION = pd.Timestamp(0, unit="ns", tz="UTC") + pd.Timedelta(days=24000)


def _synthetic_context(
    *,
    decision_time: pd.Timestamp = DEFAULT_DECISION,
    symbol_count: int = 28,
    common_drift: float = 0.0008,
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
        loading = (symbol_index - center) / max(1.0, center)
        closes = [100.0 + symbol_index]
        for return_index in range(strategy.HISTORY_RETURN_BARS):
            common = common_drift + 0.0012 * math.sin(return_index / 11.0)
            relative = 0.0007 * math.sin(return_index / 7.0 + symbol_index * 0.53)
            if return_index >= strategy.HISTORY_RETURN_BARS - strategy.SLOW_TREND_BARS:
                relative += 0.00045 * loading
            if return_index >= strategy.HISTORY_RETURN_BARS - strategy.SHORT_REVERSAL_BARS:
                relative += 0.0012 * loading
            closes.append(closes[-1] * math.exp(common + relative))
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


def test_deterministic_finite_broad_two_sided_targets() -> None:
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
    assert abs(sum(first.values())) <= strategy.MAXIMUM_DIRECTIONAL_NET + 1e-10
    assert max(abs(value) for value in first.values()) <= strategy.MAXIMUM_SYMBOL_EXPOSURE + 1e-10


def test_common_market_state_changes_directional_side_budget() -> None:
    bull = _targets(_synthetic_context(common_drift=0.0015))
    bear = _targets(_synthetic_context(common_drift=-0.0015))

    assert sum(bull.values()) > 0.0
    assert sum(bear.values()) < 0.0
    assert any(value > 0.0 for value in bull.values())
    assert any(value < 0.0 for value in bull.values())
    assert any(value > 0.0 for value in bear.values())
    assert any(value < 0.0 for value in bear.values())


def test_short_residual_shock_has_a_reversal_forecast() -> None:
    market = (0.0,) * strategy.HISTORY_RETURN_BARS
    asset = (0.0,) * (strategy.HISTORY_RETURN_BARS - 3) + (0.01, 0.01, 0.01)
    feature = strategy._relative_feature(asset, market)

    assert feature is not None
    assert feature.short_reversal < 0.0
    assert feature.medium_trend > 0.0
    assert feature.slow_trend > 0.0


def test_future_rows_and_unused_fields_do_not_change_targets() -> None:
    base = _synthetic_context()
    expected = _targets(base)
    changed = SimpleNamespace(**vars(base))
    changed.bars = {}
    for symbol, frame in base.bars.items():
        mutated = frame.copy()
        mutated["open"] = [1.0e12 if index % 2 else 1.0e-12 for index in range(len(mutated))]
        mutated["high"] = 1.0e15
        mutated["low"] = 1.0e-15
        future = pd.DataFrame(
            {
                "open_time": [base.decision_time, base.decision_time + pd.Timedelta(hours=8)],
                "close": [1.0e12, 1.0e-12],
                "open": [1.0e-12, 1.0e12],
                "high": [1.0e15, 1.0e15],
                "low": [1.0e-15, 1.0e-15],
            }
        )
        changed.bars[symbol] = pd.concat([mutated, future], ignore_index=True)
    changed.auxiliary = {"unused": pd.DataFrame({"value": [1.0e12]})}

    assert _targets(changed) == expected


def test_exact_history_failure_flattens() -> None:
    context = _synthetic_context()
    context.bars = {symbol: frame.iloc[:-1].copy() for symbol, frame in context.bars.items()}
    assert _targets(context) == {}

    duplicate = _synthetic_context()
    duplicate.bars = {
        symbol: pd.concat([frame, frame.iloc[[-1]]], ignore_index=True)
        for symbol, frame in duplicate.bars.items()
    }
    assert _targets(duplicate) == {}


def test_funding_must_be_strictly_past() -> None:
    context = _synthetic_context()
    context.funding = pd.DataFrame(
        {
            "funding_time": [context.decision_time],
            "symbol": [context.eligible_symbols[0]],
            "funding_rate": [0.0001],
        }
    )
    assert _targets(context) == {}


def test_past_funding_enters_with_carry_direction() -> None:
    context = _synthetic_context()
    positive = context.eligible_symbols[0]
    negative = context.eligible_symbols[-1]
    context.funding = pd.DataFrame(
        {
            "funding_time": [
                context.decision_time - pd.Timedelta(hours=16),
                context.decision_time - pd.Timedelta(hours=16),
            ],
            "symbol": [positive, negative],
            "funding_rate": [0.001, -0.001],
        }
    )
    carry = strategy._past_funding_carry(
        context.funding,
        decision_time=context.decision_time,
        eligible=set(context.eligible_symbols),
    )

    assert carry is not None
    assert carry[positive] < 0.0
    assert carry[negative] > 0.0


def test_point_in_time_membership_is_the_only_candidate_set() -> None:
    context = _synthetic_context(symbol_count=32)
    excluded = set(sorted(context.bars)[-5:])
    context.eligible_symbols = tuple(sorted(set(context.bars) - excluded))
    targets = _targets(context)

    assert targets
    assert set(targets).issubset(set(context.eligible_symbols))
    assert not excluded & set(targets)


def test_boundary_is_called_once_before_selection_and_side_sizing(monkeypatch) -> None:
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
    hold = SimpleNamespace(**vars(base))
    hold.decision_time = base.decision_time + pd.Timedelta(hours=8)
    assert strategy.build_strategy().target_weights(hold, seed=strategy.FROZEN_SEED) is None

    off_grid = SimpleNamespace(**vars(base))
    off_grid.decision_time = base.decision_time + pd.Timedelta(hours=1)
    assert strategy.build_strategy().target_weights(off_grid, seed=strategy.FROZEN_SEED) == {}
    assert calls == 0


def test_boundary_returned_scores_drive_selection_and_direction(monkeypatch) -> None:
    context = _synthetic_context(common_drift=0.0015)
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
    assert sum(inverted.values()) < 0.0 < sum(baseline.values())


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


def test_frozen_config_matches_executable_constants() -> None:
    config = json.loads((TEAM_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    assert config["family_id"] == strategy.ACTIVE_FAMILY_ID
    assert config["candidate_id"] == strategy.ACTIVE_CANDIDATE_ID
    assert config["seed"] == strategy.FROZEN_SEED
    assert config["parameters"] == {
        "bar_interval_hours": strategy.BAR_INTERVAL_HOURS,
        "funding_carry_weight": strategy.FUNDING_CARRY_WEIGHT,
        "funding_lookback_events": strategy.FUNDING_LOOKBACK_EVENTS,
        "gross_target": strategy.GROSS_TARGET,
        "history_return_bars": strategy.HISTORY_RETURN_BARS,
        "market_breadth_weight": strategy.MARKET_BREADTH_WEIGHT,
        "market_fast_bars": strategy.MARKET_FAST_BARS,
        "market_fast_weight": strategy.MARKET_FAST_WEIGHT,
        "market_score_offset": strategy.MARKET_SCORE_OFFSET,
        "market_slow_bars": strategy.MARKET_SLOW_BARS,
        "market_slow_weight": strategy.MARKET_SLOW_WEIGHT,
        "market_trend_z_scale": strategy.MARKET_TREND_Z_SCALE,
        "maximum_directional_net": strategy.MAXIMUM_DIRECTIONAL_NET,
        "maximum_symbol_exposure": strategy.MAXIMUM_SYMBOL_EXPOSURE,
        "medium_relative_trend_weight": strategy.MEDIUM_RELATIVE_TREND_WEIGHT,
        "medium_trend_bars": strategy.MEDIUM_TREND_BARS,
        "minimum_positions_per_side": strategy.MINIMUM_POSITIONS_PER_SIDE,
        "minimum_return_volatility": strategy.MINIMUM_RETURN_VOLATILITY,
        "minimum_valid_symbols": strategy.MINIMUM_VALID_SYMBOLS,
        "rebalance_interval_bars": strategy.REBALANCE_INTERVAL_BARS,
        "relative_trend_base_weight": strategy.RELATIVE_TREND_BASE_WEIGHT,
        "relative_trend_state_weight": strategy.RELATIVE_TREND_STATE_WEIGHT,
        "selected_fraction_per_side": "1/4",
        "short_reversal_bars": strategy.SHORT_REVERSAL_BARS,
        "slow_relative_trend_weight": strategy.SLOW_RELATIVE_TREND_WEIGHT,
        "slow_trend_bars": strategy.SLOW_TREND_BARS,
        "volatility_bars": strategy.VOLATILITY_BARS,
    }

    risk = json.loads((TEAM_DIR / "risk_policy.json").read_text(encoding="utf-8"))
    assert risk["drawdown_brakes"] == []
    assert risk["position_stop"]["enabled"] is False
    assert risk["time_stop"]["enabled"] is False
    assert risk["turnover_limit"]["enabled"] is False
    assert risk["volatility_target"]["enabled"] is False
