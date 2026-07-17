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
    "team10_pivot02_strategy_under_test",
    TEAM_DIR / "strategy.py",
)
assert SPEC is not None and SPEC.loader is not None
STRATEGY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = STRATEGY
SPEC.loader.exec_module(STRATEGY)


def _market_context(*, periods: int = 96, symbol_count: int = 20) -> SimpleNamespace:
    decision_time = pd.Timestamp("2022-02-10T00:00:00Z")
    open_times = pd.date_range(
        end=decision_time - pd.Timedelta(hours=8),
        periods=periods,
        freq="8h",
    )
    step = np.arange(periods, dtype=float)
    symbols = [f"COIN{index:02d}USDT" for index in range(symbol_count)]
    bars: dict[str, pd.DataFrame] = {}
    for index, symbol in enumerate(symbols):
        phase = 2.0 * np.pi * index / max(symbol_count, 1)
        log_return = 0.00025 + 0.00035 * np.sin(step / 11.0 + phase)
        close = np.exp(np.log(100.0 + index) + np.cumsum(log_return))
        quote_volume = 2_000_000.0 * (1.0 + 0.08 * np.cos(step / 9.0 + phase))
        bars[symbol] = pd.DataFrame(
            {
                "open_time": open_times,
                "open": np.r_[close[0], close[:-1]],
                "close": close,
                "quote_volume": quote_volume,
            }
        )

    funding_times = pd.date_range(
        end=decision_time - pd.Timedelta(hours=8),
        periods=42,
        freq="8h",
    )
    funding_rows: list[dict[str, object]] = []
    for index, symbol in enumerate(symbols):
        center = (index - (symbol_count - 1) / 2.0) * 0.00001
        for event_index, funding_time in enumerate(funding_times):
            rate = center + 0.000001 * np.sin(event_index / 4.0)
            funding_rows.append(
                {
                    "funding_time": funding_time,
                    "funding_rate": rate,
                    "mark_price": 100.0 + index,
                    "symbol": symbol,
                }
            )
    return SimpleNamespace(
        auxiliary={},
        bars=bars,
        decision_time=decision_time,
        eligible_symbols=tuple(symbols),
        funding=pd.DataFrame(funding_rows),
    )


def _assert_balanced_final_pivot(weights: dict[str, float]) -> None:
    assert len(weights) == 8
    values = np.asarray(tuple(weights.values()), dtype=float)
    assert np.isfinite(values).all()
    assert sum(value > 0.0 for value in values) == 4
    assert sum(value < 0.0 for value in values) == 4
    assert np.abs(values).sum() == pytest.approx(0.12)
    assert values.sum() == pytest.approx(0.0, abs=1e-12)
    assert np.abs(values).max() == pytest.approx(0.015)


def _longs(weights: dict[str, float]) -> set[str]:
    return {symbol for symbol, weight in weights.items() if weight > 0.0}


def _shorts(weights: dict[str, float]) -> set[str]:
    return {symbol for symbol, weight in weights.items() if weight < 0.0}


def test_reference_pivot_is_finite_balanced_and_eligible() -> None:
    context = _market_context()
    weights = dict(STRATEGY.build_strategy().target_weights(context, seed=20260801))
    _assert_balanced_final_pivot(weights)
    assert set(weights) <= set(context.eligible_symbols)


def test_public_score_boundary_is_frozen_a5_identity() -> None:
    scores = {"BTCUSDT": 1.0, "ETHUSDT": -1.0}
    assert STRATEGY.score_boundary.__module__ == (
        "crypto_trade.tournament.score_adapter_protocol_v5"
    )
    assert STRATEGY.score_boundary(scores) is scores


def test_boundary_has_one_exact_literal_call_and_drives_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = (TEAM_DIR / "strategy.py").read_text(encoding="utf-8")
    assert source.count("captured_scores = score_boundary(scores)") == 1
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
    assert _longs(weights) == expected_longs
    assert _shorts(weights) == expected_shorts


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


def test_unchanged_weekly_sleeves_hold_instead_of_rebalancing() -> None:
    strategy = STRATEGY.build_strategy()
    context = _market_context()
    first = strategy.target_weights(context, seed=20260801)
    assert first is not None and first
    assert strategy.target_weights(context, seed=20260801) is None


def test_funding_pressure_direction_is_economic_and_not_invariant() -> None:
    context = _market_context()
    normal = dict(STRATEGY.build_strategy().target_weights(context, seed=20260801))
    inverted_funding = context.funding.copy()
    inverted_funding["funding_rate"] *= -1.0
    inverted = dict(
        STRATEGY.build_strategy().target_weights(
            SimpleNamespace(**{**vars(context), "funding": inverted_funding}),
            seed=20260801,
        )
    )
    assert _longs(normal) == _shorts(inverted)
    assert _shorts(normal) == _longs(inverted)


def test_stale_and_anomalous_funding_exclude_coin() -> None:
    context = _market_context()
    baseline = dict(STRATEGY.build_strategy().target_weights(context, seed=20260801))
    chosen = next(iter(baseline))

    stale_funding = context.funding.copy()
    selected = stale_funding["symbol"].eq(chosen)
    stale_funding.loc[selected, "funding_time"] -= pd.Timedelta(hours=48)
    stale = SimpleNamespace(**{**vars(context), "funding": stale_funding})
    assert chosen not in STRATEGY.build_strategy().target_weights(stale, seed=20260801)

    anomalous_funding = context.funding.copy()
    selected_index = anomalous_funding.index[anomalous_funding["symbol"].eq(chosen)][-1]
    anomalous_funding.loc[selected_index, "funding_rate"] = 0.02
    anomalous = SimpleNamespace(**{**vars(context), "funding": anomalous_funding})
    assert chosen not in STRATEGY.build_strategy().target_weights(anomalous, seed=20260801)


def test_price_quarantine_excludes_extreme_recent_coin() -> None:
    context = _market_context()
    baseline = STRATEGY.build_strategy().target_weights(context, seed=20260801)
    assert baseline
    chosen = next(iter(baseline))
    bars = dict(context.bars)
    bars[chosen] = bars[chosen].copy()
    bars[chosen].loc[bars[chosen].index[-1], "close"] *= 1.50
    changed = SimpleNamespace(**{**vars(context), "bars": bars})
    assert chosen not in STRATEGY.build_strategy().target_weights(changed, seed=20260801)


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


def test_corrupt_appended_future_bars_and_funding_are_invariant() -> None:
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
    future_funding = pd.DataFrame(
        {
            "funding_time": [context.decision_time + pd.Timedelta(hours=8)],
            "funding_rate": [np.nan],
            "mark_price": [np.nan],
            "symbol": [context.eligible_symbols[0]],
        }
    )
    changed = SimpleNamespace(
        **{
            **vars(context),
            "bars": bars,
            "funding": pd.concat([context.funding, future_funding], ignore_index=True),
        }
    )
    assert STRATEGY.build_strategy().target_weights(changed, seed=20260801) == expected


def test_pure_crypto_membership_is_upstream_and_noneligible_products_cannot_enter() -> None:
    context = _market_context()
    bars = dict(context.bars)
    funding = context.funding.copy()
    exemplar = next(iter(bars.values()))
    for product in ("USDCUSDT", "XAUUSDT", "SPXUSDT", "TESLAUSDT"):
        bars[product] = exemplar.copy()
        product_funding = funding.loc[funding["symbol"].eq(context.eligible_symbols[0])].copy()
        product_funding["symbol"] = product
        funding = pd.concat([funding, product_funding], ignore_index=True)
    changed = SimpleNamespace(**{**vars(context), "bars": bars, "funding": funding})
    weights = dict(STRATEGY.build_strategy().target_weights(changed, seed=20260801))
    _assert_balanced_final_pivot(weights)
    assert set(weights) <= set(context.eligible_symbols)
    assert not set(weights) & {"USDCUSDT", "XAUUSDT", "SPXUSDT", "TESLAUSDT"}


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
    _assert_balanced_final_pivot(dict(weights))
    assert "NEWCOINUSDT" not in weights
    assert "OUTSIDERUSDT" not in weights


def test_input_order_and_seed_are_invariant() -> None:
    context = _market_context()
    expected = STRATEGY.build_strategy().target_weights(context, seed=1)
    bars = {
        symbol: context.bars[symbol].iloc[::-1].copy()
        for symbol in reversed(context.eligible_symbols)
    }
    changed = SimpleNamespace(
        **{
            **vars(context),
            "bars": bars,
            "eligible_symbols": tuple(reversed(context.eligible_symbols)),
            "funding": context.funding.iloc[::-1].copy(),
        }
    )
    assert STRATEGY.build_strategy().target_weights(changed, seed=999999) == expected


def test_insufficient_breadth_requests_flat_and_captures_one_empty_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[dict[str, float]] = []

    def capture(scores: dict[str, float]) -> dict[str, float]:
        captured.append(scores)
        return scores

    monkeypatch.setattr(STRATEGY, "score_boundary", capture)
    assert (
        STRATEGY.build_strategy().target_weights(_market_context(symbol_count=9), seed=20260801)
        == {}
    )
    assert captured == [{}]


def test_duplicate_or_invalid_past_inputs_fail_closed() -> None:
    context = _market_context()
    symbol = context.eligible_symbols[0]
    bars = dict(context.bars)
    bars[symbol] = pd.concat([bars[symbol], bars[symbol].iloc[[-1]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        STRATEGY.build_strategy().target_weights(
            SimpleNamespace(**{**vars(context), "bars": bars}), seed=20260801
        )

    funding = pd.concat([context.funding, context.funding.iloc[[-1]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate funding"):
        STRATEGY.build_strategy().target_weights(
            SimpleNamespace(**{**vars(context), "funding": funding}), seed=20260801
        )

    funding = context.funding.copy()
    funding.loc[funding.index[-1], "funding_rate"] = np.nan
    with pytest.raises(ValueError, match="finite"):
        STRATEGY.build_strategy().target_weights(
            SimpleNamespace(**{**vars(context), "funding": funding}), seed=20260801
        )


def test_frozen_config_matches_executable_and_neighbors_are_forbidden() -> None:
    center = STRATEGY.StrategyConfig()
    center.validate()
    frozen = json.loads((TEAM_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    assert frozen["strategy"] == dataclasses.asdict(center)
    neighborhood = json.loads(
        (TEAM_DIR / "parameter_neighborhood.json").read_text(encoding="utf-8")
    )
    assert neighborhood["candidate_id"] == "t10-fpu-core-v1"
    assert neighborhood["center_parameters"] == dataclasses.asdict(center)
    assert neighborhood["neighbors"] == []
    assert neighborhood["status"] == "final_pivot_neighbors_forbidden"


def test_a7_and_final_pivot_a5_manifest_identities_are_exact() -> None:
    authority = json.loads((TEAM_DIR / "a7_execution_authority.json").read_text(encoding="utf-8"))
    assert authority["candidate_id"] == "t10-fpu-core-v1"
    assert authority["family_id"] == "t10-funding-pressure-unwind-v1"
    assert authority["status"] == "pivot_02_final_prospective_identity_draft"
    assert authority["pure_crypto_report"]["violations"] == 0
    manifest = json.loads(
        (
            TEAM_DIR / "score-adapters/t10-fpu-core-v1.score-adapter-manifest.template.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["hook"] == "strategy.score_boundary"
    assert manifest["capture_boundary"] == (
        "candidate-declared-post-transform-pre-selection-weight-cap-risk"
    )
    assert manifest["schedule_utc"] == {
        "anchor_timestamp_utc": "1970-01-01T00:00:00Z",
        "interval_hours": 168,
    }
    assert manifest["label"]["holding_horizon_hours"] == 168
    assert manifest["label"]["minimum_pairs"] == 240


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"decision_interval_hours": 170}, "multiple"),
        ({"tail_horizon_bars": 50}, "strictly increasing"),
        ({"recent_funding_events": 13}, "cannot exceed"),
        ({"minimum_cross_section": 9}, "below"),
        ({"selection_count_per_side": 2}, "gross exposure"),
        ({"minimum_scored_symbols": 4}, "overlapping sleeves"),
        ({"maximum_abs_one_bar_return": 1.0}, "thresholds"),
    ],
)
def test_invalid_configuration_is_rejected(override: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        dataclasses.replace(STRATEGY.StrategyConfig(), **override).validate()
