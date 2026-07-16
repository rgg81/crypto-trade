"""Focused synthetic tests for Team 05.

These tests use generated bars only.  They are authored for later organizer/QE execution and are
not executed during clean-room design.
"""

from __future__ import annotations

import dataclasses
import math
from collections import OrderedDict

import pandas as pd
import pytest

from crypto_trade.tournament.protocol import DecisionContext
from strategy import (
    BASE_PARAMETERS,
    build_strategy,
    build_strategy_from_parameters,
    preconstruction_scores,
    scores_to_target_weights,
)


DECISION = pd.Timestamp("2020-07-17T00:00:00Z")


def _bars(symbol_number: int, *, future_days: int = 0) -> pd.DataFrame:
    end = DECISION + pd.Timedelta(days=future_days)
    index = pd.date_range("2020-01-01T00:00:00Z", end=end, freq="8h")
    centered = symbol_number - 9.5
    drift = centered * 0.000018
    close = [
        100.0
        * math.exp(
            drift * step
            + 0.004 * math.sin(step / (5.0 + (symbol_number % 4)))
            + 0.0015 * math.cos(step / 2.7 + symbol_number)
        )
        for step in range(len(index))
    ]
    return pd.DataFrame(
        {
            "open": [value * (1.0 + 0.0005) for value in close],
            "high": [value * (1.0 + 0.0020) for value in close],
            "low": [value * (1.0 - 0.0020) for value in close],
            "close": close,
            "quote_volume": [1_000_000.0 + symbol_number for _ in close],
        },
        index=index,
    )


def _frames(*, future_days: int = 0) -> OrderedDict[str, pd.DataFrame]:
    return OrderedDict(
        (f"S{number:02d}USDT", _bars(number, future_days=future_days))
        for number in range(20)
    )


def _context(
    frames: OrderedDict[str, pd.DataFrame] | dict[str, pd.DataFrame],
    *,
    decision: pd.Timestamp = DECISION,
    eligible: list[str] | None = None,
    funding: pd.DataFrame | None = None,
    auxiliary: dict[str, pd.DataFrame] | None = None,
) -> DecisionContext:
    return DecisionContext(
        decision_time=decision,
        bars=frames,
        funding=pd.DataFrame() if funding is None else funding,
        auxiliary={} if auxiliary is None else auxiliary,
        eligible_symbols=list(frames) if eligible is None else eligible,
    )


def _targets(context: DecisionContext, *, seed: int = 20260801) -> dict[str, float]:
    result = build_strategy().target_weights(context, seed=seed)
    assert result is not None
    return dict(result)


def test_future_append_truncation_and_corruption_invariance() -> None:
    with_future = _frames(future_days=5)
    truncated = OrderedDict(
        (symbol, frame.loc[frame.index <= DECISION].copy())
        for symbol, frame in with_future.items()
    )
    corrupted = OrderedDict((symbol, frame.copy()) for symbol, frame in with_future.items())
    for frame in corrupted.values():
        future = frame.index > DECISION
        frame.loc[future, "close"] = [float("nan") if i % 2 else 1e100 for i in range(future.sum())]
        frame.loc[future, "open"] = -1e100

    baseline_scores = preconstruction_scores(_context(truncated))
    assert preconstruction_scores(_context(with_future)) == baseline_scores
    assert preconstruction_scores(_context(corrupted)) == baseline_scores
    assert _targets(_context(with_future)) == _targets(_context(truncated))
    assert _targets(_context(corrupted)) == _targets(_context(truncated))


def test_non_close_fields_funding_and_auxiliary_cannot_change_targets() -> None:
    frames = _frames()
    altered = OrderedDict((symbol, frame.copy()) for symbol, frame in frames.items())
    for frame in altered.values():
        frame.loc[:, "open"] = -999999.0
        frame.loc[:, "high"] = 1e50
        frame.loc[:, "low"] = -1e50
        frame.loc[:, "quote_volume"] = float("nan")
    hostile_funding = pd.DataFrame(
        {"symbol": ["S00USDT"], "funding_rate": [999.0]},
        index=[DECISION - pd.Timedelta(hours=1)],
    )
    hostile_auxiliary = {
        "oracle": pd.DataFrame({"future_target": [1e100]}, index=[DECISION])
    }
    assert _targets(_context(frames)) == _targets(
        _context(
            altered,
            funding=hostile_funding,
            auxiliary=hostile_auxiliary,
        )
    )


def test_point_in_time_membership_excludes_ineligible_symbol() -> None:
    frames = _frames()
    frames["HOTUSDT"] = _bars(40)
    eligible = [symbol for symbol in frames if symbol != "HOTUSDT"]
    scores = preconstruction_scores(_context(frames, eligible=eligible))
    targets = _targets(_context(frames, eligible=eligible))
    assert "HOTUSDT" not in scores
    assert "HOTUSDT" not in targets
    assert set(targets) <= set(eligible)


def test_mapping_order_seed_and_fresh_instance_reproducibility() -> None:
    frames = _frames()
    reversed_frames = OrderedDict(reversed(list(frames.items())))
    first = build_strategy().target_weights(_context(frames), seed=0)
    second = build_strategy().target_weights(_context(reversed_frames), seed=999999)
    third = build_strategy().target_weights(_context(frames), seed=20260801)
    assert first == second == third


def test_adapter_emits_finite_two_sided_conservative_targets() -> None:
    scores = preconstruction_scores(_context(_frames()))
    targets = scores_to_target_weights(scores)
    assert targets
    assert all(math.isfinite(weight) for weight in targets.values())
    assert any(weight > 0 for weight in targets.values())
    assert any(weight < 0 for weight in targets.values())
    gross = sum(abs(weight) for weight in targets.values())
    net = sum(targets.values())
    assert gross <= BASE_PARAMETERS.target_gross + 1e-12
    assert abs(net) <= BASE_PARAMETERS.maximum_abs_net_tilt + 1e-12
    assert max(abs(weight) for weight in targets.values()) <= (
        BASE_PARAMETERS.maximum_symbol_weight + 1e-12
    )
    assert list(targets) == sorted(targets)


def test_adapter_rejects_an_invalid_score_record_instead_of_imputing() -> None:
    scores = preconstruction_scores(_context(_frames()))
    first_symbol = sorted(scores)[0]
    corrupted = dict(scores)
    corrupted[first_symbol] = dataclasses.replace(
        corrupted[first_symbol], score=float("inf")
    )
    assert scores_to_target_weights(corrupted) == {}


def test_score_order_identifies_relative_winner_and_loser() -> None:
    scores = preconstruction_scores(_context(_frames()))
    assert scores["S19USDT"].score > scores["S00USDT"].score


def test_insufficient_or_degenerate_history_fails_closed_to_flat() -> None:
    too_small = OrderedDict(list(_frames().items())[:11])
    assert preconstruction_scores(_context(too_small)) == {}
    assert _targets(_context(too_small)) == {}

    constant = OrderedDict()
    index = pd.date_range("2020-01-01T00:00:00Z", end=DECISION, freq="8h")
    for number in range(20):
        constant[f"C{number:02d}USDT"] = pd.DataFrame(
            {"close": [100.0] * len(index)}, index=index
        )
    assert preconstruction_scores(_context(constant)) == {}
    assert _targets(_context(constant)) == {}


def test_non_rebalance_boundary_returns_none_not_flat() -> None:
    off_schedule = DECISION + pd.Timedelta(days=1)
    frames = OrderedDict((symbol, _bars(number, future_days=1)) for number, symbol in enumerate(_frames()))
    result = build_strategy().target_weights(
        _context(frames, decision=off_schedule),
        seed=20260801,
    )
    assert result is None


def test_neighbor_override_is_explicit_and_unknown_axis_is_rejected() -> None:
    neighbor = build_strategy_from_parameters({"slow_horizon_days": 50})
    assert neighbor.parameters.slow_horizon_days == 50
    assert neighbor.parameters.selection_fraction == BASE_PARAMETERS.selection_fraction
    with pytest.raises(ValueError, match="unknown strategy parameters"):
        build_strategy_from_parameters({"secret_parameter": 1})


def test_invalid_seed_is_rejected_but_valid_seed_has_no_signal_effect() -> None:
    context = _context(_frames())
    assert build_strategy().target_weights(context, seed=1) == build_strategy().target_weights(
        context, seed=2
    )
    with pytest.raises(ValueError, match="seed"):
        build_strategy().target_weights(context, seed=-1)
