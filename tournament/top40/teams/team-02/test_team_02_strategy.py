from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament.data import point_in_time_top40
from crypto_trade.tournament.engine import evaluate_base_and_double_cost
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN, DecisionContext

TEAM_DIR = Path(__file__).resolve().parent


@pytest.fixture(scope="module")
def strategy_module():
    path = TEAM_DIR / "strategy.py"
    spec = importlib.util.spec_from_file_location("team02_frozen_strategy", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _utc(year: int, month: int, day: int, hour: int = 0) -> pd.Timestamp:
    return pd.Timestamp(year=year, month=month, day=day, hour=hour, tz="UTC")


def _synthetic_market(
    *,
    asset_count: int = 15,
    history_periods: int = 650,
    future_periods: int = 8,
) -> tuple[tuple[str, ...], dict[str, pd.DataFrame], pd.Timestamp]:
    rng = np.random.default_rng(1702)
    total_returns = history_periods + future_periods
    symbols = tuple(f"S{index:02d}USDT" for index in range(asset_count))
    shocks = rng.normal(size=(total_returns, asset_count))
    market = rng.normal(scale=0.0015, size=total_returns)
    returns = np.empty((total_returns, asset_count), dtype=np.float64)
    for timestamp in range(total_returns):
        prior = shocks[timestamp - 1] if timestamp else np.zeros(asset_count)
        for follower in range(asset_count):
            returns[timestamp, follower] = market[timestamp] + 0.006 * (
                0.85 * prior[(follower - 1) % asset_count] + 0.25 * shocks[timestamp, follower]
            )

    decision_time = _utc(2023, 10, 4, 8)
    first_close = decision_time - history_periods * pd.Timedelta(hours=8)
    close_times = pd.date_range(
        first_close,
        periods=total_returns + 1,
        freq="8h",
        tz="UTC",
    )
    bars: dict[str, pd.DataFrame] = {}
    for asset, symbol in enumerate(symbols):
        prices = 100.0 * np.exp(np.r_[0.0, np.cumsum(returns[:, asset])])
        bars[symbol] = pd.DataFrame(
            {
                "open_time": close_times - pd.Timedelta(hours=8),
                "symbol": symbol,
                "open": prices,
                "close": prices,
                "quote_volume": 1_000_000_000.0,
            }
        )
    return symbols, bars, decision_time


def _context(
    symbols: tuple[str, ...],
    bars: dict[str, pd.DataFrame],
    decision_time: pd.Timestamp,
) -> DecisionContext:
    return DecisionContext(
        decision_time=decision_time,
        bars=bars,
        funding=pd.DataFrame(),
        auxiliary={},
        eligible_symbols=symbols,
    )


def _weight_signature(weights: object) -> tuple[tuple[str, str], ...] | None:
    if weights is None:
        return None
    assert isinstance(weights, dict)
    return tuple(sorted((symbol, float(value).hex()) for symbol, value in weights.items()))


def test_future_truncation_corruption_append_and_clean_rerun_are_identical(strategy_module):
    symbols, full_bars, decision_time = _synthetic_market()
    truncated = {
        symbol: frame[frame["open_time"] + pd.Timedelta(hours=8) <= decision_time].copy()
        for symbol, frame in full_bars.items()
    }
    corrupted = {symbol: frame.copy() for symbol, frame in full_bars.items()}
    for asset, symbol in enumerate(symbols):
        future = corrupted[symbol]["open_time"] + pd.Timedelta(hours=8) > decision_time
        corrupted[symbol].loc[future, "close"] = 10_000.0 + asset
        corrupted[symbol].loc[future, "open"] = 20_000.0 + asset

    variants = (truncated, full_bars, corrupted, full_bars)
    signatures = []
    for bars in variants:
        instance = strategy_module.build_strategy()
        weights = instance.target_weights(
            _context(symbols, bars, decision_time),
            seed=strategy_module.EXPECTED_SEED,
        )
        signatures.append(_weight_signature(weights))
    assert signatures[0] is not None
    assert signatures.count(signatures[0]) == len(signatures)


def test_finite_eligible_two_sided_caps_and_current_missing_rule(strategy_module):
    symbols, bars, decision_time = _synthetic_market()
    bars = {symbol: frame.copy() for symbol, frame in bars.items()}
    missing_symbol = symbols[0]
    close_time = bars[missing_symbol]["open_time"] + pd.Timedelta(hours=8)
    bars[missing_symbol] = bars[missing_symbol][close_time != decision_time]
    weights = strategy_module.build_strategy().target_weights(
        _context(symbols, bars, decision_time),
        seed=strategy_module.EXPECTED_SEED,
    )
    assert isinstance(weights, dict) and weights
    assert set(weights) == set(symbols)
    assert weights[missing_symbol] == 0.0
    values = np.asarray(list(weights.values()), dtype=np.float64)
    assert np.isfinite(values).all()
    assert float(np.sum(np.abs(values))) <= 0.80 + 1e-12
    assert abs(float(np.sum(values))) <= 1e-10
    assert float(np.max(np.abs(values))) <= 0.075 + 1e-12
    assert np.any(values > 0.0) and np.any(values < 0.0)


def test_refit_is_forced_hold_is_none_and_invalid_fit_is_flat(strategy_module):
    symbols, bars, decision_time = _synthetic_market()
    instance = strategy_module.build_strategy()
    first = instance.target_weights(
        _context(symbols, bars, decision_time),
        seed=strategy_module.EXPECTED_SEED,
    )
    assert isinstance(first, dict) and first
    held = instance.target_weights(
        _context(symbols, bars, decision_time),
        seed=strategy_module.EXPECTED_SEED,
    )
    assert held is None

    invalid_symbols = symbols[:11]
    flat = instance.target_weights(
        _context(invalid_symbols, bars, decision_time),
        seed=strategy_module.EXPECTED_SEED,
    )
    assert flat == {}
    assert instance._last_weights == {}


def test_exact_seed_is_enforced(strategy_module):
    symbols, bars, decision_time = _synthetic_market(asset_count=11)
    with pytest.raises(ValueError, match="strategy seed"):
        strategy_module.build_strategy().target_weights(
            _context(symbols, bars, decision_time),
            seed=strategy_module.EXPECTED_SEED + 1,
        )


def _execution_fixture():
    times = pd.date_range(_utc(2024, 1, 1), periods=4, freq="8h")
    price_paths = {
        "AAAUSDT": (100.0, 101.0, 103.0, 104.0),
        "BBBUSDT": (100.0, 99.0, 97.0, 96.0),
    }
    bar_rows = []
    mark_rows = []
    for symbol, prices in price_paths.items():
        for timestamp, price in zip(times, prices, strict=True):
            bar_rows.append(
                {
                    "open_time": timestamp,
                    "symbol": symbol,
                    "open": price,
                    "close": price + 0.25,
                    "quote_volume": 20_000_000.0,
                }
            )
            mark_rows.append({"mark_time": timestamp, "symbol": symbol, "mark_price": price})
    membership = pd.DataFrame(
        {
            "reconstitution_time": [times[0], times[0]],
            "symbol": list(price_paths),
            "liquidity_rank": [1, 2],
        }
    )
    funding = pd.DataFrame(
        {
            "funding_time": [times[2], times[2]],
            "symbol": list(price_paths),
            "funding_rate": [0.001, 0.001],
            "mark_price": [103.0, 97.0],
        }
    )
    targets = pd.DataFrame(
        {
            "AAAUSDT": [0.0, 0.05, 0.0, 0.0],
            "BBBUSDT": [0.0, -0.05, 0.0, 0.0],
            REBALANCE_INSTRUCTION_COLUMN: [False, True, False, True],
        },
        index=times,
    )
    return (
        pd.DataFrame(bar_rows),
        funding,
        membership,
        targets,
        pd.DataFrame(mark_rows),
        times,
    )


def test_common_execution_is_next_open_costed_funded_and_double_cost_is_fresh():
    bars, funding, membership, targets, marks, times = _execution_fixture()
    base, stressed = evaluate_base_and_double_cost(
        bars,
        funding,
        membership,
        targets,
        mark_prices=marks,
    )
    entries = base.events[
        (base.events["event_type"] == "trade") & (base.events["timestamp"] == times[1])
    ].set_index("symbol")
    assert entries.loc["AAAUSDT", "price"] == 101.0
    assert entries.loc["BBBUSDT", "price"] == 99.0
    assert (entries["fee"] > 0.0).all() and (entries["slippage"] > 0.0).all()

    funding_events = base.events[base.events["event_type"] == "funding"].set_index("symbol")
    assert funding_events.loc["AAAUSDT", "cashflow"] < 0.0
    assert funding_events.loc["BBBUSDT", "cashflow"] > 0.0
    assert funding_events.loc["AAAUSDT", "timestamp"] == times[2]
    assert float(stressed.events["fee"].sum()) == pytest.approx(
        2.0 * float(base.events["fee"].sum())
    )
    assert float(stressed.events["slippage"].sum()) == pytest.approx(
        2.0 * float(base.events["slippage"].sum())
    )
    stressed_funding = stressed.events[stressed.events["event_type"] == "funding"]
    assert float(stressed_funding["cashflow"].sum()) == pytest.approx(
        float(funding_events["cashflow"].sum())
    )


def test_participation_limited_delist_uses_shared_capacity_and_adverse_settlement():
    times = pd.date_range(_utc(2024, 3, 4), periods=4, freq="8h")
    rows = []
    marks = []
    for timestamp in times:
        rows.append(
            {
                "open_time": timestamp,
                "symbol": "ANCHORUSDT",
                "open": 100.0,
                "close": 100.0,
                "quote_volume": 20_000_000.0,
            }
        )
        marks.append({"mark_time": timestamp, "symbol": "ANCHORUSDT", "mark_price": 100.0})
    for timestamp in times[:2]:
        rows.append(
            {
                "open_time": timestamp,
                "symbol": "DELISTUSDT",
                "open": 100.0,
                "close": 90.0,
                "quote_volume": 5_000_000.0 if timestamp == times[0] else 100.0,
            }
        )
        marks.append({"mark_time": timestamp, "symbol": "DELISTUSDT", "mark_price": 100.0})
    membership = pd.DataFrame(
        {
            "reconstitution_time": [times[0], times[0]],
            "symbol": ["ANCHORUSDT", "DELISTUSDT"],
            "liquidity_rank": [1, 2],
        }
    )
    target_frame = pd.DataFrame(
        {
            "ANCHORUSDT": [0.0, 0.0, 0.0, 0.0],
            "DELISTUSDT": [0.0, 0.05, 0.0, 0.0],
            REBALANCE_INSTRUCTION_COLUMN: [False, True, False, False],
        },
        index=times,
    )
    empty_funding = pd.DataFrame(columns=("funding_time", "symbol", "funding_rate", "mark_price"))
    base, _stressed = evaluate_base_and_double_cost(
        pd.DataFrame(rows),
        empty_funding,
        membership,
        target_frame,
        mark_prices=pd.DataFrame(marks),
    )
    settlement = base.events[base.events["event_type"] == "conservative_settlement"]
    assert len(settlement) == 1
    assert settlement.iloc[0]["symbol"] == "DELISTUSDT"
    assert settlement.iloc[0]["cashflow"] < 0.0
    assert base.returns.loc[times[1], "forced_exit_unfilled_notional"] > 0.0
    assert base.returns.loc[times[1], "conservative_settlement_notional"] > 0.0


def test_point_in_time_membership_ignores_future_volume():
    reconstitution = _utc(2024, 2, 5)
    start = reconstitution - pd.Timedelta(days=30)
    symbols = ("AAAUSDT", "BBBUSDT")
    rows = []
    for day in range(30):
        for bar in range(3):
            for rank, symbol in enumerate(symbols):
                rows.append(
                    {
                        "open_time": start + pd.Timedelta(days=day, hours=8 * bar),
                        "symbol": symbol,
                        "quote_volume": 2_000.0 - 1_000.0 * rank,
                    }
                )
    historical = pd.DataFrame(rows)
    future = pd.DataFrame(
        {
            "open_time": [reconstitution + pd.Timedelta(hours=8)],
            "symbol": ["BBBUSDT"],
            "quote_volume": [1_000_000_000.0],
        }
    )
    metadata = pd.DataFrame(
        {
            "symbol": list(symbols),
            "contract_type": ["PERPETUAL", "PERPETUAL"],
            "quote_asset": ["USDT", "USDT"],
            "margin_asset": ["USDT", "USDT"],
            "is_crypto": [True, True],
            "onboard_date": [_utc(2020, 1, 1), _utc(2020, 1, 1)],
            "delivery_date": [pd.NaT, pd.NaT],
        }
    )
    before = point_in_time_top40(
        historical,
        metadata,
        [reconstitution],
        top_n=1,
    )
    after = point_in_time_top40(
        pd.concat((historical, future), ignore_index=True),
        metadata,
        [reconstitution],
        top_n=1,
    )
    pd.testing.assert_frame_equal(before, after)
    assert before.iloc[0]["symbol"] == "AAAUSDT"
