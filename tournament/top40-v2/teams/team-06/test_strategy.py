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
    times = pd.date_range(end=decision, periods=128, freq="8h", tz="UTC")
    bars: dict[str, pd.DataFrame] = {}
    for symbol_index in range(symbol_count):
        symbol = f"S{symbol_index:02d}USDT"
        slope = (symbol_index - (symbol_count - 1) / 2.0) * 0.00018
        closes = [
            100.0
            * math.exp(slope * offset)
            * (1.0 + 0.006 * math.sin(offset / 5.0 + symbol_index / 3.0))
            for offset in range(len(times))
        ]
        bars[symbol] = pd.DataFrame({"close_time": times, "close": closes})
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
    future_times = pd.date_range(
        start=base.decision_time + pd.Timedelta(hours=8), periods=3, freq="8h"
    )
    for symbol, frame in base.bars.items():
        corrupt_future = pd.DataFrame(
            {"close_time": future_times, "close": [1.0e-12, 1.0e12, float("nan")]}
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
        symbol: frame.loc[frame["close_time"] <= base.decision_time].copy()
        for symbol, frame in appended.bars.items()
    }
    assert _targets(truncated) == expected_targets


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


def test_preconstruction_identity_hook_observes_but_cannot_modify_scores() -> None:
    context = _synthetic_context()
    observed: dict[str, object] = {}

    def echo(timestamp, scores):
        observed["timestamp"] = timestamp
        observed["scores"] = dict(scores)
        return dict(scores)

    hooked = strategy.build_strategy(score_identity_hook=echo)
    hooked_targets = hooked.target_weights(context, seed=strategy.FROZEN_SEED)
    assert dict(hooked_targets or {}) == _targets(context)
    assert observed["timestamp"] == context.decision_time
    assert len(observed["scores"]) == len(context.eligible_symbols)

    def mutate_one_score(timestamp, scores):
        del timestamp
        changed = dict(scores)
        first_symbol = sorted(changed)[0]
        changed[first_symbol] += 1.0
        return changed

    with pytest.raises(ValueError, match="exact preconstruction scores"):
        strategy.build_strategy(score_identity_hook=mutate_one_score).target_weights(
            context, seed=strategy.FROZEN_SEED
        )


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
    assert parameters["slow_lookback_bars"] == strategy.SLOW_LOOKBACK_BARS
    assert parameters["selection_fraction"] == strategy.SELECTION_FRACTION
    assert parameters["base_gross_exposure"] == strategy.BASE_GROSS_EXPOSURE
    assert parameters["maximum_abs_net_exposure"] == strategy.MAXIMUM_ABS_NET_EXPOSURE
    assert parameters["maximum_symbol_exposure"] == strategy.MAXIMUM_SYMBOL_EXPOSURE

    risk = json.loads((TEAM_DIR / "risk_policy.json").read_text(encoding="utf-8"))
    assert risk["same_boundary_reentry"] is False
    assert risk["volatility_target"]["enabled"] is True
    assert risk["drawdown_brakes"] == [
        {"drawdown": 0.1, "gross_scale": 0.75},
        {"drawdown": 0.18, "gross_scale": 0.45},
        {"drawdown": 0.25, "gross_scale": 0.25},
    ]
    assert risk["position_stop"]["enabled"] is False
    assert risk["time_stop"]["enabled"] is False
    assert risk["turnover_limit"] == {
        "enabled": True,
        "maximum_one_way_turnover": 0.18,
    }
