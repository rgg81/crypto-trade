"""Focused synthetic tests for Team05 UDCC pivot-01."""

from __future__ import annotations

import dataclasses
import math
from collections import OrderedDict

import candidate_variant as candidate_variant_module
import numpy as np
import pandas as pd
import pytest
import strategy as strategy_module
from strategy import (
    BASE_PARAMETERS,
    CANONICAL_SEED,
    PREREGISTERED_CANDIDATE_OVERRIDES,
    PREREGISTERED_RISK_POLICY_TEMPLATES,
    PreconstructionScore,
    build_strategy,
    build_strategy_from_parameters,
    candidate_score_payload_bytes,
    candidate_score_values,
    preconstruction_scores,
    scores_to_target_weights,
)

from crypto_trade.tournament.protocol import DecisionContext

DECISION = pd.Timestamp(year=2024, month=1, day=4, tz="UTC")
SYMBOLS = tuple(f"S{number:02d}USDT" for number in range(20))
MARKET_RETURNS = np.asarray(
    [
        (0.0045 + 0.0005 * math.sin(index / 7.0))
        if index % 2 == 0
        else (-0.0040 + 0.0004 * math.cos(index / 9.0))
        for index in range(252)
    ],
    dtype=float,
)


def _frame(
    symbol_number: int,
    *,
    return_order: np.ndarray | None = None,
) -> pd.DataFrame:
    centered = (symbol_number - 9.5) / 9.5
    beta_up = 1.0 + 0.55 * centered
    beta_down = 1.0 - 0.55 * centered
    market = MARKET_RETURNS if return_order is None else MARKET_RETURNS[return_order]
    returns = np.where(market > 0.0, beta_up * market, beta_down * market)
    prices = 100.0 * np.exp(np.concatenate(([0.0], np.cumsum(returns))))
    close_times = pd.date_range(end=DECISION, periods=253, freq="8h")
    open_times = close_times - pd.Timedelta(hours=8)
    return pd.DataFrame(
        {
            "open_time": open_times,
            "open": prices * 1.0001,
            "high": prices * 1.002,
            "low": prices * 0.998,
            "close": prices,
            "quote_volume": np.full(len(prices), 1_000_000.0 + symbol_number),
        }
    )


def _frames(*, return_order: np.ndarray | None = None) -> OrderedDict[str, pd.DataFrame]:
    return OrderedDict(
        (symbol, _frame(number, return_order=return_order)) for number, symbol in enumerate(SYMBOLS)
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


def _targets(context: DecisionContext) -> dict[str, float]:
    result = build_strategy().target_weights(context, seed=CANONICAL_SEED)
    assert result is not None
    return dict(result)


def _score_bytes(context: DecisionContext) -> bytes:
    return candidate_score_payload_bytes(preconstruction_scores(context))


def test_synthetic_convex_and_concave_assets_have_expected_order_and_book() -> None:
    context = _context(_frames())
    scores = preconstruction_scores(context)
    assert len(scores) == 20
    assert scores["S19USDT"].score == pytest.approx(1.0)
    assert scores["S00USDT"].score == pytest.approx(-1.0)
    assert scores["S19USDT"].beta_up > scores["S00USDT"].beta_up
    assert scores["S19USDT"].beta_down < scores["S00USDT"].beta_down

    targets = _targets(context)
    assert set(targets) == {
        "S00USDT",
        "S01USDT",
        "S02USDT",
        "S03USDT",
        "S04USDT",
        "S15USDT",
        "S16USDT",
        "S17USDT",
        "S18USDT",
        "S19USDT",
    }
    assert all(targets[symbol] > 0.0 for symbol in SYMBOLS[15:])
    assert all(targets[symbol] < 0.0 for symbol in SYMBOLS[:5])
    assert sum(abs(weight) for weight in targets.values()) == pytest.approx(0.48)
    assert sum(targets.values()) == pytest.approx(0.0, abs=1e-15)
    assert max(abs(weight) for weight in targets.values()) <= 0.05


def test_paired_observation_permutation_does_not_change_scores_or_targets() -> None:
    permutation = np.arange(252, dtype=int)[::-1]
    baseline = _context(_frames())
    permuted = _context(_frames(return_order=permutation))
    assert _score_bytes(permuted) == _score_bytes(baseline)
    assert _targets(permuted) == _targets(baseline)


def test_global_return_sign_inversion_swaps_capture_order_and_sleeves() -> None:
    frames = _frames()
    inverted = OrderedDict((symbol, frame.copy()) for symbol, frame in frames.items())
    for frame in inverted.values():
        frame.loc[:, "close"] = 10_000.0 / frame["close"].to_numpy(dtype=float)
    original_scores = preconstruction_scores(_context(frames))
    inverted_scores = preconstruction_scores(_context(inverted))
    for symbol in SYMBOLS:
        assert inverted_scores[symbol].score == pytest.approx(-original_scores[symbol].score)
    original_targets = _targets(_context(frames))
    inverted_targets = _targets(_context(inverted))
    assert {symbol for symbol, weight in original_targets.items() if weight > 0.0} == {
        symbol for symbol, weight in inverted_targets.items() if weight < 0.0
    }
    assert {symbol for symbol, weight in original_targets.items() if weight < 0.0} == {
        symbol for symbol, weight in inverted_targets.items() if weight > 0.0
    }


def test_future_append_and_corruption_are_irrelevant() -> None:
    baseline = _frames()
    with_future = OrderedDict((symbol, frame.copy()) for symbol, frame in baseline.items())
    for frame in with_future.values():
        future = pd.DataFrame(
            {
                "open_time": [DECISION, DECISION + pd.Timedelta(hours=8)],
                "open": [-1e100, -1e100],
                "high": [1e100, 1e100],
                "low": [-1e100, -1e100],
                "close": [float("nan"), 1e100],
                "quote_volume": [float("nan"), float("nan")],
            }
        )
        frame.loc[len(frame)] = future.iloc[0]
        frame.loc[len(frame)] = future.iloc[1]
    assert _score_bytes(_context(with_future)) == _score_bytes(_context(baseline))
    assert _targets(_context(with_future)) == _targets(_context(baseline))


def test_open_time_plus_eight_hours_is_the_exact_availability_boundary() -> None:
    frames = _frames()
    with_unclosed = OrderedDict((symbol, frame.copy()) for symbol, frame in frames.items())
    for frame in with_unclosed.values():
        frame.loc[len(frame)] = {
            "open_time": DECISION,
            "open": 1e100,
            "high": 1e100,
            "low": -1e100,
            "close": 1e100,
            "quote_volume": 0.0,
        }
    assert _score_bytes(_context(with_unclosed)) == _score_bytes(_context(frames))

    changed = OrderedDict((symbol, frame.copy()) for symbol, frame in frames.items())
    changed["S19USDT"].loc[252, "close"] *= 1.10
    changed_beta = preconstruction_scores(_context(changed))["S19USDT"].beta_down
    baseline_beta = preconstruction_scores(_context(frames))["S19USDT"].beta_down
    assert changed_beta != baseline_beta


def test_numeric_millisecond_timestamps_match_datetime_timestamps() -> None:
    frames = _frames()
    numeric = OrderedDict((symbol, frame.copy()) for symbol, frame in frames.items())
    for frame in numeric.values():
        frame["open_time"] = pd.Series(
            [
                int(timestamp.value // 1_000_000)
                for timestamp in pd.to_datetime(frame["open_time"], utc=True)
            ],
            dtype="int64",
        )
    assert _score_bytes(_context(numeric)) == _score_bytes(_context(frames))
    assert _targets(_context(numeric)) == _targets(_context(frames))


@pytest.mark.parametrize("failure", ["stale", "gap", "duplicate", "nonpositive"])
def test_invalid_or_noncontiguous_histories_fail_closed(failure: str) -> None:
    frames = _frames()
    for symbol, frame in tuple(frames.items()):
        if failure == "stale":
            frames[symbol] = frame.iloc[:-2].copy().reset_index(drop=True)
        elif failure == "gap":
            frames[symbol] = frame.drop(index=120).reset_index(drop=True)
        elif failure == "duplicate":
            duplicate = frame.iloc[[120]].copy()
            frames[symbol] = pd.concat([frame, duplicate], ignore_index=True)
        else:
            frame.loc[120, "close"] = 0.0
    assert preconstruction_scores(_context(frames)) == {}
    assert _targets(_context(frames)) == {}


def test_point_in_time_membership_controls_common_tape_and_targets() -> None:
    frames = _frames()
    augmented = OrderedDict((symbol, frame.copy()) for symbol, frame in frames.items())
    augmented["HOTUSDT"] = _frame(100)
    eligible = list(SYMBOLS)
    assert _score_bytes(_context(augmented, eligible=eligible)) == _score_bytes(_context(frames))
    targets = _targets(_context(augmented, eligible=eligible))
    assert "HOTUSDT" not in targets
    assert set(targets) <= set(eligible)


def test_mapping_and_eligible_order_do_not_change_bytes_or_targets() -> None:
    frames = _frames()
    reversed_frames = OrderedDict(reversed(tuple(frames.items())))
    baseline = _context(frames)
    reordered = _context(reversed_frames, eligible=list(reversed(SYMBOLS)))
    assert _score_bytes(reordered) == _score_bytes(baseline)
    assert _targets(reordered) == _targets(baseline)


def test_non_close_fields_funding_auxiliary_and_positions_have_no_effect() -> None:
    frames = _frames()
    altered = OrderedDict((symbol, frame.copy()) for symbol, frame in frames.items())
    for frame in altered.values():
        frame.loc[:, "open"] = -1e100
        frame.loc[:, "high"] = 1e100
        frame.loc[:, "low"] = -1e100
        frame.loc[:, "quote_volume"] = float("nan")
    funding = pd.DataFrame(
        {"symbol": ["S19USDT"], "funding_rate": [999.0]},
        index=[DECISION - pd.Timedelta(hours=1)],
    )
    auxiliary = {
        "future_oracle": pd.DataFrame({"target": [1e100]}, index=[DECISION]),
        "positions": pd.DataFrame({"quantity": [1e100]}, index=[DECISION]),
    }
    assert _score_bytes(_context(altered, funding=funding, auxiliary=auxiliary)) == _score_bytes(
        _context(frames)
    )
    assert _targets(_context(altered, funding=funding, auxiliary=auxiliary)) == _targets(
        _context(frames)
    )


def test_a5_receives_builtin_final_scores_and_its_return_is_consumed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scores = preconstruction_scores(_context(_frames()))
    observed: dict[str, float] = {}

    def flat_boundary(values: dict[str, float]) -> dict[str, float]:
        assert type(values) is dict
        assert list(values) == sorted(values)
        assert all(type(symbol) is str for symbol in values)
        assert all(type(value) is float and math.isfinite(value) for value in values.values())
        observed.update(values)
        return {symbol: 0.0 for symbol in values}

    monkeypatch.setattr(strategy_module, "score_boundary", flat_boundary)
    assert scores_to_target_weights(scores) == {}
    assert observed == {symbol: scores[symbol].score for symbol in sorted(scores)}


@pytest.mark.parametrize("bad_value", [True, float("nan"), float("inf"), 2.0])
def test_a5_invalid_value_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    bad_value: object,
) -> None:
    scores = preconstruction_scores(_context(_frames()))

    def bad_boundary(values: dict[str, float]) -> dict[str, float]:
        result = dict(values)
        result[sorted(result)[0]] = bad_value  # type: ignore[assignment]
        return result

    monkeypatch.setattr(strategy_module, "score_boundary", bad_boundary)
    assert candidate_score_values(scores) == {}
    assert scores_to_target_weights(scores) == {}


def test_a5_key_change_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    scores = preconstruction_scores(_context(_frames()))

    def missing_key(values: dict[str, float]) -> dict[str, float]:
        return {symbol: value for symbol, value in values.items() if symbol != "S00USDT"}

    monkeypatch.setattr(strategy_module, "score_boundary", missing_key)
    assert scores_to_target_weights(scores) == {}


def test_schedule_seed_and_fresh_instance_contract() -> None:
    context = _context(_frames())
    first = build_strategy()
    second = build_strategy_from_parameters({})
    assert first is not second
    assert first.parameters == second.parameters == BASE_PARAMETERS
    assert first.target_weights(context, seed=CANONICAL_SEED)
    off_schedule = _context(_frames(), decision=DECISION + pd.Timedelta(hours=8))
    assert first.target_weights(off_schedule, seed=CANONICAL_SEED) is None
    with pytest.raises(ValueError, match="canonical seed"):
        first.target_weights(context, seed=CANONICAL_SEED + 1)


def test_candidate_identity_and_parameter_bindings_are_exact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert candidate_variant_module.ACTIVE_CANDIDATE_ID == "team05-udcc-pivot01-core-v1"
    assert candidate_variant_module.ACTIVE_OVERRIDES == {}
    assert candidate_variant_module.ACTIVE_RISK_POLICY_TEMPLATE == "risk_policies/no-control.json"
    assert PREREGISTERED_CANDIDATE_OVERRIDES == {"team05-udcc-pivot01-core-v1": {}}
    assert PREREGISTERED_RISK_POLICY_TEMPLATES == {
        "team05-udcc-pivot01-core-v1": "risk_policies/no-control.json"
    }
    with pytest.raises(ValueError, match="unknown strategy parameters"):
        build_strategy_from_parameters({"secret_parameter": 1})
    monkeypatch.setattr(candidate_variant_module, "ACTIVE_CANDIDATE_ID", "unregistered")
    with pytest.raises(ValueError, match="not preregistered"):
        build_strategy()


def test_malformed_preconstruction_record_fails_closed() -> None:
    scores = preconstruction_scores(_context(_frames()))
    corrupted = dict(scores)
    corrupted["S00USDT"] = dataclasses.replace(
        corrupted["S00USDT"],
        score=float("nan"),
    )
    assert candidate_score_values(corrupted) == {}
    assert candidate_score_payload_bytes(corrupted) == b""
    assert scores_to_target_weights(corrupted) == {}

    wrong_symbol = dict(scores)
    wrong_symbol["S00USDT"] = PreconstructionScore(
        symbol="OTHERUSDT",
        score=-1.0,
        beta_up=0.5,
        beta_down=1.5,
    )
    assert scores_to_target_weights(wrong_symbol) == {}
