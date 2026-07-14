"""Independent QE tests for T05-AER12-H80-R72-v1.

All market fixtures are synthetic and dated inside the in-sample window.  This
suite never opens the frozen snapshot or requests public-OOS evaluation.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament.data import point_in_time_top40
from crypto_trade.tournament.engine import (
    EvaluatorConfig,
    _validate_weight_limits,
    evaluate_base_and_double_cost,
    evaluate_targets,
    generate_targets,
)
from crypto_trade.tournament.protocol import (
    REBALANCE_INSTRUCTION_COLUMN,
    DecisionContext,
)

TEAM_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = TEAM_DIR.parents[3]
STRATEGY_PATH = TEAM_DIR / "strategy.py"
SEED = 20260713
INTERVAL = pd.Timedelta(hours=8)


def _utc_date(year: int, month: int, day: int) -> pd.Timestamp:
    return pd.Timestamp(year=year, month=month, day=day, tz="UTC")


DECISION_TIME = _utc_date(2023, 4, 3)


def _load_strategy_module() -> ModuleType:
    name = "team_05_strategy_under_test"
    spec = importlib.util.spec_from_file_location(name, STRATEGY_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


STRATEGY = _load_strategy_module()


def _membership(symbols: tuple[str, ...], timestamp: pd.Timestamp = DECISION_TIME) -> pd.DataFrame:
    reconstitution = timestamp.floor("D") - pd.Timedelta(days=7)
    reconstitution -= pd.Timedelta(days=reconstitution.weekday())
    return pd.DataFrame(
        {
            "reconstitution_time": [reconstitution] * len(symbols),
            "symbol": list(symbols),
            "liquidity_rank": np.arange(1, len(symbols) + 1),
            "trailing_quote_volume": np.linspace(1.0e9, 1.0e8, len(symbols)),
        }
    )


def _strategy_market(
    *,
    decision_time: pd.Timestamp = DECISION_TIME,
    symbol_count: int = 24,
    completed_history: int = 110,
    future_slots: int = 12,
) -> dict[str, object]:
    symbols = ("BTCUSDT",) + tuple(f"C{index:02d}USDT" for index in range(symbol_count - 1))
    open_times = pd.date_range(
        start=decision_time - completed_history * INTERVAL,
        periods=completed_history + future_slots + 1,
        freq=INTERVAL,
        tz="UTC",
    )
    # Multiplication by seven permutes 0..23 and keeps auction geometry independent of the
    # smooth return/liquidity nuisances used in the fixture.
    alpha_order = np.asarray([(index * 7) % symbol_count for index in range(symbol_count)])
    bar_frames: list[pd.DataFrame] = []
    mark_rows: list[dict[str, object]] = []
    for symbol_index, symbol in enumerate(symbols):
        previous_close = 80.0 + 3.0 * symbol_index
        alpha = (alpha_order[symbol_index] - (symbol_count - 1) / 2.0) / ((symbol_count - 1) / 2.0)
        rows: list[dict[str, object]] = []
        for time_index, open_time in enumerate(open_times):
            gap = 0.00025 * math.sin(0.17 * time_index + 0.11 * symbol_index)
            open_price = previous_close * math.exp(gap)
            close_return = 0.002 * math.sin(
                0.31 * time_index + 0.27 * symbol_index
            ) + 0.00045 * math.cos(0.09 * time_index * (symbol_index + 1))
            close_price = open_price * math.exp(close_return)
            high = max(open_price, close_price) * (1.001 + 0.0045 * max(-alpha, 0.0))
            low = min(open_price, close_price) * (1.0 - (0.001 + 0.0045 * max(alpha, 0.0)))
            quote_volume = 25_000_000.0 * (1.0 + 0.015 * symbol_index)
            rows.append(
                {
                    "open_time": open_time,
                    "close_time": open_time + INTERVAL,
                    "symbol": symbol,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close_price,
                    "quote_volume": quote_volume,
                }
            )
            mark_rows.append({"mark_time": open_time, "symbol": symbol, "mark_price": open_price})
            previous_close = close_price
        bar_frames.append(pd.DataFrame(rows))
    bars = pd.concat(bar_frames, ignore_index=True).sort_values(
        ["open_time", "symbol"], kind="mergesort"
    )

    funding_rows: list[dict[str, object]] = []
    for funding_time in pd.date_range(
        start=decision_time - 2 * INTERVAL,
        end=decision_time + future_slots * INTERVAL,
        freq=INTERVAL,
        tz="UTC",
    ):
        for symbol_index, symbol in enumerate(symbols):
            funding_rows.append(
                {
                    "funding_time": funding_time,
                    "symbol": symbol,
                    "funding_rate": (symbol_index - symbol_count / 2.0) * 1.0e-6,
                    "mark_price": 100.0 + symbol_index,
                }
            )
    return {
        "symbols": symbols,
        "bars": bars.reset_index(drop=True),
        "funding": pd.DataFrame(funding_rows),
        "membership": _membership(symbols, decision_time),
        "marks": pd.DataFrame(mark_rows),
    }


def _context_from_market(market: dict[str, object], decision_time: pd.Timestamp) -> DecisionContext:
    bars = market["bars"]
    funding = market["funding"]
    symbols = market["symbols"]
    assert isinstance(bars, pd.DataFrame)
    assert isinstance(funding, pd.DataFrame)
    assert isinstance(symbols, tuple)
    by_symbol: dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        frame = bars[bars["symbol"] == symbol]
        by_symbol[symbol] = frame[frame["close_time"] <= decision_time].reset_index(drop=True)
    past_funding = funding[funding["funding_time"] < decision_time].reset_index(drop=True)
    return DecisionContext(
        decision_time=decision_time,
        bars=by_symbol,
        funding=past_funding,
        auxiliary={},
        eligible_symbols=symbols,
    )


def _frame_digest(frame: pd.DataFrame) -> str:
    canonical = frame.copy()
    canonical.index = canonical.index.map(str)
    payload = canonical.to_csv(index=True, float_format="%.17g", lineterminator="\n").encode()
    return hashlib.sha256(payload).hexdigest()


def _deterministic_artifact_hashes() -> dict[str, str]:
    market = _strategy_market(future_slots=4)
    decisions = [DECISION_TIME + offset * INTERVAL for offset in range(4)]
    targets = generate_targets(
        STRATEGY.build_strategy(),
        market["bars"],
        market["funding"],
        market["membership"],
        decisions,
        seed=SEED,
    )
    base, doubled = evaluate_base_and_double_cost(
        market["bars"],
        market["funding"],
        market["membership"],
        targets,
        mark_prices=market["marks"],
    )
    hashes = {
        "targets": _frame_digest(targets),
        "positions": _frame_digest(base.positions),
        "returns": _frame_digest(base.returns),
        "double_cost_returns": _frame_digest(doubled.returns),
    }
    hashes["manifest"] = hashlib.sha256(
        json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return hashes


def _execution_market(
    *, quote_volume: float = 100_000_000.0
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, tuple[str, ...]]:
    symbols = ("AAAUSDT", "BBBUSDT")
    times = pd.date_range(
        start=DECISION_TIME - 3 * INTERVAL,
        periods=7,
        freq=INTERVAL,
        tz="UTC",
    )
    rows: list[dict[str, object]] = []
    marks: list[dict[str, object]] = []
    for symbol_index, symbol in enumerate(symbols):
        for time_index, timestamp in enumerate(times):
            open_price = (
                100.0 + 2.0 * symbol_index + (1.0 if symbol_index == 0 else -1.0) * time_index
            )
            rows.append(
                {
                    "open_time": timestamp,
                    "symbol": symbol,
                    "open": open_price,
                    "high": open_price * 1.01,
                    "low": open_price * 0.99,
                    "close": open_price * (1.002 if symbol_index == 0 else 0.998),
                    "quote_volume": quote_volume,
                }
            )
            marks.append({"mark_time": timestamp, "symbol": symbol, "mark_price": open_price})
    funding = pd.DataFrame(
        [
            {
                "funding_time": DECISION_TIME + INTERVAL,
                "symbol": symbol,
                "funding_rate": 0.001,
                "mark_price": 104.0,
            }
            for symbol in symbols
        ]
    )
    return (
        pd.DataFrame(rows),
        funding,
        _membership(symbols),
        pd.DataFrame(marks),
        symbols,
    )


def _explicit_targets(rows: list[dict[str, float]], times: list[pd.Timestamp]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, index=pd.DatetimeIndex(times))
    frame[REBALANCE_INSTRUCTION_COLUMN] = True
    return frame


def test_factory_is_fresh_and_seed_is_pinned() -> None:
    first = STRATEGY.build_strategy()
    second = STRATEGY.build_strategy()
    assert first is not second
    market = _strategy_market()
    with pytest.raises(ValueError, match="requires seed"):
        first.target_weights(_context_from_market(market, DECISION_TIME), seed=1)


def test_canonical_utc_datetimes_use_identity_fast_path() -> None:
    values = pd.Series(pd.date_range(DECISION_TIME, periods=3, freq=INTERVAL))

    assert STRATEGY._datetime_series(values) is values


def test_history_is_tailed_before_column_projection() -> None:
    calls: list[tuple[str, int]] = []

    class TailFirstFrame:
        def __init__(self, label: str, frame: pd.DataFrame) -> None:
            self.label = label
            self.frame = frame
            self.columns = frame.columns

        @property
        def empty(self) -> bool:
            return self.frame.empty

        @property
        def loc(self) -> object:
            raise AssertionError("full-history column projection happened before tail")

        def tail(self, rows: int) -> pd.DataFrame:
            calls.append((self.label, rows))
            return self.frame.tail(rows)

    open_times = pd.date_range(
        end=DECISION_TIME - INTERVAL,
        periods=129,
        freq=INTERVAL,
        tz="UTC",
    )
    bars = pd.DataFrame(
        {
            "open_time": open_times,
            "open": np.full(len(open_times), 100.0),
            "high": np.full(len(open_times), 101.0),
            "low": np.full(len(open_times), 99.0),
            "close": np.full(len(open_times), 100.5),
            "quote_volume": np.full(len(open_times), 1_000_000.0),
        }
    )
    normalised = STRATEGY._normalise_symbol_bars(
        TailFirstFrame("bars", bars), DECISION_TIME
    )
    assert len(normalised) == 128

    funding_times = pd.date_range(
        end=DECISION_TIME - INTERVAL,
        periods=4097,
        freq=INTERVAL,
        tz="UTC",
    )
    funding = pd.DataFrame(
        {
            "symbol": "AAAUSDT",
            "funding_time": funding_times,
            "funding_rate": np.full(len(funding_times), 0.001),
        }
    )
    features = STRATEGY._funding_features(
        TailFirstFrame("funding", funding), ("AAAUSDT",), DECISION_TIME
    )
    assert features["AAAUSDT"] == (0.001, 0.0)
    assert calls == [("bars", 128), ("funding", 4096)]


def test_auction_geometry_body_confirmation_and_gap_rules() -> None:
    index = pd.date_range(_utc_date(2023, 1, 1), periods=13, freq=INTERVAL)
    rows = pd.DataFrame(
        {
            "open": np.full(13, 100.0),
            "high": np.full(13, 103.0),
            "low": np.full(13, 95.0),
            "close": np.full(13, 102.0),
            "quote_volume": np.full(13, 1_000_000.0),
            "_present": np.ones(13, dtype=bool),
        },
        index=index,
    )
    # u=1/8, d=5/8, b=2/8, so q=(1/2)*(1+1/8)=0.5625.
    assert STRATEGY._auction_score(rows) == pytest.approx(0.5625)

    one_gap = rows.copy()
    one_gap.iloc[4, one_gap.columns.get_loc("_present")] = False
    # The missing bar invalidates its q and the following predecessor-dependent q, leaving ten.
    assert STRATEGY._auction_score(one_gap) == pytest.approx(0.5625)
    two_gaps = rows.copy()
    two_gaps.iloc[[3, 8], two_gaps.columns.get_loc("_present")] = False
    assert STRATEGY._auction_score(two_gaps) is None

    gap_range = rows.copy()
    gap_range.iloc[0, gap_range.columns.get_loc("close")] = 90.0
    score = STRATEGY._auction_score(gap_range)
    q_gap = (4.0 / 13.0) * (1.0 + 0.5 * (2.0 / 13.0))
    expected = np.median([q_gap] + [0.5625] * 11)
    assert score == pytest.approx(expected)


def test_log_return_windows_and_demeaned_beta_are_exact() -> None:
    btc_returns = 0.008 * np.sin(np.arange(63) * 0.37) + np.linspace(-0.002, 0.002, 63)
    symbol_returns = 2.0 * btc_returns + 0.0003

    def rows_from_returns(returns: np.ndarray) -> pd.DataFrame:
        closes = 100.0 * np.exp(np.r_[0.0, np.cumsum(returns)])
        opens = closes * math.exp(-0.0005)
        return pd.DataFrame(
            {
                "open": opens,
                "high": np.maximum(opens, closes) * 1.005,
                "low": np.minimum(opens, closes) * 0.98,
                "close": closes,
                "quote_volume": np.full(64, 2_000_000.0),
                "_present": np.ones(64, dtype=bool),
            },
            index=pd.date_range(_utc_date(2022, 1, 1), periods=64, freq=INTERVAL),
        )

    btc_rows = rows_from_returns(btc_returns)
    symbol_rows = rows_from_returns(symbol_returns)
    recovered_btc = STRATEGY._adjacent_log_returns(btc_rows)
    np.testing.assert_allclose(recovered_btc, btc_returns, rtol=0.0, atol=2.5e-16)
    features = STRATEGY._symbol_features(symbol_rows, recovered_btc)
    assert features is not None
    assert features["r24"] == pytest.approx(symbol_returns[-3:].sum())
    assert features["r7d"] == pytest.approx(symbol_returns[-21:].sum())
    assert features["volatility"] == pytest.approx(
        math.sqrt(1095.0 * np.mean(np.square(symbol_returns[-21:])))
    )
    assert features["beta"] == pytest.approx(2.0, abs=1.0e-12)

    broken = symbol_rows.copy()
    broken.iloc[-10, broken.columns.get_loc("_present")] = False
    broken_returns = STRATEGY._adjacent_log_returns(broken)
    assert np.isnan(broken_returns[-10:-8]).all()
    assert STRATEGY._symbol_features(broken, recovered_btc) is None


def test_funding_strict_lag_age_and_missing_indicator() -> None:
    symbols = ("AAAUSDT", "BBBUSDT", "CCCUSDT", "DDDUSDT")
    funding = pd.DataFrame(
        [
            {
                "symbol": "AAAUSDT",
                "funding_time": DECISION_TIME - pd.Timedelta(hours=16),
                "funding_rate": 0.001,
            },
            {
                "symbol": "BBBUSDT",
                "funding_time": DECISION_TIME - pd.Timedelta(hours=16, seconds=1),
                "funding_rate": 0.002,
            },
            {"symbol": "CCCUSDT", "funding_time": DECISION_TIME, "funding_rate": 0.003},
        ]
    )
    result = STRATEGY._funding_features(funding, symbols, DECISION_TIME)
    assert result["AAAUSDT"] == (0.001, 0.0)
    assert result["BBBUSDT"] == (0.0, 1.0)
    assert result["CCCUSDT"] == (0.0, 1.0)
    assert result["DDDUSDT"] == (0.0, 1.0)


def test_robust_z_and_zero_alpha_mad_rule(monkeypatch: pytest.MonkeyPatch) -> None:
    values = np.asarray([0.0, 1.0, 2.0, 100.0])
    z, mad = STRATEGY._robust_z(values)
    expected_median = 1.5
    expected_mad = 1.0
    np.testing.assert_allclose(
        z,
        np.clip((values - expected_median) / (1.4826 * expected_mad), -3.0, 3.0),
    )
    assert mad == expected_mad
    zero, zero_mad = STRATEGY._robust_z(np.ones(12))
    assert zero_mad == 0.0
    assert np.array_equal(zero, np.zeros(12))

    market = _strategy_market()
    monkeypatch.setattr(STRATEGY, "_auction_score", lambda _rows: 0.25)
    output = STRATEGY.build_strategy().target_weights(
        _context_from_market(market, DECISION_TIME), seed=SEED
    )
    assert output == {}


def test_tail_hysteresis_retains_then_fills_extremes() -> None:
    symbols = [f"S{index:02d}" for index in range(20)]
    frame = pd.DataFrame({"percentile": np.linspace(0.0, 1.0, len(symbols))}, index=symbols)
    prior_longs = frozenset({"S12", "S18"})
    prior_shorts = frozenset({"S00", "S01", "S08"})
    longs, shorts = STRATEGY._select_tails(frame, prior_longs, prior_shorts)
    # N=20 gives K=3. S12 is retained above 0.55 even though it is below the 0.80 entry gate;
    # the remaining vacancy is filled by the strongest new extreme S19.
    assert longs == frozenset({"S12", "S18", "S19"})
    # S08 remains below 0.45 despite being outside the 0.20 new-entry tail.
    assert shorts == frozenset({"S00", "S01", "S08"})


def _qp_cross_section(
    symbols: tuple[str, ...],
    beta: list[float],
    funding: list[float],
    *,
    beta_on: bool,
    funding_on: bool,
) -> object:
    frame = pd.DataFrame(
        {
            "z_beta": beta,
            "z_funding": funding,
            "percentile": np.linspace(0.0, 1.0, len(symbols)),
        },
        index=symbols,
    )
    return STRATEGY._CrossSection(frame, beta_on, funding_on)


def test_qp_constraints_and_deterministic_fallbacks() -> None:
    symbols = ("L0", "L1", "L2", "S0", "S1", "S2")
    longs = frozenset(symbols[:3])
    shorts = frozenset(symbols[3:])
    feasible = _qp_cross_section(
        symbols,
        [-1.0, 0.0, 1.0, -1.0, 0.0, 1.0],
        [1.0, -1.0, 0.0, 1.0, -1.0, 0.0],
        beta_on=True,
        funding_on=True,
    )
    first = STRATEGY._solve_qp(feasible, longs, shorts, {}, False)
    second = STRATEGY._solve_qp(feasible, longs, shorts, {}, False)
    assert first is not None and second is not None
    weights, level = first
    assert level == 1
    assert weights == second[0]
    vector = np.asarray([weights[symbol] for symbol in symbols])
    assert vector.sum() == pytest.approx(0.0, abs=1.0e-10)
    assert np.abs(vector).sum() == pytest.approx(0.36, abs=1.0e-10)
    assert np.dot(feasible.frame["z_beta"], vector) == pytest.approx(0.0, abs=1.0e-8)
    assert np.dot(feasible.frame["z_funding"], vector) == pytest.approx(0.0, abs=1.0e-8)
    assert np.max(np.abs(vector)) <= 0.08 + 1.0e-10

    side_factor = [1.0, 1.0, 1.0, -1.0, -1.0, -1.0]
    funding_infeasible = _qp_cross_section(
        symbols,
        [0.0] * 6,
        side_factor,
        beta_on=False,
        funding_on=True,
    )
    dropped_funding = STRATEGY._solve_qp(funding_infeasible, longs, shorts, {}, False)
    assert dropped_funding is not None and dropped_funding[1] == 2

    beta_infeasible = _qp_cross_section(
        symbols,
        side_factor,
        [0.0] * 6,
        beta_on=True,
        funding_on=False,
    )
    dropped_beta = STRATEGY._solve_qp(beta_infeasible, longs, shorts, {}, False)
    assert dropped_beta is not None and dropped_beta[1] == 3


def test_stress_estimator_and_hysteresis_equalities() -> None:
    index = pd.date_range(_utc_date(2022, 1, 1), periods=90, freq=INTERVAL)
    ratio = math.exp(math.sqrt(0.70**2 * 4.0 * math.log(2.0) / 1095.0))
    rows = pd.DataFrame(
        {
            "high": np.full(90, ratio),
            "low": np.ones(90),
            "_present": np.ones(90, dtype=bool),
        },
        index=index,
    )
    assert STRATEGY._stress_value(rows) == pytest.approx(0.70)
    assert STRATEGY._next_stress(False, 0.80) is False
    assert STRATEGY._next_stress(False, 0.8000001) is True
    assert STRATEGY._next_stress(True, 0.65) is True
    assert STRATEGY._next_stress(True, 0.6499999) is False
    assert STRATEGY._next_stress(False, None) is True
    missing = rows.copy()
    missing.loc[missing.index[:16], "_present"] = False
    assert STRATEGY._stress_value(missing) is None


def test_state_machine_72h_refresh_stress_and_membership_loss(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    symbols = ("BTCUSDT",) + tuple(f"S{index:02d}USDT" for index in range(19))
    bare_frame = pd.DataFrame(
        {
            "open_time": [DECISION_TIME - INTERVAL],
            "close_time": [DECISION_TIME],
            "open": [100.0],
            "high": [101.0],
            "low": [99.0],
            "close": [100.0],
            "quote_volume": [1_000_000.0],
        }
    )
    bars = {symbol: bare_frame.copy() for symbol in symbols}
    volatility = [0.50]

    def fake_cross(_context: DecisionContext, normalised: dict[str, pd.DataFrame]) -> object:
        active = tuple(sorted(normalised))
        frame = pd.DataFrame(
            {
                "percentile": np.linspace(0.0, 1.0, len(active)),
                "z_beta": np.zeros(len(active)),
                "z_funding": np.zeros(len(active)),
            },
            index=active,
        )
        return STRATEGY._CrossSection(frame, False, False)

    monkeypatch.setattr(STRATEGY, "_build_cross_section", fake_cross)
    monkeypatch.setattr(STRATEGY, "_stress_value", lambda _rows: volatility[0])
    strategy = STRATEGY.build_strategy()

    def context_at(timestamp: pd.Timestamp, active: tuple[str, ...] = symbols) -> DecisionContext:
        shifted = {}
        for symbol in active:
            frame = bars[symbol].copy()
            delta = timestamp - DECISION_TIME
            frame["open_time"] += delta
            frame["close_time"] += delta
            shifted[symbol] = frame
        return DecisionContext(timestamp, shifted, pd.DataFrame(), {}, active)

    first = strategy.target_weights(context_at(DECISION_TIME), seed=SEED)
    assert first is not None and first
    assert strategy.target_weights(context_at(DECISION_TIME + INTERVAL), seed=SEED) is None
    refreshed = strategy.target_weights(
        context_at(DECISION_TIME + pd.Timedelta(hours=72)), seed=SEED
    )
    assert refreshed is not None and refreshed

    volatility[0] = 0.81
    stressed = strategy.target_weights(
        context_at(DECISION_TIME + pd.Timedelta(hours=80)), seed=SEED
    )
    assert stressed is not None and stressed
    volatility[0] = 0.65
    assert (
        strategy.target_weights(context_at(DECISION_TIME + pd.Timedelta(hours=88)), seed=SEED)
        is None
    )
    volatility[0] = 0.64
    exited = strategy.target_weights(context_at(DECISION_TIME + pd.Timedelta(hours=96)), seed=SEED)
    assert exited is not None and exited

    removed = max(exited, key=exited.get)
    active = tuple(symbol for symbol in symbols if symbol != removed)
    after_membership_loss = strategy.target_weights(
        context_at(DECISION_TIME + pd.Timedelta(hours=104), active), seed=SEED
    )
    assert after_membership_loss is not None
    assert removed not in after_membership_loss


def test_real_strategy_targets_are_finite_signed_neutral_and_capped() -> None:
    market = _strategy_market()
    context = _context_from_market(market, DECISION_TIME)
    first = STRATEGY.build_strategy().target_weights(context, seed=SEED)
    second = STRATEGY.build_strategy().target_weights(context, seed=SEED)
    assert first == second
    assert first is not None and first
    weights = np.asarray(list(first.values()))
    assert np.isfinite(weights).all()
    assert (weights > 0.0).sum() >= 2
    assert (weights < 0.0).sum() >= 2
    assert abs(weights.sum()) <= 1.0e-8
    assert np.abs(weights).sum() <= 0.72 + 1.0e-8
    assert np.max(np.abs(weights)) <= 0.08 + 1.0e-8
    assert set(first).issubset(context.eligible_symbols)


@pytest.mark.parametrize("variant", ["truncate", "corrupt_future", "append_future"])
def test_target_history_invariance(variant: str) -> None:
    market = _strategy_market(future_slots=16)
    baseline_bars = market["bars"]
    baseline_funding = market["funding"]
    assert isinstance(baseline_bars, pd.DataFrame)
    assert isinstance(baseline_funding, pd.DataFrame)

    if variant == "truncate":
        changed_bars = baseline_bars[baseline_bars["open_time"] <= DECISION_TIME].copy()
        changed_funding = baseline_funding[baseline_funding["funding_time"] < DECISION_TIME].copy()
        reference_bars = baseline_bars
        reference_funding = baseline_funding
    elif variant == "corrupt_future":
        reference_bars = baseline_bars
        reference_funding = baseline_funding
        changed_bars = baseline_bars.copy()
        future = changed_bars["open_time"] >= DECISION_TIME
        changed_bars.loc[future, ["open", "high", "low", "close", "quote_volume"]] *= 17.0
        changed_funding = baseline_funding.copy()
        future_funding = changed_funding["funding_time"] >= DECISION_TIME
        changed_funding.loc[future_funding, "funding_rate"] += 0.25
        changed_funding.loc[future_funding, "mark_price"] *= 9.0
    else:
        reference_bars = baseline_bars[baseline_bars["open_time"] <= DECISION_TIME].copy()
        reference_funding = baseline_funding[
            baseline_funding["funding_time"] < DECISION_TIME
        ].copy()
        changed_bars = baseline_bars
        changed_funding = baseline_funding

    reference = generate_targets(
        STRATEGY.build_strategy(),
        reference_bars,
        reference_funding,
        market["membership"],
        [DECISION_TIME],
        seed=SEED,
    )
    changed = generate_targets(
        STRATEGY.build_strategy(),
        changed_bars,
        changed_funding,
        market["membership"],
        [DECISION_TIME],
        seed=SEED,
    )
    assert _frame_digest(reference) == _frame_digest(changed)
    pd.testing.assert_frame_equal(reference, changed, check_exact=True)


def test_context_contains_only_closed_bars_and_strictly_prior_funding() -> None:
    market = _strategy_market(future_slots=2)

    class AuditStrategy:
        def __init__(self) -> None:
            self.called = False

        def target_weights(self, context: DecisionContext, *, seed: int) -> dict[str, float]:
            self.called = True
            for frame in context.bars.values():
                assert (frame["open_time"] + INTERVAL <= context.decision_time).all()
                assert not (frame["open_time"] == context.decision_time).any()
            assert (context.funding["funding_time"] < context.decision_time).all()
            return {}

    audit = AuditStrategy()
    targets = generate_targets(
        audit,
        market["bars"],
        market["funding"],
        market["membership"],
        [DECISION_TIME],
        seed=SEED,
    )
    assert audit.called
    assert bool(targets.loc[DECISION_TIME, REBALANCE_INSTRUCTION_COLUMN])


def test_point_in_time_top40_uses_prior_complete_dates_only() -> None:
    reconstitution = DECISION_TIME
    prior_dates = pd.date_range(
        end=reconstitution - pd.Timedelta(days=1), periods=30, freq="D", tz="UTC"
    )
    rows: list[dict[str, object]] = []
    for date in prior_dates:
        for hour in (0, 8, 16):
            for symbol, volume in (("AAAUSDT", 100.0), ("BBBUSDT", 50.0)):
                rows.append(
                    {
                        "open_time": date + pd.Timedelta(hours=hour),
                        "symbol": symbol,
                        "quote_volume": volume,
                    }
                )
    # This same-day observation must not enter the completed-prior-date ranking.
    rows.append({"open_time": reconstitution, "symbol": "BBBUSDT", "quote_volume": 1.0e12})
    metadata = pd.DataFrame(
        {
            "symbol": ["AAAUSDT", "BBBUSDT"],
            "contract_type": ["PERPETUAL", "PERPETUAL"],
            "quote_asset": ["USDT", "USDT"],
            "margin_asset": ["USDT", "USDT"],
            "is_crypto": [True, True],
            "onboard_date": [_utc_date(2020, 1, 1)] * 2,
            "delivery_date": [pd.NaT, pd.NaT],
        }
    )
    membership = point_in_time_top40(pd.DataFrame(rows), metadata, [reconstitution], top_n=1)
    assert membership["symbol"].tolist() == ["AAAUSDT"]


def test_next_open_funding_signs_costs_and_long_short_pnl() -> None:
    bars, funding, membership, marks, symbols = _execution_market()
    times = [DECISION_TIME + offset * INTERVAL for offset in range(3)]
    targets = _explicit_targets(
        [
            {symbols[0]: 0.05, symbols[1]: -0.05},
            {symbols[0]: -0.04, symbols[1]: 0.04},
            {symbols[0]: 0.0, symbols[1]: 0.0},
        ],
        times,
    )
    result = evaluate_targets(bars, funding, membership, targets, mark_prices=marks)
    trades = result.events[result.events["event_type"] == "trade"]
    first_trades = trades[trades["timestamp"] == DECISION_TIME]
    assert set(first_trades["symbol"]) == set(symbols)
    expected_open = bars[bars["open_time"] == DECISION_TIME].set_index("symbol")["open"]
    for row in first_trades.itertuples(index=False):
        assert row.price == expected_open[row.symbol]
        assert row.fee > 0.0 and row.slippage > 0.0
    assert set(trades["timestamp"]) == set(times)
    assert (trades["fee"] > 0.0).all()
    assert (trades["slippage"] > 0.0).all()

    boundary_funding = result.events[
        (result.events["event_type"] == "funding")
        & (result.events["timestamp"] == DECISION_TIME + INTERVAL)
    ].set_index("symbol")
    assert boundary_funding.at[symbols[0], "quantity"] > 0.0
    assert boundary_funding.at[symbols[0], "cashflow"] < 0.0
    assert boundary_funding.at[symbols[1], "quantity"] < 0.0
    assert boundary_funding.at[symbols[1], "cashflow"] > 0.0
    assert result.returns["long_price_pnl"].abs().sum() > 0.0
    assert result.returns["short_price_pnl"].abs().sum() > 0.0
    assert (result.positions.clip(lower=0.0).sum(axis=1) > 0.0).any()
    assert (-result.positions.clip(upper=0.0).sum(axis=1) > 0.0).any()
    assert trades.loc[trades["notional"] > 0.0, "notional"].sum() > 1_000.0
    assert -trades.loc[trades["notional"] < 0.0, "notional"].sum() > 1_000.0


def test_double_cost_is_fresh_and_doubles_fee_slippage_not_funding() -> None:
    bars, funding, membership, marks, symbols = _execution_market()
    times = [DECISION_TIME + offset * INTERVAL for offset in range(3)]
    targets = _explicit_targets(
        [
            {symbols[0]: 0.05, symbols[1]: -0.05},
            {symbols[0]: 0.05, symbols[1]: -0.05},
            {symbols[0]: 0.0, symbols[1]: 0.0},
        ],
        times,
    )
    base, doubled = evaluate_base_and_double_cost(
        bars, funding, membership, targets, mark_prices=marks
    )
    assert doubled.returns["fees"].sum() == pytest.approx(2.0 * base.returns["fees"].sum())
    assert doubled.returns["slippage"].sum() == pytest.approx(2.0 * base.returns["slippage"].sum())
    assert doubled.returns["funding_pnl"].iloc[0] == base.returns["funding_pnl"].iloc[0]
    assert not doubled.returns.equals(base.returns)


def test_participation_cap_carries_unfilled_gap() -> None:
    bars, funding, membership, marks, symbols = _execution_market(quote_volume=100_000.0)
    times = [DECISION_TIME, DECISION_TIME + INTERVAL]
    targets = _explicit_targets(
        [
            {symbols[0]: 0.05, symbols[1]: -0.05},
            {symbols[0]: 0.0, symbols[1]: 0.0},
        ],
        times,
    )
    result = evaluate_targets(bars, funding, membership, targets, mark_prices=marks)
    assert result.returns.iloc[0]["unfilled_notional"] > 0.0
    assert result.returns.iloc[0]["turnover"] < 0.01


def test_delist_exit_shares_capacity_and_residual_gets_haircut() -> None:
    symbols = ("AAAUSDT", "BBBUSDT")
    prior = DECISION_TIME - INTERVAL
    rows = [
        {
            "open_time": prior,
            "symbol": "AAAUSDT",
            "open": 100.0,
            "close": 100.0,
            "quote_volume": 10_000_000.0,
        },
        {
            "open_time": prior,
            "symbol": "BBBUSDT",
            "open": 100.0,
            "close": 100.0,
            "quote_volume": 10_000_000.0,
        },
        {
            "open_time": DECISION_TIME,
            "symbol": "AAAUSDT",
            "open": 100.0,
            "close": 100.0,
            "quote_volume": 6_000_000.0,
        },
        {
            "open_time": DECISION_TIME,
            "symbol": "BBBUSDT",
            "open": 100.0,
            "close": 100.0,
            "quote_volume": 10_000_000.0,
        },
        {
            "open_time": DECISION_TIME + INTERVAL,
            "symbol": "BBBUSDT",
            "open": 100.0,
            "close": 100.0,
            "quote_volume": 10_000_000.0,
        },
    ]
    bars = pd.DataFrame(rows)
    marks = pd.DataFrame(
        [{"mark_time": DECISION_TIME, "symbol": symbol, "mark_price": 100.0} for symbol in symbols]
        + [{"mark_time": DECISION_TIME + INTERVAL, "symbol": "BBBUSDT", "mark_price": 100.0}]
    )
    targets = _explicit_targets(
        [
            {"AAAUSDT": 0.05, "BBBUSDT": -0.05},
            {"AAAUSDT": 0.0, "BBBUSDT": 0.0},
        ],
        [DECISION_TIME, DECISION_TIME + INTERVAL],
    )
    funding = pd.DataFrame(columns=["funding_time", "symbol", "funding_rate", "mark_price"])
    result = evaluate_targets(
        bars,
        funding,
        _membership(symbols),
        targets,
        mark_prices=marks,
    )
    forced = result.events[result.events["event_type"] == "forced_exit"]
    settlement = result.events[result.events["event_type"] == "conservative_settlement"]
    assert not forced.empty and forced.iloc[0]["fee"] > 0.0 and forced.iloc[0]["slippage"] > 0.0
    assert not settlement.empty and settlement.iloc[0]["cashflow"] < 0.0
    assert result.returns.iloc[0]["forced_exit_unfilled_notional"] > 0.0
    assert result.returns.iloc[0]["conservative_settlement_loss"] > 0.0


def test_nonfinite_caps_missing_prices_and_duplicates_fail_closed() -> None:
    bars, funding, membership, marks, symbols = _execution_market()
    times = [DECISION_TIME, DECISION_TIME + INTERVAL]
    valid = _explicit_targets(
        [{symbols[0]: 0.05, symbols[1]: -0.05}, {symbols[0]: 0.0, symbols[1]: 0.0}],
        times,
    )
    for nonfinite in (np.nan, np.inf, -np.inf):
        bad = valid.copy()
        bad.loc[DECISION_TIME, symbols[0]] = nonfinite
        with pytest.raises(ValueError, match="non-finite"):
            evaluate_targets(bars, funding, membership, bad, mark_prices=marks)

    class BadStrategy:
        def __init__(self, value: float) -> None:
            self.value = value

        def target_weights(self, context: DecisionContext, *, seed: int) -> dict[str, float]:
            return {context.eligible_symbols[0]: self.value}

    market = _strategy_market(future_slots=1)
    for nonfinite in (np.nan, np.inf, -np.inf):
        with pytest.raises(ValueError, match="non-finite"):
            generate_targets(
                BadStrategy(nonfinite),
                market["bars"],
                market["funding"],
                market["membership"],
                [DECISION_TIME],
                seed=SEED,
            )

    config = EvaluatorConfig()
    with pytest.raises(ValueError, match="gross exposure"):
        _validate_weight_limits(pd.Series([0.6, -0.6]), config, DECISION_TIME)
    with pytest.raises(ValueError, match="net exposure"):
        _validate_weight_limits(pd.Series([0.09, 0.09, 0.09]), config, DECISION_TIME)
    with pytest.raises(ValueError, match="symbol exposure"):
        _validate_weight_limits(pd.Series([0.11, -0.11]), config, DECISION_TIME)

    missing_mark = marks[~((marks["mark_time"] == DECISION_TIME) & (marks["symbol"] == symbols[0]))]
    with pytest.raises(ValueError, match="missing current mark for eligible"):
        evaluate_targets(bars, funding, membership, valid, mark_prices=missing_mark)
    duplicate = pd.concat([bars, bars.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        evaluate_targets(duplicate, funding, membership, valid, mark_prices=marks)


def test_empty_mapping_is_explicit_flat_and_none_is_hold() -> None:
    market = _strategy_market(future_slots=2)

    class SparseStrategy:
        def __init__(self) -> None:
            self.calls = 0

        def target_weights(self, context: DecisionContext, *, seed: int) -> dict[str, float] | None:
            self.calls += 1
            return {} if self.calls == 1 else None

    times = [DECISION_TIME, DECISION_TIME + INTERVAL]
    output = generate_targets(
        SparseStrategy(),
        market["bars"],
        market["funding"],
        market["membership"],
        times,
        seed=SEED,
    )
    assert bool(output.loc[times[0], REBALANCE_INSTRUCTION_COLUMN])
    assert not bool(output.loc[times[1], REBALANCE_INSTRUCTION_COLUMN])

    too_small = _strategy_market(symbol_count=9)
    assert (
        STRATEGY.build_strategy().target_weights(
            _context_from_market(too_small, DECISION_TIME), seed=SEED
        )
        == {}
    )


def test_two_clean_processes_reproduce_targets_positions_returns_and_manifest() -> None:
    code = (
        "import importlib.util,json,sys;"
        f"p={str(Path(__file__).resolve())!r};"
        "s=importlib.util.spec_from_file_location('team05_qe_clean',p);"
        "m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);"
        "print(json.dumps(m._deterministic_artifact_hashes(),sort_keys=True))"
    )
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONHASHSEED"] = "0"
    commands = [sys.executable, "-c", code]
    first = subprocess.run(
        commands,
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    second = subprocess.run(
        commands,
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert first == second
    assert json.loads(first) == _deterministic_artifact_hashes()


def test_strategy_source_is_public_data_only_and_has_no_side_effect_capabilities() -> None:
    source = STRATEGY_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            called_names.add(node.func.id)
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
    assert called_names.isdisjoint({"open", "eval", "exec", "compile", "__import__"})
    forbidden_tokens = (
        "socket",
        "requests",
        "httpx",
        "urllib",
        "subprocess",
        "crypto_trade.portfolio",
    )
    assert all(token not in source for token in forbidden_tokens)
