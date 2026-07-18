"""Focused synthetic tests for Team05 final liquidity-depth migration pivot."""

from __future__ import annotations

import dataclasses
import json
import math
from collections import OrderedDict
from pathlib import Path

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
    _closed_bar_suffix,
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


def _default_improvement(symbol_number: int) -> float:
    return 0.80 * (symbol_number - 9.5) / 9.5


def _frame(
    symbol_number: int,
    *,
    improvement: float | None = None,
    price_scale: float = 1.0,
) -> pd.DataFrame:
    raw_improvement = _default_improvement(symbol_number) if improvement is None else improvement
    log_ranges = np.full(BASE_PARAMETERS.history_bars, 0.02, dtype=float)
    log_ranges[BASE_PARAMETERS.baseline_bars :] *= math.exp(-raw_improvement)
    center = (
        price_scale
        * (100.0 + symbol_number)
        * np.exp(np.linspace(0.0, 0.05, BASE_PARAMETERS.history_bars))
    )
    close_times = pd.date_range(
        end=DECISION,
        periods=BASE_PARAMETERS.history_bars,
        freq=f"{BASE_PARAMETERS.bar_interval_hours}h",
    )
    return pd.DataFrame(
        {
            "open_time": close_times - pd.Timedelta(hours=BASE_PARAMETERS.bar_interval_hours),
            "open": center * 0.999,
            "high": center * np.exp(log_ranges / 2.0),
            "low": center * np.exp(-log_ranges / 2.0),
            "close": center * 1.001,
            "quote_volume": np.full(BASE_PARAMETERS.history_bars, 1_000_000.0),
        }
    )


def _frames() -> OrderedDict[str, pd.DataFrame]:
    return OrderedDict((symbol, _frame(number)) for number, symbol in enumerate(SYMBOLS))


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


def _invalidate_all(
    frames: OrderedDict[str, pd.DataFrame],
    indices: range,
    *,
    field: str,
    value: object,
) -> None:
    for frame in frames.values():
        if isinstance(value, bool):
            frame[field] = frame[field].astype(object)
        frame.loc[list(indices), field] = value


def test_synthetic_depth_improvement_has_expected_order_and_balanced_book() -> None:
    context = _context(_frames())
    scores = preconstruction_scores(context)
    assert len(scores) == 20
    assert scores["S19USDT"].score == pytest.approx(1.0)
    assert scores["S00USDT"].score == pytest.approx(-1.0)
    assert scores["S19USDT"].raw_depth_improvement == pytest.approx(0.80)
    assert scores["S00USDT"].raw_depth_improvement == pytest.approx(-0.80)
    assert scores["S19USDT"].recent_impact < scores["S19USDT"].baseline_impact
    assert scores["S00USDT"].recent_impact > scores["S00USDT"].baseline_impact

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
    assert sum(abs(weight) for weight in targets.values()) == pytest.approx(0.36)
    assert sum(targets.values()) == pytest.approx(0.0, abs=1e-15)
    assert max(abs(weight) for weight in targets.values()) <= 0.04


def test_future_append_and_corruption_are_irrelevant() -> None:
    baseline = _frames()
    with_future = OrderedDict((symbol, frame.copy()) for symbol, frame in baseline.items())
    for frame in with_future.values():
        frame.loc[len(frame)] = {
            "open_time": DECISION,
            "open": -1e100,
            "high": float("nan"),
            "low": -1e100,
            "close": 1e100,
            "quote_volume": 0.0,
        }
        frame.loc[len(frame)] = {
            "open_time": DECISION + pd.Timedelta(hours=8),
            "open": 1e100,
            "high": -1e100,
            "low": 1e100,
            "close": float("nan"),
            "quote_volume": float("nan"),
        }
    assert _score_bytes(_context(with_future)) == _score_bytes(_context(baseline))
    assert _targets(_context(with_future)) == _targets(_context(baseline))


def test_open_time_plus_eight_hours_is_the_exact_availability_boundary() -> None:
    frames = _frames()
    suffix = _closed_bar_suffix(
        frames["S19USDT"],
        decision_time=DECISION,
        parameters=BASE_PARAMETERS,
    )
    assert suffix is not None
    assert suffix.index[-1] == DECISION
    assert suffix.iloc[-1]["high"] == frames["S19USDT"].iloc[-1]["high"]

    with_unclosed = OrderedDict((symbol, frame.copy()) for symbol, frame in frames.items())
    for frame in with_unclosed.values():
        frame.loc[len(frame)] = {
            "open_time": DECISION,
            "open": -1e100,
            "high": 1e100,
            "low": -1e100,
            "close": 1e100,
            "quote_volume": 0.0,
        }
    assert _score_bytes(_context(with_unclosed)) == _score_bytes(_context(frames))


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


@pytest.mark.parametrize("failure", ["stale", "gap", "duplicate", "non_range_index"])
def test_invalid_or_noncontiguous_histories_fail_closed(failure: str) -> None:
    frames = _frames()
    for symbol, frame in tuple(frames.items()):
        if failure == "stale":
            frames[symbol] = frame.iloc[:-2].copy().reset_index(drop=True)
        elif failure == "gap":
            frames[symbol] = frame.drop(index=60).reset_index(drop=True)
        elif failure == "duplicate":
            frames[symbol] = pd.concat([frame, frame.iloc[[60]].copy()], ignore_index=True)
        else:
            frames[symbol] = frame.set_index("open_time", drop=False)
    assert preconstruction_scores(_context(frames)) == {}
    assert _targets(_context(frames)) == {}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("quote_volume", 0.0),
        ("quote_volume", True),
        ("low", 0.0),
        ("high", 1.0),
        ("high", float("nan")),
    ],
)
def test_invalid_values_are_unavailable_and_bounded_by_baseline_floor(
    field: str,
    value: object,
) -> None:
    allowed = _frames()
    _invalidate_all(allowed, range(10), field=field, value=value)
    assert len(preconstruction_scores(_context(allowed))) == len(SYMBOLS)

    excessive = _frames()
    _invalidate_all(excessive, range(11), field=field, value=value)
    assert preconstruction_scores(_context(excessive)) == {}


def test_recent_validity_floor_is_exact_and_zero_volume_is_never_floored() -> None:
    recent_start = BASE_PARAMETERS.baseline_bars
    allowed = _frames()
    _invalidate_all(
        allowed,
        range(recent_start, recent_start + 2),
        field="quote_volume",
        value=0.0,
    )
    baseline_scores = preconstruction_scores(_context(_frames()))
    allowed_scores = preconstruction_scores(_context(allowed))
    assert candidate_score_payload_bytes(allowed_scores) == candidate_score_payload_bytes(
        baseline_scores
    )
    assert {
        symbol: row.raw_depth_improvement for symbol, row in allowed_scores.items()
    } == pytest.approx(
        {symbol: row.raw_depth_improvement for symbol, row in baseline_scores.items()}
    )

    excessive = _frames()
    _invalidate_all(
        excessive,
        range(recent_start, recent_start + 3),
        field="quote_volume",
        value=0.0,
    )
    assert preconstruction_scores(_context(excessive)) == {}


def test_range_and_raw_improvement_ceilings_fail_closed() -> None:
    excessive_ranges = _frames()
    for frame in excessive_ranges.values():
        indices = list(range(11))
        frame.loc[indices, "high"] = frame.loc[indices, "low"].to_numpy(dtype=float) * math.exp(
            BASE_PARAMETERS.maximum_log_range + 0.01
        )
    assert preconstruction_scores(_context(excessive_ranges)) == {}

    excessive_ratio = OrderedDict(
        (
            symbol,
            _frame(
                number,
                improvement=BASE_PARAMETERS.maximum_abs_log_impact_ratio + 0.10,
            ),
        )
        for number, symbol in enumerate(SYMBOLS)
    )
    assert preconstruction_scores(_context(excessive_ratio)) == {}


def test_valid_tiny_volume_share_uses_the_frozen_floor() -> None:
    baseline = _frames()
    tiny = OrderedDict((symbol, frame.copy()) for symbol, frame in baseline.items())
    tiny["S00USDT"].loc[:, "quote_volume"] = 1.0
    tiny["S00USDT"].loc[BASE_PARAMETERS.baseline_bars :, "quote_volume"] = 2.0
    baseline_value = preconstruction_scores(_context(baseline))["S00USDT"].raw_depth_improvement
    tiny_value = preconstruction_scores(_context(tiny))["S00USDT"].raw_depth_improvement
    assert tiny_value == pytest.approx(baseline_value)


def test_price_scale_is_irrelevant() -> None:
    baseline = _frames()
    scaled = OrderedDict((symbol, frame.copy()) for symbol, frame in baseline.items())
    for number, frame in enumerate(scaled.values()):
        scale = 10.0 ** ((number % 7) - 3)
        for field in ("open", "high", "low", "close"):
            frame.loc[:, field] = frame[field].to_numpy(dtype=float) * scale
    assert _score_bytes(_context(scaled)) == _score_bytes(_context(baseline))
    assert _targets(_context(scaled)) == _targets(_context(baseline))


def test_market_wide_volume_scaling_at_each_timestamp_is_irrelevant() -> None:
    baseline = _frames()
    scaled = OrderedDict((symbol, frame.copy()) for symbol, frame in baseline.items())
    time_scales = np.exp(np.sin(np.arange(BASE_PARAMETERS.history_bars) / 9.0))
    for frame in scaled.values():
        frame.loc[:, "quote_volume"] = frame["quote_volume"].to_numpy(dtype=float) * time_scales
    assert _score_bytes(_context(scaled)) == _score_bytes(_context(baseline))
    assert _targets(_context(scaled)) == _targets(_context(baseline))


def test_symbol_specific_volume_migration_changes_depth_improvement() -> None:
    baseline = _frames()
    changed = OrderedDict((symbol, frame.copy()) for symbol, frame in baseline.items())
    changed["S00USDT"].loc[BASE_PARAMETERS.baseline_bars :, "quote_volume"] *= 4.0
    baseline_scores = preconstruction_scores(_context(baseline))
    changed_scores = preconstruction_scores(_context(changed))
    assert (
        changed_scores["S00USDT"].raw_depth_improvement
        > baseline_scores["S00USDT"].raw_depth_improvement + 1.0
    )
    assert candidate_score_payload_bytes(changed_scores) != candidate_score_payload_bytes(
        baseline_scores
    )


def test_membership_controls_cross_section_and_targets() -> None:
    frames = _frames()
    augmented = OrderedDict((symbol, frame.copy()) for symbol, frame in frames.items())
    augmented["HOTUSDT"] = _frame(19, improvement=2.0)
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


def test_open_close_funding_auxiliary_and_positions_have_no_effect() -> None:
    frames = _frames()
    altered = OrderedDict((symbol, frame.copy()) for symbol, frame in frames.items())
    for frame in altered.values():
        frame.loc[:, "open"] = -1e100
        frame.loc[:, "close"] = float("nan")
    funding = pd.DataFrame(
        {"symbol": ["S19USDT"], "funding_rate": [999.0]},
        index=[DECISION - pd.Timedelta(hours=1)],
    )
    auxiliary = {
        "future_oracle": pd.DataFrame({"signal": [1e100]}, index=[DECISION]),
        "positions": pd.DataFrame({"quantity": [1e100]}, index=[DECISION]),
    }
    changed = _context(altered, funding=funding, auxiliary=auxiliary)
    assert _score_bytes(changed) == _score_bytes(_context(frames))
    assert _targets(changed) == _targets(_context(frames))


def test_a5_receives_final_rank_scores_and_its_return_is_consumed(
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


def test_valid_a5_reordering_changes_selected_membership(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scores = preconstruction_scores(_context(_frames()))

    def reorder_boundary(values: dict[str, float]) -> dict[str, float]:
        result = dict(values)
        result["S14USDT"], result["S15USDT"] = result["S15USDT"], result["S14USDT"]
        return result

    monkeypatch.setattr(strategy_module, "score_boundary", reorder_boundary)
    targets = scores_to_target_weights(scores)
    assert targets["S14USDT"] > 0.0
    assert "S15USDT" not in targets
    assert all(targets[symbol] < 0.0 for symbol in SYMBOLS[:5])


def test_scheduled_failure_calls_a5_once_with_empty_scores(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captures: list[dict[str, float]] = []

    def capture_boundary(values: dict[str, float]) -> dict[str, float]:
        captures.append(dict(values))
        return dict(values)

    monkeypatch.setattr(strategy_module, "score_boundary", capture_boundary)
    too_small = OrderedDict(tuple(_frames().items())[: BASE_PARAMETERS.minimum_symbols - 1])
    result = build_strategy().target_weights(_context(too_small), seed=CANONICAL_SEED)
    assert result == {}
    assert captures == [{}]


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
    assert candidate_score_values(scores) == {}
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
    assert candidate_variant_module.ACTIVE_CANDIDATE_ID == "team05-ldm-pivot02-core-v1"
    assert candidate_variant_module.ACTIVE_OVERRIDES == {}
    assert candidate_variant_module.ACTIVE_RISK_POLICY_TEMPLATE == "risk_policies/no-control.json"
    assert PREREGISTERED_CANDIDATE_OVERRIDES == {"team05-ldm-pivot02-core-v1": {}}
    assert PREREGISTERED_RISK_POLICY_TEMPLATES == {
        "team05-ldm-pivot02-core-v1": "risk_policies/no-control.json"
    }
    with pytest.raises(ValueError, match="unknown strategy parameters"):
        build_strategy_from_parameters({"secret_parameter": 1})
    monkeypatch.setattr(candidate_variant_module, "ACTIVE_CANDIDATE_ID", "unregistered")
    with pytest.raises(ValueError, match="not preregistered"):
        build_strategy()


def test_frozen_config_matches_executable_parameters_and_identity() -> None:
    config = json.loads((Path(__file__).resolve().parent / "frozen_config.json").read_text())
    assert config["team_id"] == "team-05"
    assert config["family_id"] == "team05-liquidity-depth-migration-v1"
    assert config["parent_family_id"] == "team05-up-down-capture-convexity-v1"
    assert config["candidate_id"] == "team05-ldm-pivot02-core-v1"
    assert config["pivot_number"] == 2
    assert config["parameters"] == dataclasses.asdict(BASE_PARAMETERS)


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
        raw_depth_improvement=-0.8,
        baseline_impact=0.4,
        recent_impact=0.9,
    )
    assert scores_to_target_weights(wrong_symbol) == {}
