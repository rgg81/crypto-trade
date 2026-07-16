"""Synthetic, market-data-free tests for Team 04 BER pivot 01; organizer-validated."""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pandas as pd
import pytest

from crypto_trade.tournament import score_adapter_protocol_v5
from crypto_trade.tournament.generic_score_adapter_v5 import build_adapter
from crypto_trade.tournament.protocol import DecisionContext
from crypto_trade.tournament.risk_policy import risk_policy_from_dict

DECISION_TIME = pd.Timestamp("2023-01-05T00:00:00Z")
CUTOFF = DECISION_TIME - pd.Timedelta(hours=8)
INTERVAL = pd.Timedelta(hours=8)
TEST_DIR = Path(__file__).resolve().parent
TEAM_DIR = TEST_DIR.parent if TEST_DIR.name == "pivot-01" else TEST_DIR
RUNTIME_DIR = TEST_DIR
TEMPLATE_DIR = TEAM_DIR / "pivot-01"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ber = _load("_team04_ber_test_strategy", RUNTIME_DIR / "strategy.py")
score_adapter = _load("_team04_ber_test_score_adapter", TEMPLATE_DIR / "organizer_score_adapter.py")


def synthetic_symbols(count: int = 40) -> tuple[str, ...]:
    return tuple(f"S{index:02d}USDT" for index in range(count))


def _bar_frame(symbol: str, index: int, *, include_future: bool = False) -> pd.DataFrame:
    expected = ber._expected_open_times(CUTOFF, ber._REFERENCE.history_return_bars)
    baseline_bars = ber._REFERENCE.baseline_bars
    midpoint = 19.5
    shock_direction = ((index - midpoint) / midpoint) * 0.0012
    price = 100.0 + index
    rows: list[dict[str, object]] = []
    for step, open_time in enumerate(expected):
        if step == 0:
            move = 0.0
        elif step <= baseline_bars:
            move = 0.00055 * math.sin(0.43 * step + 0.17 * index) + 0.00025 * math.cos(
                0.19 * step - 0.11 * index
            )
        else:
            move = shock_direction + 0.00004 * math.sin(0.71 * step + 0.13 * index)
        price *= math.exp(move)
        rows.append(
            {
                "symbol": symbol,
                "open_time": open_time,
                "close_time": open_time + INTERVAL,
                "close": price,
            }
        )
    if include_future:
        rows.append(
            {
                "symbol": symbol,
                "open_time": CUTOFF,
                "close_time": DECISION_TIME,
                "close": price * 100.0,
            }
        )
    return pd.DataFrame(rows)


def synthetic_bars(
    symbols: tuple[str, ...] | None = None, *, include_future: bool = False
) -> dict[str, pd.DataFrame]:
    eligible = symbols or synthetic_symbols()
    return {
        symbol: _bar_frame(symbol, index, include_future=include_future)
        for index, symbol in enumerate(eligible)
    }


def synthetic_context(
    *,
    symbols: tuple[str, ...] | None = None,
    decision_time: pd.Timestamp = DECISION_TIME,
    bars: dict[str, pd.DataFrame] | None = None,
    auxiliary: dict[str, object] | None = None,
) -> DecisionContext:
    eligible = symbols or synthetic_symbols()
    return DecisionContext(
        decision_time=decision_time,
        bars=synthetic_bars(eligible) if bars is None else bars,
        funding=pd.DataFrame(),
        auxiliary={} if auxiliary is None else auxiliary,
        eligible_symbols=eligible,
    )


def _reference_scores() -> dict[str, float]:
    result = ber.build_strategy().preconstruction_scores(synthetic_context(), seed=20260801)
    assert isinstance(result, dict) and result
    return result


def _reference_weights() -> dict[str, float]:
    result = ber.build_strategy().target_weights(synthetic_context(), seed=20260801)
    assert isinstance(result, dict) and result
    return result


def test_exact_shock_volatility_efficiency_and_raw_score() -> None:
    frame = _bar_frame("AUSDT", 7)
    closes = frame["close"].tolist()
    returns = [math.log(current / previous) for previous, current in zip(closes, closes[1:])]
    feature = ber._shock_feature(frame, cutoff=CUTOFF)
    assert feature is not None
    baseline = returns[:63]
    shock_path = returns[63:]
    mean = math.fsum(baseline) / 63
    volatility = math.sqrt(math.fsum((value - mean) ** 2 for value in baseline) / 63)
    shock = math.fsum(shock_path)
    absolute_path = math.fsum(abs(value) for value in shock_path)
    efficiency = min(1.0, abs(shock) / absolute_path)
    expected_raw = -(shock / (volatility * math.sqrt(9))) * (0.5 + 0.5 * efficiency)
    assert feature.shock_log_return == shock
    assert feature.baseline_volatility == volatility
    assert feature.path_efficiency == efficiency
    assert feature.raw_reversal_score == expected_raw
    assert ber._shock_feature(frame.iloc[1:], cutoff=CUTOFF) is None


def test_exact_average_rank_ties() -> None:
    ranks = ber._average_ranks({"A": 1.0, "B": 1.0, "C": 3.0, "D": 5.0})
    assert ranks is not None
    assert ranks["A"] == ranks["B"] == 2.0 * (1.5 - 1.0) / 3.0 - 1.0
    assert ranks["C"] == 2.0 * (3.0 - 1.0) / 3.0 - 1.0
    assert ranks["D"] == 1.0


def test_a5_boundary_is_exact_ranked_score_used_by_construction(monkeypatch) -> None:
    captured: list[dict[str, float]] = []

    def identity_boundary(scores: dict[str, float]) -> dict[str, float]:
        captured.append(scores)
        return scores

    monkeypatch.setattr(ber, "score_boundary", identity_boundary)
    context = synthetic_context()
    scores = ber.build_strategy().preconstruction_scores(context, seed=20260801)
    assert isinstance(scores, dict) and scores
    assert len(captured) == 1
    assert captured[0] == scores
    weights = ber.build_strategy().target_weights(context, seed=20260801)
    assert isinstance(weights, dict) and weights
    assert len(captured) == 2
    assert captured[1] == scores
    assert min(captured[1][symbol] for symbol, weight in weights.items() if weight > 0.0) > max(
        captured[1][symbol] for symbol, weight in weights.items() if weight < 0.0
    )

    monkeypatch.setattr(ber, "score_boundary", lambda scores: dict(scores))
    with pytest.raises(RuntimeError, match="return its input dictionary by identity"):
        ber.build_strategy().preconstruction_scores(context, seed=20260801)


def test_real_a5_adapter_schedule_and_empty_capture_contract() -> None:
    anchor = pd.Timestamp("1970-01-01T00:00:00Z")
    assert (DECISION_TIME - anchor).value % pd.Timedelta(hours=48).value == 0
    context = synthetic_context()
    strategy = ber.build_strategy()
    adapter = build_adapter(score_adapter_protocol_v5.ADAPTER_ID, strategy)
    result = adapter.evaluate(
        lambda: strategy.target_weights(context, seed=20260801),
        scheduled=True,
        eligible_symbols=context.eligible_symbols,
    )
    assert isinstance(result.weights, dict) and result.weights
    assert isinstance(result.scores, dict) and result.scores
    assert min(
        result.scores[symbol] for symbol, weight in result.weights.items() if weight > 0.0
    ) > max(result.scores[symbol] for symbol, weight in result.weights.items() if weight < 0.0)

    insufficient = synthetic_context(symbols=synthetic_symbols(23))
    insufficient_strategy = ber.build_strategy()
    insufficient_result = build_adapter(
        score_adapter_protocol_v5.ADAPTER_ID, insufficient_strategy
    ).evaluate(
        lambda: insufficient_strategy.target_weights(insufficient, seed=20260801),
        scheduled=True,
        eligible_symbols=insufficient.eligible_symbols,
    )
    assert insufficient_result.weights == {}
    assert insufficient_result.scores == {}

    unscheduled = synthetic_context(decision_time=DECISION_TIME + INTERVAL)
    unscheduled_strategy = ber.build_strategy()
    unscheduled_result = build_adapter(
        score_adapter_protocol_v5.ADAPTER_ID, unscheduled_strategy
    ).evaluate(
        lambda: unscheduled_strategy.target_weights(unscheduled, seed=20260801),
        scheduled=False,
        eligible_symbols=unscheduled.eligible_symbols,
    )
    assert unscheduled_result.weights is None
    assert unscheduled_result.scores is None

    off_grid = synthetic_context(decision_time=DECISION_TIME + pd.Timedelta(hours=1))
    off_grid_strategy = ber.build_strategy()
    off_grid_result = build_adapter(
        score_adapter_protocol_v5.ADAPTER_ID, off_grid_strategy
    ).evaluate(
        lambda: off_grid_strategy.target_weights(off_grid, seed=20260801),
        scheduled=False,
        eligible_symbols=off_grid.eligible_symbols,
    )
    assert off_grid_result.weights == {}
    assert off_grid_result.scores is None

    pre_anchor = synthetic_context(decision_time=anchor - INTERVAL)
    pre_anchor_strategy = ber.build_strategy()
    pre_anchor_result = build_adapter(
        score_adapter_protocol_v5.ADAPTER_ID, pre_anchor_strategy
    ).evaluate(
        lambda: pre_anchor_strategy.target_weights(pre_anchor, seed=20260801),
        scheduled=False,
        eligible_symbols=pre_anchor.eligible_symbols,
    )
    assert pre_anchor_result.weights == {}
    assert pre_anchor_result.scores is None


def test_a5_boundary_input_bytes_are_future_and_auxiliary_invariant(monkeypatch) -> None:
    captured: list[bytes] = []

    def capture_boundary(scores: dict[str, float]) -> dict[str, float]:
        captured.append(
            json.dumps(
                scores,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ).encode("ascii")
        )
        return scores

    monkeypatch.setattr(ber, "score_boundary", capture_boundary)
    clean = synthetic_context()
    poisoned = synthetic_context(auxiliary={"forward_label": object(), "outcome": object()})
    future_bars = synthetic_bars(include_future=True)
    appended = synthetic_context(bars=future_bars)
    corrupted_bars = {symbol: frame.copy(deep=True) for symbol, frame in future_bars.items()}
    for frame in corrupted_bars.values():
        frame.loc[frame["close_time"] > CUTOFF, "close"] = float("inf")
    corrupted = synthetic_context(bars=corrupted_bars)
    truncated = synthetic_context(
        bars={
            symbol: frame.loc[frame["close_time"] <= CUTOFF].copy()
            for symbol, frame in future_bars.items()
        }
    )
    for context in (clean, poisoned, appended, corrupted, truncated):
        scores = ber.build_strategy().preconstruction_scores(context, seed=20260801)
        assert isinstance(scores, dict) and scores
    assert len(captured) == 5
    assert all(score_bytes == captured[0] for score_bytes in captured[1:])


def test_deprecated_audit_serializer_is_label_free_and_stable_bytes(monkeypatch) -> None:
    monkeypatch.setattr(ber, "score_boundary", lambda scores: scores)
    monkeypatch.setattr(score_adapter.ber, "score_boundary", lambda scores: scores)
    clean = synthetic_context()
    poisoned = synthetic_context(auxiliary={"forward_label": object(), "outcome": object()})
    expected = ber.build_strategy().preconstruction_scores(clean, seed=20260801)
    adapter = score_adapter.build_score_adapter()
    assert not adapter.canonical
    assert not adapter.official_score_source
    assert adapter.extract_scores(poisoned, seed=20260801) == expected
    record = adapter.score_record(poisoned, seed=20260801)
    assert record is not None
    assert record["uses_labels"] is False
    assert record["construction_stage"] == "after-feature-eligibility-and-ranking-before-sleeves"
    assert record["scores"] == expected
    serialized = adapter.serialize_score_record(poisoned, seed=20260801)
    assert serialized is not None
    assert json.loads(serialized) == record
    assert serialized == adapter.serialize_score_record(poisoned, seed=20260801)
    assert serialized == adapter.serialize_score_record(clean, seed=20260801)


def test_reversal_direction_broad_sleeves_budget_cap_and_net() -> None:
    scores = _reference_scores()
    weights = _reference_weights()
    positives = {symbol: weight for symbol, weight in weights.items() if weight > 0.0}
    negatives = {symbol: weight for symbol, weight in weights.items() if weight < 0.0}
    assert len(positives) == len(negatives) == 12
    assert min(scores[symbol] for symbol in positives) > max(scores[symbol] for symbol in negatives)
    assert all(int(symbol[1:3]) < 20 for symbol in positives)
    assert all(int(symbol[1:3]) >= 20 for symbol in negatives)
    assert math.fsum(positives.values()) == pytest.approx(0.24, abs=1e-12)
    assert math.fsum(-weight for weight in negatives.values()) == pytest.approx(0.24, abs=1e-12)
    assert math.fsum(abs(weight) for weight in weights.values()) == pytest.approx(0.48, abs=1e-12)
    assert math.fsum(weights.values()) == pytest.approx(0.0, abs=1e-12)
    assert max(abs(weight) for weight in weights.values()) <= 0.03


def test_future_append_corrupt_and_truncate_invariance_for_scores_targets_and_audit_bytes(
    monkeypatch,
) -> None:
    monkeypatch.setattr(ber, "score_boundary", lambda scores: scores)
    monkeypatch.setattr(score_adapter.ber, "score_boundary", lambda scores: scores)
    baseline_scores = _reference_scores()
    baseline_weights = _reference_weights()
    adapter = score_adapter.build_score_adapter()
    baseline_bytes = adapter.serialize_score_record(synthetic_context(), seed=20260801)
    assert baseline_bytes is not None
    bars = synthetic_bars(include_future=True)
    appended = synthetic_context(bars=bars)
    assert ber.build_strategy().preconstruction_scores(appended, seed=20260801) == baseline_scores
    assert ber.build_strategy().target_weights(appended, seed=20260801) == baseline_weights
    assert adapter.serialize_score_record(appended, seed=20260801) == baseline_bytes
    corrupted = {symbol: frame.copy(deep=True) for symbol, frame in bars.items()}
    for frame in corrupted.values():
        frame.loc[frame["close_time"] > CUTOFF, "close"] = float("inf")
    corrupted_context = synthetic_context(bars=corrupted)
    assert (
        ber.build_strategy().preconstruction_scores(corrupted_context, seed=20260801)
        == baseline_scores
    )
    assert ber.build_strategy().target_weights(corrupted_context, seed=20260801) == baseline_weights
    assert adapter.serialize_score_record(corrupted_context, seed=20260801) == baseline_bytes
    truncated = {
        symbol: frame.loc[frame["close_time"] <= CUTOFF].copy() for symbol, frame in bars.items()
    }
    truncated_context = synthetic_context(bars=truncated)
    assert (
        ber.build_strategy().preconstruction_scores(truncated_context, seed=20260801)
        == baseline_scores
    )
    assert ber.build_strategy().target_weights(truncated_context, seed=20260801) == baseline_weights
    assert adapter.serialize_score_record(truncated_context, seed=20260801) == baseline_bytes


def test_missing_duplicate_nonfinite_and_wrong_close_time_fail_closed() -> None:
    symbols = synthetic_symbols()
    affected = symbols[:17]
    baseline_scores = _reference_scores()
    valid_plus_invalid = synthetic_bars(symbols)
    for symbol in symbols:
        malformed_extra = valid_plus_invalid[symbol].tail(1).copy()
        malformed_extra.loc[:, "close_time"] += pd.Timedelta(hours=1)
        malformed_extra.loc[:, "close"] = float("nan")
        valid_plus_invalid[symbol] = pd.concat(
            [valid_plus_invalid[symbol], malformed_extra], ignore_index=True
        )
    assert (
        ber.build_strategy().preconstruction_scores(
            synthetic_context(bars=valid_plus_invalid), seed=20260801
        )
        == baseline_scores
    )
    missing = synthetic_bars(symbols)
    for symbol in affected:
        missing[symbol] = missing[symbol].iloc[1:].copy()
    assert ber.build_strategy().target_weights(synthetic_context(bars=missing), seed=20260801) == {}
    duplicated = synthetic_bars(symbols)
    for symbol in affected:
        # Both copies satisfy the exact expected-row predicate, so the symbol is invalid.
        duplicated[symbol] = pd.concat(
            [duplicated[symbol], duplicated[symbol].tail(1)], ignore_index=True
        )
    assert (
        ber.build_strategy().preconstruction_scores(
            synthetic_context(bars=duplicated), seed=20260801
        )
        == {}
    )
    nonfinite = synthetic_bars(symbols)
    for symbol in affected:
        nonfinite[symbol].loc[nonfinite[symbol].index[-1], "close"] = float("nan")
    assert (
        ber.build_strategy().target_weights(synthetic_context(bars=nonfinite), seed=20260801) == {}
    )
    wrong_close = synthetic_bars(symbols)
    for symbol in affected:
        row = wrong_close[symbol].index[-1]
        wrong_close[symbol].loc[row, "close_time"] += pd.Timedelta(hours=1)
    assert (
        ber.build_strategy().target_weights(synthetic_context(bars=wrong_close), seed=20260801)
        == {}
    )


def test_membership_input_order_determinism_and_context_immutability() -> None:
    context = synthetic_context()
    baseline_scores = _reference_scores()
    baseline_weights = _reference_weights()
    extra_bars = dict(context.bars)
    extra_bars["ZZZUSDT"] = _bar_frame("ZZZUSDT", 99)
    assert (
        ber.build_strategy().target_weights(synthetic_context(bars=extra_bars), seed=20260801)
        == baseline_weights
    )
    reordered = DecisionContext(
        decision_time=context.decision_time,
        bars={
            symbol: context.bars[symbol].iloc[::-1].reset_index(drop=True)
            for symbol in reversed(context.eligible_symbols)
        },
        funding=pd.DataFrame(),
        auxiliary={"ignored_label": 1.0},
        eligible_symbols=tuple(reversed(context.eligible_symbols)),
    )
    assert ber.build_strategy().preconstruction_scores(reordered, seed=20260801) == baseline_scores
    assert ber.build_strategy().target_weights(reordered, seed=20260801) == baseline_weights
    assert score_adapter.build_score_adapter().serialize_score_record(
        reordered, seed=20260801
    ) == score_adapter.build_score_adapter().serialize_score_record(context, seed=20260801)
    before = {symbol: frame.copy(deep=True) for symbol, frame in context.bars.items()}
    assert ber.build_strategy().target_weights(context, seed=20260801) == baseline_weights
    for symbol in context.eligible_symbols:
        pd.testing.assert_frame_equal(context.bars[symbol], before[symbol])


def test_clock_cross_section_seed_stateless_a5_and_legacy_audit_contract(monkeypatch) -> None:
    boundary_calls: list[dict[str, float]] = []

    def identity_boundary(scores: dict[str, float]) -> dict[str, float]:
        boundary_calls.append(scores)
        return scores

    monkeypatch.setattr(ber, "score_boundary", identity_boundary)
    monkeypatch.setattr(score_adapter.ber, "score_boundary", lambda scores: scores)
    insufficient = synthetic_context(symbols=synthetic_symbols(23))
    assert ber.build_strategy().target_weights(insufficient, seed=20260801) == {}
    assert boundary_calls == [{}]
    insufficient_record = score_adapter.build_score_adapter().score_record(
        insufficient, seed=20260801
    )
    assert insufficient_record is not None
    assert insufficient_record["scores"] == {}
    off_grid = synthetic_context(decision_time=DECISION_TIME + pd.Timedelta(hours=1))
    assert ber.build_strategy().target_weights(off_grid, seed=20260801) == {}
    # This empty record belongs only to the deprecated audit serializer. The
    # canonical A5 path above makes no off-schedule call and emits no score row.
    off_grid_record = score_adapter.build_score_adapter().score_record(off_grid, seed=20260801)
    assert off_grid_record is not None
    assert off_grid_record["scores"] == {}
    assert boundary_calls == [{}]
    unscheduled = synthetic_context(decision_time=DECISION_TIME + INTERVAL)
    assert ber.build_strategy().target_weights(unscheduled, seed=20260801) is None
    assert ber.build_strategy().preconstruction_scores(unscheduled, seed=20260801) is None
    assert score_adapter.build_score_adapter().score_record(unscheduled, seed=20260801) is None
    with pytest.raises(ValueError, match="canonical runtime seed"):
        ber.build_strategy().target_weights(synthetic_context(), seed=2026080104)
    first = ber.build_strategy().target_weights(synthetic_context(), seed=20260801)
    second = ber.build_strategy().target_weights(synthetic_context(), seed=20260801)
    assert first == second
    assert len(boundary_calls) == 3
    assert boundary_calls[0] == {}


def test_frozen_pivot_config_score_contract_and_no_control_policy() -> None:
    frozen = json.loads((RUNTIME_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    assert frozen["candidate_id"] == "team-04-ber-reference-001"
    assert frozen["family_id"] == "team-04-broad-exhaustion-reversal-v1"
    assert frozen["canonical_runtime_seed"] == 20260801
    assert frozen["parameters"] == {
        "baseline_volatility_days": 21,
        "coherence_base_weight": 0.5,
        "gross_target": 0.48,
        "minimum_baseline_volatility": 1e-6,
        "minimum_cross_section": 24,
        "minimum_names_per_sleeve": 8,
        "rebalance_bars": 6,
        "selected_fraction_per_side": "3/10",
        "shock_days": 3,
        "side_budget": 0.24,
        "symbol_cap": 0.03,
    }
    assert frozen["score_contract"]["uses_labels"] is False
    assert frozen["score_contract"]["boundary_import"] == (
        "from crypto_trade.tournament.score_adapter_protocol_v5 import score_boundary"
    )
    assert frozen["score_contract"]["boundary_call"] == "scores=score_boundary(scores)"
    assert frozen["score_contract"]["a5_authority_status"] == (
        "active-prospective-opt-in-not-yet-materialized"
    )
    assert frozen["score_contract"]["identity_requirement"] == (
        "return-exact-input-dictionary-object"
    )
    assert frozen["score_contract"]["legacy_team_adapter_role"] == (
        "noncanonical-audit-only-not-promoted-not-executed-by-a5"
    )
    assert frozen["score_contract"]["schedule_utc"] == {
        "anchor_timestamp_utc": "1970-01-01T00:00:00Z",
        "interval_hours": 48,
    }
    assert frozen["score_contract"]["off_grid_output"] == (
        "flat-target-with-no-boundary-call-no-score-capture-and-no-score-artifact-row"
    )
    assert frozen["ic_contract"]["label"] == (
        "simple-executable-open-t-to-executable-open-t-plus-48h-return"
    )
    assert frozen["ic_contract"]["fold_minimum_pairs"] == 240
    assert frozen["ic_contract"]["aggregate_minimum_pairs"] == 1440
    policy_raw = json.loads((RUNTIME_DIR / "risk_policy.json").read_text(encoding="utf-8"))
    policy = risk_policy_from_dict(policy_raw)
    assert policy.policy_id == frozen["risk_policy_id"] == "team-04-ber-reference-no-control"
    assert not policy.enabled
    assert not policy.same_boundary_reentry


def test_canonical_promotion_is_byte_identical_when_run_from_team_root() -> None:
    if TEST_DIR.name == "pivot-01":
        assert RUNTIME_DIR == TEMPLATE_DIR
        return
    for filename in (
        "strategy.py",
        "frozen_config.json",
        "risk_policy.json",
        "test_strategy.py",
    ):
        assert (RUNTIME_DIR / filename).read_bytes() == (TEMPLATE_DIR / filename).read_bytes()


def test_registration_templates_use_exact_fractions_and_active_a5_a6_shapes() -> None:
    family = json.loads(
        (TEMPLATE_DIR / "family-registration-input.json").read_text(encoding="utf-8")
    )
    trial = json.loads(
        (TEMPLATE_DIR / "trial-registration-input.template.json").read_text(encoding="utf-8")
    )
    neighborhood = json.loads(
        (TEMPLATE_DIR / "parameter_neighborhood.json").read_text(encoding="utf-8")
    )
    assert family["parameter_ranges"]["selected_fraction_per_side"] == [
        "1/4",
        "3/10",
        "7/20",
    ]
    assert family["parameter_ranges"]["minimum_baseline_volatility"] == [1e-6]
    assert family["parameter_ranges"]["minimum_names_per_sleeve"] == [8]
    assert family["parameter_ranges"]["shock_days"] == [1, 2, 3, 4]
    assert family["parameter_ranges"]["coherence_base_weight"] == [
        0.25,
        0.5,
        0.75,
        1.0,
    ]
    assert family["registered_at_utc"] == "1970-01-01T00:00:00Z"
    assert trial["timestamp_utc"] == "1970-01-01T00:00:00Z"
    assert trial["parameters"]["selected_fraction_per_side"] == "3/10"
    assert [
        item["value"]
        for item in neighborhood["neighbors"]
        if item["axis"] == "selected_fraction_per_side"
    ] == ["1/4", "7/20"]

    active = json.loads((TEAM_DIR / "active-pivot.json").read_text(encoding="utf-8"))
    assert active["promotion"]["target_strategy"] == "strategy.py"
    assert active["promotion"]["target_frozen_config"] == "frozen_config.json"
    assert active["promotion"]["target_test"] == "test_strategy.py"
    assert active["promotion"]["target_risk_policy"] == "risk_policy.json"
    assert active["promotion"]["root_lifecycle_entrypoint_required"] is True
    assert active["promotion"]["canonical_validation_path_after_promotion"] == ("test_strategy.py")
    assert active["promotion"]["excluded_from_promotion"] == ["organizer_score_adapter.py"]
    assert active["active_tournament_authority"]["active_entrypoint"] == {
        "path": "scripts/top40_v2_tournament_score_diagnostics_v5.py",
        "sha256": "0dc9228f3b9c6fe41b2655055f766fc92f323a289a050e6bdf4e48a30b0105f4",
    }
    pure_crypto = active["active_tournament_authority"][
        "delegated_amendment_0006_pure_crypto_universe"
    ]
    assert pure_crypto["canonical_report_sha256"] == (
        "b9c55b40fef331861af068272159f45860870182a58c93652eff2a819b3d5d1b"
    )
    assert pure_crypto["violations"] == 0
    assert active["material_trial_accounting"]["material_trials_consumed_before_ber"] == 1
    assert (
        active["material_trial_accounting"]["ber_reference_registration_would_consume_trial_number"]
        == 2
    )
    assert active["family_registration_before_final_source_hash"] is True
    assert active["score_schedule_anchor_authority"] == {
        "anchor_timestamp_utc": "1970-01-01T00:00:00Z",
        "interval_hours": 48,
        "placeholder": False,
    }

    executable = json.loads(
        (TEMPLATE_DIR / "executable-source-manifest.template.json").read_text(encoding="utf-8")
    )
    assert executable["manifest_kind"] == "top40-v2-executable-source-manifest-v1"
    executable_paths = [item["path"] for item in executable["files"]]
    assert executable_paths == [
        "frozen_config.json",
        "pivot-01/frozen_config.json",
        "pivot-01/organizer_score_adapter.py",
        "pivot-01/strategy.py",
        "pivot-01/test_strategy.py",
        "risk_policy.json",
        "strategy.py",
        "test_strategy.py",
    ]
    assert set(item["sha256"] for item in executable["files"]) == {"0" * 64}

    semantic = json.loads(
        (TEMPLATE_DIR / "semantic-coupling-review.template.json").read_text(encoding="utf-8")
    )
    assert semantic["review_kind"] == ("top40-v2-score-semantic-coupling-static-review-v1")
    assert semantic["reviewed_at_utc"] == "1970-01-01T00:00:00Z"
    assert semantic["reviewer_id"].startswith("TEMPLATE-ONLY")
    score_manifest = json.loads(
        (TEMPLATE_DIR / "score-adapter-manifest.template.json").read_text(encoding="utf-8")
    )
    assert score_manifest["adapter_id"] == "top40-v2-declared-score-boundary-v1"
    assert score_manifest["hook"] == "strategy.score_boundary"
    assert score_manifest["schedule_utc"] == {
        "anchor_timestamp_utc": "1970-01-01T00:00:00Z",
        "interval_hours": 48,
    }
    assert score_manifest["label"]["holding_horizon_hours"] == 48
    assert score_manifest["label"]["minimum_pairs"] == 240

    prospective = json.loads(
        (TEMPLATE_DIR / "prospective-a5-score-opt-in.template.json").read_text(encoding="utf-8")
    )
    assert prospective == {
        "_top40_v2_score_adapter": {
            "adapter_id": "top40-v2-declared-score-boundary-v1",
            "manifest_sha256": "0" * 64,
            "schema_version": 1,
        }
    }
    assert trial["parameters"]["_top40_v2_score_adapter"] == prospective["_top40_v2_score_adapter"]
