"""Synthetic, market-data-free tests for Team 04 PARD pivot 02."""

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
TEAM_DIR = TEST_DIR.parent if TEST_DIR.name == "pivot-02" else TEST_DIR
RUNTIME_DIR = TEST_DIR
TEMPLATE_DIR = TEAM_DIR / "pivot-02"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


pard = _load("_team04_pard_test_strategy", RUNTIME_DIR / "strategy.py")


def synthetic_symbols(count: int = 40) -> tuple[str, ...]:
    return tuple(f"C{index:02d}USDT" for index in range(count))


def _bar_frame(
    symbol: str,
    index: int,
    *,
    timestamp_encoding: str = "naive",
    include_future: bool = False,
) -> pd.DataFrame:
    count = pard._REFERENCE.history_return_bars + 1
    times = [CUTOFF - (count - 1 - step) * INTERVAL for step in range(count)]
    midpoint = 19.5
    relative = (index - midpoint) / midpoint
    price = 100.0 + index
    rows: list[dict[str, object]] = []
    for step, close_time in enumerate(times):
        if step:
            if step <= pard._REFERENCE.established_bars:
                move = 0.00065 * relative + 0.00018 * math.sin(0.55 * step + 0.09 * index)
            else:
                move = -0.00045 * relative + 0.00010 * math.sin(0.91 * step - 0.07 * index)
            price *= math.exp(move)
        if timestamp_encoding == "naive":
            encoded: object = close_time.tz_localize(None)
        elif timestamp_encoding == "aware":
            encoded = close_time
        elif timestamp_encoding == "milliseconds":
            encoded = int(close_time.timestamp() * 1_000)
        else:
            raise ValueError(timestamp_encoding)
        rows.append({"symbol": symbol, "close_time": encoded, "close": price})
    if include_future:
        future = CUTOFF + INTERVAL
        rows.append(
            {
                "symbol": symbol,
                "close_time": future.tz_localize(None) if timestamp_encoding == "naive" else future,
                "close": price * 100.0,
            }
        )
    return pd.DataFrame(rows)


def synthetic_bars(
    symbols: tuple[str, ...] | None = None,
    *,
    timestamp_encoding: str = "naive",
    include_future: bool = False,
) -> dict[str, pd.DataFrame]:
    eligible = symbols or synthetic_symbols()
    return {
        symbol: _bar_frame(
            symbol,
            index,
            timestamp_encoding=timestamp_encoding,
            include_future=include_future,
        )
        for index, symbol in enumerate(eligible)
    }


def synthetic_context(
    *,
    symbols: tuple[str, ...] | None = None,
    decision_time: object = DECISION_TIME,
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
    result = pard.build_strategy().preconstruction_scores(synthetic_context(), seed=20260801)
    assert isinstance(result, dict) and result
    return result


def _reference_weights() -> dict[str, float]:
    result = pard.build_strategy().target_weights(synthetic_context(), seed=20260801)
    assert isinstance(result, dict) and result
    return result


def test_organizer_utc_storage_encodings_are_equivalent() -> None:
    aware = pard._utc_timestamp(pd.Timestamp("2023-01-01T00:00:00Z"))
    naive = pard._utc_timestamp(pd.Timestamp("2023-01-01T00:00:00"))
    milliseconds = pard._utc_timestamp(1672531200000)
    assert aware == naive == milliseconds == pd.Timestamp("2023-01-01T00:00:00Z")
    baseline = _reference_scores()
    for encoding in ("aware", "milliseconds"):
        context = synthetic_context(bars=synthetic_bars(timestamp_encoding=encoding))
        assert pard.build_strategy().preconstruction_scores(context, seed=20260801) == baseline
    inclusive = synthetic_bars(timestamp_encoding="aware")
    for frame in inclusive.values():
        frame.loc[:, "close_time"] = frame["close_time"] - pd.Timedelta(milliseconds=1)
    inclusive_context = synthetic_context(bars=inclusive)
    assert (
        pard.build_strategy().preconstruction_scores(inclusive_context, seed=20260801) == baseline
    )


def test_exact_feature_formula_uses_independent_displacement() -> None:
    frame = _bar_frame("XUSDT", 31)
    feature = pard._path_feature(frame, cutoff=CUTOFF)
    assert feature is not None
    closes = frame["close"].tolist()
    returns = [
        math.log(current / previous)
        for previous, current in zip(closes[:-1], closes[1:], strict=True)
    ]
    established = returns[:63]
    displacement = returns[63:]
    medium = established[-21:]
    mean = math.fsum(established) / 63
    sigma = math.sqrt(math.fsum((value - mean) ** 2 for value in established) / 63)
    assert feature.established_z == pytest.approx(
        math.fsum(established) / (sigma * math.sqrt(63)), abs=1e-12
    )
    assert feature.medium_z == pytest.approx(math.fsum(medium) / (sigma * math.sqrt(21)), abs=1e-12)
    assert feature.displacement_z == pytest.approx(
        math.fsum(displacement) / (sigma * math.sqrt(6)), abs=1e-12
    )
    assert 0.0 <= feature.coherence <= 1.0


def test_naive_reference_produces_scores_trades_and_balanced_book() -> None:
    scores = _reference_scores()
    weights = _reference_weights()
    positives = {symbol: weight for symbol, weight in weights.items() if weight > 0.0}
    negatives = {symbol: weight for symbol, weight in weights.items() if weight < 0.0}
    assert len(scores) == 40
    assert len(positives) == len(negatives) == 10
    assert min(scores[symbol] for symbol in positives) > max(scores[symbol] for symbol in negatives)
    assert math.fsum(positives.values()) == pytest.approx(0.25, abs=1e-12)
    assert math.fsum(-weight for weight in negatives.values()) == pytest.approx(0.25, abs=1e-12)
    assert math.fsum(abs(weight) for weight in weights.values()) == pytest.approx(0.50, abs=1e-12)
    assert math.fsum(weights.values()) == pytest.approx(0.0, abs=1e-12)
    assert max(abs(weight) for weight in weights.values()) <= 0.03


def test_zero_or_one_sided_scores_never_form_an_ascii_selected_book() -> None:
    symbols = synthetic_symbols()
    assert pard._select_sleeves({symbol: 0.0 for symbol in symbols}) is None
    assert (
        pard._select_sleeves({symbol: float(index) for index, symbol in enumerate(symbols)}) is None
    )
    assert (
        pard._select_sleeves({symbol: -float(index) for index, symbol in enumerate(symbols)})
        is None
    )


def test_a5_boundary_is_exact_final_rank_used_by_construction(monkeypatch) -> None:
    captured: list[dict[str, float]] = []

    def identity_boundary(scores: dict[str, float]) -> dict[str, float]:
        captured.append(scores)
        return scores

    monkeypatch.setattr(pard, "score_boundary", identity_boundary)
    context = synthetic_context()
    scores = pard.build_strategy().preconstruction_scores(context, seed=20260801)
    weights = pard.build_strategy().target_weights(context, seed=20260801)
    assert isinstance(scores, dict) and scores
    assert isinstance(weights, dict) and weights
    assert len(captured) == 2
    assert captured[0] == captured[1] == scores
    assert min(captured[1][symbol] for symbol, weight in weights.items() if weight > 0) > max(
        captured[1][symbol] for symbol, weight in weights.items() if weight < 0
    )
    monkeypatch.setattr(pard, "score_boundary", lambda scores: dict(scores))
    with pytest.raises(RuntimeError, match="return its input dictionary by identity"):
        pard.build_strategy().target_weights(context, seed=20260801)


def test_real_a5_adapter_schedule_and_scheduled_empty_capture() -> None:
    anchor = pd.Timestamp("1970-01-01T00:00:00Z")
    assert (DECISION_TIME - anchor).value % pd.Timedelta(hours=48).value == 0
    context = synthetic_context()
    strategy = pard.build_strategy()
    result = build_adapter(score_adapter_protocol_v5.ADAPTER_ID, strategy).evaluate(
        lambda: strategy.target_weights(context, seed=20260801),
        scheduled=True,
        eligible_symbols=context.eligible_symbols,
    )
    assert isinstance(result.weights, dict) and result.weights
    assert isinstance(result.scores, dict) and result.scores
    sparse = synthetic_context(symbols=synthetic_symbols(19))
    sparse_strategy = pard.build_strategy()
    sparse_result = build_adapter(score_adapter_protocol_v5.ADAPTER_ID, sparse_strategy).evaluate(
        lambda: sparse_strategy.target_weights(sparse, seed=20260801),
        scheduled=True,
        eligible_symbols=sparse.eligible_symbols,
    )
    assert sparse_result.weights == {}
    assert sparse_result.scores == {}


def test_hold_and_off_grid_never_call_a5_boundary(monkeypatch) -> None:
    captured: list[dict[str, float]] = []

    def identity_boundary(scores: dict[str, float]) -> dict[str, float]:
        captured.append(scores)
        return scores

    monkeypatch.setattr(pard, "score_boundary", identity_boundary)
    hold = synthetic_context(decision_time=DECISION_TIME + INTERVAL)
    assert pard.build_strategy().target_weights(hold, seed=20260801) is None
    off_grid = synthetic_context(decision_time=DECISION_TIME + pd.Timedelta(hours=1))
    assert pard.build_strategy().target_weights(off_grid, seed=20260801) == {}
    before_anchor = synthetic_context(decision_time=pd.Timestamp("1970-01-01T00:00:00Z") - INTERVAL)
    assert pard.build_strategy().target_weights(before_anchor, seed=20260801) == {}
    assert captured == []


def test_future_auxiliary_and_row_order_are_invariant(monkeypatch) -> None:
    captured: list[bytes] = []

    def capture(scores: dict[str, float]) -> dict[str, float]:
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

    monkeypatch.setattr(pard, "score_boundary", capture)
    baseline = synthetic_context()
    poisoned = synthetic_context(auxiliary={"forward_return": object(), "outcome": object()})
    future_bars = synthetic_bars(include_future=True)
    future = synthetic_context(bars=future_bars)
    corrupted_future_bars = {symbol: frame.copy(deep=True) for symbol, frame in future_bars.items()}
    for frame in corrupted_future_bars.values():
        frame.loc[frame.index[-1], "close"] = float("inf")
    corrupted_future = synthetic_context(bars=corrupted_future_bars)
    reversed_rows = synthetic_context(
        bars={
            symbol: frame.iloc[::-1].reset_index(drop=True)
            for symbol, frame in synthetic_bars().items()
        }
    )
    reversed_symbols = tuple(reversed(synthetic_symbols()))
    ordered_bars = synthetic_bars()
    reordered = synthetic_context(
        symbols=reversed_symbols,
        bars={symbol: ordered_bars[symbol] for symbol in reversed_symbols},
    )
    for context in (
        baseline,
        poisoned,
        future,
        corrupted_future,
        reversed_rows,
        reordered,
    ):
        result = pard.build_strategy().preconstruction_scores(context, seed=20260801)
        assert isinstance(result, dict) and result
    assert len(captured) == 6
    assert all(value == captured[0] for value in captured[1:])


def test_latest_duplicate_gap_and_insufficient_complete_names_fail_closed() -> None:
    symbols = synthetic_symbols(24)
    affected = symbols[:5]
    duplicated = synthetic_bars(symbols)
    for symbol in affected:
        duplicated[symbol] = pd.concat(
            [duplicated[symbol], duplicated[symbol].tail(1)], ignore_index=True
        )
    assert (
        pard.build_strategy().target_weights(
            synthetic_context(symbols=symbols, bars=duplicated), seed=20260801
        )
        == {}
    )
    gapped = synthetic_bars(symbols)
    for symbol in affected:
        gapped[symbol] = gapped[symbol].drop(gapped[symbol].index[-10]).reset_index(drop=True)
    assert (
        pard.build_strategy().preconstruction_scores(
            synthetic_context(symbols=symbols, bars=gapped), seed=20260801
        )
        == {}
    )


def test_old_duplicate_outside_selected_suffix_does_not_flatten_symbol() -> None:
    baseline = _reference_scores()
    bars = synthetic_bars()
    for symbol, frame in bars.items():
        old_time = pd.Timestamp(frame.iloc[0]["close_time"]) - INTERVAL
        old = pd.DataFrame(
            [
                {"symbol": symbol, "close_time": old_time, "close": 99.0},
                {"symbol": symbol, "close_time": old_time, "close": 101.0},
            ]
        )
        bars[symbol] = pd.concat([old, frame], ignore_index=True)
    result = pard.build_strategy().preconstruction_scores(
        synthetic_context(bars=bars), seed=20260801
    )
    assert result == baseline


def test_seed_statelessness_config_and_no_control_proposal() -> None:
    first = pard.build_strategy().target_weights(synthetic_context(), seed=20260801)
    second = pard.build_strategy().target_weights(synthetic_context(), seed=20260801)
    assert first == second
    with pytest.raises(ValueError, match="canonical runtime seed"):
        pard.build_strategy().target_weights(synthetic_context(), seed=2026080104)
    frozen = json.loads((RUNTIME_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    assert frozen["candidate_id"] == "team-04-pard-reference-001"
    assert frozen["family_id"] == "team-04-path-adaptive-relative-dynamics-v1"
    assert frozen["status"] == (
        "promoted-serial-validation-passed-awaiting-review-hashes-and-registration"
    )
    assert frozen["development_authority"]["candidate_specific_a7_rebind_required"] is False
    policy_raw = json.loads((RUNTIME_DIR / "risk_policy.json").read_text(encoding="utf-8"))
    policy = risk_policy_from_dict(policy_raw)
    assert policy.policy_id == frozen["risk_policy_id"] == ("team-04-pard-reference-no-control")
    assert not policy.enabled
    assert not policy.same_boundary_reentry


def test_canonical_promotion_is_byte_identical_when_run_from_team_root() -> None:
    if TEST_DIR.name == "pivot-02":
        assert RUNTIME_DIR == TEMPLATE_DIR
        return
    for filename in (
        "strategy.py",
        "frozen_config.json",
        "risk_policy.json",
        "test_strategy.py",
    ):
        assert (RUNTIME_DIR / filename).read_bytes() == (TEMPLATE_DIR / filename).read_bytes()


def test_complete_numeric_gates_and_noncircular_staging_are_frozen() -> None:
    frozen = json.loads((RUNTIME_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    core = frozen["qualification_gates"]["core_pre_neighbor"]
    assert core == {
        "annualized_return_strict_minimum": 0.0,
        "calmar_minimum": 0.4,
        "combined_chop_return_strict_minimum": 0.0,
        "doubled_cost_sharpe_minimum": 0.35,
        "long_bull_return_strict_minimum": 0.0,
        "maximum_drawdown_maximum": 0.3,
        "maximum_positive_pnl_concentration": 0.4,
        "minimum_positive_fold_count": 4,
        "minimum_positive_quarter_fraction": 0.55,
        "minimum_positive_regime_sharpe_count": 3,
        "net_sharpe_minimum": 0.75,
        "positive_return_regimes": ["bull", "bear", "chop"],
        "regime_sharpe_set": ["bull", "bear", "chop", "stress"],
        "short_bear_return_strict_minimum": 0.0,
        "sleeve_active_bar_fraction_minimum_each_side": 0.1,
        "sleeve_executed_notional_minimum_usdt_each_side": 1000.0,
        "sleeve_exposure_minimum_each_side": 0.01,
        "sleeve_mean_exposure_minimum_each_side": 0.01,
        "trial_adjusted_positive_probability_minimum": 0.9,
        "walk_forward_fold_count": 6,
        "worst_regime_sharpe_minimum": -0.25,
    }
    a5 = frozen["qualification_gates"]["a5_complete_evidence"]
    assert a5["pooled_score_ic_strict_minimum"] == 0.0
    assert a5["minimum_positive_fold_ics"] == 4
    assert a5["fold_minimum_pairs"] == 240
    assert a5["fold_minimum_scheduled_decisions"] == 10
    assert a5["aggregate_minimum_pairs"] == 1440
    assert a5["require_complete_scheduled_score_coverage"] is True
    assert a5["require_independent_semantic_review"] is True
    neighborhood = json.loads(
        (TEMPLATE_DIR / "parameter_neighborhood.json").read_text(encoding="utf-8")
    )
    assert neighborhood["size_including_center"] == 9
    assert neighborhood["minimum_profitable_count"] == 7
    assert neighborhood["minimum_profitable_fraction"] == 0.7
    assert neighborhood["minimum_median_sharpe"] == 0.5
    assert neighborhood["evaluation_sequence"][0] == ("observe-exact-no-control-center-only")


def test_templates_are_prospective_and_require_fresh_governance() -> None:
    family = json.loads(
        (TEMPLATE_DIR / "family-registration-input.template.json").read_text(encoding="utf-8")
    )
    trial = json.loads(
        (TEMPLATE_DIR / "trial-registration-input.template.json").read_text(encoding="utf-8")
    )
    score = json.loads(
        (TEMPLATE_DIR / "score-adapter-manifest.template.json").read_text(encoding="utf-8")
    )
    executable = json.loads(
        (TEMPLATE_DIR / "executable-source-manifest.template.json").read_text(encoding="utf-8")
    )
    semantic = json.loads(
        (TEMPLATE_DIR / "semantic-coupling-review.template.json").read_text(encoding="utf-8")
    )
    assert family["parent_family_id"] == "team-04-broad-exhaustion-reversal-v1"
    assert family["falsifier"] == trial["falsifier"]
    assert "net Sharpe at least 0.75" in family["falsifier"]
    assert "Only after every core and A5 pre-neighbor gate passes" in family["falsifier"]
    assert family["registered_at_utc"] == "1970-01-01T00:00:00Z"
    assert trial["timestamp_utc"] == "1970-01-01T00:00:00Z"
    assert set(
        value for key, value in trial.items() if key.endswith("sha256") and isinstance(value, str)
    ) == {"0" * 64}
    assert score["schedule_utc"] == {
        "anchor_timestamp_utc": "1970-01-01T00:00:00Z",
        "interval_hours": 48,
    }
    assert score["semantic_coupling_review_sha256"] == "0" * 64
    assert executable["manifest_kind"] == "top40-v2-executable-source-manifest-v1"
    assert set(item["sha256"] for item in executable["files"]) == {"0" * 64}
    assert semantic["reviewer_id"].startswith("TEMPLATE-ONLY")
    handoff = (TEMPLATE_DIR / "README.md").read_text(encoding="utf-8")
    assert "governed A7 rebind" in handoff
    assert "Registration or execution before the governed A7 rebind is forbidden" in handoff
