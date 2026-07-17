from __future__ import annotations

import dataclasses
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

TEAM_DIR = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "team10_strategy_under_test", TEAM_DIR / "strategy.py"
)
assert SPEC is not None and SPEC.loader is not None
STRATEGY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = STRATEGY
SPEC.loader.exec_module(STRATEGY)

MARKET_START = pd.Timestamp(year=2022, month=1, day=1, tz="UTC")
EFFICIENCY_DECISION = pd.Timestamp(year=2022, month=6, day=1, tz="UTC")


def _market_context(*, periods: int = 100, symbol_count: int = 20) -> SimpleNamespace:
    open_times = pd.date_range(MARKET_START, periods=periods, freq="8h")
    decision_time = open_times[-1] + pd.Timedelta(hours=8)
    step = np.arange(periods, dtype=float)
    symbols = [f"COIN{index:02d}USDT" for index in range(symbol_count)]
    bars: dict[str, pd.DataFrame] = {}
    for index, symbol in enumerate(symbols):
        common = 0.0012 + 0.00025 * np.sin(step / 11.0)
        relative_level = (index - (symbol_count - 1) / 2.0) * 0.00009
        relative_cycle = 0.00018 * np.sin(step / (3.0 + index % 5) + index * 0.4)
        log_close = np.log(100.0 + index) + np.cumsum(common + relative_level + relative_cycle)
        close = np.exp(log_close)
        bars[symbol] = pd.DataFrame(
            {
                "open_time": open_times,
                "open": np.r_[close[0], close[:-1]],
                "close": close,
                "quote_volume": np.full(periods, 2_000_000.0 + index),
            }
        )
    funding = pd.DataFrame(
        {
            "funding_time": [decision_time - pd.Timedelta(hours=8)],
            "funding_rate": [0.0001],
            "mark_price": [100.0],
            "symbol": [symbols[0]],
        }
    )
    return SimpleNamespace(
        auxiliary={},
        bars=bars,
        decision_time=decision_time,
        eligible_symbols=tuple(symbols),
        funding=funding,
    )


def _assert_balanced_reference(weights: dict[str, float]) -> None:
    assert len(weights) == 10
    values = np.asarray(list(weights.values()), dtype=float)
    assert np.isfinite(values).all()
    assert sum(value > 0.0 for value in values) == 5
    assert sum(value < 0.0 for value in values) == 5
    assert np.abs(values).sum() == pytest.approx(0.8)
    assert values.sum() == pytest.approx(0.0, abs=1e-12)
    assert np.abs(values).max() == pytest.approx(0.08)


def test_reference_strategy_is_finite_balanced_and_eligible() -> None:
    context = _market_context()
    weights = dict(STRATEGY.build_strategy().target_weights(context, seed=20260810))
    _assert_balanced_reference(weights)
    assert set(weights) <= set(context.eligible_symbols)


def test_public_score_boundary_is_an_exact_identity() -> None:
    scores = {"BTCUSDT": 1.25, "ETHUSDT": -0.75}
    assert STRATEGY.score_boundary.__module__ == (
        "crypto_trade.tournament.score_adapter_protocol_v5"
    )
    assert STRATEGY.score_boundary.__name__ == "score_boundary"
    assert STRATEGY.score_boundary(scores) is scores


def test_score_boundary_is_called_once_and_its_exact_object_drives_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _market_context()
    captured: list[dict[str, float]] = []

    def capture(scores: dict[str, float]) -> dict[str, float]:
        assert type(scores) is dict
        assert all(type(symbol) is str for symbol in scores)
        assert np.isfinite(np.asarray(tuple(scores.values()), dtype=float)).all()
        captured.append(scores)
        return scores

    monkeypatch.setattr(STRATEGY, "score_boundary", capture)
    weights = STRATEGY.build_strategy().target_weights(context, seed=20260801)
    assert len(captured) == 1
    operative_scores = captured[0]
    expected_longs = set(
        sorted(operative_scores, key=lambda symbol: (-operative_scores[symbol], symbol))[:5]
    )
    expected_shorts = set(
        sorted(operative_scores, key=lambda symbol: (operative_scores[symbol], symbol))[:5]
    )
    assert {symbol for symbol, weight in weights.items() if weight > 0.0} == expected_longs
    assert {symbol for symbol, weight in weights.items() if weight < 0.0} == expected_shorts


def test_score_boundary_copy_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(STRATEGY, "score_boundary", lambda scores: dict(scores))
    with pytest.raises(TypeError, match="exact input object"):
        STRATEGY.build_strategy().target_weights(_market_context(), seed=20260801)


def test_appended_corrupt_future_is_invariant() -> None:
    context = _market_context()
    expected = STRATEGY.build_strategy().target_weights(context, seed=20260810)
    appended: dict[str, pd.DataFrame] = {}
    for symbol, frame in context.bars.items():
        future = pd.DataFrame(
            {
                "open_time": [context.decision_time],
                "open": [np.nan],
                "close": [np.nan],
                "quote_volume": [np.nan],
            }
        )
        appended[symbol] = pd.concat([frame, future], ignore_index=True)
    changed = SimpleNamespace(**{**vars(context), "bars": appended})
    actual = STRATEGY.build_strategy().target_weights(changed, seed=20260810)
    assert actual == expected


def test_input_and_seed_order_are_invariant() -> None:
    context = _market_context()
    expected = STRATEGY.build_strategy().target_weights(context, seed=1)
    reversed_bars = {
        symbol: context.bars[symbol].iloc[::-1].copy()
        for symbol in reversed(context.eligible_symbols)
    }
    reordered = SimpleNamespace(
        **{
            **vars(context),
            "bars": reversed_bars,
            "eligible_symbols": tuple(reversed(context.eligible_symbols)),
        }
    )
    assert STRATEGY.build_strategy().target_weights(reordered, seed=999999) == expected


def test_missing_bar_is_not_compressed_and_stale_symbol_is_not_scored() -> None:
    context = _market_context()
    baseline = dict(STRATEGY.build_strategy().target_weights(context, seed=20260810))
    chosen = next(iter(baseline))
    gapped_bars = dict(context.bars)
    gapped_bars[chosen] = gapped_bars[chosen].drop(gapped_bars[chosen].index[-3])
    gapped = SimpleNamespace(**{**vars(context), "bars": gapped_bars})
    assert chosen not in STRATEGY.build_strategy().target_weights(gapped, seed=20260810)

    stale_bars = dict(context.bars)
    stale_bars[chosen] = stale_bars[chosen].iloc[:-1]
    stale = SimpleNamespace(**{**vars(context), "bars": stale_bars})
    assert chosen not in STRATEGY.build_strategy().target_weights(stale, seed=20260810)


def test_under_history_new_member_does_not_abort_the_book() -> None:
    context = _market_context()
    new_symbol = "NEWCOINUSDT"
    bars = dict(context.bars)
    bars[new_symbol] = next(iter(bars.values())).iloc[-12:].copy()
    changed = SimpleNamespace(
        **{
            **vars(context),
            "bars": bars,
            "eligible_symbols": (*context.eligible_symbols, new_symbol),
        }
    )
    weights = dict(STRATEGY.build_strategy().target_weights(changed, seed=20260810))
    _assert_balanced_reference(weights)
    assert new_symbol not in weights


def test_funding_is_not_a_feature() -> None:
    context = _market_context()
    expected = STRATEGY.build_strategy().target_weights(context, seed=20260810)
    opposite_funding = context.funding.copy()
    opposite_funding["funding_rate"] *= -1000.0
    changed = SimpleNamespace(**{**vars(context), "funding": opposite_funding})
    assert STRATEGY.build_strategy().target_weights(changed, seed=20260810) == expected


def test_noneligible_bar_can_never_be_returned() -> None:
    context = _market_context()
    bars = dict(context.bars)
    bars["OUTSIDERUSDT"] = next(iter(bars.values())).copy()
    changed = SimpleNamespace(**{**vars(context), "bars": bars})
    weights = STRATEGY.build_strategy().target_weights(changed, seed=20260810)
    assert "OUTSIDERUSDT" not in weights


def test_insufficient_breadth_and_constant_market_request_flat() -> None:
    context = _market_context(symbol_count=11)
    assert STRATEGY.build_strategy().target_weights(context, seed=20260810) == {}

    wide = _market_context()
    constant_bars = {}
    for symbol, frame in wide.bars.items():
        constant = frame.copy()
        constant["close"] = 100.0
        constant_bars[symbol] = constant
    constant_context = SimpleNamespace(**{**vars(wide), "bars": constant_bars})
    assert STRATEGY.build_strategy().target_weights(constant_context, seed=20260810) == {}


def test_adaptive_efficiency_interpolates_between_reversion_and_trend() -> None:
    strategy = STRATEGY.build_strategy()
    decision_time = EFFICIENCY_DECISION
    index = pd.date_range(
        end=decision_time,
        periods=strategy.config.regime_horizon_bars,
        freq="8h",
    )
    oscillating = pd.Series(np.resize([1.0, -1.0], len(index)), index=index)
    trending = pd.Series(np.ones(len(index)), index=index)
    mixed = pd.Series(np.r_[np.ones(39), -np.ones(24)], index=index)

    low = strategy._trend_share(oscillating, decision_time, pd.Timedelta(hours=8))
    middle = strategy._trend_share(mixed, decision_time, pd.Timedelta(hours=8))
    high = strategy._trend_share(trending, decision_time, pd.Timedelta(hours=8))
    assert low == 0.0
    assert middle is not None and 0.0 < middle < 1.0
    assert high == 1.0


def test_duplicate_or_invalid_past_close_fails_closed() -> None:
    context = _market_context()
    symbol = context.eligible_symbols[0]
    duplicated_bars = dict(context.bars)
    duplicated_bars[symbol] = pd.concat(
        [duplicated_bars[symbol], duplicated_bars[symbol].iloc[[-1]]],
        ignore_index=True,
    )
    duplicate_context = SimpleNamespace(**{**vars(context), "bars": duplicated_bars})
    with pytest.raises(ValueError, match="duplicate"):
        STRATEGY.build_strategy().target_weights(duplicate_context, seed=20260810)

    invalid_bars = dict(context.bars)
    invalid_bars[symbol] = invalid_bars[symbol].copy()
    invalid_bars[symbol].loc[invalid_bars[symbol].index[-2], "close"] = -1.0
    invalid_context = SimpleNamespace(**{**vars(context), "bars": invalid_bars})
    with pytest.raises(ValueError, match="positive and finite"):
        STRATEGY.build_strategy().target_weights(invalid_context, seed=20260810)


def test_frozen_config_and_declared_neighbors_are_executable_and_feasible() -> None:
    frozen = json.loads((TEAM_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    center = STRATEGY.StrategyConfig()
    assert frozen["strategy"] == dataclasses.asdict(center)
    center.validate()

    manifest = json.loads((TEAM_DIR / "parameter_neighborhood.json").read_text(encoding="utf-8"))
    assert manifest["center_parameters"] == dataclasses.asdict(center)
    axes = {}
    for neighbor in manifest["neighbors"]:
        candidate = dataclasses.replace(center, **{neighbor["axis"]: neighbor["value"]})
        candidate.validate()
        axes.setdefault(neighbor["axis"], []).append(neighbor["value"])
    assert len(manifest["neighbors"]) == 12
    assert all(len(values) == 2 for values in axes.values())


def test_a7_and_a5_score_identities_are_exact() -> None:
    authority = json.loads((TEAM_DIR / "a7_execution_authority.json").read_text(encoding="utf-8"))
    assert authority["active_entrypoint"] == {
        "path": "scripts/top40_v2_tournament_runtime_preload_v7.py",
        "sha256": "8a4ada10176d2606df3f358fc188e21b45153ad9a7270f36908736f03322a3a9",
    }
    contract = authority["operative_a5_score_contract"]
    manifest = json.loads(
        (
            TEAM_DIR / "score-adapters/t10-rtre-core-v1.score-adapter-manifest.template.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["adapter_id"] == contract["adapter_id"]
    assert manifest["capture_boundary"] == contract["capture_boundary"]
    assert manifest["hook"] == "strategy.score_boundary"
    assert manifest["label"] == {
        "executable_price_column": "open",
        "holding_horizon_hours": 8,
        "label_id": "manifest-horizon-simple-executable-open-to-open-return-v1",
        "minimum_pairs": 240,
        "purge_cross_fold_endpoints": True,
        "return_definition": "simple-executable-open-to-open",
        "score_direction": "higher-score-higher-return",
        "statistic_id": "globally-pooled-pearson-v1",
    }
    assert manifest["schedule_utc"] == {
        "anchor_timestamp_utc": "1970-01-01T00:00:00Z",
        "interval_hours": 8,
    }
    trial = json.loads((TEAM_DIR / "trial-registration.template.json").read_text(encoding="utf-8"))
    assert trial["parameters"]["_top40_v2_score_adapter"] == {
        "adapter_id": "top40-v2-declared-score-boundary-v1",
        "manifest_sha256": "0" * 64,
        "schema_version": 1,
    }


def test_score_review_templates_cover_complete_candidate_source_set() -> None:
    source_manifest = json.loads(
        (
            TEAM_DIR / "score-adapters/t10-rtre-core-v1.executable-source-manifest.template.json"
        ).read_text(encoding="utf-8")
    )
    assert [entry["path"] for entry in source_manifest["files"]] == [
        "frozen_config.json",
        "risk_policy.json",
        "strategy.py",
        "test_risk_policy_contract.py",
        "test_strategy.py",
    ]
    review = json.loads(
        (TEAM_DIR / "score-adapters/t10-rtre-core-v1.semantic-review.template.json").read_text(
            encoding="utf-8"
        )
    )
    assert set(review["findings"]) == {
        "direct_hook_call_found",
        "hook_after_declared_score_transform",
        "hook_before_selection_weight_caps_and_risk",
        "no_decoy_or_transient_score_path_found",
        "score_object_is_declared_model_ranking_signal",
    }
    assert review["runtime_proof_limit"] == ("static-review-attestation-not-runtime-semantic-proof")


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"fast_horizon_bars": 18}, "strictly increasing"),
        ({"efficiency_lower": 0.4, "efficiency_upper": 0.3}, "efficiency"),
        ({"selection_count_per_side": 3}, "gross exposure"),
        ({"minimum_scored_symbols": 4}, "overlapping sleeves"),
        ({"ensemble_mode": "oracle"}, "ensemble_mode"),
    ],
)
def test_invalid_configuration_is_rejected(override: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        dataclasses.replace(STRATEGY.StrategyConfig(), **override).validate()
