"""Independent QE tests for T06-HWDS-001 using synthetic, pre-public-OOS data only."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from crypto_trade.tournament.data import point_in_time_top40
from crypto_trade.tournament.engine import (
    evaluate_base_and_double_cost,
    evaluate_targets,
    generate_targets,
)
from crypto_trade.tournament.protocol import (
    REBALANCE_INSTRUCTION_COLUMN,
    DecisionContext,
)

TEAM_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TEAM_DIR.parents[3]
STRATEGY_PATH = TEAM_DIR / "strategy.py"
MODULE_NAME = "team06_hwds_strategy_under_test"
SPEC = importlib.util.spec_from_file_location(MODULE_NAME, STRATEGY_PATH)
assert SPEC is not None and SPEC.loader is not None
STRATEGY = importlib.util.module_from_spec(SPEC)
sys.modules[MODULE_NAME] = STRATEGY
SPEC.loader.exec_module(STRATEGY)


def _empty_funding() -> pd.DataFrame:
    return pd.DataFrame(columns=["funding_time", "symbol", "funding_rate", "mark_price"])


def _utc(year: int, month: int, day: int) -> pd.Timestamp:
    return pd.Timestamp(year=year, month=month, day=day, tz="UTC")


@lru_cache(maxsize=1)
def _strategy_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp, tuple[str, ...]]:
    """Create 400 daily observations with beta-independent Monday effects."""

    decision_time = _utc(2023, 2, 6)
    symbols = ("BTCUSDT", *(f"C{index:02d}USDT" for index in range(13)))
    dates = pd.date_range(
        decision_time - pd.Timedelta(days=400),
        decision_time + pd.Timedelta(days=3),
        freq="D",
    )
    day_number = np.arange(len(dates) - 1, dtype=np.float64)
    btc_returns = 0.008 * np.sin(day_number * 0.31) + 0.003 * np.cos(day_number * 0.17)
    weekday_effects = np.asarray(
        [
            0.0,
            -0.018,
            0.017,
            -0.015,
            0.014,
            -0.012,
            0.011,
            -0.009,
            0.008,
            -0.006,
            0.005,
            -0.004,
            0.003,
            -0.002,
        ],
        dtype=np.float64,
    )
    frames: list[pd.DataFrame] = []
    for symbol_index, symbol in enumerate(symbols):
        beta = 0.50 + 0.08 * symbol_index
        noise = 0.0015 * np.sin(day_number * (0.13 + 0.003 * symbol_index) + symbol_index)
        daily_returns = beta * btc_returns + noise
        weekday_mask = pd.DatetimeIndex(dates[:-1]).weekday == decision_time.weekday()
        daily_returns = daily_returns + weekday_mask * weekday_effects[symbol_index]
        initial_log_price = np.log(100.0 + 3.0 * symbol_index)
        log_prices = np.concatenate(
            ([initial_log_price], initial_log_price + np.cumsum(daily_returns))
        )
        rows: list[dict[str, object]] = []
        for date_index, date in enumerate(dates[:-1]):
            for hour in (0, 8, 16):
                start_fraction = hour / 24.0
                end_fraction = (hour + 8) / 24.0
                rows.append(
                    {
                        "open_time": date + pd.Timedelta(hours=hour),
                        "symbol": symbol,
                        "open": float(
                            np.exp(
                                log_prices[date_index] + daily_returns[date_index] * start_fraction
                            )
                        ),
                        "close": float(
                            np.exp(
                                log_prices[date_index] + daily_returns[date_index] * end_fraction
                            )
                        ),
                        "quote_volume": float(100_000_000.0 * (1.0 + 0.03 * symbol_index)),
                    }
                )
        frames.append(pd.DataFrame(rows))
    bars = pd.concat(frames, ignore_index=True).sort_values(
        ["open_time", "symbol"], kind="mergesort", ignore_index=True
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": [decision_time] * len(symbols),
            "symbol": symbols,
            "liquidity_rank": np.arange(1, len(symbols) + 1),
            "trailing_quote_volume": np.linspace(2.0e9, 1.0e9, len(symbols)),
        }
    )
    return bars, membership, decision_time, symbols


def _context(
    bars: pd.DataFrame,
    decision_time: pd.Timestamp,
    symbols: tuple[str, ...],
) -> DecisionContext:
    interval = pd.Timedelta(hours=8)
    by_symbol = {
        symbol: bars[
            (bars["symbol"] == symbol) & (bars["open_time"] + interval <= decision_time)
        ].reset_index(drop=True)
        for symbol in symbols
    }
    return DecisionContext(
        decision_time=decision_time,
        bars=by_symbol,
        funding=_empty_funding(),
        auxiliary={},
        eligible_symbols=symbols,
    )


def _target_grid(
    bars: pd.DataFrame, membership: pd.DataFrame, decision_time: pd.Timestamp
) -> pd.DataFrame:
    decisions = [
        decision_time - pd.Timedelta(hours=16),
        decision_time - pd.Timedelta(hours=8),
        decision_time,
    ]
    return generate_targets(
        STRATEGY.build_strategy(),
        bars,
        _empty_funding(),
        membership,
        decisions,
        seed=STRATEGY.STRATEGY_SEED,
    )


def _frame_hash(frame: pd.DataFrame) -> str:
    payload = frame.to_csv(float_format="%.17g", lineterminator="\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _engine_inputs(
    *, periods: int = 4, quote_volume: float = 1_000_000_000.0
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    start = _utc(2023, 1, 2)
    symbols = ("AUSDT", "BUSDT")
    rows: list[dict[str, object]] = []
    for offset in (-24, -16, -8):
        for symbol in symbols:
            rows.append(
                {
                    "open_time": start + pd.Timedelta(hours=offset),
                    "symbol": symbol,
                    "open": 100.0,
                    "close": 100.0,
                    "quote_volume": quote_volume,
                }
            )
    for index in range(periods):
        timestamp = start + pd.Timedelta(hours=8 * index)
        rows.extend(
            [
                {
                    "open_time": timestamp,
                    "symbol": "AUSDT",
                    "open": 100.0 + 10.0 * min(index, 1),
                    "close": 100.0 + 10.0 * min(index + 1, 1),
                    "quote_volume": quote_volume,
                },
                {
                    "open_time": timestamp,
                    "symbol": "BUSDT",
                    "open": 100.0 - 10.0 * min(index, 1),
                    "close": 100.0 - 10.0 * min(index + 1, 1),
                    "quote_volume": quote_volume,
                },
            ]
        )
    bars = pd.DataFrame(rows)
    membership = pd.DataFrame(
        {
            "reconstitution_time": [start, start],
            "symbol": list(symbols),
            "liquidity_rank": [1, 2],
            "trailing_quote_volume": [2.0e9, 1.0e9],
        }
    )
    mark_rows = []
    for index in range(periods):
        timestamp = start + pd.Timedelta(hours=8 * index)
        mark_rows.extend(
            [
                {"mark_time": timestamp, "symbol": "AUSDT", "mark_price": 100.0},
                {"mark_time": timestamp, "symbol": "BUSDT", "mark_price": 100.0},
            ]
        )
    return bars, membership, pd.DataFrame(mark_rows), start


def _long_short_targets(start: pd.Timestamp, periods: int = 4) -> pd.DataFrame:
    index = pd.date_range(start, periods=periods, freq="8h")
    result = pd.DataFrame(0.0, index=index, columns=["AUSDT", "BUSDT"])
    result.loc[index[0], ["AUSDT", "BUSDT"]] = [0.10, -0.10]
    result[REBALANCE_INSTRUCTION_COLUMN] = False
    result.loc[index[0], REBALANCE_INSTRUCTION_COLUMN] = True
    result.loc[index[-1], REBALANCE_INSTRUCTION_COLUMN] = True
    return result


def _reproduction_hashes() -> dict[str, str]:
    strategy_bars, membership, decision_time, _ = _strategy_inputs()
    targets = _target_grid(strategy_bars, membership, decision_time)
    engine_bars, engine_membership, marks, start = _engine_inputs()
    evaluation = evaluate_targets(
        engine_bars,
        _empty_funding(),
        engine_membership,
        _long_short_targets(start),
        mark_prices=marks,
    )
    hashes = {
        "targets": _frame_hash(targets),
        "positions": _frame_hash(evaluation.positions),
        "returns": _frame_hash(evaluation.returns),
    }
    manifest_payload = json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()
    hashes["manifest"] = hashlib.sha256(manifest_payload).hexdigest()
    return hashes


def test_factory_returns_fresh_instances_and_seed_is_pinned() -> None:
    first = STRATEGY.build_strategy()
    second = STRATEGY.build_strategy()
    assert first is not second
    bars, _, decision_time, symbols = _strategy_inputs()
    with pytest.raises(ValueError, match="requires seed"):
        first.target_weights(_context(bars, decision_time, symbols), seed=1)


def test_midnight_rebalances_and_intraday_decisions_hold_quantities() -> None:
    bars, _, decision_time, symbols = _strategy_inputs()
    strategy = STRATEGY.build_strategy()
    target = strategy.target_weights(
        _context(bars, decision_time, symbols), seed=STRATEGY.STRATEGY_SEED
    )
    hold = strategy.target_weights(
        _context(bars, decision_time + pd.Timedelta(hours=8), symbols),
        seed=STRATEGY.STRATEGY_SEED,
    )
    assert isinstance(target, dict) and target
    assert hold is None


def test_hwds_mapping_is_finite_two_sided_neutral_capped_and_eligible() -> None:
    bars, _, decision_time, symbols = _strategy_inputs()
    target = STRATEGY.build_strategy().target_weights(
        _context(bars, decision_time, symbols), seed=STRATEGY.STRATEGY_SEED
    )
    assert target is not None and target
    assert set(target) <= set(symbols)
    weights = np.asarray(list(target.values()))
    assert np.isfinite(weights).all()
    assert np.count_nonzero(weights > 0.0) == 5
    assert np.count_nonzero(weights < 0.0) == 5
    assert sum(abs(value) for value in target.values()) == pytest.approx(0.8, abs=1e-14)
    assert sum(target.values()) == pytest.approx(0.0, abs=1e-14)
    assert max(abs(value) for value in target.values()) <= 0.09


def test_flat_mapping_when_btc_or_minimum_cross_section_is_missing() -> None:
    bars, _, decision_time, symbols = _strategy_inputs()
    no_btc = tuple(symbol for symbol in symbols if symbol != "BTCUSDT")
    assert (
        STRATEGY.build_strategy().target_weights(
            _context(bars, decision_time, no_btc), seed=STRATEGY.STRATEGY_SEED
        )
        == {}
    )
    too_small = symbols[:9]
    assert (
        STRATEGY.build_strategy().target_weights(
            _context(bars, decision_time, too_small), seed=STRATEGY.STRATEGY_SEED
        )
        == {}
    )


def test_truncating_master_data_after_decision_is_bit_identical() -> None:
    bars, membership, decision_time, _ = _strategy_inputs()
    baseline = _target_grid(bars, membership, decision_time)
    truncated = bars[bars["open_time"] <= decision_time].copy()
    actual = _target_grid(truncated, membership, decision_time)
    pdt.assert_frame_equal(actual, baseline, check_exact=True)


def test_corrupting_every_future_numeric_row_preserves_prior_targets() -> None:
    bars, membership, decision_time, _ = _strategy_inputs()
    baseline = _target_grid(bars, membership, decision_time)
    corrupted = bars.copy()
    future = corrupted["open_time"] >= decision_time
    ordinal = np.arange(int(future.sum()), dtype=np.float64) + 1.0
    corrupted.loc[future, "open"] = 10_000.0 + ordinal
    corrupted.loc[future, "close"] = 20_000.0 + ordinal
    corrupted.loc[future, "quote_volume"] = 30_000.0 + ordinal
    actual = _target_grid(corrupted, membership, decision_time)
    pdt.assert_frame_equal(actual, baseline, check_exact=True)


def test_appending_future_rows_preserves_prior_targets() -> None:
    bars, membership, decision_time, _ = _strategy_inputs()
    through_decision = bars[bars["open_time"] <= decision_time].copy()
    baseline = _target_grid(through_decision, membership, decision_time)
    appended = pd.concat(
        [through_decision, bars[bars["open_time"] > decision_time]], ignore_index=True
    )
    actual = _target_grid(appended, membership, decision_time)
    pdt.assert_frame_equal(actual, baseline, check_exact=True)


def test_helper_ignores_future_rows_even_if_context_is_not_pretruncated() -> None:
    bars, _, decision_time, symbols = _strategy_inputs()
    truncated_context = _context(bars, decision_time, symbols)
    deliberately_untruncated = DecisionContext(
        decision_time=decision_time,
        bars={symbol: bars[bars["symbol"] == symbol].copy() for symbol in symbols},
        funding=_empty_funding(),
        auxiliary={},
        eligible_symbols=symbols,
    )
    first = STRATEGY.build_strategy().target_weights(truncated_context, seed=STRATEGY.STRATEGY_SEED)
    second = STRATEGY.build_strategy().target_weights(
        deliberately_untruncated, seed=STRATEGY.STRATEGY_SEED
    )
    assert first == second


def test_chronological_history_cache_is_bit_identical_to_fresh_daily_refits() -> None:
    bars, _, first_decision, symbols = _strategy_inputs()
    stateful = STRATEGY.build_strategy()
    for offset in range(3):
        decision_time = first_decision + pd.Timedelta(days=offset)
        context = _context(bars, decision_time, symbols)
        cached_target = stateful.target_weights(context, seed=STRATEGY.STRATEGY_SEED)
        fresh_target = STRATEGY.build_strategy().target_weights(
            context, seed=STRATEGY.STRATEGY_SEED
        )
        assert cached_target == fresh_target


def test_partial_pooling_formula_and_weighted_weekday_variance() -> None:
    decision_time = _utc(2023, 2, 6)
    index = pd.date_range(decision_time - pd.Timedelta(days=364), periods=364, freq="D")
    day = np.arange(len(index), dtype=np.float64)
    btc = pd.Series(0.01 * np.sin(day * 0.37) + 0.002 * np.cos(day * 0.11), index=index)
    asset = 1.4 * btc + pd.Series(
        np.where(index.weekday == decision_time.weekday(), 0.007, 0.0), index=index
    )
    estimate = STRATEGY._seasonal_estimate(asset, btc, decision_time)
    assert estimate is not None
    pairs = pd.concat([asset.rename("asset"), btc.rename("btc")], axis=1)
    beta_pairs = pairs[pairs.index >= decision_time - pd.Timedelta(days=60)]
    x = beta_pairs["btc"].to_numpy()
    y = beta_pairs["asset"].to_numpy()
    expected_beta = float(((x - x.mean()) @ (y - y.mean())) / ((x - x.mean()) @ (x - x.mean())))
    weekday = pairs[pairs.index.weekday == decision_time.weekday()]
    residual = weekday["asset"].to_numpy() - expected_beta * weekday["btc"].to_numpy()
    ages = np.arange(len(residual) - 1, -1, -1, dtype=np.float64)
    weights = 2.0 ** (-ages / 13.0)
    expected_mean = float(weights @ residual / weights.sum())
    sample_variance = float(
        weights
        @ np.square(residual - expected_mean)
        / (weights.sum() - (weights @ weights) / weights.sum())
    )
    effective_count = float(weights.sum() ** 2 / (weights @ weights))
    assert estimate.beta == pytest.approx(expected_beta, abs=1e-15)
    assert estimate.mean == pytest.approx(expected_mean, abs=1e-15)
    assert estimate.variance_of_mean == pytest.approx(sample_variance / effective_count, abs=1e-18)


def test_robust_transform_and_iterative_sleeve_redistribution_are_deterministic() -> None:
    assert np.array_equal(STRATEGY._robust_cross_section(np.asarray([3.0, 3.0, 3.0])), np.zeros(3))
    transformed = STRATEGY._robust_cross_section(np.asarray([0.0, 0.0, 0.0, 4.0]))
    assert np.isfinite(transformed).all()
    volatilities = {"A": 0.001, "B": 0.02, "C": 0.03, "D": 0.04, "E": 0.05}
    first = STRATEGY._allocate_sleeve(list(reversed(volatilities)), volatilities, 0.40)
    second = STRATEGY._allocate_sleeve(list(volatilities), volatilities, 0.40)
    assert first == second
    assert sum(first.values()) == pytest.approx(0.40, abs=1e-15)
    assert max(first.values()) <= 0.09
    assert first["A"] == pytest.approx(0.09)


def test_point_in_time_membership_uses_only_complete_prior_dates() -> None:
    reconstitution = _utc(2023, 2, 6)
    rows = []
    for date in pd.date_range(reconstitution - pd.Timedelta(days=30), periods=30, freq="D"):
        for hour in (0, 8, 16):
            rows.extend(
                [
                    {
                        "open_time": date + pd.Timedelta(hours=hour),
                        "symbol": "AUSDT",
                        "quote_volume": 100.0,
                    },
                    {
                        "open_time": date + pd.Timedelta(hours=hour),
                        "symbol": "BUSDT",
                        "quote_volume": 90.0,
                    },
                ]
            )
            if date < reconstitution - pd.Timedelta(days=1):
                rows.append(
                    {
                        "open_time": date + pd.Timedelta(hours=hour),
                        "symbol": "CUSDT",
                        "quote_volume": 1_000.0,
                    }
                )
    bars = pd.DataFrame(rows)
    metadata = pd.DataFrame(
        {
            "symbol": ["AUSDT", "BUSDT", "CUSDT"],
            "contract_type": ["PERPETUAL"] * 3,
            "quote_asset": ["USDT"] * 3,
            "margin_asset": ["USDT"] * 3,
            "is_crypto": [True] * 3,
            "onboard_date": [_utc(2020, 1, 1)] * 3,
            "delivery_date": [pd.NaT] * 3,
        }
    )
    baseline = point_in_time_top40(bars, metadata, [reconstitution], top_n=3)
    future = pd.DataFrame(
        [
            {
                "open_time": reconstitution + pd.Timedelta(hours=hour),
                "symbol": "BUSDT",
                "quote_volume": 1e15,
            }
            for hour in (0, 8, 16)
        ]
    )
    appended = point_in_time_top40(
        pd.concat([bars, future], ignore_index=True), metadata, [reconstitution], top_n=3
    )
    pdt.assert_frame_equal(baseline, appended, check_exact=True)
    assert baseline["symbol"].tolist() == ["AUSDT", "BUSDT"]


def test_ineligible_nonzero_target_is_rejected() -> None:
    bars, membership, marks, start = _engine_inputs()
    membership = membership[membership["symbol"] == "AUSDT"]
    targets = _long_short_targets(start)
    with pytest.raises(ValueError, match="ineligible target symbols"):
        evaluate_targets(bars, _empty_funding(), membership, targets, mark_prices=marks)


def test_signal_close_can_only_fill_at_the_next_unseen_transaction_open() -> None:
    start = _utc(2023, 1, 2)
    bars = pd.DataFrame(
        [
            {
                "open_time": start - pd.Timedelta(hours=24),
                "symbol": "AUSDT",
                "open": 9.0,
                "close": 9.0,
                "quote_volume": 1e9,
            },
            {
                "open_time": start - pd.Timedelta(hours=16),
                "symbol": "AUSDT",
                "open": 9.0,
                "close": 9.0,
                "quote_volume": 1e9,
            },
            {
                "open_time": start - pd.Timedelta(hours=8),
                "symbol": "AUSDT",
                "open": 9.0,
                "close": 11.0,
                "quote_volume": 1e9,
            },
            {
                "open_time": start,
                "symbol": "AUSDT",
                "open": 123.0,
                "close": 124.0,
                "quote_volume": 1e9,
            },
            {
                "open_time": start + pd.Timedelta(hours=8),
                "symbol": "AUSDT",
                "open": 125.0,
                "close": 126.0,
                "quote_volume": 1e9,
            },
        ]
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": [start],
            "symbol": ["AUSDT"],
            "liquidity_rank": [1],
            "trailing_quote_volume": [1e9],
        }
    )

    class CloseDriven:
        def target_weights(self, context: DecisionContext, *, seed: int) -> dict[str, float] | None:
            if context.decision_time == start:
                assert context.bars["AUSDT"]["open_time"].max() == start - pd.Timedelta(hours=8)
                assert context.bars["AUSDT"]["close"].iloc[-1] == 11.0
                return {"AUSDT": 0.05}
            return None

    targets = generate_targets(
        CloseDriven(),
        bars,
        _empty_funding(),
        membership,
        [start, start + pd.Timedelta(hours=8)],
        seed=7,
    )
    marks = pd.DataFrame(
        [
            {"mark_time": start, "symbol": "AUSDT", "mark_price": 123.0},
            {"mark_time": start + pd.Timedelta(hours=8), "symbol": "AUSDT", "mark_price": 125.0},
        ]
    )
    result = evaluate_targets(bars, _empty_funding(), membership, targets, mark_prices=marks)
    first_trade = result.events[result.events["event_type"] == "trade"].iloc[0]
    assert first_trade["timestamp"] == start
    assert first_trade["price"] == 123.0


def test_positive_funding_debits_longs_and_credits_shorts_at_actual_timestamp() -> None:
    bars, membership, marks, start = _engine_inputs()
    funding_time = start + pd.Timedelta(hours=4)
    funding = pd.DataFrame(
        [
            {
                "funding_time": funding_time,
                "symbol": "AUSDT",
                "funding_rate": 0.01,
                "mark_price": 100.0,
            },
            {
                "funding_time": funding_time,
                "symbol": "BUSDT",
                "funding_rate": 0.01,
                "mark_price": 100.0,
            },
        ]
    )
    result = evaluate_targets(
        bars, funding, membership, _long_short_targets(start), mark_prices=marks
    )
    events = result.events[result.events["event_type"] == "funding"].set_index("symbol")
    assert set(events["timestamp"]) == {funding_time}
    for symbol in ("AUSDT", "BUSDT"):
        event = events.loc[symbol]
        assert event["cashflow"] == pytest.approx(
            -event["quantity"] * event["price"] * event["funding_rate"], abs=1e-12
        )
    assert events.loc["AUSDT", "cashflow"] < 0.0
    assert events.loc["BUSDT", "cashflow"] > 0.0
    assert result.returns.iloc[0]["long_funding_pnl"] < 0.0
    assert result.returns.iloc[0]["short_funding_pnl"] > 0.0


def test_entry_rebalance_and_exit_each_charge_fee_and_slippage() -> None:
    bars, membership, marks, start = _engine_inputs()
    times = pd.date_range(start, periods=4, freq="8h")
    targets = pd.DataFrame(
        {
            "AUSDT": [0.05, -0.05, 0.0, 0.0],
            "BUSDT": [0.0, 0.0, 0.0, 0.0],
            REBALANCE_INSTRUCTION_COLUMN: [True, True, True, False],
        },
        index=times,
    )
    result = evaluate_targets(bars, _empty_funding(), membership, targets, mark_prices=marks)
    trades = result.events[result.events["event_type"] == "trade"]
    assert set(trades["timestamp"]) == set(times[:3])
    assert (trades.groupby("timestamp")["fee"].sum() > 0.0).all()
    assert (trades.groupby("timestamp")["slippage"].sum() > 0.0).all()


def test_forced_delist_exit_shares_participation_and_residual_gets_adverse_haircut() -> None:
    bars, membership, marks, start = _engine_inputs(periods=3)
    # Remove the next A bar so its t+8 candle becomes the last executable bar, then make that
    # candle's close capacity only one dollar.
    disappearing_time = start + pd.Timedelta(hours=16)
    bars = bars[~((bars["symbol"] == "AUSDT") & (bars["open_time"] == disappearing_time))].copy()
    last_a = (bars["symbol"] == "AUSDT") & (bars["open_time"] == start + pd.Timedelta(hours=8))
    bars.loc[last_a, "quote_volume"] = 1_000.0
    times = pd.date_range(start, periods=3, freq="8h")
    targets = pd.DataFrame(
        {
            "AUSDT": [0.09, 0.0, 0.0],
            "BUSDT": [0.0, 0.0, 0.0],
            REBALANCE_INSTRUCTION_COLUMN: [True, False, True],
        },
        index=times,
    )
    result = evaluate_targets(bars, _empty_funding(), membership, targets, mark_prices=marks)
    forced = result.events[result.events["event_type"] == "forced_exit"]
    settlement = result.events[result.events["event_type"] == "conservative_settlement"]
    assert len(forced) == 1
    assert abs(float(forced.iloc[0]["notional"])) <= 1.0 + 1e-12
    assert forced.iloc[0]["fee"] > 0.0 and forced.iloc[0]["slippage"] > 0.0
    assert len(settlement) == 1
    assert settlement.iloc[0]["cashflow"] < 0.0
    assert result.returns["conservative_settlement_loss"].sum() > 0.0


def test_participation_limited_fill_records_unfilled_notional() -> None:
    bars, membership, marks, start = _engine_inputs(quote_volume=1_000.0)
    result = evaluate_targets(
        bars, _empty_funding(), membership, _long_short_targets(start), mark_prices=marks
    )
    first = result.returns.iloc[0]
    assert first["requested_notional"] > first["turnover"] * 100_000.0
    assert first["unfilled_notional"] > 0.0
    first_trades = result.events[
        (result.events["event_type"] == "trade") & (result.events["timestamp"] == start)
    ]
    assert first_trades["notional"].abs().sum() <= 6.0 + 1e-12


def test_double_cost_is_an_independent_fresh_run_with_exact_doubled_cost_rates() -> None:
    bars, membership, marks, start = _engine_inputs()
    base, stressed = evaluate_base_and_double_cost(
        bars, _empty_funding(), membership, _long_short_targets(start), mark_prices=marks
    )
    assert base is not stressed
    for result, multiplier in ((base, 1.0), (stressed, 2.0)):
        executions = result.events[
            result.events["event_type"].isin(["trade", "risk_reduction", "forced_exit"])
        ]
        assert np.allclose(
            executions["fee"] / executions["notional"].abs(),
            0.0005 * multiplier,
            rtol=0.0,
            atol=1e-15,
        )
        assert np.allclose(
            executions["slippage"] / executions["notional"].abs(),
            0.00025 * multiplier,
            rtol=0.0,
            atol=1e-15,
        )
    assert stressed.returns["fees"].sum() > base.returns["fees"].sum()
    assert stressed.returns["slippage"].sum() > base.returns["slippage"].sum()
    assert stressed.returns["net_return"].sum() < base.returns["net_return"].sum()


def test_long_and_short_price_pnl_signs_reconcile_independently() -> None:
    bars, membership, marks, start = _engine_inputs()
    result = evaluate_targets(
        bars, _empty_funding(), membership, _long_short_targets(start), mark_prices=marks
    )
    first = result.returns.iloc[0]
    assert first["long_price_pnl"] > 0.0
    assert first["short_price_pnl"] > 0.0
    assert first["price_pnl"] == pytest.approx(first["long_price_pnl"] + first["short_price_pnl"])
    assert result.positions.iloc[0]["AUSDT"] > 0.0
    assert result.positions.iloc[0]["BUSDT"] < 0.0


@pytest.mark.parametrize(
    "a_weight,b_weight,error",
    [
        (0.11, 0.0, "symbol exposure"),
        (0.70, 0.40, "gross exposure"),
        (0.30, 0.0, "net exposure"),
    ],
)
def test_symbol_gross_and_net_caps_reject_invalid_targets(
    a_weight: float, b_weight: float, error: str
) -> None:
    bars, membership, marks, start = _engine_inputs()
    targets = _long_short_targets(start)
    targets.loc[start, ["AUSDT", "BUSDT"]] = [a_weight, b_weight]
    with pytest.raises(ValueError, match=error):
        evaluate_targets(bars, _empty_funding(), membership, targets, mark_prices=marks)


@pytest.mark.parametrize(
    "bad_value",
    [np.nan, np.inf, -np.inf],
)
def test_nonfinite_targets_fail_closed(bad_value: float) -> None:
    bars, membership, marks, start = _engine_inputs()
    targets = _long_short_targets(start)
    targets.loc[start, "AUSDT"] = bad_value
    with pytest.raises(ValueError, match="non-finite target"):
        evaluate_targets(bars, _empty_funding(), membership, targets, mark_prices=marks)


def test_missing_marks_duplicate_bars_and_duplicate_target_times_fail_closed() -> None:
    bars, membership, marks, start = _engine_inputs()
    missing_mark = marks[
        ~((marks["symbol"] == "AUSDT") & (marks["mark_time"] == start + pd.Timedelta(hours=8)))
    ]
    with pytest.raises(ValueError, match="missing current mark for held symbols"):
        evaluate_targets(
            bars, _empty_funding(), membership, _long_short_targets(start), mark_prices=missing_mark
        )
    with pytest.raises(ValueError, match="duplicate .* bars"):
        evaluate_targets(
            pd.concat([bars, bars.iloc[[0]]], ignore_index=True),
            _empty_funding(),
            membership,
            _long_short_targets(start),
            mark_prices=marks,
        )
    duplicate_targets = pd.concat(
        [_long_short_targets(start), _long_short_targets(start).iloc[[0]]]
    )
    with pytest.raises(ValueError, match="duplicate timestamps"):
        evaluate_targets(bars, _empty_funding(), membership, duplicate_targets, mark_prices=marks)


def test_empty_mapping_is_explicit_flat_while_none_is_hold() -> None:
    bars, membership, _, start = _engine_inputs()

    class Sparse:
        def target_weights(self, context: DecisionContext, *, seed: int) -> dict[str, float] | None:
            return {} if context.decision_time == start else None

    targets = generate_targets(
        Sparse(), bars, _empty_funding(), membership, [start, start + pd.Timedelta(hours=8)], seed=1
    )
    assert bool(targets.loc[start, REBALANCE_INSTRUCTION_COLUMN]) is True
    assert bool(targets.loc[start + pd.Timedelta(hours=8), REBALANCE_INSTRUCTION_COLUMN]) is False


def test_realized_two_sleeve_exposure_and_execution_floors_on_two_synthetic_windows() -> None:
    bars, membership, marks, start = _engine_inputs(periods=40)
    times = pd.date_range(start, periods=40, freq="8h")
    targets = pd.DataFrame(0.0, index=times, columns=["AUSDT", "BUSDT"])
    targets[REBALANCE_INSTRUCTION_COLUMN] = False
    targets.loc[times[0], ["AUSDT", "BUSDT", REBALANCE_INSTRUCTION_COLUMN]] = [0.10, -0.10, True]
    targets.loc[times[20], ["AUSDT", "BUSDT", REBALANCE_INSTRUCTION_COLUMN]] = [-0.10, 0.10, True]
    result = evaluate_targets(bars, _empty_funding(), membership, targets, mark_prices=marks)
    for window_times in (times[:20], times[20:]):
        realized = result.returns.loc[result.returns.index.intersection(window_times)]
        assert (realized["long_exposure"] >= 0.01).mean() >= 0.05
        assert (realized["short_exposure"] >= 0.01).mean() >= 0.05
        assert realized["long_exposure"].mean() >= 0.005
        assert realized["short_exposure"].mean() >= 0.005
        events = result.events[result.events["timestamp"].isin(window_times)]
        trades = events[events["event_type"].isin(["trade", "forced_exit"])]
        assert trades.loc[trades["notional"] > 0.0, "notional"].sum() >= 1_000.0
        assert -trades.loc[trades["notional"] < 0.0, "notional"].sum() >= 1_000.0


def test_two_clean_processes_reproduce_target_position_return_and_manifest_hashes() -> None:
    script = f"""
import importlib.util, json, sys
path = {str(Path(__file__).resolve())!r}
spec = importlib.util.spec_from_file_location('team06_qe_repro', path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
print(json.dumps(module._reproduction_hashes(), sort_keys=True))
"""
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    outputs = []
    for _ in range(2):
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=PROJECT_ROOT,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        outputs.append(completed.stdout.strip())
    assert outputs[0] == outputs[1]
    assert set(json.loads(outputs[0])) == {"targets", "positions", "returns", "manifest"}


def test_strategy_source_scanner_allows_only_context_market_inputs_and_no_io() -> None:
    source = STRATEGY_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = set()
    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "typing",
        "numpy",
        "pandas",
        "crypto_trade",
    }
    assert not (
        {"open", "exec", "eval", "compile", "system", "popen", "connect", "urlopen"} & calls
    )
    assert "2024-" + "07-01" not in source and "2026-" + "07-01" not in source


def test_feature_lineage_declares_only_public_binance_and_deterministic_calendar_inputs() -> None:
    lineage = json.loads((TEAM_DIR / "feature_lineage.json").read_text(encoding="utf-8"))
    for feature in lineage["features"]:
        endpoint = feature["endpoint_archive"]
        assert (
            "data.binance.vision" in endpoint
            or "fapi.binance.com" in endpoint
            or endpoint == "deterministic calendar"
            or endpoint.startswith("derived from lagged transaction quote_volume plus ")
        )
    source = STRATEGY_PATH.read_text(encoding="utf-8")
    assert "context.funding" not in source
    assert "context.auxiliary" not in source


def test_team_lock_is_byte_identical_to_repository_root_lock_and_config_is_bound() -> None:
    team_lock = (TEAM_DIR / "uv.lock").read_bytes()
    root_lock = (PROJECT_ROOT / "uv.lock").read_bytes()
    assert team_lock == root_lock
    config = json.loads((TEAM_DIR / "frozen_config.json").read_text(encoding="utf-8"))
    assert config["phase0_record_commit"] == "012727865acecad6ea0c3327745359820b8e45c6"
    assert config["common_freeze_commit"] == "48df09341f02eba7a3469abd1ccda6649a4ef0ba"
    assert config["strategy_seed"] == STRATEGY.STRATEGY_SEED
    assert config["parameters"]["cross_sectional_feature_order"] == [
        "beta",
        "momentum_20d",
        "sample_volatility_20d",
        "log_median_quote_volume_20d",
    ]
