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
    "team10_pivot01_strategy_under_test",
    TEAM_DIR / "strategy.py",
)
assert SPEC is not None and SPEC.loader is not None
STRATEGY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = STRATEGY
SPEC.loader.exec_module(STRATEGY)


def _market_context(*, periods: int = 120, symbol_count: int = 20) -> SimpleNamespace:
    open_times = pd.date_range("2022-01-01T00:00:00Z", periods=periods, freq="8h")
    decision_time = open_times[-1] + pd.Timedelta(hours=8)
    step = np.arange(periods, dtype=float)
    symbols = [f"COIN{index:02d}USDT" for index in range(symbol_count)]
    bars: dict[str, pd.DataFrame] = {}
    for index, symbol in enumerate(symbols):
        phase = 2.0 * np.pi * index / symbol_count
        common = 0.00035 + 0.00012 * np.sin(step / 17.0)
        relative = 0.00075 * np.sin(step / 8.0 + phase)
        log_close = np.log(100.0 + index) + np.cumsum(common + relative)
        close = np.exp(log_close)
        quote_volume = 2_000_000.0 * (1.0 + 0.08 * np.cos(step / 9.0 + phase))
        bars[symbol] = pd.DataFrame(
            {
                "open_time": open_times,
                "open": np.r_[close[0], close[:-1]],
                "close": close,
                "quote_volume": quote_volume,
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


def _assert_balanced_pivot(weights: dict[str, float]) -> None:
    assert len(weights) == 8
    values = np.asarray(tuple(weights.values()), dtype=float)
    assert np.isfinite(values).all()
    assert sum(value > 0.0 for value in values) == 4
    assert sum(value < 0.0 for value in values) == 4
    assert np.abs(values).sum() == pytest.approx(0.20)
    assert values.sum() == pytest.approx(0.0, abs=1e-12)
    assert np.abs(values).max() == pytest.approx(0.025)


def test_reference_pivot_is_finite_balanced_and_eligible() -> None:
    context = _market_context()
    weights = dict(STRATEGY.build_strategy().target_weights(context, seed=20260801))
    _assert_balanced_pivot(weights)
    assert set(weights) <= set(context.eligible_symbols)


def test_public_score_boundary_is_frozen_a5_identity() -> None:
    scores = {"BTCUSDT": 1.0, "ETHUSDT": -1.0}
    assert STRATEGY.score_boundary.__module__ == (
        "crypto_trade.tournament.score_adapter_protocol_v5"
    )
    assert STRATEGY.score_boundary(scores) is scores


def test_boundary_is_once_and_exact_scores_drive_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[dict[str, float]] = []

    def capture(scores: dict[str, float]) -> dict[str, float]:
        assert type(scores) is dict
        assert np.isfinite(np.asarray(tuple(scores.values()), dtype=float)).all()
        captured.append(scores)
        return scores

    monkeypatch.setattr(STRATEGY, "score_boundary", capture)
    weights = STRATEGY.build_strategy().target_weights(_market_context(), seed=20260801)
    assert len(captured) == 1
    scores = captured[0]
    expected_longs = set(sorted(scores, key=lambda symbol: (-scores[symbol], symbol))[:4])
    expected_shorts = set(sorted(scores, key=lambda symbol: (scores[symbol], symbol))[:4])
    assert {symbol for symbol, weight in weights.items() if weight > 0.0} == expected_longs
    assert {symbol for symbol, weight in weights.items() if weight < 0.0} == expected_shorts


def test_boundary_copy_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(STRATEGY, "score_boundary", lambda scores: dict(scores))
    with pytest.raises(TypeError, match="exact input object"):
        STRATEGY.build_strategy().target_weights(_market_context(), seed=20260801)


def test_unscheduled_boundaries_hold_without_score_capture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _market_context()
    context.decision_time += pd.Timedelta(hours=8)

    def forbidden(_: dict[str, float]) -> dict[str, float]:
        raise AssertionError("off-schedule decision captured a score")

    monkeypatch.setattr(STRATEGY, "score_boundary", forbidden)
    assert STRATEGY.build_strategy().target_weights(context, seed=20260801) is None


def test_unchanged_daily_sleeves_hold_instead_of_rebalancing() -> None:
    strategy = STRATEGY.build_strategy()
    context = _market_context()
    first = strategy.target_weights(context, seed=20260801)
    assert first is not None and first
    assert strategy.target_weights(context, seed=20260801) is None


def test_crash_quarantine_excludes_extreme_recent_coin() -> None:
    context = _market_context()
    baseline = STRATEGY.build_strategy().target_weights(context, seed=20260801)
    assert baseline
    chosen = next(iter(baseline))
    bars = dict(context.bars)
    bars[chosen] = bars[chosen].copy()
    bars[chosen].loc[bars[chosen].index[-1], "close"] *= 1.50
    changed = SimpleNamespace(**{**vars(context), "bars": bars})
    weights = STRATEGY.build_strategy().target_weights(changed, seed=20260801)
    assert chosen not in weights


def test_missing_bar_is_not_compressed_and_stale_coin_is_excluded() -> None:
    context = _market_context()
    baseline = STRATEGY.build_strategy().target_weights(context, seed=20260801)
    assert baseline
    chosen = next(iter(baseline))
    gapped_bars = dict(context.bars)
    gapped_bars[chosen] = gapped_bars[chosen].drop(gapped_bars[chosen].index[-3])
    gapped = SimpleNamespace(**{**vars(context), "bars": gapped_bars})
    assert chosen not in STRATEGY.build_strategy().target_weights(gapped, seed=20260801)

    stale_bars = dict(context.bars)
    stale_bars[chosen] = stale_bars[chosen].iloc[:-1]
    stale = SimpleNamespace(**{**vars(context), "bars": stale_bars})
    assert chosen not in STRATEGY.build_strategy().target_weights(stale, seed=20260801)


def test_corrupt_appended_future_is_invariant() -> None:
    context = _market_context()
    expected = STRATEGY.build_strategy().target_weights(context, seed=20260801)
    bars = {}
    for symbol, frame in context.bars.items():
        future = pd.DataFrame(
            {
                "open_time": [context.decision_time],
                "open": [np.nan],
                "close": [np.nan],
                "quote_volume": [np.nan],
            }
        )
        bars[symbol] = pd.concat([frame, future], ignore_index=True)
    changed = SimpleNamespace(**{**vars(context), "bars": bars})
    assert STRATEGY.build_strategy().target_weights(changed, seed=20260801) == expected


def test_under_history_member_and_noneligible_bars_cannot_enter() -> None:
    context = _market_context()
    bars = dict(context.bars)
    bars["NEWCOINUSDT"] = next(iter(bars.values())).iloc[-20:].copy()
    bars["OUTSIDERUSDT"] = next(iter(bars.values())).copy()
    changed = SimpleNamespace(
        **{
            **vars(context),
            "bars": bars,
            "eligible_symbols": (*context.eligible_symbols, "NEWCOINUSDT"),
        }
    )
    weights = STRATEGY.build_strategy().target_weights(changed, seed=20260801)
    _assert_balanced_pivot(dict(weights))
    assert "NEWCOINUSDT" not in weights
    assert "OUTSIDERUSDT" not in weights


def test_funding_and_input_order_are_invariant() -> None:
    context = _market_context()
    expected = STRATEGY.build_strategy().target_weights(context, seed=1)
    funding = context.funding.copy()
    funding["funding_rate"] *= -1000.0
    bars = {
        symbol: context.bars[symbol].iloc[::-1].copy()
        for symbol in reversed(context.eligible_symbols)
    }
    changed = SimpleNamespace(
        **{
            **vars(context),
            "bars": bars,
            "eligible_symbols": tuple(reversed(context.eligible_symbols)),
            "funding": funding,
        }
    )
    assert STRATEGY.build_strategy().target_weights(changed, seed=999999) == expected


def test_insufficient_breadth_requests_flat() -> None:
    assert (
        STRATEGY.build_strategy().target_weights(_market_context(symbol_count=11), seed=20260801)
        == {}
    )


def test_insufficient_scheduled_breadth_captures_one_empty_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[dict[str, float]] = []

    def capture(scores: dict[str, float]) -> dict[str, float]:
        captured.append(scores)
        return scores

    monkeypatch.setattr(STRATEGY, "score_boundary", capture)
    assert (
        STRATEGY.build_strategy().target_weights(_market_context(symbol_count=11), seed=20260801)
        == {}
    )
    assert captured == [{}]


def test_duplicate_or_invalid_past_bar_fails_closed() -> None:
    context = _market_context()
    symbol = context.eligible_symbols[0]
    bars = dict(context.bars)
    bars[symbol] = pd.concat([bars[symbol], bars[symbol].iloc[[-1]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        STRATEGY.build_strategy().target_weights(
            SimpleNamespace(**{**vars(context), "bars": bars}), seed=20260801
        )

    bars = dict(context.bars)
    bars[symbol] = bars[symbol].copy()
    bars[symbol].loc[bars[symbol].index[-2], "quote_volume"] = -1.0
    with pytest.raises(ValueError, match="nonnegative"):
        STRATEGY.build_strategy().target_weights(
            SimpleNamespace(**{**vars(context), "bars": bars}), seed=20260801
        )


def test_frozen_config_and_neighbors_match_executable_config() -> None:
    center = STRATEGY.StrategyConfig()
    center.validate()
    frozen = json.loads((TEAM_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    assert frozen["strategy"] == dataclasses.asdict(center)
    neighbors = json.loads((TEAM_DIR / "parameter_neighborhood.json").read_text(encoding="utf-8"))
    assert neighbors["center_parameters"] == dataclasses.asdict(center)
    axes: dict[str, list[object]] = {}
    for neighbor in neighbors["neighbors"]:
        dataclasses.replace(center, **{neighbor["axis"]: neighbor["value"]}).validate()
        axes.setdefault(neighbor["axis"], []).append(neighbor["value"])
    assert len(neighbors["neighbors"]) == 12
    assert all(len(values) == 2 for values in axes.values())


def test_a7_and_pivot_a5_manifest_identities_are_exact() -> None:
    authority = json.loads((TEAM_DIR / "a7_execution_authority.json").read_text(encoding="utf-8"))
    assert authority["candidate_id"] == "t10-dac-core-v1"
    assert authority["family_id"] == "t10-defensive-anchor-convergence-v1"
    assert authority["status"] == "pivot_01_prospective_identity_draft"
    assert authority["pure_crypto_report"]["violations"] == 0
    manifest = json.loads(
        (
            TEAM_DIR / "score-adapters/t10-dac-core-v1.score-adapter-manifest.template.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["hook"] == "strategy.score_boundary"
    assert manifest["capture_boundary"] == (
        "candidate-declared-post-transform-pre-selection-weight-cap-risk"
    )
    assert manifest["schedule_utc"] == {
        "anchor_timestamp_utc": "1970-01-01T00:00:00Z",
        "interval_hours": 24,
    }
    assert manifest["label"]["holding_horizon_hours"] == 24
    assert manifest["label"]["minimum_pairs"] == 240


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"decision_interval_hours": 10}, "multiple"),
        ({"tail_horizon_bars": 50}, "strictly increasing"),
        ({"selection_count_per_side": 3}, "gross exposure"),
        ({"minimum_scored_symbols": 4}, "overlapping sleeves"),
        ({"maximum_abs_one_bar_return": 1.0}, "thresholds"),
    ],
)
def test_invalid_configuration_is_rejected(override: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        dataclasses.replace(STRATEGY.StrategyConfig(), **override).validate()
