"""Focused synthetic tests for Team 03's preregistration candidate."""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext

_STRATEGY_PATH = Path(__file__).with_name("strategy.py")
_SPEC = importlib.util.spec_from_file_location("team03_preregistered_strategy", _STRATEGY_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_STRATEGY = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _STRATEGY
_SPEC.loader.exec_module(_STRATEGY)
BTC_SYMBOL = _STRATEGY.BTC_SYMBOL
DEFAULT_PARAMETERS = _STRATEGY.DEFAULT_PARAMETERS
EXPECTED_SEED = _STRATEGY.EXPECTED_SEED
build_strategy = _STRATEGY.build_strategy
SYNTHETIC_SYMBOLS = tuple(f"ALT{number:02d}USDT" for number in range(24))
SYNTHETIC_SHOCKS = {
    symbol: float(shock)
    for symbol, shock in zip(
        SYNTHETIC_SYMBOLS,
        np.linspace(-0.12, 0.12, len(SYNTHETIC_SYMBOLS)),
        strict=True,
    )
}


def _decision(*, hour: int = 0) -> pd.Timestamp:
    return pd.Timestamp(year=2023, month=1, day=3, hour=hour, tz="UTC")


def _frame(
    decision_time: pd.Timestamp,
    *,
    shock: float,
    btc: bool = False,
    periods: int = 240,
) -> pd.DataFrame:
    open_times = pd.date_range(
        end=decision_time - pd.Timedelta(hours=8),
        periods=periods,
        freq="8h",
        tz="UTC",
    )
    index = np.arange(periods, dtype=float)
    common = 0.0008 + 0.003 * np.sin(index / 9.0)
    residual = np.zeros(periods) if btc else 0.0015 * np.cos(index / 7.0)
    log_returns = common + residual
    if not btc:
        log_returns[-3:] += shock / 3.0
    closes = 100.0 * np.exp(np.cumsum(log_returns))
    quote_volume = np.full(periods, 1_000_000.0)
    if not btc:
        quote_volume[-3:] = 5_000_000.0
    return pd.DataFrame(
        {
            "open_time": open_times,
            "close": closes,
            "quote_volume": quote_volume,
        }
    )


def _context(decision_time: pd.Timestamp) -> DecisionContext:
    bars = {BTC_SYMBOL: _frame(decision_time, shock=0.0, btc=True)}
    bars.update(
        {symbol: _frame(decision_time, shock=shock) for symbol, shock in SYNTHETIC_SHOCKS.items()}
    )
    return DecisionContext(
        decision_time=decision_time,
        bars=bars,
        funding=pd.DataFrame(columns=["funding_time", "symbol", "funding_rate"]),
        auxiliary={},
        eligible_symbols=(BTC_SYMBOL, *SYNTHETIC_SYMBOLS),
    )


def test_daily_schedule_holds_between_rebalances() -> None:
    context = _context(_decision(hour=8))
    assert build_strategy().target_weights(context, seed=EXPECTED_SEED) is None


def test_residual_exhaustion_builds_both_capped_sleeves_deterministically() -> None:
    context = _context(_decision())
    first = build_strategy().target_weights(context, seed=EXPECTED_SEED)
    second = build_strategy().target_weights(context, seed=EXPECTED_SEED)
    assert first == second
    assert first
    assert any(value > 0.0 for value in first.values())
    assert any(value < 0.0 for value in first.values())
    assert max(abs(value) for value in first.values()) <= 0.08
    assert math.isclose(sum(abs(value) for value in first.values()), 0.80)
    assert abs(sum(first.values())) <= 0.10 + 1.0e-12

    tail_count = max(
        DEFAULT_PARAMETERS.minimum_names_per_side,
        math.floor(len(SYNTHETIC_SYMBOLS) * DEFAULT_PARAMETERS.rank_tail_fraction),
    )
    ordered_by_shock = sorted(
        SYNTHETIC_SYMBOLS,
        key=lambda symbol: (SYNTHETIC_SHOCKS[symbol], symbol),
    )
    expected_longs = set(ordered_by_shock[:tail_count])
    expected_shorts = set(ordered_by_shock[-tail_count:])
    actual_longs = {symbol for symbol, weight in first.items() if weight > 0.0}
    actual_shorts = {symbol for symbol, weight in first.items() if weight < 0.0}
    assert actual_longs == expected_longs
    assert actual_shorts == expected_shorts


def test_rows_not_closed_by_the_boundary_cannot_change_targets() -> None:
    decision_time = _decision()
    context = _context(decision_time)
    baseline = build_strategy().target_weights(context, seed=EXPECTED_SEED)
    corrupted: dict[str, pd.DataFrame] = {}
    for symbol, frame in context.bars.items():
        future = pd.DataFrame(
            {
                "open_time": [decision_time],
                "close": [1.0e12 if symbol != BTC_SYMBOL else 1.0],
                "quote_volume": [1.0e15],
            }
        )
        corrupted[symbol] = pd.concat([frame, future], ignore_index=True)
    future_context = DecisionContext(
        decision_time=decision_time,
        bars=corrupted,
        funding=context.funding,
        auxiliary={},
        eligible_symbols=context.eligible_symbols,
    )
    assert build_strategy().target_weights(future_context, seed=EXPECTED_SEED) == baseline


def test_insufficient_cross_section_requests_flat_book() -> None:
    context = _context(_decision())
    symbols = tuple(context.eligible_symbols[:10])
    reduced = DecisionContext(
        decision_time=context.decision_time,
        bars={symbol: context.bars[symbol] for symbol in symbols},
        funding=context.funding,
        auxiliary={},
        eligible_symbols=symbols,
    )
    assert build_strategy().target_weights(reduced, seed=EXPECTED_SEED) == {}


def test_unexpected_seed_fails_closed() -> None:
    context = _context(_decision())
    try:
        build_strategy().target_weights(context, seed=EXPECTED_SEED + 1)
    except ValueError as exc:
        assert "unexpected seed" in str(exc)
    else:  # pragma: no cover - explicit fail-closed assertion
        raise AssertionError("unexpected seed was accepted")
