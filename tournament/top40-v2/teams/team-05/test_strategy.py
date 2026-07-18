"""Focused synthetic tests for Team 05.

These tests use generated bars only.  They are authored for later organizer/QE execution and are
not executed during clean-room design.
"""

from __future__ import annotations

import dataclasses
import json
import math
from collections import OrderedDict
from pathlib import Path

import candidate_variant as candidate_variant_module
import pandas as pd
import pytest
import strategy as strategy_module
from strategy import (
    BASE_PARAMETERS,
    CANONICAL_SEED,
    PREREGISTERED_CANDIDATE_OVERRIDES,
    PREREGISTERED_RISK_POLICY_TEMPLATES,
    build_strategy,
    build_strategy_from_parameters,
    candidate_score_payload_bytes,
    candidate_score_values,
    preconstruction_scores,
    scores_to_target_weights,
)

from crypto_trade.tournament.protocol import DecisionContext

UTC_START = pd.Timestamp(year=2020, month=1, day=1, tz="UTC")
DECISION = pd.Timestamp(year=2020, month=7, day=17, tz="UTC")
TEAM_ROOT = Path(__file__).resolve().parent


def _bars(symbol_number: int, *, future_days: int = 0) -> pd.DataFrame:
    end = DECISION + pd.Timedelta(days=future_days)
    open_times = pd.date_range(UTC_START, end=end, freq="8h")
    centered = symbol_number - 9.5
    drift = centered * 0.000018
    close = [
        100.0
        * math.exp(
            drift * step
            + 0.004 * math.sin(step / (5.0 + (symbol_number % 4)))
            + 0.0015 * math.cos(step / 2.7 + symbol_number)
        )
        for step in range(len(open_times))
    ]
    return pd.DataFrame(
        {
            "open_time": open_times,
            "open": [value * (1.0 + 0.0005) for value in close],
            "high": [value * (1.0 + 0.0020) for value in close],
            "low": [value * (1.0 - 0.0020) for value in close],
            "close": close,
            "quote_volume": [1_000_000.0 + symbol_number for _ in close],
        }
    )


def _frames(*, future_days: int = 0) -> OrderedDict[str, pd.DataFrame]:
    return OrderedDict(
        (f"S{number:02d}USDT", _bars(number, future_days=future_days)) for number in range(20)
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


def _score_bytes(context: DecisionContext) -> bytes:
    return candidate_score_payload_bytes(preconstruction_scores(context))


def test_future_append_truncation_and_corruption_invariance() -> None:
    with_future = _frames(future_days=5)
    truncated = OrderedDict(
        (
            symbol,
            frame.loc[
                pd.to_datetime(frame["open_time"], utc=True) + pd.Timedelta(hours=8) <= DECISION
            ]
            .copy()
            .reset_index(drop=True),
        )
        for symbol, frame in with_future.items()
    )
    corrupted = OrderedDict((symbol, frame.copy()) for symbol, frame in with_future.items())
    for frame in corrupted.values():
        unavailable = (
            pd.to_datetime(frame["open_time"], utc=True) + pd.Timedelta(hours=8) > DECISION
        )
        frame.loc[unavailable, "close"] = [
            float("nan") if i % 2 else 1e100 for i in range(unavailable.sum())
        ]
        frame.loc[unavailable, "open"] = -1e100

    baseline_scores = preconstruction_scores(_context(truncated))
    assert preconstruction_scores(_context(with_future)) == baseline_scores
    assert preconstruction_scores(_context(corrupted)) == baseline_scores
    assert _score_bytes(_context(with_future)) == _score_bytes(_context(truncated))
    assert _score_bytes(_context(corrupted)) == _score_bytes(_context(truncated))
    assert _targets(_context(with_future)) == _targets(_context(truncated))
    assert _targets(_context(corrupted)) == _targets(_context(truncated))


def test_open_time_plus_eight_hours_is_the_exact_availability_boundary() -> None:
    frames = _frames()
    assert all(isinstance(frame.index, pd.RangeIndex) for frame in frames.values())
    baseline_bytes = _score_bytes(_context(frames))

    not_closed = OrderedDict((symbol, frame.copy()) for symbol, frame in frames.items())
    for frame in not_closed.values():
        row = pd.to_datetime(frame["open_time"], utc=True) == DECISION
        assert row.sum() == 1
        frame.loc[row, "close"] = 1e100
    assert _score_bytes(_context(not_closed)) == baseline_bytes

    last_closed_changed = OrderedDict((symbol, frame.copy()) for symbol, frame in frames.items())
    changed_frame = last_closed_changed["S19USDT"]
    row = pd.to_datetime(changed_frame["open_time"], utc=True) + pd.Timedelta(hours=8) == DECISION
    assert row.sum() == 1
    changed_frame.loc[row, "close"] *= 1.50
    assert _score_bytes(_context(last_closed_changed)) != baseline_bytes


def test_numeric_millisecond_open_time_has_identical_score_and_target_bytes() -> None:
    frames = _frames()
    numeric_milliseconds = OrderedDict((symbol, frame.copy()) for symbol, frame in frames.items())
    for frame in numeric_milliseconds.values():
        frame["open_time"] = pd.Series(
            [
                int(timestamp.value // 1_000_000)
                for timestamp in pd.to_datetime(frame["open_time"], utc=True)
            ],
            dtype="int64",
        )

    assert _score_bytes(_context(numeric_milliseconds)) == _score_bytes(_context(frames))
    assert _targets(_context(numeric_milliseconds)) == _targets(_context(frames))


def test_stale_and_sparse_histories_each_fail_closed() -> None:
    stale = _frames()
    for symbol, frame in tuple(stale.items()):
        close_times = pd.to_datetime(frame["open_time"], utc=True) + pd.Timedelta(hours=8)
        stale[symbol] = (
            frame.loc[close_times <= DECISION - pd.Timedelta(hours=16)]
            .copy()
            .reset_index(drop=True)
        )
    assert preconstruction_scores(_context(stale)) == {}
    assert _targets(_context(stale)) == {}

    sparse = _frames()
    for symbol, frame in tuple(sparse.items()):
        closed = pd.to_datetime(frame["open_time"], utc=True) + pd.Timedelta(hours=8) <= DECISION
        keep = ~closed | (frame.index % 2 == 0)
        sparse[symbol] = frame.loc[keep].copy().reset_index(drop=True)
    assert preconstruction_scores(_context(sparse)) == {}
    assert _targets(_context(sparse)) == {}


def test_malformed_timestamp_and_close_each_fail_closed_without_raising() -> None:
    malformed_timestamp = _frames()
    for frame in malformed_timestamp.values():
        frame["open_time"] = ["not-a-timestamp"] * len(frame)
    assert preconstruction_scores(_context(malformed_timestamp)) == {}
    assert _targets(_context(malformed_timestamp)) == {}

    malformed_close = _frames()
    for frame in malformed_close.values():
        frame["close"] = ["not-a-close"] * len(frame)
    assert preconstruction_scores(_context(malformed_close)) == {}
    assert _targets(_context(malformed_close)) == {}


def test_duplicate_open_time_uses_the_last_input_row_before_stable_time_sort() -> None:
    frames = _frames()
    duplicated = OrderedDict((symbol, frame.copy()) for symbol, frame in frames.items())
    reference = OrderedDict((symbol, frame.copy()) for symbol, frame in frames.items())
    symbol = "S19USDT"
    duplicate_open_time = DECISION - pd.Timedelta(hours=8)
    duplicate_mask = (
        pd.to_datetime(duplicated[symbol]["open_time"], utc=True) == duplicate_open_time
    )
    assert duplicate_mask.sum() == 1
    duplicate_row = duplicated[symbol].loc[duplicate_mask].copy()
    duplicate_row.loc[:, "close"] *= 1.10
    duplicated[symbol] = pd.concat(
        [duplicated[symbol], duplicate_row],
        ignore_index=True,
    )
    reference[symbol].loc[duplicate_mask, "close"] *= 1.10

    assert _score_bytes(_context(duplicated)) == _score_bytes(_context(reference))
    assert _targets(_context(duplicated)) == _targets(_context(reference))
    assert _score_bytes(_context(duplicated)) != _score_bytes(_context(frames))


def test_missing_open_time_or_canonical_range_index_fails_closed() -> None:
    missing_open_time = _frames()
    for frame in missing_open_time.values():
        frame.drop(columns=["open_time"], inplace=True)
    assert preconstruction_scores(_context(missing_open_time)) == {}
    assert _targets(_context(missing_open_time)) == {}

    datetime_indexed = _frames()
    for symbol, frame in tuple(datetime_indexed.items()):
        datetime_indexed[symbol] = frame.set_index("open_time", drop=False)
    assert preconstruction_scores(_context(datetime_indexed)) == {}
    assert _targets(_context(datetime_indexed)) == {}


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
    hostile_auxiliary = {"oracle": pd.DataFrame({"future_target": [1e100]}, index=[DECISION])}
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


def test_reserved_rebalance_key_is_excluded_from_scores_and_targets() -> None:
    frames = _frames()
    with_reserved_key = OrderedDict((symbol, frame.copy()) for symbol, frame in frames.items())
    with_reserved_key["__crypto_trade_rebalance__"] = _bars(99)

    assert preconstruction_scores(_context(with_reserved_key)) == preconstruction_scores(
        _context(frames)
    )
    assert _score_bytes(_context(with_reserved_key)) == _score_bytes(_context(frames))
    assert _targets(_context(with_reserved_key)) == _targets(_context(frames))


def test_mapping_order_and_fresh_instance_reproducibility() -> None:
    frames = _frames()
    reversed_frames = OrderedDict(reversed(list(frames.items())))
    first = build_strategy().target_weights(_context(frames), seed=CANONICAL_SEED)
    second = build_strategy().target_weights(_context(reversed_frames), seed=CANONICAL_SEED)
    third = build_strategy().target_weights(_context(frames), seed=CANONICAL_SEED)
    assert first == second == third


def test_fresh_instances_emit_exactly_equal_candidate_score_payload_bytes() -> None:
    context = _context(_frames())
    first = build_strategy_from_parameters()
    second = build_strategy_from_parameters({})
    first_bytes = candidate_score_payload_bytes(
        preconstruction_scores(context, parameters=first.parameters)
    )
    second_bytes = candidate_score_payload_bytes(
        preconstruction_scores(context, parameters=second.parameters)
    )
    assert first is not second
    assert first.parameters is not second.parameters
    assert first.parameters == second.parameters
    assert first_bytes
    assert first_bytes == second_bytes


def test_a5_boundary_gets_builtin_finite_floats_and_return_is_consumed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scores = preconstruction_scores(_context(_frames()))
    observed: dict[str, float] = {}

    def diagnostic_boundary(values: dict[str, float]) -> dict[str, float]:
        assert type(values) is dict
        assert list(values) == sorted(values)
        assert all(type(symbol) is str for symbol in values)
        assert all(type(value) is float and math.isfinite(value) for value in values.values())
        observed.update(values)
        return {symbol: 0.0 for symbol in values}

    monkeypatch.setattr(strategy_module, "score_boundary", diagnostic_boundary)
    assert scores_to_target_weights(scores) == {}
    assert observed == {symbol: float(scores[symbol].score) for symbol in sorted(scores)}


def test_a5_identity_and_score_payload_bytes_are_order_invariant() -> None:
    frames = _frames()
    scores = preconstruction_scores(_context(frames))
    values = candidate_score_values(scores)
    assert values == {symbol: float(scores[symbol].score) for symbol in sorted(scores)}
    assert all(type(value) is float and math.isfinite(value) for value in values.values())

    reversed_frames = OrderedDict(reversed(list(frames.items())))
    reversed_scores = preconstruction_scores(_context(reversed_frames))
    assert candidate_score_payload_bytes(scores) == candidate_score_payload_bytes(reversed_scores)


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
    corrupted[first_symbol] = dataclasses.replace(corrupted[first_symbol], score=float("inf"))
    assert candidate_score_values(corrupted) == {}
    assert candidate_score_payload_bytes(corrupted) == b""
    assert scores_to_target_weights(corrupted) == {}


@pytest.mark.parametrize(
    ("field_name", "malformed_value"),
    [
        ("symbol", 7),
        ("score", "0.25"),
        ("short_log_return", None),
        ("medium_log_return", True),
        ("slow_log_return", 0),
        ("realized_bar_volatility", "0.01"),
        ("market_direction_log_return", 0j),
        ("score", float("nan")),
        ("score", 1.01),
        ("realized_bar_volatility", 0.0),
    ],
)
def test_every_malformed_score_field_fails_closed_to_empty_values_and_bytes(
    field_name: str,
    malformed_value: object,
) -> None:
    scores = preconstruction_scores(_context(_frames()))
    first_symbol = sorted(scores)[0]
    corrupted = dict(scores)
    corrupted[first_symbol] = dataclasses.replace(
        corrupted[first_symbol],
        **{field_name: malformed_value},
    )

    assert candidate_score_values(corrupted) == {}
    assert candidate_score_payload_bytes(corrupted) == b""
    assert scores_to_target_weights(corrupted) == {}


def test_score_order_identifies_relative_winner_and_loser() -> None:
    scores = preconstruction_scores(_context(_frames()))
    assert scores["S19USDT"].score > scores["S00USDT"].score


def test_insufficient_or_degenerate_history_fails_closed_to_flat() -> None:
    too_small = OrderedDict(list(_frames().items())[:11])
    assert preconstruction_scores(_context(too_small)) == {}
    assert _targets(_context(too_small)) == {}

    constant = OrderedDict()
    open_times = pd.date_range(UTC_START, end=DECISION, freq="8h")
    for number in range(20):
        constant[f"C{number:02d}USDT"] = pd.DataFrame(
            {
                "open_time": open_times,
                "close": [100.0] * len(open_times),
            }
        )
    assert preconstruction_scores(_context(constant)) == {}
    assert _targets(_context(constant)) == {}


def test_every_sparse_scheduled_decision_crosses_the_empty_a5_hook_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, float]] = []

    def recording_boundary(values: dict[str, float]) -> dict[str, float]:
        calls.append(dict(values))
        return dict(values)

    monkeypatch.setattr(strategy_module, "score_boundary", recording_boundary)
    too_small = OrderedDict(list(_frames().items())[:11])
    assert _targets(_context(too_small)) == {}
    assert calls == [{}]


def test_non_rebalance_boundary_returns_none_not_flat() -> None:
    off_schedule = DECISION + pd.Timedelta(days=1)
    frames = OrderedDict(
        (symbol, _bars(number, future_days=1)) for number, symbol in enumerate(_frames())
    )
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


@pytest.mark.parametrize(
    ("artifact_name", "axis", "neighbor_value"),
    [
        ("team05-crtr-n01-slow-50d.json", "slow_horizon_days", 50),
        ("team05-crtr-n02-slow-70d.json", "slow_horizon_days", 70),
        ("team05-crtr-n03-selection-020.json", "selection_fraction", 0.20),
        ("team05-crtr-n04-selection-030.json", "selection_fraction", 0.30),
        ("team05-crtr-n05-gross-050.json", "target_gross", 0.50),
        ("team05-crtr-n06-gross-070.json", "target_gross", 0.70),
        ("team05-crtr-n07-chop-reversal-015.json", "chop_reversal_weight", 0.15),
        ("team05-crtr-n08-chop-reversal-025.json", "chop_reversal_weight", 0.25),
    ],
)
def test_every_declared_neighbor_changes_exactly_its_one_registered_axis(
    artifact_name: str,
    axis: str,
    neighbor_value: int | float,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = json.loads((TEAM_ROOT / "neighbors" / artifact_name).read_text(encoding="utf-8"))
    expected_override = {axis: neighbor_value}
    assert artifact["one_axis"] == axis
    assert artifact["overrides"] == expected_override
    assert artifact["canonical_materialization"] == {
        "active_candidate_id": artifact["neighbor_id"],
        "active_overrides": expected_override,
        "active_risk_policy_template": "risk_ablations/combined.json",
        "path": "candidate_variant.py",
    }
    assert PREREGISTERED_CANDIDATE_OVERRIDES[artifact["neighbor_id"]] == expected_override

    monkeypatch.setattr(
        candidate_variant_module,
        "ACTIVE_CANDIDATE_ID",
        artifact["canonical_materialization"]["active_candidate_id"],
    )
    monkeypatch.setattr(
        candidate_variant_module,
        "ACTIVE_OVERRIDES",
        artifact["canonical_materialization"]["active_overrides"],
    )
    monkeypatch.setattr(
        candidate_variant_module,
        "ACTIVE_RISK_POLICY_TEMPLATE",
        artifact["canonical_materialization"]["active_risk_policy_template"],
    )
    neighbor = build_strategy()
    changed = {
        field.name: getattr(neighbor.parameters, field.name)
        for field in dataclasses.fields(BASE_PARAMETERS)
        if getattr(neighbor.parameters, field.name) != getattr(BASE_PARAMETERS, field.name)
    }
    assert changed == expected_override


def test_canonical_builder_rejects_unregistered_or_mismatched_materialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(candidate_variant_module, "ACTIVE_CANDIDATE_ID", "team05-undeclared-v1")
    with pytest.raises(ValueError, match="not preregistered"):
        build_strategy()

    monkeypatch.setattr(
        candidate_variant_module,
        "ACTIVE_CANDIDATE_ID",
        "team05-crtr-core-v2-infra-r1",
    )
    monkeypatch.setattr(candidate_variant_module, "ACTIVE_OVERRIDES", {"target_gross": 0.5})
    with pytest.raises(ValueError, match="do not match"):
        build_strategy()

    monkeypatch.setattr(candidate_variant_module, "ACTIVE_OVERRIDES", {})
    monkeypatch.setattr(
        candidate_variant_module,
        "ACTIVE_RISK_POLICY_TEMPLATE",
        "risk_ablations/combined.json",
    )
    with pytest.raises(ValueError, match="risk template does not match"):
        build_strategy()


@pytest.mark.parametrize(
    "candidate_id",
    [
        "team05-crtr-core-v2",
        "team05-crtr-core-v2-infra-r1",
        "team05-crtr-ab-vol",
        "team05-crtr-ab-dd",
        "team05-crtr-ab-stop",
        "team05-crtr-ab-turnover",
        "team05-crtr-base-v1",
    ],
)
def test_every_predeclared_base_parameter_cell_uses_canonical_zero_arg_builder(
    candidate_id: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(candidate_variant_module, "ACTIVE_CANDIDATE_ID", candidate_id)
    monkeypatch.setattr(candidate_variant_module, "ACTIVE_OVERRIDES", {})
    monkeypatch.setattr(
        candidate_variant_module,
        "ACTIVE_RISK_POLICY_TEMPLATE",
        PREREGISTERED_RISK_POLICY_TEMPLATES[candidate_id],
    )
    assert build_strategy().parameters == BASE_PARAMETERS


def test_infrastructure_replacement_has_no_scientific_or_risk_delta() -> None:
    historical = "team05-crtr-core-v2"
    replacement = "team05-crtr-core-v2-infra-r1"
    assert PREREGISTERED_CANDIDATE_OVERRIDES[historical] == {}
    assert PREREGISTERED_CANDIDATE_OVERRIDES[replacement] == {}
    assert (
        PREREGISTERED_CANDIDATE_OVERRIDES[historical]
        == PREREGISTERED_CANDIDATE_OVERRIDES[replacement]
    )
    assert PREREGISTERED_RISK_POLICY_TEMPLATES[historical] == "risk_ablations/none.json"
    assert PREREGISTERED_RISK_POLICY_TEMPLATES[replacement] == "risk_ablations/none.json"
    assert (
        PREREGISTERED_RISK_POLICY_TEMPLATES[historical]
        == PREREGISTERED_RISK_POLICY_TEMPLATES[replacement]
    )


def test_every_noncanonical_seed_is_rejected() -> None:
    context = _context(_frames())
    assert build_strategy().target_weights(context, seed=CANONICAL_SEED)
    for seed in (-1, 0, 1, 20260800, 20260802, True, 20260801.0):
        with pytest.raises(ValueError, match="canonical seed"):
            build_strategy().target_weights(context, seed=seed)  # type: ignore[arg-type]
