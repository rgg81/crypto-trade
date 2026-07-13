from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from crypto_trade.tournament import engine
from crypto_trade.tournament.data import eligible_at, point_in_time_top40
from crypto_trade.tournament.engine import (
    EvaluatorConfig,
    evaluate_base_and_double_cost,
    evaluate_targets,
    generate_targets,
)
from crypto_trade.tournament.protocol import (
    REBALANCE_INSTRUCTION_COLUMN,
    DecisionContext,
)

TEAM_DIR = Path(__file__).resolve().parent
ROOT = TEAM_DIR.parents[3]
SEED = 20260713
INTERVAL = pd.Timedelta(hours=8)
FACTOR = "BTCUSDT"


def _load_team_module() -> ModuleType:
    name = "_team07_strategy_under_test"
    spec = importlib.util.spec_from_file_location(name, TEAM_DIR / "strategy.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


TEAM_STRATEGY = _load_team_module()


def _decision() -> pd.Timestamp:
    return pd.Timestamp(year=2023, month=1, day=2, tz="UTC")


def _empty_funding() -> pd.DataFrame:
    return pd.DataFrame(columns=["funding_time", "symbol", "funding_rate", "mark_price"])


def _factor_returns() -> np.ndarray:
    index = np.arange(210, dtype=np.float64)
    return 0.003 * np.sin(index * 0.37) + 0.0015 * np.cos(index * 0.11)


def _asset_returns(factor_returns: np.ndarray, index: int, recent_positive: bool) -> np.ndarray:
    fit_index = np.arange(189, dtype=np.float64)
    baseline = 0.0007 * np.sin(fit_index * (0.19 + index * 0.007) + index * 0.31)
    formation_shift = np.zeros(189, dtype=np.float64)
    formation_shift[-63:] = (index - 5.5) * 0.00032
    fitted_window = 0.65 * factor_returns[:189] + baseline + formation_shift
    recent = np.full(21, 0.002 if recent_positive else -0.002, dtype=np.float64)
    return np.concatenate([fitted_window, recent])


def _bar_frame(
    symbol: str,
    returns: np.ndarray,
    *,
    decision: pd.Timestamp | None = None,
) -> pd.DataFrame:
    boundary = decision or _decision()
    opens = pd.date_range(
        end=boundary - INTERVAL,
        periods=len(returns) + 1,
        freq=INTERVAL,
    )
    closes = 100.0 * np.exp(np.concatenate([[0.0], np.cumsum(returns)]))
    return pd.DataFrame(
        {
            "open_time": opens,
            "symbol": symbol,
            "open": closes,
            "close": closes,
            "quote_volume": 100_000_000.0,
        }
    )


def _symbol(index: int) -> str:
    return f"A{index:02d}USDT"


def _strategy_context(
    *,
    count: int = 12,
    recent_signs: Sequence[bool] | None = None,
) -> tuple[DecisionContext, np.ndarray, dict[str, np.ndarray]]:
    factor_returns = _factor_returns()
    signs = tuple(recent_signs or tuple(index < count / 2 for index in range(count)))
    assert len(signs) == count
    bars: dict[str, pd.DataFrame] = {FACTOR: _bar_frame(FACTOR, factor_returns)}
    asset_returns: dict[str, np.ndarray] = {}
    for index in range(count):
        symbol = _symbol(index)
        values = _asset_returns(factor_returns, index, signs[index])
        asset_returns[symbol] = values
        bars[symbol] = _bar_frame(symbol, values)
    eligible = (FACTOR, *(sorted(asset_returns)))
    context = DecisionContext(
        decision_time=_decision(),
        bars=bars,
        funding=_empty_funding(),
        auxiliary={},
        eligible_symbols=eligible,
    )
    return context, factor_returns, asset_returns


def _reference_score(asset_returns: np.ndarray, factor_returns: np.ndarray) -> float:
    x = factor_returns[:189]
    y = asset_returns[:189]
    x_centered = x - x.mean()
    beta = np.dot(x_centered, y - y.mean()) / np.dot(x_centered, x_centered)
    alpha = y.mean() - beta * x.mean()
    residuals = y - alpha - beta * x
    residual_rms = np.sqrt(np.dot(residuals, residuals) / 187)
    return float(residuals[-63:].sum() / (residual_rms * np.sqrt(63)))


def _weights(context: DecisionContext) -> Mapping[str, float] | None:
    return TEAM_STRATEGY.build_strategy().target_weights(context, seed=SEED)


def test_exact_handoff_formula_schedule_and_disjoint_sleeves() -> None:
    context, factor_returns, asset_returns = _strategy_context()
    observed = _weights(context)
    assert observed is not None

    ranked_descending = sorted(
        asset_returns,
        key=lambda symbol: (-_reference_score(asset_returns[symbol], factor_returns), symbol),
    )
    expected_longs = ranked_descending[:6]
    ranked_ascending = sorted(
        asset_returns,
        key=lambda symbol: (_reference_score(asset_returns[symbol], factor_returns), symbol),
    )
    expected_shorts = [symbol for symbol in ranked_ascending if symbol not in expected_longs][:6]
    expected = {symbol: 0.05 for symbol in expected_longs}
    expected.update({symbol: -0.05 for symbol in expected_shorts})

    assert observed == expected
    assert FACTOR not in observed
    assert len(observed) == 12
    assert sum(weight > 0.0 for weight in observed.values()) == 6
    assert sum(weight < 0.0 for weight in observed.values()) == 6
    assert sum(abs(weight) for weight in observed.values()) == pytest.approx(0.60)
    assert sum(observed.values()) == pytest.approx(0.0, abs=1e-15)
    assert max(abs(weight) for weight in observed.values()) == pytest.approx(0.05)

    monday_later = dataclasses.replace(context, decision_time=_decision() + INTERVAL)
    tuesday = dataclasses.replace(context, decision_time=_decision() + pd.Timedelta(days=1))
    assert _weights(monday_later) is None
    assert _weights(tuesday) is None

    all_positive, _, _ = _strategy_context(recent_signs=[True] * 12)
    assert _weights(all_positive) == {}


def test_truncation_corrupt_future_append_and_context_read_only_invariance() -> None:
    context, _, _ = _strategy_context()
    snapshots = {symbol: frame.copy(deep=True) for symbol, frame in context.bars.items()}
    baseline = _weights(context)

    appended: dict[str, pd.DataFrame] = {}
    for symbol, frame in context.bars.items():
        future_rows = frame.tail(2).copy(deep=True)
        future_rows["open_time"] = [_decision(), _decision() + INTERVAL]
        future_rows["close"] = [np.nan, np.inf]
        appended[symbol] = pd.concat([frame, future_rows], ignore_index=True)
    future_funding = pd.DataFrame(
        {
            "funding_time": [_decision() + INTERVAL],
            "symbol": [FACTOR],
            "funding_rate": [np.inf],
            "mark_price": [np.nan],
        }
    )
    future_context = dataclasses.replace(context, bars=appended, funding=future_funding)

    assert _weights(future_context) == baseline
    assert _weights(context) == baseline
    for symbol, expected in snapshots.items():
        pdt.assert_frame_equal(context.bars[symbol], expected)


def test_strategy_faults_fail_flat_and_seed_or_membership_faults_fail_closed() -> None:
    context, factor_returns, _ = _strategy_context()
    first_asset = _symbol(0)

    cases: list[DecisionContext] = []
    without_factor = dict(context.bars)
    without_factor.pop(FACTOR)
    cases.append(dataclasses.replace(context, bars=without_factor))

    short_history = dict(context.bars)
    short_history[first_asset] = short_history[first_asset].tail(100)
    cases.append(dataclasses.replace(context, bars=short_history))

    gap_history = dict(context.bars)
    gap_history[first_asset] = gap_history[first_asset].drop(
        gap_history[first_asset].index[-20]
    )
    cases.append(dataclasses.replace(context, bars=gap_history))

    for bad_close in (0.0, -1.0, np.nan, np.inf):
        bad_history = dict(context.bars)
        corrupted = bad_history[first_asset].copy()
        corrupted.loc[corrupted.index[-1], "close"] = bad_close
        bad_history[first_asset] = corrupted
        cases.append(dataclasses.replace(context, bars=bad_history))

    duplicate_history = dict(context.bars)
    duplicate_history[first_asset] = pd.concat(
        [duplicate_history[first_asset], duplicate_history[first_asset].tail(1)],
        ignore_index=True,
    )
    cases.append(dataclasses.replace(context, bars=duplicate_history))

    constant_factor = dict(context.bars)
    constant_factor[FACTOR] = _bar_frame(FACTOR, np.zeros_like(factor_returns))
    cases.append(dataclasses.replace(context, bars=constant_factor))

    zero_residual = dict(context.bars)
    for index in range(12):
        symbol = _symbol(index)
        values = np.concatenate(
            [0.65 * factor_returns[:189], np.full(21, 0.002 if index < 6 else -0.002)]
        )
        zero_residual[symbol] = _bar_frame(symbol, values)
    cases.append(dataclasses.replace(context, bars=zero_residual))

    for case in cases:
        assert _weights(case) == {}

    duplicate_eligible = dataclasses.replace(
        context,
        eligible_symbols=(*context.eligible_symbols, context.eligible_symbols[-1]),
    )
    with pytest.raises(ValueError, match="duplicates"):
        _weights(duplicate_eligible)
    with pytest.raises(ValueError, match="seed"):
        TEAM_STRATEGY.build_strategy().target_weights(context, seed=SEED + 1)


def test_point_in_time_membership_and_strategy_target_boundary() -> None:
    decision = _decision()
    daily_times = pd.date_range(end=decision - pd.Timedelta(days=1), periods=30, freq="D")
    rows: list[dict[str, Any]] = []
    for timestamp in daily_times:
        rows.extend(
            [
                {"open_time": timestamp, "symbol": "AAAUSDT", "quote_volume": 100.0},
                {"open_time": timestamp, "symbol": "BBBUSDT", "quote_volume": 50.0},
            ]
        )
    rows.append(
        {"open_time": decision, "symbol": "BBBUSDT", "quote_volume": 1_000_000_000.0}
    )
    metadata = pd.DataFrame(
        {
            "symbol": ["AAAUSDT", "BBBUSDT"],
            "contract_type": ["PERPETUAL", "PERPETUAL"],
            "quote_asset": ["USDT", "USDT"],
            "margin_asset": ["USDT", "USDT"],
            "is_crypto": [True, True],
            "onboard_date": [decision - pd.Timedelta(days=365)] * 2,
            "delivery_date": [pd.NaT, pd.NaT],
        }
    )
    membership = point_in_time_top40(
        pd.DataFrame(rows),
        metadata,
        [decision],
        top_n=1,
        trailing_days=30,
        min_history_days=30,
        bars_per_day=1,
    )
    assert tuple(membership["symbol"]) == ("AAAUSDT",)

    context, _, _ = _strategy_context(count=13)
    allowed = (FACTOR, *(_symbol(index) for index in range(12)))
    future_membership = pd.DataFrame(
        {
            "reconstitution_time": [
                decision - pd.Timedelta(days=7),
                decision + pd.Timedelta(days=7),
            ],
            "symbol": [_symbol(0), _symbol(12)],
            "liquidity_rank": [1, 1],
            "trailing_quote_volume": [1.0, 2.0],
        }
    )
    assert eligible_at(future_membership, decision) == (_symbol(0),)
    restricted = dataclasses.replace(context, eligible_symbols=allowed)
    observed = _weights(restricted)
    assert observed is not None and _symbol(12) not in observed


def _market(
    symbols: Sequence[str],
    times: pd.DatetimeIndex,
    *,
    open_prices: Mapping[tuple[pd.Timestamp, str], float] | None = None,
    history_quote_volume: float = 100_000_000.0,
    current_quote_volume: float = 100_000_000.0,
    omitted: set[tuple[pd.Timestamp, str]] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    price_overrides = open_prices or {}
    omitted_rows = omitted or set()
    history = pd.date_range(end=times[0] - INTERVAL, periods=3, freq=INTERVAL)
    rows: list[dict[str, Any]] = []
    marks: list[dict[str, Any]] = []
    for timestamp in (*history, *times):
        for symbol in symbols:
            if (timestamp, symbol) in omitted_rows:
                continue
            price = float(price_overrides.get((timestamp, symbol), 100.0))
            rows.append(
                {
                    "open_time": timestamp,
                    "symbol": symbol,
                    "open": price,
                    "close": price,
                    "quote_volume": (
                        history_quote_volume if timestamp < times[0] else current_quote_volume
                    ),
                }
            )
            if timestamp in times:
                marks.append({"mark_time": timestamp, "symbol": symbol, "mark_price": price})
    membership = pd.DataFrame(
        {
            "reconstitution_time": [times[0] - pd.Timedelta(days=7)] * len(symbols),
            "symbol": list(symbols),
            "liquidity_rank": list(range(1, len(symbols) + 1)),
            "trailing_quote_volume": [1.0] * len(symbols),
        }
    )
    return pd.DataFrame(rows), pd.DataFrame(marks), membership


def test_closed_signal_fills_at_next_transaction_open() -> None:
    decision = _decision()
    times = pd.date_range(start=decision, periods=2, freq=INTERVAL)
    symbol = "AAAUSDT"
    bars, marks, membership = _market([symbol], times)
    prior_index = bars.index[bars["open_time"] == decision - INTERVAL][0]
    bars.loc[prior_index, "close"] = 77.0
    current_index = bars.index[(bars["open_time"] == decision) & (bars["symbol"] == symbol)][0]
    bars.loc[current_index, ["open", "close"]] = 123.0
    marks.loc[(marks["mark_time"] == decision) & (marks["symbol"] == symbol), "mark_price"] = 123.0

    class ProbeStrategy:
        def __init__(self) -> None:
            self.last_visible: list[pd.Timestamp] = []

        def target_weights(self, context: DecisionContext, *, seed: int) -> Mapping[str, float]:
            assert seed == SEED
            self.last_visible.append(pd.Timestamp(context.bars[symbol]["open_time"].iloc[-1]))
            return {symbol: 0.05}

    probe = ProbeStrategy()
    targets = generate_targets(
        probe,
        bars,
        _empty_funding(),
        membership,
        times,
        seed=SEED,
    )
    result = evaluate_targets(
        bars,
        _empty_funding(),
        membership,
        targets,
        mark_prices=marks,
    )
    assert probe.last_visible[0] == decision - INTERVAL
    first_trade = result.events[result.events["event_type"] == "trade"].iloc[0]
    assert first_trade["timestamp"] == decision
    assert first_trade["price"] == pytest.approx(123.0)
    assert first_trade["price"] != 77.0


def test_funding_cost_stress_rebalance_and_long_short_attribution() -> None:
    times = pd.date_range(start=_decision(), periods=3, freq=INTERVAL)
    long_symbol, short_symbol = "AAAUSDT", "BBBUSDT"
    prices = {
        (times[1], long_symbol): 110.0,
        (times[2], long_symbol): 110.0,
        (times[1], short_symbol): 90.0,
        (times[2], short_symbol): 90.0,
    }
    bars, marks, membership = _market([long_symbol, short_symbol], times, open_prices=prices)
    funding = pd.DataFrame(
        {
            "funding_time": [times[1], times[1]],
            "symbol": [long_symbol, short_symbol],
            "funding_rate": [0.01, 0.01],
            "mark_price": [110.0, 90.0],
        }
    )
    targets = pd.DataFrame(
        {
            long_symbol: [0.05, 0.03, 0.0],
            short_symbol: [-0.05, -0.03, 0.0],
            REBALANCE_INSTRUCTION_COLUMN: [True, True, True],
        },
        index=times,
    )
    base, stressed = evaluate_base_and_double_cost(
        bars,
        funding,
        membership,
        targets,
        mark_prices=marks,
    )

    boundary_funding = base.events[
        (base.events["event_type"] == "funding") & (base.events["timestamp"] == times[1])
    ].set_index("symbol")
    assert boundary_funding.loc[long_symbol, "phase"] == "before_rebalance"
    assert boundary_funding.loc[long_symbol, "cashflow"] < 0.0
    assert boundary_funding.loc[short_symbol, "cashflow"] > 0.0
    assert base.returns.loc[times[0], "long_price_pnl"] > 0.0
    assert base.returns.loc[times[0], "short_price_pnl"] > 0.0
    np.testing.assert_allclose(
        base.returns["long_price_pnl"] + base.returns["short_price_pnl"],
        base.returns["price_pnl"],
        atol=1e-15,
    )
    np.testing.assert_allclose(
        base.returns["long_funding_pnl"] + base.returns["short_funding_pnl"],
        base.returns["funding_pnl"],
        atol=1e-15,
    )

    base_trades = base.events[base.events["event_type"].isin(["trade", "forced_exit"])]
    stress_trades = stressed.events[
        stressed.events["event_type"].isin(["trade", "forced_exit"])
    ]
    assert set(base_trades["timestamp"]) == set(times)
    assert (base_trades["fee"] > 0.0).all() and (base_trades["slippage"] > 0.0).all()
    assert (stress_trades["fee"] > 0.0).all() and (stress_trades["slippage"] > 0.0).all()
    np.testing.assert_allclose(base_trades["fee"] / base_trades["notional"].abs(), 0.0005)
    np.testing.assert_allclose(base_trades["slippage"] / base_trades["notional"].abs(), 0.00025)
    np.testing.assert_allclose(stress_trades["fee"] / stress_trades["notional"].abs(), 0.001)
    np.testing.assert_allclose(stress_trades["slippage"] / stress_trades["notional"].abs(), 0.0005)
    assert stressed.returns["fees"].sum() > 1.99 * base.returns["fees"].sum()
    assert stressed.returns["slippage"].sum() > 1.99 * base.returns["slippage"].sum()
    assert stressed.returns.loc[times[0], "funding_pnl"] == pytest.approx(
        base.returns.loc[times[0], "funding_pnl"]
    )

    first_positions = base.positions.loc[times[0]]
    assert first_positions[long_symbol] > 0.01
    assert first_positions[short_symbol] < -0.01
    assert base.returns.loc[times[0], "long_exposure"] > 0.01
    assert base.returns.loc[times[0], "short_exposure"] > 0.01
    assert base_trades.loc[base_trades["notional"] > 0.0, "notional"].sum() > 1_000.0
    assert -base_trades.loc[base_trades["notional"] < 0.0, "notional"].sum() > 1_000.0


def test_double_cost_helper_performs_two_fresh_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[float] = []
    results = [object(), object()]

    def fake_evaluate(*args: Any, cost_multiplier: float, **kwargs: Any) -> object:
        calls.append(cost_multiplier)
        return results[len(calls) - 1]

    monkeypatch.setattr(engine, "evaluate_targets", fake_evaluate)
    observed = engine.evaluate_base_and_double_cost(
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        mark_prices=pd.DataFrame(),
    )
    assert calls == [1.0, 2.0]
    assert observed == tuple(results)
    assert observed[0] is not observed[1]


def test_participation_risk_reduction_and_delist_fault_paths() -> None:
    times = pd.date_range(start=_decision(), periods=3, freq=INTERVAL)
    symbol = "AAAUSDT"
    bars, marks, membership = _market(
        [symbol],
        times,
        history_quote_volume=333_333.333333,
    )
    participation_targets = pd.DataFrame(
        {
            symbol: [0.10, 0.0, 0.0],
            REBALANCE_INSTRUCTION_COLUMN: [True, True, True],
        },
        index=times,
    )
    limited = evaluate_targets(
        bars,
        _empty_funding(),
        membership,
        participation_targets,
        mark_prices=marks,
    )
    first_trade = limited.events[limited.events["event_type"] == "trade"].iloc[0]
    assert abs(first_trade["notional"]) == pytest.approx(999.999999999)
    assert limited.returns.loc[times[0], "unfilled_notional"] > 8_900.0

    drift_prices = {
        (times[1], symbol): 200.0,
        (times[2], symbol): 200.0,
    }
    drift_bars, drift_marks, drift_membership = _market(
        [symbol], times, open_prices=drift_prices
    )
    drift_targets = pd.DataFrame(
        {
            symbol: [0.09, 0.0, 0.0],
            REBALANCE_INSTRUCTION_COLUMN: [True, False, False],
        },
        index=times,
    )
    drift = evaluate_targets(
        drift_bars,
        _empty_funding(),
        drift_membership,
        drift_targets,
        mark_prices=drift_marks,
    )
    risk_events = drift.events[
        (drift.events["event_type"] == "risk_reduction")
        & (drift.events["timestamp"] == times[1])
    ]
    assert not risk_events.empty
    assert (risk_events["fee"] > 0.0).all() and (risk_events["slippage"] > 0.0).all()
    assert abs(drift.positions.loc[times[1], symbol]) <= 0.1000000001

    delist_times = times[:2]
    anchor = "ZZZUSDT"
    omitted = {(delist_times[1], symbol)}
    for current_volume, expected_event in (
        (20_000_000.0, "forced_exit"),
        (5_000_000.0, "conservative_settlement"),
    ):
        delist_bars, delist_marks, delist_membership = _market(
            [symbol, anchor],
            delist_times,
            current_quote_volume=current_volume,
            omitted=omitted,
        )
        delist_targets = pd.DataFrame(
            {
                symbol: [0.09, 0.0],
                anchor: [0.0, 0.0],
                REBALANCE_INSTRUCTION_COLUMN: [True, True],
            },
            index=delist_times,
        )
        result = evaluate_targets(
            delist_bars,
            _empty_funding(),
            delist_membership,
            delist_targets,
            mark_prices=delist_marks,
        )
        events = result.events[result.events["event_type"] == expected_event]
        assert not events.empty
        if expected_event == "forced_exit":
            assert (events["fee"] > 0.0).all() and (events["slippage"] > 0.0).all()
            assert result.returns.loc[delist_times[0], "forced_exit_turnover"] > 0.0
        else:
            assert events.iloc[0]["phase"] == "delisting_residual_100pct_haircut"
            assert events.iloc[0]["cashflow"] < 0.0
            assert result.returns.loc[
                delist_times[0], "conservative_settlement_notional"
            ] > 0.0


def test_common_fault_rejection_caps_and_empty_output() -> None:
    timestamp = _decision()
    cfg = EvaluatorConfig()
    with pytest.raises(ValueError, match="gross"):
        engine._validate_weight_limits(pd.Series([0.6, 0.5]), cfg, timestamp)
    with pytest.raises(ValueError, match="net"):
        engine._validate_weight_limits(pd.Series([0.10, 0.10, 0.10]), cfg, timestamp)
    with pytest.raises(ValueError, match="symbol"):
        engine._validate_weight_limits(pd.Series([0.11, -0.11]), cfg, timestamp)

    class EmptyStrategy:
        def target_weights(self, context: DecisionContext, *, seed: int) -> None:
            return None

    empty = generate_targets(
        EmptyStrategy(),
        pd.DataFrame(columns=["open_time", "symbol", "open", "close", "quote_volume"]),
        _empty_funding(),
        pd.DataFrame(),
        [],
        seed=SEED,
    )
    assert empty.empty

    times = pd.date_range(start=timestamp, periods=2, freq=INTERVAL)
    symbols = ["AAAUSDT", "BBBUSDT"]
    bars, marks, membership = _market(symbols, times)
    base_targets = pd.DataFrame(
        {
            symbols[0]: [0.05, 0.0],
            REBALANCE_INSTRUCTION_COLUMN: [True, True],
        },
        index=times,
    )
    bad_numeric = base_targets.copy()
    bad_numeric.iloc[0, 0] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        evaluate_targets(
            bars,
            _empty_funding(),
            membership,
            bad_numeric,
            mark_prices=marks,
        )

    restricted_membership = membership[membership["symbol"] == symbols[0]]
    ineligible = pd.DataFrame(
        {
            symbols[1]: [0.05, 0.0],
            REBALANCE_INSTRUCTION_COLUMN: [True, True],
        },
        index=times,
    )
    with pytest.raises(ValueError, match="ineligible"):
        evaluate_targets(
            bars,
            _empty_funding(),
            restricted_membership,
            ineligible,
            mark_prices=marks,
        )

    duplicate_bars = pd.concat([bars, bars.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        evaluate_targets(
            duplicate_bars,
            _empty_funding(),
            membership,
            base_targets,
            mark_prices=marks,
        )

    duplicate_funding = pd.DataFrame(
        {
            "funding_time": [times[0], times[0]],
            "symbol": [symbols[0], symbols[0]],
            "funding_rate": [0.01, 0.01],
            "mark_price": [100.0, 100.0],
        }
    )
    with pytest.raises(ValueError, match="duplicate"):
        evaluate_targets(
            bars,
            duplicate_funding,
            membership,
            base_targets,
            mark_prices=marks,
        )

    missing_mark = marks[~((marks["mark_time"] == times[1]) & (marks["symbol"] == symbols[0]))]
    hold_targets = base_targets.copy()
    hold_targets.loc[times[1], REBALANCE_INSTRUCTION_COLUMN] = False
    with pytest.raises(ValueError, match="missing current mark"):
        evaluate_targets(
            bars,
            _empty_funding(),
            membership,
            hold_targets,
            mark_prices=missing_mark,
        )


def _frame_digest(frame: pd.DataFrame) -> str:
    payload = frame.to_json(orient="split", date_format="iso", double_precision=15)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _deterministic_payload() -> dict[str, str]:
    context, _, _ = _strategy_context()
    weights = _weights(context)
    assert weights is not None
    target_hash = hashlib.sha256(
        json.dumps(weights, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()

    times = pd.date_range(start=_decision(), periods=3, freq=INTERVAL)
    bars, marks, membership = _market(["AAAUSDT", "BBBUSDT"], times)
    targets = pd.DataFrame(
        {
            "AAAUSDT": [0.05, 0.03, 0.0],
            "BBBUSDT": [-0.05, -0.03, 0.0],
            REBALANCE_INSTRUCTION_COLUMN: [True, True, True],
        },
        index=times,
    )
    result = evaluate_targets(
        bars,
        _empty_funding(),
        membership,
        targets,
        mark_prices=marks,
    )
    values = {
        "target_hash": target_hash,
        "position_hash": _frame_digest(result.positions),
        "return_hash": _frame_digest(result.returns),
    }
    values["manifest_hash"] = hashlib.sha256(
        json.dumps(values, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return values


def test_clean_process_target_position_return_and_manifest_hashes_are_identical() -> None:
    code = (
        "import json; import test_team_07_strategy as suite; "
        "print(json.dumps(suite._deterministic_payload(), sort_keys=True))"
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT / "src"), str(TEAM_DIR), environment.get("PYTHONPATH", "")]
    )
    outputs = [
        subprocess.check_output(
            [sys.executable, "-c", code],
            cwd=TEAM_DIR,
            env=environment,
            text=True,
        ).strip()
        for _ in range(2)
    ]
    assert outputs[0] == outputs[1]
    assert json.loads(outputs[0]) == _deterministic_payload()
