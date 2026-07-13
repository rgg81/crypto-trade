from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from crypto_trade.tournament.data import point_in_time_top40
from crypto_trade.tournament.engine import (
    EvaluatorConfig,
    evaluate_base_and_double_cost,
    evaluate_targets,
    generate_targets,
)
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN, DecisionContext
from crypto_trade.tournament.runner import _copy_team_source_bundle, source_bundle_fingerprint
from crypto_trade.tournament.top40 import HARD_COMPLIANCE_CHECKS

TEAM_DIR = Path(__file__).resolve().parent
ROOT = TEAM_DIR.parents[3]
STRATEGY_PATH = TEAM_DIR / "strategy.py"
CONFIG_PATH = TEAM_DIR / "frozen_config.json"
LOCK_PATH = TEAM_DIR / "uv.lock"
SEED = 20260713
SYMBOLS = ("BTCUSDT",) + tuple(f"A{index:02d}USDT" for index in range(23))


def _anchor() -> pd.Timestamp:
    return pd.Timestamp(year=2020, month=2, day=3, tz="UTC")


def _decision(index: int = 67) -> pd.Timestamp:
    return _anchor() + index * pd.Timedelta(hours=72)


def _load_strategy(name: str = "team_08_strategy_test") -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, STRATEGY_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def strategy_module() -> ModuleType:
    return _load_strategy()


def _bars(
    module: ModuleType,
    decision_time: pd.Timestamp,
    *,
    symbols: tuple[str, ...] = SYMBOLS,
    future_intervals: int = 0,
) -> dict[str, pd.DataFrame]:
    endpoints = pd.date_range(
        decision_time - 252 * pd.Timedelta(hours=8),
        decision_time + future_intervals * pd.Timedelta(hours=8),
        freq=pd.Timedelta(hours=8),
    )
    sample = np.arange(len(endpoints) - 1, dtype=np.float64)
    btc_returns = 0.004 * np.sin(sample * 0.41) + 0.002 * np.cos(sample * 0.13)
    output: dict[str, pd.DataFrame] = {}
    for index, symbol in enumerate(symbols):
        if symbol == "BTCUSDT":
            returns = btc_returns
        else:
            beta = 0.4 + (index % 6) * 0.35
            residual = 0.0025 * np.sin(sample * (0.17 + 0.003 * index) + index)
            returns = beta * btc_returns + residual
        closes = 100.0 * np.exp(np.r_[0.0, np.cumsum(returns)])
        output[symbol] = pd.DataFrame(
            {
                "open_time": endpoints - pd.Timedelta(hours=8),
                "open": closes,
                "close": closes,
                "quote_volume": np.full(len(endpoints), 1.0e9),
            }
        )
    return output


def _funding(
    decision_time: pd.Timestamp,
    *,
    symbols: tuple[str, ...] = SYMBOLS,
    rates: dict[str, float] | None = None,
    future_intervals: int = 0,
) -> pd.DataFrame:
    times = pd.date_range(
        decision_time - pd.Timedelta(days=90),
        decision_time + future_intervals * pd.Timedelta(hours=8),
        freq=pd.Timedelta(hours=8),
    )
    rows: list[dict[str, object]] = []
    midpoint = (len(symbols) - 1) / 2.0
    for index, symbol in enumerate(symbols):
        rate = rates[symbol] if rates is not None else (index - midpoint) * 1.0e-5
        rows.extend(
            {
                "funding_time": timestamp,
                "symbol": symbol,
                "funding_rate": rate,
                "mark_price": 100.0,
            }
            for timestamp in times
        )
    return pd.DataFrame(rows).sort_values(["funding_time", "symbol"]).reset_index(drop=True)


def _context(
    module: ModuleType,
    decision_time: pd.Timestamp | None = None,
    *,
    symbols: tuple[str, ...] = SYMBOLS,
    rates: dict[str, float] | None = None,
    future_intervals: int = 0,
) -> DecisionContext:
    timestamp = decision_time if decision_time is not None else _decision()
    return DecisionContext(
        decision_time=timestamp,
        bars=_bars(module, timestamp, symbols=symbols, future_intervals=future_intervals),
        funding=_funding(
            timestamp,
            symbols=symbols,
            rates=rates,
            future_intervals=future_intervals,
        ),
        auxiliary={},
        eligible_symbols=symbols,
    )


def _master_frames(
    module: ModuleType, decision_time: pd.Timestamp
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    bars = (
        pd.concat(
            [
                frame.assign(symbol=symbol)
                for symbol, frame in _bars(module, decision_time, future_intervals=4).items()
            ],
            ignore_index=True,
        )
        .sort_values(["open_time", "symbol"])
        .reset_index(drop=True)
    )
    funding = _funding(decision_time, future_intervals=4)
    membership = pd.DataFrame(
        {
            "reconstitution_time": [_anchor()] * len(SYMBOLS),
            "symbol": list(SYMBOLS),
            "liquidity_rank": np.arange(1, len(SYMBOLS) + 1),
            "trailing_quote_volume": np.arange(len(SYMBOLS), 0, -1, dtype=float),
        }
    )
    return bars, funding, membership


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _frame_sha(frame: pd.DataFrame) -> str:
    return _sha(frame.to_csv(index=True, lineterminator="\n").encode("utf-8"))


def _simple_market() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    start = _decision()
    times = pd.date_range(start - pd.Timedelta(hours=24), periods=7, freq=pd.Timedelta(hours=8))
    rows: list[dict[str, object]] = []
    for symbol, opens in {
        "LONGUSDT": (98.0, 99.0, 99.5, 100.0, 110.0, 120.0, 121.0),
        "SHORTUSDT": (98.0, 99.0, 99.5, 100.0, 110.0, 120.0, 121.0),
    }.items():
        for timestamp, price in zip(times, opens, strict=True):
            rows.append(
                {
                    "open_time": timestamp,
                    "symbol": symbol,
                    "open": price,
                    "close": price + 0.5,
                    "quote_volume": 1.0e9,
                }
            )
    bars = pd.DataFrame(rows)
    membership = pd.DataFrame(
        {
            "reconstitution_time": [start - pd.Timedelta(days=7)] * 2,
            "symbol": ["LONGUSDT", "SHORTUSDT"],
            "liquidity_rank": [1, 2],
            "trailing_quote_volume": [2.0, 1.0],
        }
    )
    funding = pd.DataFrame(
        {
            "funding_time": [start + pd.Timedelta(hours=8)] * 2,
            "symbol": ["LONGUSDT", "SHORTUSDT"],
            "funding_rate": [0.001, 0.001],
            "mark_price": [110.0, 110.0],
        }
    )
    evaluation_times = times[3:6]
    marks = pd.DataFrame(
        [
            {"mark_time": timestamp, "symbol": symbol, "mark_price": price}
            for timestamp, price_index in zip(evaluation_times, range(3, 6), strict=True)
            for symbol, price in (
                ("LONGUSDT", (98.0, 99.0, 99.5, 100.0, 110.0, 120.0, 121.0)[price_index]),
                ("SHORTUSDT", (98.0, 99.0, 99.5, 100.0, 110.0, 120.0, 121.0)[price_index]),
            )
        ]
    )
    targets = pd.DataFrame(
        {
            "LONGUSDT": [0.10, 0.05, 0.0],
            "SHORTUSDT": [-0.10, -0.05, 0.0],
        },
        index=evaluation_times,
    )
    return bars, funding, membership, marks, targets


def test_factory_returns_fresh_strategy_and_none_hold_semantics(
    strategy_module: ModuleType,
) -> None:
    first = strategy_module.build_strategy()
    second = strategy_module.build_strategy()
    assert first is not second
    context = _context(strategy_module)
    weights = first.target_weights(context, seed=SEED)
    assert weights and first._longs and first._shorts
    off_clock = DecisionContext(
        decision_time=context.decision_time + pd.Timedelta(hours=8),
        bars=context.bars,
        funding=context.funding,
        auxiliary={},
        eligible_symbols=context.eligible_symbols,
    )
    before = (first._longs, first._shorts)
    assert first.target_weights(off_clock, seed=SEED) is None
    assert (first._longs, first._shorts) == before


def test_exact_actual_interval_funding_and_strict_boundary(strategy_module: ModuleType) -> None:
    timestamp = _decision()
    event_times = [timestamp - pd.Timedelta(days=90)]
    step = 0
    while event_times[-1] < timestamp:
        event_times.append(event_times[-1] + pd.Timedelta(hours=4 if step % 2 == 0 else 12))
        step += 1
    event_times = [value for value in event_times if value < timestamp]
    rates = 0.0002 + np.arange(len(event_times), dtype=float) * 1.0e-8
    frame = pd.DataFrame(
        {
            "funding_time": event_times + [timestamp],
            "symbol": ["XUSDT"] * (len(event_times) + 1),
            "funding_rate": list(rates) + [-10.0],
        }
    )
    actual = strategy_module._funding_score(frame, "XUSDT", timestamp)
    times = pd.DatetimeIndex(event_times)
    intervals = np.r_[
        np.nan,
        (times[1:] - times[:-1]).total_seconds().to_numpy(dtype=float) / 3600.0,
    ]
    window = times >= timestamp - pd.Timedelta(days=84)
    window_times = times[window]
    window_rates = rates[window]
    window_intervals = intervals[window]
    age_hours = (timestamp - window_times).total_seconds().to_numpy() / 3600.0
    carry = []
    for half_life in (7.0, 28.0):
        decay = np.exp2(-age_hours / (24.0 * half_life))
        carry.append(24.0 * np.dot(decay, window_rates) / np.dot(decay, window_intervals))
    coverage = window_times >= timestamp - pd.Timedelta(days=28)
    coverage_age = (timestamp - window_times[coverage]).total_seconds().to_numpy() / 3600.0
    persistence_decay = np.exp2(-coverage_age / (24.0 * 28.0))
    persistence_duration = persistence_decay * window_intervals[coverage]
    persistence = (
        np.dot(persistence_duration, np.sign(window_rates[coverage])) / persistence_duration.sum()
    )
    expected = min(carry) * max(0.0, (abs(persistence) - 0.25) / 0.75)
    assert actual == pytest.approx(expected, rel=1.0e-13, abs=1.0e-16)
    without_predecessor = frame.loc[frame["funding_time"] >= timestamp - pd.Timedelta(days=84)]
    assert strategy_module._funding_score(without_predecessor, "XUSDT", timestamp) is None


def test_price_windows_quarantines_and_ddof(strategy_module: ModuleType) -> None:
    timestamp = _decision()
    frame = _bars(strategy_module, timestamp, symbols=("BTCUSDT",))["BTCUSDT"]
    features = strategy_module._price_features(frame, timestamp, require_btc=True)
    assert features is not None
    closes = frame["close"].to_numpy(dtype=float)
    returns = np.diff(np.log(closes))
    assert features.sigma_28d == pytest.approx(float(np.std(returns[-84:], ddof=1)))

    accelerated = frame.copy()
    base_returns = np.diff(np.log(accelerated["close"].to_numpy(dtype=float)))
    base_returns[-21:] *= 20.0
    accelerated["close"] = 100.0 * np.exp(np.r_[0.0, np.cumsum(base_returns)])
    assert strategy_module._price_features(accelerated, timestamp, require_btc=False) is None
    assert strategy_module._price_features(accelerated, timestamp, require_btc=True) is not None


def test_projection_is_bounded_dollar_and_beta_neutral(strategy_module: ModuleType) -> None:
    context = _context(strategy_module)
    weights = strategy_module.build_strategy().target_weights(context, seed=SEED)
    assert weights and any(value > 0.0 for value in weights.values())
    assert any(value < 0.0 for value in weights.values())
    assert all(np.isfinite(list(weights.values())))
    assert sum(abs(value) for value in weights.values()) == pytest.approx(0.80, abs=2.0e-9)
    assert sum(weights.values()) == pytest.approx(0.0, abs=2.0e-9)
    assert max(abs(value) for value in weights.values()) <= 0.075 + 1.0e-10
    btc = strategy_module._price_features(
        context.bars["BTCUSDT"], context.decision_time, require_btc=True
    )
    assert btc is not None
    beta_notional = 0.0
    for symbol, weight in weights.items():
        price = strategy_module._price_features(
            context.bars[symbol], context.decision_time, require_btc=symbol == "BTCUSDT"
        )
        assert price is not None
        beta = strategy_module._beta(price.returns, btc.returns)
        assert beta is not None
        beta_notional += weight * beta
    assert beta_notional == pytest.approx(0.0, abs=2.0e-9)


def test_buffer_retains_rank_crossing_and_flat_clears_state(
    strategy_module: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: list[tuple[set[str], set[str]]] = []

    def equal_solution(longs: set[str], shorts: set[str], _candidates: object) -> dict[str, float]:
        captured.append((set(longs), set(shorts)))
        return {**{symbol: 0.04 for symbol in longs}, **{symbol: -0.04 for symbol in shorts}}

    monkeypatch.setattr(strategy_module, "_solve_sleeves", equal_solution)
    first_rates = {symbol: (index - 11.5) * 1.0e-5 for index, symbol in enumerate(SYMBOLS)}
    second_order = list(SYMBOLS)
    second_order[9], second_order[10] = second_order[10], second_order[9]
    second_rates = {symbol: (index - 11.5) * 1.0e-5 for index, symbol in enumerate(second_order)}
    strategy = strategy_module.build_strategy()
    first_context = _context(strategy_module, rates=first_rates)
    assert strategy.target_weights(first_context, seed=SEED)
    crossing = SYMBOLS[9]
    second_context = _context(
        strategy_module,
        first_context.decision_time + pd.Timedelta(hours=72),
        rates=second_rates,
    )
    assert strategy.target_weights(second_context, seed=SEED)
    assert crossing in captured[1][0]
    too_small = tuple(SYMBOLS[:19])
    flat_context = _context(
        strategy_module,
        second_context.decision_time + pd.Timedelta(hours=72),
        symbols=too_small,
    )
    assert strategy.target_weights(flat_context, seed=SEED) == {}
    assert strategy._longs == () and strategy._shorts == ()


def test_projection_fallback_expands_symmetric_pairs(
    strategy_module: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    sizes: list[tuple[int, int]] = []

    def delayed_solution(longs: set[str], shorts: set[str], _candidates: object):
        sizes.append((len(longs), len(shorts)))
        if len(sizes) < 3:
            return None
        scale = 0.4 / len(longs)
        return {**{symbol: scale for symbol in longs}, **{symbol: -scale for symbol in shorts}}

    monkeypatch.setattr(strategy_module, "_solve_sleeves", delayed_solution)
    output = strategy_module.build_strategy().target_weights(_context(strategy_module), seed=SEED)
    assert output
    assert sizes == [(10, 10), (11, 11), (12, 12)]


def test_bad_non_btc_data_is_local_but_bad_btc_flattens(strategy_module: ModuleType) -> None:
    context = _context(strategy_module)
    local_symbol = "A05USDT"
    bad_local_bars = dict(context.bars)
    damaged = bad_local_bars[local_symbol].copy()
    damaged.loc[damaged.index[-1], "close"] = np.inf
    bad_local_bars[local_symbol] = damaged
    local_context = DecisionContext(
        context.decision_time,
        bad_local_bars,
        context.funding,
        {},
        context.eligible_symbols,
    )
    local_weights = strategy_module.build_strategy().target_weights(local_context, seed=SEED)
    assert local_weights and local_symbol not in local_weights
    assert all(np.isfinite(list(local_weights.values())))

    bad_funding = context.funding.copy()
    mask = (bad_funding["symbol"] == "A06USDT") & (
        bad_funding["funding_time"] < context.decision_time
    )
    bad_funding.loc[mask, "funding_rate"] = np.nan
    funding_context = DecisionContext(
        context.decision_time, context.bars, bad_funding, {}, context.eligible_symbols
    )
    funding_weights = strategy_module.build_strategy().target_weights(funding_context, seed=SEED)
    assert funding_weights and "A06USDT" not in funding_weights

    duplicated = dict(context.bars)
    duplicated["A07USDT"] = pd.concat(
        [duplicated["A07USDT"], duplicated["A07USDT"].iloc[[-1]]], ignore_index=True
    )
    duplicate_context = DecisionContext(
        context.decision_time, duplicated, context.funding, {}, context.eligible_symbols
    )
    duplicate_weights = strategy_module.build_strategy().target_weights(
        duplicate_context, seed=SEED
    )
    assert duplicate_weights and "A07USDT" not in duplicate_weights

    gapped = dict(context.bars)
    gapped["A08USDT"] = gapped["A08USDT"].drop(gapped["A08USDT"].index[-2])
    gap_context = DecisionContext(
        context.decision_time, gapped, context.funding, {}, context.eligible_symbols
    )
    gap_weights = strategy_module.build_strategy().target_weights(gap_context, seed=SEED)
    assert gap_weights and "A08USDT" not in gap_weights

    bad_btc_bars = dict(context.bars)
    btc = bad_btc_bars["BTCUSDT"].copy()
    btc.loc[btc.index[-1], "close"] = np.nan
    bad_btc_bars["BTCUSDT"] = btc
    btc_context = DecisionContext(
        context.decision_time, bad_btc_bars, context.funding, {}, context.eligible_symbols
    )
    assert strategy_module.build_strategy().target_weights(btc_context, seed=SEED) == {}


def test_truncation_corrupt_future_and_append_invariance(strategy_module: ModuleType) -> None:
    timestamp = _decision()
    bars, funding, membership = _master_frames(strategy_module, timestamp)

    def targets(bar_frame: pd.DataFrame, funding_frame: pd.DataFrame) -> pd.DataFrame:
        return generate_targets(
            strategy_module.build_strategy(),
            bar_frame,
            funding_frame,
            membership,
            [timestamp],
            seed=SEED,
        )

    baseline = targets(bars, funding)
    truncated = targets(
        bars.loc[bars["open_time"] <= timestamp].copy(),
        funding.loc[funding["funding_time"] < timestamp].copy(),
    )
    pdt.assert_frame_equal(baseline, truncated, check_exact=True)

    corrupted_bars = bars.copy()
    future_bars = corrupted_bars["open_time"] >= timestamp
    corrupted_bars.loc[future_bars, ["open", "close", "quote_volume"]] *= 7.0
    corrupted_funding = funding.copy()
    corrupted_funding.loc[corrupted_funding["funding_time"] >= timestamp, "funding_rate"] = 9.0
    pdt.assert_frame_equal(baseline, targets(corrupted_bars, corrupted_funding), check_exact=True)

    appended_bars = bars.copy()
    tail = bars.loc[bars["open_time"] == bars["open_time"].max()].copy()
    tail["open_time"] += pd.Timedelta(hours=8)
    tail[["open", "close"]] *= 1.3
    appended_bars = pd.concat([appended_bars, tail], ignore_index=True)
    appended_funding = pd.concat(
        [
            funding,
            funding.loc[funding["funding_time"] == funding["funding_time"].max()].assign(
                funding_time=lambda frame: frame["funding_time"] + pd.Timedelta(hours=8)
            ),
        ],
        ignore_index=True,
    )
    pdt.assert_frame_equal(baseline, targets(appended_bars, appended_funding), check_exact=True)


def test_point_in_time_membership_uses_completed_prior_dates_only() -> None:
    reconstitution = _anchor()
    dates = pd.date_range(reconstitution - pd.Timedelta(days=30), periods=31, freq="D")
    rows: list[dict[str, object]] = []
    for date in dates:
        for symbol, daily_volume in (("AAAUSDT", 300.0), ("BBBUSDT", 200.0)):
            if date == reconstitution:
                daily_volume = 1.0 if symbol == "AAAUSDT" else 1.0e12
            for hour in (0, 8, 16):
                rows.append(
                    {
                        "open_time": date + pd.Timedelta(hours=hour),
                        "symbol": symbol,
                        "quote_volume": daily_volume / 3.0,
                    }
                )
    bars = pd.DataFrame(rows)
    metadata = pd.DataFrame(
        {
            "symbol": ["AAAUSDT", "BBBUSDT"],
            "contract_type": ["PERPETUAL", "PERPETUAL"],
            "quote_asset": ["USDT", "USDT"],
            "margin_asset": ["USDT", "USDT"],
            "is_crypto": [True, True],
            "onboard_date": [reconstitution - pd.Timedelta(days=100)] * 2,
            "delivery_date": [pd.NaT, pd.NaT],
        }
    )
    membership = point_in_time_top40(
        bars, metadata, [reconstitution], top_n=2, trailing_days=30, min_history_days=30
    )
    assert membership.sort_values("liquidity_rank")["symbol"].tolist() == [
        "AAAUSDT",
        "BBBUSDT",
    ]


def test_next_open_actual_funding_signs_costs_and_long_short_reconciliation() -> None:
    bars, funding, membership, marks, targets = _simple_market()
    result = evaluate_targets(bars, funding, membership, targets, mark_prices=marks)
    start = targets.index[0]
    entry = result.events[
        (result.events["event_type"] == "trade") & (result.events["timestamp"] == start)
    ]
    assert set(entry["price"]) == {100.0}
    assert (entry["fee"] > 0.0).all() and (entry["slippage"] > 0.0).all()
    assert result.returns["fees"].sum() > 0.0
    assert result.returns["slippage"].sum() > 0.0
    assert (result.returns["turnover"] > 0.0).sum() == 3
    funding_events = result.events[result.events["event_type"] == "funding"]
    long_cashflow = funding_events.loc[funding_events["symbol"] == "LONGUSDT", "cashflow"].sum()
    short_cashflow = funding_events.loc[funding_events["symbol"] == "SHORTUSDT", "cashflow"].sum()
    assert long_cashflow < 0.0 < short_cashflow
    assert set(funding_events["phase"]) == {"before_rebalance"}
    assert result.returns["long_price_pnl"].sum() > 0.0
    assert result.returns["short_price_pnl"].sum() < 0.0
    assert np.allclose(
        result.returns["price_pnl"],
        result.returns["long_price_pnl"] + result.returns["short_price_pnl"],
    )
    assert np.allclose(
        result.returns["funding_pnl"],
        result.returns["long_funding_pnl"] + result.returns["short_funding_pnl"],
    )


def test_fresh_double_cost_run_doubles_execution_cost_rates() -> None:
    bars, funding, membership, marks, targets = _simple_market()
    base, stressed = evaluate_base_and_double_cost(
        bars, funding, membership, targets, mark_prices=marks
    )
    assert base is not stressed and base.events is not stressed.events
    base_first = base.events[base.events["event_type"] == "trade"].iloc[0]
    stressed_first = stressed.events[stressed.events["event_type"] == "trade"].iloc[0]
    assert stressed_first["fee"] == pytest.approx(2.0 * base_first["fee"])
    assert stressed_first["slippage"] == pytest.approx(2.0 * base_first["slippage"])
    assert stressed.returns["net_return"].sum() < base.returns["net_return"].sum()


def test_participation_limited_fills_and_delist_residual_settlement() -> None:
    start = _decision()
    times = pd.date_range(start - pd.Timedelta(hours=24), periods=6, freq=pd.Timedelta(hours=8))
    rows = []
    for timestamp in times[:5]:
        rows.append(
            {
                "open_time": timestamp,
                "symbol": "DELISTUSDT",
                "open": 100.0,
                "close": 90.0,
                "quote_volume": 1000.0 if timestamp == start + pd.Timedelta(hours=8) else 1.0e9,
            }
        )
    for timestamp in times:
        rows.append(
            {
                "open_time": timestamp,
                "symbol": "KEEPUSDT",
                "open": 100.0,
                "close": 100.0,
                "quote_volume": 1.0e9,
            }
        )
    bars = pd.DataFrame(rows)
    membership = pd.DataFrame(
        {
            "reconstitution_time": [start - pd.Timedelta(days=7)] * 2,
            "symbol": ["DELISTUSDT", "KEEPUSDT"],
            "liquidity_rank": [1, 2],
            "trailing_quote_volume": [2.0, 1.0],
        }
    )
    funding = pd.DataFrame(columns=["funding_time", "symbol", "funding_rate", "mark_price"])
    marks = pd.DataFrame(
        [
            {"mark_time": timestamp, "symbol": symbol, "mark_price": 100.0}
            for timestamp in times[3:6]
            for symbol in ("DELISTUSDT", "KEEPUSDT")
            if not (symbol == "DELISTUSDT" and timestamp > start + pd.Timedelta(hours=8))
        ]
    )
    targets = pd.DataFrame(
        {"DELISTUSDT": [0.10, 0.0], "KEEPUSDT": [0.0, 0.0]},
        index=[start, start + pd.Timedelta(hours=16)],
    )
    result = evaluate_targets(bars, funding, membership, targets, mark_prices=marks)
    forced = result.events[result.events["event_type"] == "forced_exit"]
    settlements = result.events[result.events["event_type"] == "conservative_settlement"]
    assert len(forced) == 1 and forced.iloc[0]["fee"] > 0.0 and forced.iloc[0]["slippage"] > 0.0
    assert len(settlements) == 1 and settlements.iloc[0]["cashflow"] < 0.0
    assert result.returns["forced_exit_unfilled_notional"].sum() > 0.0
    assert result.returns["conservative_settlement_loss"].sum() > 0.0

    low_volume = bars.copy()
    low_volume.loc[low_volume["open_time"] < start, "quote_volume"] = 1000.0
    limited = evaluate_targets(low_volume, funding, membership, targets, mark_prices=marks)
    assert limited.returns.iloc[0]["unfilled_notional"] > 0.0
    assert limited.returns.iloc[0]["gross_exposure"] < 0.01


def test_fail_closed_nonfinite_caps_duplicates_missing_prices_and_empty_outputs(
    strategy_module: ModuleType,
) -> None:
    bars, funding, membership, marks, targets = _simple_market()
    nonfinite = targets.copy()
    nonfinite.iloc[0, 0] = np.inf
    with pytest.raises(ValueError, match="non-finite"):
        evaluate_targets(bars, funding, membership, nonfinite, mark_prices=marks)
    over_cap = targets.copy()
    over_cap.iloc[0, 0] = 0.11
    with pytest.raises(ValueError, match="symbol exposure"):
        evaluate_targets(bars, funding, membership, over_cap, mark_prices=marks)
    with pytest.raises(ValueError, match="gross exposure"):
        evaluate_targets(
            bars,
            funding,
            membership,
            targets,
            mark_prices=marks,
            config=EvaluatorConfig(max_gross_exposure=0.15, max_abs_net_exposure=0.15),
        )
    net_breach = targets.copy()
    net_breach.iloc[0] = [0.10, 0.0]
    with pytest.raises(ValueError, match="net exposure"):
        evaluate_targets(
            bars,
            funding,
            membership,
            net_breach,
            mark_prices=marks,
            config=EvaluatorConfig(max_abs_net_exposure=0.05),
        )
    ineligible = targets.copy()
    ineligible["OUTSIDERUSDT"] = [0.01, 0.0, 0.0]
    with pytest.raises(ValueError, match="ineligible target"):
        evaluate_targets(bars, funding, membership, ineligible, mark_prices=marks)
    duplicate = pd.concat([targets.iloc[[0]], targets.iloc[[0]], targets.iloc[1:]])
    with pytest.raises(ValueError, match="duplicate timestamps"):
        evaluate_targets(bars, funding, membership, duplicate, mark_prices=marks)
    duplicate_bars = pd.concat([bars, bars.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate .* bars"):
        evaluate_targets(duplicate_bars, funding, membership, targets, mark_prices=marks)
    duplicate_funding = pd.concat([funding, funding.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate .* rows"):
        evaluate_targets(bars, duplicate_funding, membership, targets, mark_prices=marks)
    missing_marks = marks.loc[marks["symbol"] != "LONGUSDT"]
    with pytest.raises(ValueError, match="missing current mark for eligible"):
        evaluate_targets(bars, funding, membership, targets, mark_prices=missing_marks)

    no_targets = generate_targets(
        strategy_module.build_strategy(), bars, funding, membership, [], seed=SEED
    )
    assert no_targets.empty
    empty_result = evaluate_targets(bars, funding, membership, pd.DataFrame(), mark_prices=marks)
    assert empty_result.returns.empty and empty_result.positions.empty and empty_result.events.empty


def test_explicit_empty_mapping_and_false_instruction_have_distinct_semantics() -> None:
    bars, funding, membership, marks, targets = _simple_market()
    sparse = targets.copy()
    sparse[REBALANCE_INSTRUCTION_COLUMN] = [True, False, True]
    held = evaluate_targets(bars, funding, membership, sparse, mark_prices=marks)
    explicit = targets.copy()
    explicit.iloc[1] = 0.0
    flattened = evaluate_targets(bars, funding, membership, explicit, mark_prices=marks)
    middle = targets.index[1]
    held_middle = held.events[
        (held.events["event_type"] == "trade") & (held.events["timestamp"] == middle)
    ]
    flat_middle = flattened.events[
        (flattened.events["event_type"] == "trade") & (flattened.events["timestamp"] == middle)
    ]
    assert held_middle.empty
    assert not flat_middle.empty


def test_fixed_sleeve_and_execution_floors_in_both_synthetic_windows() -> None:
    start = _decision()
    evaluation_times = pd.date_range(start, periods=12, freq=pd.Timedelta(hours=8))
    all_times = pd.date_range(
        start - pd.Timedelta(hours=24), periods=15, freq=pd.Timedelta(hours=8)
    )
    symbols = ("L1USDT", "L2USDT", "S1USDT", "S2USDT")
    bars = pd.DataFrame(
        [
            {
                "open_time": timestamp,
                "symbol": symbol,
                "open": 100.0,
                "close": 100.0,
                "quote_volume": 1.0e9,
            }
            for timestamp in all_times
            for symbol in symbols
        ]
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": [start - pd.Timedelta(days=7)] * 4,
            "symbol": list(symbols),
            "liquidity_rank": [1, 2, 3, 4],
            "trailing_quote_volume": [4.0, 3.0, 2.0, 1.0],
        }
    )
    marks = pd.DataFrame(
        [
            {"mark_time": timestamp, "symbol": symbol, "mark_price": 100.0}
            for timestamp in evaluation_times
            for symbol in symbols
        ]
    )
    funding = pd.DataFrame(columns=["funding_time", "symbol", "funding_rate", "mark_price"])
    target_rows = []
    for index, _timestamp in enumerate(evaluation_times):
        if index in (0, 6):
            target_rows.append([0.10, 0.0, -0.10, 0.0])
        elif index in (3, 9):
            target_rows.append([0.0, 0.10, 0.0, -0.10])
        else:
            target_rows.append([0.10, 0.0, -0.10, 0.0] if index < 6 else [0.10, 0.0, -0.10, 0.0])
    targets = pd.DataFrame(target_rows, columns=symbols, index=evaluation_times)
    result = evaluate_targets(bars, funding, membership, targets, mark_prices=marks)
    for window_times in (evaluation_times[:6], evaluation_times[6:]):
        returns = result.returns.loc[window_times]
        assert (returns["long_exposure"] >= 0.01).mean() >= 0.05
        assert (returns["short_exposure"] >= 0.01).mean() >= 0.05
        assert returns["long_exposure"].mean() >= 0.005
        assert returns["short_exposure"].mean() >= 0.005
        events = result.events[
            result.events["timestamp"].isin(window_times)
            & result.events["event_type"].isin(["trade", "risk_reduction", "forced_exit"])
        ]
        assert events.loc[events["notional"] > 0.0, "notional"].sum() >= 1000.0
        assert -events.loc[events["notional"] < 0.0, "notional"].sum() >= 1000.0


def clean_process_payload() -> dict[str, str]:
    module = _load_strategy(f"team_08_clean_{os.getpid()}")
    context = _context(module)
    weights = module.build_strategy().target_weights(context, seed=SEED)
    assert weights
    target_bytes = json.dumps(weights, sort_keys=True, separators=(",", ":")).encode("utf-8")
    bars, funding, membership, marks, targets = _simple_market()
    result = evaluate_targets(bars, funding, membership, targets, mark_prices=marks)
    manifest = {
        "config": _sha(CONFIG_PATH.read_bytes()),
        "lock": _sha(LOCK_PATH.read_bytes()),
        "strategy": _sha(STRATEGY_PATH.read_bytes()),
    }
    manifest_bytes = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "manifest": _sha(manifest_bytes),
        "positions": _frame_sha(result.positions),
        "returns": _frame_sha(result.returns),
        "targets": _sha(target_bytes),
    }


def test_clean_process_target_position_return_and_manifest_hashes() -> None:
    code = (
        "import json; from test_team_08_strategy import clean_process_payload; "
        "print(json.dumps(clean_process_payload(), sort_keys=True))"
    )
    environment = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONPATH": os.pathsep.join((str(ROOT / "src"), str(TEAM_DIR))),
    }
    first = subprocess.check_output(
        [sys.executable, "-c", code], cwd=ROOT, env=environment, text=True
    ).strip()
    second = subprocess.check_output(
        [sys.executable, "-c", code], cwd=ROOT, env=environment, text=True
    ).strip()
    assert first == second
    payload = json.loads(first)
    assert set(payload) == {"manifest", "positions", "returns", "targets"}
    assert all(len(value) == 64 for value in payload.values())


def test_source_scanner_runtime_bundle_and_neutral_imports(tmp_path: Path) -> None:
    tree = ast.parse(STRATEGY_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "math",
        "numpy",
        "pandas",
        "scipy",
        "crypto_trade",
    }
    fingerprint, entries = source_bundle_fingerprint(
        ROOT, "team-08", STRATEGY_PATH.relative_to(ROOT)
    )
    assert len(fingerprint) == 64
    assert any(entry["path"] == "strategy.py" for entry in entries)
    destination = tmp_path / "runtime"
    staged_fingerprint = _copy_team_source_bundle(TEAM_DIR, destination)
    assert staged_fingerprint == fingerprint
    staged = sorted(path.name for path in destination.iterdir())
    assert staged == ["frozen_config.json", "strategy.py", "test_team_08_strategy.py"]
    runtime_module_path = destination / "strategy.py"
    spec = importlib.util.spec_from_file_location("team_08_runtime", runtime_module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert module.build_strategy() is not module.build_strategy()


def test_dependency_lock_config_and_compliance_are_frozen_and_exact() -> None:
    assert LOCK_PATH.read_bytes() == (ROOT / "uv.lock").read_bytes()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    assert config["seed"] == SEED
    assert config["phase0_record"] == "012727865acecad6ea0c3327745359820b8e45c6"
    assert config["common_freeze_commit"] == "48df09341f02eba7a3469abd1ccda6649a4ef0ba"
    compliance = json.loads((TEAM_DIR / "compliance.json").read_text(encoding="utf-8"))
    assert set(compliance) == set(HARD_COMPLIANCE_CHECKS)
    assert all(compliance.values())
