"""Independent QE tests for team-04's Funding Receiver Aftershock strategy."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament._strategy_worker import _HistoryBuffer
from crypto_trade.tournament.data import point_in_time_top40
from crypto_trade.tournament.engine import (
    EvaluatorConfig,
    _validate_weight_limits,
    evaluate_base_and_double_cost,
    evaluate_targets,
    generate_targets,
)
from crypto_trade.tournament.protocol import DecisionContext

TEAM_DIR = Path(__file__).resolve().parent
STRATEGY_PATH = TEAM_DIR / "strategy.py"
SPEC = importlib.util.spec_from_file_location("team04_funding_receiver_aftershock", STRATEGY_PATH)
assert SPEC is not None and SPEC.loader is not None
t04 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = t04
SPEC.loader.exec_module(t04)


def _utc_date(year: int, month: int, day: int) -> pd.Timestamp:
    return pd.Timestamp(year=year, month=month, day=day, tz="UTC")


def _mechanism_inputs(
    *, include_btc: bool = True, neutral_count: int = 4
) -> tuple[DecisionContext, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    response_open = _utc_date(2023, 6, 1)
    decision_time = response_open + pd.Timedelta(hours=8)
    longs = ["L1USDT", "L2USDT"]
    shorts = ["S1USDT", "S2USDT"]
    neutrals = [f"N{index:02d}USDT" for index in range(1, neutral_count + 1)]
    symbols = longs + shorts + neutrals + (["BTCUSDT"] if include_btc else [])
    betas = {
        "L1USDT": 0.90,
        "L2USDT": 1.00,
        "S1USDT": 0.95,
        "S2USDT": 1.05,
        "BTCUSDT": 1.00,
        **{symbol: 1.00 for symbol in neutrals},
    }
    shocks = {
        "L1USDT": 0.012,
        "L2USDT": 0.010,
        "S1USDT": -0.011,
        "S2USDT": -0.009,
    }
    funding_rates = {
        "L1USDT": -0.001,
        "L2USDT": -0.001,
        "S1USDT": 0.001,
        "S2USDT": 0.001,
    }

    history_times = pd.date_range(
        end=response_open - pd.Timedelta(hours=8), periods=300, freq="8h", tz="UTC"
    )
    phase = np.arange(len(history_times), dtype=float)
    market_returns = 0.0020 * np.sin(phase * 0.37) + 0.0010 * np.cos(phase * 0.11)
    market_response = 0.0013
    bars_by_symbol: dict[str, pd.DataFrame] = {}
    flat_bars: list[pd.DataFrame] = []
    for symbol in symbols:
        beta = betas[symbol]
        historical = beta * market_returns
        response_return = beta * market_response + shocks.get(symbol, 0.0)
        open_times = history_times.append(
            pd.DatetimeIndex(
                [
                    response_open,
                    decision_time,
                    decision_time + pd.Timedelta(hours=8),
                ]
            )
        )
        log_returns = np.concatenate([historical, [response_return, 0.40 + beta, -0.30 - beta]])
        frame = pd.DataFrame(
            {
                "open_time": open_times,
                "symbol": symbol,
                "open": 100.0,
                "close": 100.0 * np.exp(log_returns),
                "quote_volume": 10_000_000.0,
            }
        )
        bars_by_symbol[symbol] = frame.copy()
        flat_bars.append(frame)

    historical_funding_times = pd.date_range(
        end=response_open - pd.Timedelta(hours=8), periods=90, freq="8h", tz="UTC"
    )
    funding_parts: list[pd.DataFrame] = []
    for symbol in symbols:
        times = historical_funding_times.append(pd.DatetimeIndex([response_open]))
        rates = np.zeros(len(times), dtype=float)
        rates[-1] = funding_rates.get(symbol, 0.0)
        funding_parts.append(
            pd.DataFrame(
                {
                    "funding_time": times,
                    "symbol": symbol,
                    "funding_rate": rates,
                    "mark_price": 100.0,
                }
            )
        )
    funding = pd.concat(funding_parts, ignore_index=True).sort_values(
        ["funding_time", "symbol"], kind="mergesort"
    )
    eligible = tuple(sorted(symbols))
    context = DecisionContext(
        decision_time=decision_time,
        bars=bars_by_symbol,
        funding=funding,
        auxiliary={},
        eligible_symbols=eligible,
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": _utc_date(2023, 5, 29),
            "symbol": list(eligible),
            "liquidity_rank": np.arange(1, len(eligible) + 1),
            "trailing_quote_volume": 1_000_000.0,
        }
    )
    return context, pd.concat(flat_bars, ignore_index=True), funding, membership, decision_time


def _empty_funding() -> pd.DataFrame:
    return pd.DataFrame(columns=["funding_time", "symbol", "funding_rate", "mark_price"])


def test_canonical_worker_history_is_recognized_for_bounded_slicing() -> None:
    bars = _HistoryBuffer(
        ("open_time", "open", "close"),
        ("datetime64[ns, UTC]", "float64", "float64"),
        frozenset({"open_time"}),
    )
    bars.append(
        (
            (_utc_date(2023, 1, 1), 100.0, 101.0),
            (_utc_date(2023, 1, 1) + pd.Timedelta(hours=8), 101.0, 102.0),
        )
    )
    frame = bars.frame()

    assert t04._is_canonical_history_view(frame, "open_time", ("open", "close"))


def _evaluation_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    start = _utc_date(2023, 6, 5)
    times = pd.date_range(start=start - pd.Timedelta(hours=24), periods=6, freq="8h", tz="UTC")
    prices = {
        "AUSDT": [100.0, 100.0, 100.0, 100.0, 110.0, 105.0],
        "BUSDT": [100.0, 100.0, 100.0, 100.0, 90.0, 95.0],
    }
    rows: list[dict[str, object]] = []
    marks: list[dict[str, object]] = []
    for symbol, symbol_prices in prices.items():
        for timestamp, price in zip(times, symbol_prices, strict=True):
            rows.append(
                {
                    "open_time": timestamp,
                    "symbol": symbol,
                    "open": price,
                    "close": price,
                    "quote_volume": 10_000_000.0,
                }
            )
            marks.append({"mark_time": timestamp, "symbol": symbol, "mark_price": price})
    membership = pd.DataFrame(
        {
            "reconstitution_time": [start, start],
            "symbol": ["AUSDT", "BUSDT"],
            "liquidity_rank": [1, 2],
            "trailing_quote_volume": [1_000_000.0, 900_000.0],
        }
    )
    targets = pd.DataFrame(
        [
            {"AUSDT": 0.05, "BUSDT": -0.05},
            {"AUSDT": -0.05, "BUSDT": 0.05},
            {"AUSDT": 0.0, "BUSDT": 0.0},
        ],
        index=pd.DatetimeIndex(times[-3:]),
    )
    return pd.DataFrame(rows), pd.DataFrame(marks), membership, targets


def _hash_frame(frame: pd.DataFrame) -> str:
    canonical = frame.copy()
    canonical.index = canonical.index.map(str)
    canonical.columns = canonical.columns.map(str)
    canonical = canonical.sort_index().sort_index(axis=1)
    payload = canonical.to_json(
        orient="split", date_format="iso", date_unit="ns", double_precision=15
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def clean_process_payload() -> dict[str, str]:
    context, flat_bars, funding, membership, decision_time = _mechanism_inputs()
    weights = t04.build_strategy().target_weights(context, seed=t04.STRATEGY_SEED)
    targets = generate_targets(
        t04.build_strategy(),
        flat_bars,
        funding,
        membership,
        [decision_time],
        seed=t04.STRATEGY_SEED,
    )
    eval_bars, marks, eval_membership, eval_targets = _evaluation_inputs()
    result = evaluate_targets(
        eval_bars,
        _empty_funding(),
        eval_membership,
        eval_targets,
        mark_prices=marks,
    )
    hashes = {
        "weight_hash": hashlib.sha256(
            json.dumps(weights, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "target_hash": _hash_frame(targets),
        "position_hash": _hash_frame(result.positions),
        "return_hash": _hash_frame(result.returns),
    }
    hashes["manifest_hash"] = hashlib.sha256(
        json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return hashes


def test_factory_is_fresh_and_seed_is_pinned() -> None:
    first = t04.build_strategy()
    second = t04.build_strategy()
    assert first is not second
    context, *_ = _mechanism_inputs()
    with pytest.raises(ValueError, match="requires seed"):
        first.target_weights(context, seed=1)


def test_exact_receiver_direction_pairing_and_risk_caps() -> None:
    context, *_ = _mechanism_inputs()
    weights = t04.build_strategy().target_weights(context, seed=t04.STRATEGY_SEED)
    assert weights == {
        "L1USDT": 0.08,
        "L2USDT": 0.08,
        "S1USDT": -0.08,
        "S2USDT": -0.08,
    }
    assert math.isclose(sum(abs(value) for value in weights.values()), 0.32)
    assert math.isclose(sum(weights.values()), 0.0, abs_tol=1e-15)
    assert max(abs(value) for value in weights.values()) == 0.08
    assert all(math.isfinite(value) for value in weights.values())


def test_latest_unfinished_event_supersedes_older_match() -> None:
    context, *_ = _mechanism_inputs()
    newer = pd.DataFrame(
        {
            "funding_time": [context.decision_time - pd.Timedelta(hours=1)] * 4,
            "symbol": ["L1USDT", "L2USDT", "S1USDT", "S2USDT"],
            "funding_rate": [-0.001, -0.001, 0.001, 0.001],
            "mark_price": 100.0,
        }
    )
    changed = DecisionContext(
        decision_time=context.decision_time,
        bars=context.bars,
        funding=pd.concat([context.funding, newer], ignore_index=True),
        auxiliary={},
        eligible_symbols=context.eligible_symbols,
    )
    assert t04.build_strategy().target_weights(changed, seed=t04.STRATEGY_SEED) == {}


def test_funding_at_decision_is_strictly_unavailable() -> None:
    context, *_ = _mechanism_inputs()
    equality_rows = pd.DataFrame(
        {
            "funding_time": [context.decision_time] * 4,
            "symbol": ["L1USDT", "L2USDT", "S1USDT", "S2USDT"],
            "funding_rate": [99.0, 99.0, -99.0, -99.0],
            "mark_price": 100.0,
        }
    )
    changed = DecisionContext(
        decision_time=context.decision_time,
        bars=context.bars,
        funding=pd.concat([context.funding, equality_rows], ignore_index=True),
        auxiliary={},
        eligible_symbols=context.eligible_symbols,
    )
    expected = t04.build_strategy().target_weights(context, seed=t04.STRATEGY_SEED)
    actual = t04.build_strategy().target_weights(changed, seed=t04.STRATEGY_SEED)
    assert actual == expected


def test_subsecond_jitter_matches_but_one_hour_off_grid_waits() -> None:
    context, *_ = _mechanism_inputs()
    response_open = context.decision_time - pd.Timedelta(hours=8)
    one_symbol = ("L1USDT",)
    base = context.funding[context.funding["symbol"] == "L1USDT"].copy()
    base.loc[base["funding_time"] == response_open, "funding_time"] += pd.Timedelta(
        milliseconds=500
    )
    matched = t04._matched_funding_groups(base, one_symbol, context.decision_time, response_open)
    assert tuple(matched) == one_symbol
    base.loc[base["funding_time"].dt.floor("h") == response_open, "funding_time"] = (
        response_open + pd.Timedelta(hours=1)
    )
    assert t04._matched_funding_groups(base, one_symbol, context.decision_time, response_open) == {}


def test_all_hour_funding_fallback_and_minimum_are_exact() -> None:
    context, *_ = _mechanism_inputs()
    symbol = "L1USDT"
    response_open = context.decision_time - pd.Timedelta(hours=8)
    history_times = pd.date_range(
        end=response_open - pd.Timedelta(hours=1), periods=60, freq="1h", tz="UTC"
    )
    frame = pd.DataFrame(
        {
            "funding_time": history_times.append(pd.DatetimeIndex([response_open])),
            "symbol": symbol,
            "funding_rate": np.concatenate([np.zeros(60), [-0.001]]),
            "mark_price": 100.0,
        }
    )
    transformed = {
        symbol: t04._TransformedBars(
            history=pd.Series(
                np.arange(120, dtype=float),
                index=pd.date_range(
                    end=response_open - pd.Timedelta(hours=8), periods=120, freq="8h"
                ),
            ),
            response=0.0,
        )
    }
    scores = t04._funding_z_scores(
        frame, (symbol,), transformed, context.decision_time, response_open
    )
    assert scores[symbol] == -6.0
    insufficient = pd.concat([frame.iloc[:59], frame.iloc[[-1]]], ignore_index=True)
    assert (
        t04._funding_z_scores(
            insufficient, (symbol,), transformed, context.decision_time, response_open
        )
        == {}
    )


def test_btc_unavailable_uses_ten_name_past_only_market_fallback() -> None:
    context, *_ = _mechanism_inputs(include_btc=False, neutral_count=7)
    weights = t04.build_strategy().target_weights(context, seed=t04.STRATEGY_SEED)
    assert set(weights) == {"L1USDT", "L2USDT", "S1USDT", "S2USDT"}
    assert weights["L1USDT"] > 0.0 and weights["S1USDT"] < 0.0


def test_market_fallback_and_cross_section_minima_fail_flat() -> None:
    nine_name_context, *_ = _mechanism_inputs(include_btc=False, neutral_count=5)
    assert t04.build_strategy().target_weights(nine_name_context, seed=t04.STRATEGY_SEED) == {}
    context, *_ = _mechanism_inputs()
    eligible = context.eligible_symbols[:7]
    too_small = DecisionContext(
        context.decision_time,
        {symbol: context.bars[symbol] for symbol in eligible},
        context.funding,
        {},
        eligible,
    )
    assert t04.build_strategy().target_weights(too_small, seed=t04.STRATEGY_SEED) == {}


def test_missing_response_bar_closes_signal_instead_of_staling() -> None:
    context, *_ = _mechanism_inputs()
    response_open = context.decision_time - pd.Timedelta(hours=8)
    bars = dict(context.bars)
    bars["L1USDT"] = bars["L1USDT"].loc[bars["L1USDT"]["open_time"] != response_open]
    changed = DecisionContext(
        context.decision_time, bars, context.funding, {}, context.eligible_symbols
    )
    weights = t04.build_strategy().target_weights(changed, seed=t04.STRATEGY_SEED)
    assert weights == {}


def test_pair_sort_is_strength_then_gap_then_lexicographic_and_disjoint() -> None:
    active = {
        "L1": (1, 4.0, 1.00),
        "L2": (1, 4.0, 1.00),
        "L3": (1, 1.0, -1.00),
        "S1": (-1, 4.0, 1.00),
        "S2": (-1, 4.0, 1.00),
        "S3": (-1, 10.0, 2.00),
    }
    assert t04._select_pairs(active) == [("L1", "S1"), ("L2", "S2")]


def test_truncation_corrupt_future_and_append_invariance() -> None:
    _, bars, funding, membership, decision_time = _mechanism_inputs()
    decisions = [decision_time]
    full = generate_targets(
        t04.build_strategy(), bars, funding, membership, decisions, seed=t04.STRATEGY_SEED
    )
    truncated_bars = bars[bars["open_time"] <= decision_time].copy()
    truncated_funding = funding[funding["funding_time"] < decision_time].copy()
    truncated = generate_targets(
        t04.build_strategy(),
        truncated_bars,
        truncated_funding,
        membership,
        decisions,
        seed=t04.STRATEGY_SEED,
    )
    pd.testing.assert_frame_equal(full, truncated, check_exact=True)

    corrupted_bars = bars.copy()
    future_bar_mask = corrupted_bars["open_time"] >= decision_time
    corrupted_bars.loc[future_bar_mask, ["open", "close", "quote_volume"]] *= 123.0
    future_funding = pd.DataFrame(
        {
            "funding_time": [decision_time + pd.Timedelta(hours=1)],
            "symbol": ["L1USDT"],
            "funding_rate": [0.99],
            "mark_price": [999.0],
        }
    )
    corrupted = generate_targets(
        t04.build_strategy(),
        corrupted_bars,
        pd.concat([funding, future_funding], ignore_index=True),
        membership,
        decisions,
        seed=t04.STRATEGY_SEED,
    )
    pd.testing.assert_frame_equal(full, corrupted, check_exact=True)

    appended_rows = bars[bars["open_time"] == decision_time].copy()
    appended_rows["open_time"] += pd.Timedelta(days=30)
    appended_membership = pd.concat(
        [
            membership,
            membership.assign(
                reconstitution_time=membership["reconstitution_time"] + pd.Timedelta(days=35)
            ),
        ],
        ignore_index=True,
    )
    appended = generate_targets(
        t04.build_strategy(),
        pd.concat([bars, appended_rows], ignore_index=True),
        funding,
        appended_membership,
        decisions,
        seed=t04.STRATEGY_SEED,
    )
    pd.testing.assert_frame_equal(full, appended, check_exact=True)


def test_future_rows_in_direct_context_are_never_read() -> None:
    context, *_ = _mechanism_inputs()
    expected = t04.build_strategy().target_weights(context, seed=t04.STRATEGY_SEED)
    bars = {symbol: frame.copy() for symbol, frame in context.bars.items()}
    for frame in bars.values():
        future = frame["open_time"] >= context.decision_time
        frame.loc[future, "close"] = np.inf
        frame.loc[future, "open"] = np.nan
    funding = context.funding.copy()
    funding = pd.concat(
        [
            funding,
            pd.DataFrame(
                {
                    "funding_time": [context.decision_time + pd.Timedelta(seconds=1)],
                    "symbol": ["L1USDT"],
                    "funding_rate": [np.inf],
                    "mark_price": [np.nan],
                }
            ),
        ],
        ignore_index=True,
    )
    broad = DecisionContext(context.decision_time, bars, funding, {}, context.eligible_symbols)
    assert t04.build_strategy().target_weights(broad, seed=t04.STRATEGY_SEED) == expected


def test_point_in_time_top40_uses_only_complete_prior_dates() -> None:
    reconstitution = _utc_date(2023, 6, 5)
    rows: list[dict[str, object]] = []
    for day in pd.date_range(end=reconstitution - pd.Timedelta(days=1), periods=30, freq="D"):
        for hour in (0, 8, 16):
            for symbol, volume in (("AUSDT", 200.0), ("BUSDT", 100.0)):
                rows.append(
                    {
                        "open_time": day + pd.Timedelta(hours=hour),
                        "symbol": symbol,
                        "quote_volume": volume,
                    }
                )
    for hour in (0, 8, 16):
        rows.append(
            {
                "open_time": reconstitution + pd.Timedelta(hours=hour),
                "symbol": "BUSDT",
                "quote_volume": 1e15,
            }
        )
    metadata = pd.DataFrame(
        {
            "symbol": ["AUSDT", "BUSDT"],
            "contract_type": ["PERPETUAL", "PERPETUAL"],
            "quote_asset": ["USDT", "USDT"],
            "margin_asset": ["USDT", "USDT"],
            "is_crypto": [True, True],
            "onboard_date": [_utc_date(2020, 1, 1)] * 2,
            "delivery_date": [pd.NaT, pd.NaT],
        }
    )
    result = point_in_time_top40(pd.DataFrame(rows), metadata, [reconstitution], top_n=1)
    assert result["symbol"].tolist() == ["AUSDT"]


def test_ineligible_target_is_rejected() -> None:
    bars, marks, membership, targets = _evaluation_inputs()
    membership = membership[membership["symbol"] == "AUSDT"]
    with pytest.raises(ValueError, match="ineligible target"):
        evaluate_targets(bars, _empty_funding(), membership, targets, mark_prices=marks)


def test_decision_from_closed_bar_fills_only_at_hidden_next_open() -> None:
    bars, marks, membership, targets = _evaluation_inputs()
    result = evaluate_targets(bars, _empty_funding(), membership, targets, mark_prices=marks)
    fill_time = targets.index[0]
    first_trades = result.events[
        (result.events["event_type"] == "trade") & (result.events["timestamp"] == fill_time)
    ]
    assert set(first_trades["symbol"]) == {"AUSDT", "BUSDT"}
    assert set(first_trades["price"]) == {100.0}
    assert not (result.events["timestamp"] == fill_time - pd.Timedelta(hours=8)).any()


def test_positive_funding_debits_longs_credits_shorts_at_actual_timestamp() -> None:
    bars, marks, membership, targets = _evaluation_inputs()
    boundary = targets.index[1]
    funding = pd.DataFrame(
        {
            "funding_time": [boundary, boundary],
            "symbol": ["AUSDT", "BUSDT"],
            "funding_rate": [0.001, 0.001],
            "mark_price": [110.0, 90.0],
        }
    )
    result = evaluate_targets(bars, funding, membership, targets, mark_prices=marks)
    events = result.events[result.events["event_type"] == "funding"].set_index("symbol")
    assert set(events["timestamp"]) == {boundary}
    assert set(events["phase"]) == {"before_rebalance"}
    assert events.loc["AUSDT", "cashflow"] < 0.0
    assert events.loc["BUSDT", "cashflow"] > 0.0
    assert math.isclose(
        float(events["cashflow"].sum()),
        float(result.returns.loc[boundary, "funding_pnl"] * result.returns.iloc[0]["equity"]),
        rel_tol=0.0,
        abs_tol=1e-12,
    )


def test_entry_rebalance_exit_costs_and_long_short_pnl_reconcile() -> None:
    bars, marks, membership, targets = _evaluation_inputs()
    result = evaluate_targets(bars, _empty_funding(), membership, targets, mark_prices=marks)
    trades = result.events[result.events["event_type"] == "trade"]
    assert set(targets.index).issubset(set(trades["timestamp"]))
    assert (trades["fee"] > 0.0).all()
    assert (trades["slippage"] > 0.0).all()
    assert result.returns.iloc[0]["long_price_pnl"] > 0.0
    assert result.returns.iloc[0]["short_price_pnl"] > 0.0
    np.testing.assert_allclose(
        result.returns["price_pnl"],
        result.returns["long_price_pnl"] + result.returns["short_price_pnl"],
        rtol=0.0,
        atol=1e-15,
    )


def test_double_cost_is_fresh_and_uses_doubled_execution_rates_not_an_shortcut() -> None:
    bars, marks, membership, targets = _evaluation_inputs()
    boundary = targets.index[1]
    funding = pd.DataFrame(
        {
            "funding_time": [boundary],
            "symbol": ["AUSDT"],
            "funding_rate": [0.001],
            "mark_price": [110.0],
        }
    )
    base, stressed = evaluate_base_and_double_cost(
        bars, funding, membership, targets, mark_prices=marks
    )
    assert base is not stressed
    assert stressed.returns["fees"].sum() > base.returns["fees"].sum()
    assert stressed.returns["slippage"].sum() > base.returns["slippage"].sum()
    stressed_trades = stressed.events[stressed.events["event_type"] == "trade"]
    np.testing.assert_allclose(
        stressed_trades["fee"] / stressed_trades["notional"].abs(),
        10.0 / 10_000.0,
        rtol=0.0,
        atol=1e-15,
    )
    np.testing.assert_allclose(
        stressed_trades["slippage"] / stressed_trades["notional"].abs(),
        5.0 / 10_000.0,
        rtol=0.0,
        atol=1e-15,
    )
    base_funding = base.events.loc[base.events["event_type"] == "funding", "cashflow"]
    stressed_funding = stressed.events.loc[stressed.events["event_type"] == "funding", "cashflow"]
    np.testing.assert_allclose(stressed_funding, base_funding, rtol=0.0, atol=0.0)


def test_participation_limit_carries_unfilled_target_gap() -> None:
    bars, marks, membership, targets = _evaluation_inputs()
    pre_start = targets.index[0]
    bars.loc[bars["open_time"] < pre_start, "quote_volume"] = 1_000.0
    result = evaluate_targets(bars, _empty_funding(), membership, targets, mark_prices=marks)
    first = result.returns.loc[pre_start]
    assert first["unfilled_notional"] > 0.0
    first_trades = result.events[
        (result.events["event_type"] == "trade") & (result.events["timestamp"] == pre_start)
    ]
    assert math.isclose(float(first_trades["notional"].abs().max()), 3.0)


def test_forced_delist_exit_shares_capacity_charges_cost_and_haircuts_residual() -> None:
    start = _utc_date(2023, 6, 5)
    rows: list[dict[str, object]] = []
    marks: list[dict[str, object]] = []
    for timestamp in pd.date_range(end=start - pd.Timedelta(hours=8), periods=3, freq="8h"):
        rows.append(
            {
                "open_time": timestamp,
                "symbol": "AUSDT",
                "open": 100.0,
                "close": 100.0,
                "quote_volume": 10_000_000.0,
            }
        )
        marks.append({"mark_time": timestamp, "symbol": "AUSDT", "mark_price": 100.0})
    rows.extend(
        [
            {
                "open_time": start,
                "symbol": "AUSDT",
                "open": 100.0,
                "close": 110.0,
                "quote_volume": 1_000_000.0,
            },
            {
                "open_time": start + pd.Timedelta(hours=8),
                "symbol": "BUSDT",
                "open": 100.0,
                "close": 100.0,
                "quote_volume": 1_000_000.0,
            },
        ]
    )
    marks.extend(
        [
            {"mark_time": start, "symbol": "AUSDT", "mark_price": 100.0},
            {
                "mark_time": start + pd.Timedelta(hours=8),
                "symbol": "BUSDT",
                "mark_price": 100.0,
            },
        ]
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": [start, start],
            "symbol": ["AUSDT", "BUSDT"],
            "liquidity_rank": [1, 2],
            "trailing_quote_volume": [1e6, 1e6],
        }
    )
    targets = pd.DataFrame(
        [{"AUSDT": 0.005}, {"AUSDT": 0.0}],
        index=pd.DatetimeIndex([start, start + pd.Timedelta(hours=8)]),
    )
    result = evaluate_targets(
        pd.DataFrame(rows),
        _empty_funding(),
        membership,
        targets,
        mark_prices=pd.DataFrame(marks),
    )
    forced = result.events[result.events["event_type"] == "forced_exit"]
    settlement = result.events[result.events["event_type"] == "conservative_settlement"]
    assert len(forced) == 1 and len(settlement) == 1
    assert math.isclose(abs(float(forced.iloc[0]["notional"])), 500.0, rel_tol=1e-6)
    assert forced.iloc[0]["fee"] > 0.0 and forced.iloc[0]["slippage"] > 0.0
    assert settlement.iloc[0]["cashflow"] < 0.0
    assert result.returns.iloc[0]["conservative_settlement_notional"] > 0.0


@pytest.mark.parametrize(
    "bad_weights, message",
    [
        ({"AUSDT": 1.01, "BUSDT": 0.0}, "gross exposure"),
        ({"AUSDT": 0.11, "BUSDT": -0.01}, "symbol exposure"),
        ({"AUSDT": np.nan, "BUSDT": 0.0}, "non-finite target"),
        ({"AUSDT": np.inf, "BUSDT": 0.0}, "non-finite target"),
    ],
)
def test_evaluator_rejects_risk_caps_and_infinite_targets(
    bad_weights: dict[str, float], message: str
) -> None:
    bars, marks, membership, targets = _evaluation_inputs()
    targets.loc[targets.index[0], :] = pd.Series(bad_weights)
    with pytest.raises(ValueError, match=message):
        evaluate_targets(bars, _empty_funding(), membership, targets, mark_prices=marks)


def test_evaluator_rejects_absolute_net_exposure_over_cap() -> None:
    with pytest.raises(ValueError, match="net exposure"):
        _validate_weight_limits(
            pd.Series({"AUSDT": 0.10, "BUSDT": 0.10, "CUSDT": 0.10}),
            EvaluatorConfig(),
            _utc_date(2023, 6, 5),
        )


@pytest.mark.parametrize("bad_weight", [np.nan, np.inf])
def test_generate_targets_rejects_nonfinite_strategy_mapping(bad_weight: float) -> None:
    _, bars, funding, membership, decision_time = _mechanism_inputs()

    class BadStrategy:
        def target_weights(self, context: DecisionContext, *, seed: int) -> dict[str, float]:
            del context, seed
            return {"L1USDT": bad_weight}

    with pytest.raises(ValueError, match="non-finite target weight"):
        generate_targets(
            BadStrategy(),
            bars,
            funding,
            membership,
            [decision_time],
            seed=t04.STRATEGY_SEED,
        )


def test_nonfinite_past_inputs_flatten_and_never_emit_nonfinite_weights() -> None:
    context, *_ = _mechanism_inputs()
    funding = context.funding.copy()
    latest_mask = (funding["symbol"] == "L1USDT") & (
        funding["funding_time"] == context.decision_time - pd.Timedelta(hours=8)
    )
    funding.loc[latest_mask, "funding_rate"] = np.nan
    changed = DecisionContext(
        context.decision_time, context.bars, funding, {}, context.eligible_symbols
    )
    weights = t04.build_strategy().target_weights(changed, seed=t04.STRATEGY_SEED)
    assert weights == {}
    assert all(math.isfinite(value) for value in weights.values())


def test_missing_mark_duplicate_bars_and_duplicate_targets_fail_closed() -> None:
    bars, marks, membership, targets = _evaluation_inputs()
    first_time = targets.index[0]
    missing_mark = marks[~((marks["mark_time"] == first_time) & (marks["symbol"] == "AUSDT"))]
    with pytest.raises(ValueError, match="missing current mark"):
        evaluate_targets(bars, _empty_funding(), membership, targets, mark_prices=missing_mark)
    duplicate_bars = pd.concat([bars, bars.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        evaluate_targets(duplicate_bars, _empty_funding(), membership, targets, mark_prices=marks)
    duplicate_targets = pd.concat([targets, targets.iloc[[0]]]).sort_index()
    with pytest.raises(ValueError, match="duplicate timestamps"):
        evaluate_targets(bars, _empty_funding(), membership, duplicate_targets, mark_prices=marks)


def test_empty_decisions_and_empty_strategy_outputs_are_explicit() -> None:
    _, bars, funding, membership, _ = _mechanism_inputs()
    assert generate_targets(
        t04.build_strategy(), bars, funding, membership, [], seed=t04.STRATEGY_SEED
    ).empty
    empty_context = DecisionContext(
        _utc_date(2023, 1, 1), {}, _empty_funding(), {}, ()
    )
    assert t04.build_strategy().target_weights(empty_context, seed=t04.STRATEGY_SEED) == {}


def test_strategy_has_no_network_or_evaluator_side_effect_surface() -> None:
    source = STRATEGY_PATH.read_text(encoding="utf-8")
    forbidden = (
        "requests",
        "urllib",
        "socket",
        "http://",
        "https://",
        "evaluate_targets",
        "subprocess",
        "open(",
    )
    assert not any(token in source for token in forbidden)


def test_clean_process_reproduces_target_position_return_and_manifest_hashes() -> None:
    expected = clean_process_payload()
    code = (
        "import json,sys;"
        f"sys.path.insert(0,{str(TEAM_DIR)!r});"
        "from test_team_04_strategy import clean_process_payload;"
        "print(json.dumps(clean_process_payload(),sort_keys=True))"
    )
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    actual = json.loads(
        subprocess.check_output(
            [sys.executable, "-c", code],
            cwd=Path(__file__).resolve().parents[4],
            env=environment,
            text=True,
        )
    )
    assert actual == expected
