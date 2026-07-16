"""Focused synthetic tests for Team 06.

These tests use invented price paths only. They deliberately do not instantiate the evaluator or
read tournament data. Organizer-owned execution, funding, cost, capacity, and risk-ordering tests
remain integration tests described in ``synthetic_test_plan.md``.
"""

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

import strategy  # noqa: E402


def _synthetic_context(
    *,
    decision_time: str | pd.Timestamp = "2023-06-30T00:00:00Z",
    symbol_count: int = 24,
):
    decision = pd.Timestamp(decision_time)
    open_times = pd.date_range(
        end=decision - pd.Timedelta(hours=strategy.BAR_INTERVAL_HOURS),
        periods=128,
        freq="8h",
        tz="UTC",
    )
    bars: dict[str, pd.DataFrame] = {}
    for symbol_index in range(symbol_count):
        symbol = f"S{symbol_index:02d}USDT"
        slope = (symbol_index - (symbol_count - 1) / 2.0) * 0.00018
        closes = [
            100.0
            * math.exp(slope * offset)
            * (1.0 + 0.006 * math.sin(offset / 5.0 + symbol_index / 3.0))
            for offset in range(len(open_times))
        ]
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


def test_deterministic_finite_conservative_two_sided_targets() -> None:
    context = _synthetic_context()
    first = _targets(context)
    second = _targets(context)

    assert first == second
    assert list(first) == sorted(first)
    assert all(math.isfinite(value) for value in first.values())
    assert sum(value > 0.0 for value in first.values()) >= 4
    assert sum(value < 0.0 for value in first.values()) >= 4
    assert sum(abs(value) for value in first.values()) <= 0.48 + 1e-12
    assert abs(sum(first.values())) <= 0.04 + 1e-12
    assert max(abs(value) for value in first.values()) <= 0.07 + 1e-12


def test_future_append_corruption_and_truncation_are_invariant() -> None:
    base = _synthetic_context()
    expected_scores = dict(
        strategy.build_strategy().preconstruction_scores(base, seed=strategy.FROZEN_SEED)
    )
    expected_targets = _targets(base)

    appended_bars: dict[str, pd.DataFrame] = {}
    future_open_times = pd.date_range(
        start=base.decision_time - pd.Timedelta(hours=7, minutes=59),
        periods=3,
        freq="8h",
    )
    for symbol, frame in base.bars.items():
        corrupt_future = pd.DataFrame(
            {
                "open_time": future_open_times,
                "close": [1.0e-12, 1.0e12, float("nan")],
            }
        )
        appended_bars[symbol] = pd.concat([frame, corrupt_future], ignore_index=True)
    appended = SimpleNamespace(**vars(base))
    appended.bars = appended_bars

    observed_scores = dict(
        strategy.build_strategy().preconstruction_scores(appended, seed=strategy.FROZEN_SEED)
    )
    assert observed_scores == expected_scores
    assert _targets(appended) == expected_targets

    truncated = SimpleNamespace(**vars(appended))
    truncated.bars = {
        symbol: frame.loc[
            pd.to_datetime(frame["open_time"], utc=True)
            + pd.Timedelta(hours=strategy.BAR_INTERVAL_HOURS)
            <= base.decision_time
        ].reset_index(drop=True)
        for symbol, frame in appended.bars.items()
    }
    assert _targets(truncated) == expected_targets


def test_only_canonical_rangeindex_open_time_frames_are_admitted() -> None:
    context = _synthetic_context()
    noncanonical = SimpleNamespace(**vars(context))
    noncanonical.bars = {
        symbol: frame.set_index("open_time") for symbol, frame in context.bars.items()
    }

    assert strategy.build_strategy().target_weights(
        noncanonical, seed=strategy.FROZEN_SEED
    ) == {}


def test_point_in_time_membership_is_the_only_candidate_set() -> None:
    context = _synthetic_context()
    eligible = tuple(sorted(context.bars)[:-5])
    context.eligible_symbols = eligible
    targets = _targets(context)

    assert targets
    assert set(targets).issubset(set(eligible))
    assert not (set(context.bars) - set(eligible)) & set(targets)


def test_next_open_auxiliary_funding_and_cost_like_fields_cannot_change_signal() -> None:
    base = _synthetic_context()
    expected = _targets(base)
    mutated = SimpleNamespace(**vars(base))
    mutated.bars = {}
    for symbol, frame in base.bars.items():
        changed = frame.copy()
        changed["open"] = [1.0e9 if index % 2 else 1.0e-9 for index in range(len(changed))]
        changed["next_open"] = 7.0e11
        mutated.bars[symbol] = changed
    mutated.funding = pd.DataFrame(
        {
            "timestamp": [base.decision_time - pd.Timedelta(hours=1), base.decision_time],
            "symbol": ["S00USDT", "S00USDT"],
            "rate": [-10.0, 10.0],
        }
    )
    mutated.auxiliary = {
        "costs": pd.DataFrame(
            {"taker_fee_bps": [5.0, 10.0], "slippage_bps": [2.5, 5.0]}
        )
    }

    assert _targets(mutated) == expected


def test_direct_public_score_boundary_is_called_once_at_the_declared_boundary(
    monkeypatch,
) -> None:
    context = _synthetic_context()
    assert strategy.score_boundary is public_score_boundary
    expected_scores = strategy.build_strategy().preconstruction_snapshot(
        context, seed=strategy.FROZEN_SEED
    ).score_map()
    observed: list[dict[str, float]] = []

    def capture(scores):
        assert type(scores) is dict
        assert all(type(symbol) is str for symbol in scores)
        assert all(type(value) is float and math.isfinite(value) for value in scores.values())
        observed.append(dict(scores))
        return scores

    monkeypatch.setattr(strategy, "score_boundary", capture)
    targets = strategy.build_strategy().target_weights(context, seed=strategy.FROZEN_SEED)
    assert targets
    assert observed == [expected_scores]


def test_score_boundary_returned_values_drive_construction(monkeypatch) -> None:
    context = _synthetic_context()
    baseline = _targets(context)
    call_count = 0

    def invert_scores(scores):
        nonlocal call_count
        call_count += 1
        for symbol in scores:
            scores[symbol] = -scores[symbol]
        return scores

    monkeypatch.setattr(strategy, "score_boundary", invert_scores)
    inverted = strategy.build_strategy().target_weights(context, seed=strategy.FROZEN_SEED)
    assert call_count == 1
    assert inverted
    assert dict(inverted) != baseline


def test_score_capture_does_not_change_frozen_candidate_bytes(monkeypatch) -> None:
    context = _synthetic_context()
    frozen_paths = (
        TEAM_DIR / "strategy.py",
        TEAM_DIR / "frozen_config.json",
        TEAM_DIR / "risk_policy.json",
        TEAM_DIR / "candidate_manifest.template.json",
        TEAM_DIR / "candidate_contract.template.json",
    )
    before = {path: path.read_bytes() for path in frozen_paths}
    calls = 0

    def identity_capture(scores):
        nonlocal calls
        calls += 1
        return scores

    monkeypatch.setattr(strategy, "score_boundary", identity_capture)
    assert strategy.build_strategy().target_weights(context, seed=strategy.FROZEN_SEED)
    assert calls == 1
    assert {path: path.read_bytes() for path in frozen_paths} == before


def test_non_rebalance_holds_and_insufficient_universe_requests_flat() -> None:
    off_schedule = _synthetic_context(decision_time="2023-06-30T08:00:00Z")
    assert (
        strategy.build_strategy().target_weights(
            off_schedule, seed=strategy.FROZEN_SEED
        )
        is None
    )

    too_small = _synthetic_context(symbol_count=11)
    assert strategy.build_strategy().target_weights(too_small, seed=strategy.FROZEN_SEED) == {}


def test_wrong_seed_is_rejected_and_clean_instances_reproduce() -> None:
    context = _synthetic_context()
    with pytest.raises(ValueError, match="frozen seed"):
        strategy.build_strategy().target_weights(context, seed=strategy.FROZEN_SEED + 1)

    clean_a = strategy.BalancedTrendReversalStrategy()
    clean_b = strategy.BalancedTrendReversalStrategy()
    assert clean_a.target_weights(context, seed=strategy.FROZEN_SEED) == clean_b.target_weights(
        context, seed=strategy.FROZEN_SEED
    )


def test_frozen_config_and_declarative_risk_boundary_match_source() -> None:
    frozen = json.loads((TEAM_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    parameters = frozen["parameters"]
    assert parameters == {
        "annualization_bars": strategy.ANNUALIZATION_BARS,
        "bar_interval_hours": strategy.BAR_INTERVAL_HOURS,
        "base_gross_exposure": strategy.BASE_GROSS_EXPOSURE,
        "chop_trend_mix": strategy.CHOP_TREND_MIX,
        "direction_full_scale_return": strategy.DIRECTION_FULL_SCALE_RETURN,
        "directional_trend_mix": strategy.DIRECTIONAL_TREND_MIX,
        "fast_lookback_bars": strategy.FAST_LOOKBACK_BARS,
        "fast_trend_weight": strategy.FAST_TREND_WEIGHT,
        "maximum_abs_net_exposure": strategy.MAXIMUM_ABS_NET_EXPOSURE,
        "maximum_staleness_hours": strategy.MAXIMUM_STALENESS_HOURS,
        "maximum_symbol_exposure": strategy.MAXIMUM_SYMBOL_EXPOSURE,
        "minimum_positions_per_side": strategy.MINIMUM_POSITIONS_PER_SIDE,
        "minimum_valid_symbols": strategy.MINIMUM_VALID_SYMBOLS,
        "momentum_lag_bars": strategy.MOMENTUM_LAG_BARS,
        "rebalance_hour_utc": strategy.REBALANCE_HOUR_UTC,
        "reversal_lookback_bars": strategy.REVERSAL_LOOKBACK_BARS,
        "selection_fraction": strategy.SELECTION_FRACTION,
        "slow_lookback_bars": strategy.SLOW_LOOKBACK_BARS,
        "slow_trend_weight": strategy.SLOW_TREND_WEIGHT,
        "volatility_floor": strategy.VOLATILITY_FLOOR,
        "volatility_lookback_bars": strategy.VOLATILITY_LOOKBACK_BARS,
        "volatility_score_penalty": strategy.VOLATILITY_SCORE_PENALTY,
    }

    risk = json.loads((TEAM_DIR / "risk_policy.json").read_text(encoding="utf-8"))
    assert risk["same_boundary_reentry"] is False
    assert risk["volatility_target"]["enabled"] is False
    assert risk["drawdown_brakes"] == []
    assert risk["position_stop"]["enabled"] is False
    assert risk["time_stop"]["enabled"] is False
    assert risk["turnover_limit"]["enabled"] is False

    combined = json.loads(
        (TEAM_DIR / "risk_policies" / "combined.json").read_text(encoding="utf-8")
    )
    assert combined["volatility_target"]["enabled"] is True
    assert combined["drawdown_brakes"] == [
        {"drawdown": 0.1, "gross_scale": 0.75},
        {"drawdown": 0.18, "gross_scale": 0.45},
        {"drawdown": 0.25, "gross_scale": 0.25},
    ]
    assert combined["turnover_limit"] == {
        "enabled": True,
        "maximum_one_way_turnover": 0.18,
    }
