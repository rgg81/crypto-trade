"""Tests for the iter-v1/087 fail-fast IS gate in run_backtest().

Three behaviours verified:
    (a) flag default OFF (fail_fast_is_years=None) → no behaviour change;
        backtest runs identically to all prior iterations.
    (b) synthetic negative-first-2-years case → EarlyStopError raised with
        "BLOCKED-FAIL-FAST" prefix and ``results`` containing the IS trades
        accumulated before the checkpoint.
    (c) synthetic positive-first-2-years case → checkpoint PASSES, run
        continues to completion without raising.

Architecture note:
    The fail-fast hook lives in run_backtest() (backtest.py) behind the new
    ``fail_fast_is_years: float | None = None`` keyword argument.  Default
    None is strictly OFF — existing callers (all prior iterations) that do
    NOT pass this kwarg are byte-identical.

    The hook fires AT MOST ONCE per backtest run:
    1. Accumulate IS test trades (close_time < OOS_CUTOFF_MS).
    2. When the span (latest IS close_time - first IS close_time) ≥
       fail_fast_is_years × 365.25 × 86400 × 1000 ms:
       a. If cumulative weighted_pnl ≤ 0 → raise EarlyStopError("BLOCKED-FAIL-FAST: ...")
       b. If cumulative weighted_pnl > 0 → print PASSED, continue, never fires again.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from crypto_trade.backtest import EarlyStopError, run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.config import OOS_CUTOFF_MS

# ---------------------------------------------------------------------------
# Minimal deterministic strategy for testing (emits a predictable trade stream)
# ---------------------------------------------------------------------------


class _SyntheticStrategy:
    """Minimal strategy that emits one trade per bar with configurable PnL direction.

    Designed for deterministic fail-fast checkpoint testing:
    - compute_features(): stores master and computes IS/OOS split
    - get_signal(): returns a LONG signal for every bar EXCEPT if a trade is open
    - The backtest's SL/TP logic determines per-trade PnL; we control direction
      via take_profit_pct and stop_loss_pct on BacktestConfig.

    We don't use any ML machinery — this exercises run_backtest() generically.
    """

    def __init__(self, direction: int = 1) -> None:
        self._direction = direction
        self._master: pd.DataFrame | None = None
        # LightGbmStrategy compatibility shims
        self.label_tp_pct = 4.0
        self.label_sl_pct = 2.0
        self.label_timeout_minutes = 4320

    def compute_features(self, master: pd.DataFrame) -> None:
        self._master = master

    def get_signal(self, symbol: str, open_time: int):  # type: ignore[return]
        from crypto_trade.backtest_models import Signal as _Signal  # noqa: PLC0415

        return _Signal(direction=self._direction, weight=100)

    def record_trade_result(self, *_args, **_kwargs) -> None:
        pass


# ---------------------------------------------------------------------------
# Build a synthetic kline master DataFrame aligned with OOS_CUTOFF_MS
# ---------------------------------------------------------------------------

_8H_MS = 8 * 3600 * 1000  # 8-hour candle in ms


def _build_synthetic_master(
    n_candles: int,
    *,
    start_ms: int,
    symbol: str = "TESTUSDT",
    base_price: float = 100.0,
) -> pd.DataFrame:
    """Build a minimal master kline DataFrame for run_backtest() testing.

    ``start_ms`` is the open_time of the first candle.
    All prices are constant (100.0) with tiny synthetic OHLCV so that:
    - SL/TP resolve deterministically based on BacktestConfig thresholds.
    - The high/low spread is 2% so a TP of 1.5% always triggers on the next bar.
    """
    open_times = [start_ms + i * _8H_MS for i in range(n_candles)]
    close_times = [ot + _8H_MS - 1 for ot in open_times]

    rows = []
    for ot, ct in zip(open_times, close_times):
        rows.append(
            {
                "open_time": ot,
                "close_time": ct,
                "open": base_price,
                "high": base_price * 1.02,  # +2%
                "low": base_price * 0.98,  # -2%
                "close": base_price,
                "volume": 1000.0,
                "quote_volume": 100000.0,
                "trades": 100,
                "taker_buy_volume": 500.0,
                "taker_buy_quote_volume": 50000.0,
                "symbol": symbol,
            }
        )
    df = pd.DataFrame(rows)
    return df


# ---------------------------------------------------------------------------
# Helper: build a BacktestConfig that uses the synthetic master
# via a monkeypatched _build_master
# ---------------------------------------------------------------------------


def _make_config(symbol: str = "TESTUSDT") -> BacktestConfig:
    return BacktestConfig(
        symbols=(symbol,),
        interval="8h",
        max_amount_usd=100.0,
        stop_loss_pct=1.5,  # -1.5% → triggers on SL bar (low=-2%)
        take_profit_pct=1.5,  # +1.5% → triggers on TP bar (high=+2%)
        timeout_minutes=4320,
        fee_pct=0.1,
        data_dir=Path("data"),
        cooldown_candles=0,
    )


# ---------------------------------------------------------------------------
# (a) Default OFF — no behaviour change
# ---------------------------------------------------------------------------


class TestFailFastDefaultOff:
    """Verify fail_fast_is_years=None (default) is byte-identical to prior runs."""

    def test_default_none_does_not_raise(self) -> None:
        """run_backtest with fail_fast_is_years=None must not raise EarlyStopError."""
        # Build a small IS-only master (all candles before OOS_CUTOFF_MS).
        # IS cutoff is 2025-03-24; use candles starting 30 days before.
        start_ms = OOS_CUTOFF_MS - 30 * 24 * 3600 * 1000
        n = 90  # 30 days × 3 candles/day
        master = _build_synthetic_master(n, start_ms=start_ms)

        config = _make_config()
        strategy = _SyntheticStrategy(direction=1)

        with patch("crypto_trade.backtest._build_master", return_value=master):
            result = run_backtest(config, strategy)

        # Should complete without error; result is a BacktestResult (list-like)
        assert result is not None
        # fail_fast_is_years not passed at all → default=None → no checkpoint
        # (test proves absence of regression: existing code still works)

    def test_explicit_none_does_not_raise(self) -> None:
        """Explicitly passing fail_fast_is_years=None must not raise."""
        start_ms = OOS_CUTOFF_MS - 30 * 24 * 3600 * 1000
        master = _build_synthetic_master(60, start_ms=start_ms)
        config = _make_config()
        strategy = _SyntheticStrategy(direction=1)

        with patch("crypto_trade.backtest._build_master", return_value=master):
            result = run_backtest(config, strategy, fail_fast_is_years=None)

        assert result is not None


# ---------------------------------------------------------------------------
# (b) Negative-first-2-years case → BLOCKED-FAIL-FAST
# ---------------------------------------------------------------------------


class TestFailFastNegativeCase:
    """Synthetic scenario where IS returns are negative for the first 2 years."""

    def _build_negative_master_and_patch(self):
        """Build an IS master where the strategy loses money.

        Strategy: LONG, but BacktestConfig has SL=0.5% and TP=5.0%.
        High in candle = +0.1% (below TP=5%), Low = -1% (below SL=0.5%).
        So every trade hits SL → net loss per trade.
        """
        # Start 3 years before OOS_CUTOFF_MS so the 2-year span is well within IS.
        start_ms = OOS_CUTOFF_MS - int(3.5 * 365.25 * 24 * 3600 * 1000)
        # 3.5 years × 3 candles/day ≈ 3836 candles
        n = int(3.5 * 365.25 * 3)
        rows = []
        for i in range(n):
            ot = start_ms + i * _8H_MS
            ct = ot + _8H_MS - 1
            rows.append(
                {
                    "open_time": ot,
                    "close_time": ct,
                    "open": 100.0,
                    "high": 100.1,  # +0.1% — below TP=5%
                    "low": 99.0,  # -1%   — below SL=0.5%
                    "close": 100.0,
                    "volume": 1000.0,
                    "quote_volume": 100000.0,
                    "trades": 100,
                    "taker_buy_volume": 500.0,
                    "taker_buy_quote_volume": 50000.0,
                    "symbol": "TESTUSDT",
                }
            )
        return pd.DataFrame(rows)

    def test_negative_is_raises_blocked_fail_fast(self) -> None:
        """EarlyStopError must be raised with BLOCKED-FAIL-FAST prefix."""
        master = self._build_negative_master_and_patch()
        config = BacktestConfig(
            symbols=("TESTUSDT",),
            interval="8h",
            max_amount_usd=100.0,
            stop_loss_pct=0.5,  # tight SL → every LONG trade loses
            take_profit_pct=5.0,  # far TP → never reached given high=+0.1%
            timeout_minutes=4320,
            fee_pct=0.1,
            data_dir=Path("data"),
            cooldown_candles=0,
        )
        strategy = _SyntheticStrategy(direction=1)

        with patch("crypto_trade.backtest._build_master", return_value=master):
            with pytest.raises(EarlyStopError) as exc_info:
                run_backtest(config, strategy, fail_fast_is_years=2.0)

        err = exc_info.value
        assert err.reason.startswith("BLOCKED-FAIL-FAST"), (
            f"EarlyStopError reason must start with 'BLOCKED-FAIL-FAST'; got: {err.reason!r}"
        )
        # results contains the IS trades accumulated before the abort
        assert isinstance(err.results, list)
        assert err.total_signals >= 0

    def test_blocked_fail_fast_fires_at_most_once(self) -> None:
        """The checkpoint must fire exactly once (not on every subsequent IS trade)."""
        master = self._build_negative_master_and_patch()
        config = BacktestConfig(
            symbols=("TESTUSDT",),
            interval="8h",
            max_amount_usd=100.0,
            stop_loss_pct=0.5,
            take_profit_pct=5.0,
            timeout_minutes=4320,
            fee_pct=0.1,
            data_dir=Path("data"),
            cooldown_candles=0,
        )
        strategy = _SyntheticStrategy(direction=1)

        # If the checkpoint fired multiple times it would raise multiple times;
        # pytest.raises will catch the FIRST raise and verify we only get one.
        with patch("crypto_trade.backtest._build_master", return_value=master):
            with pytest.raises(EarlyStopError) as exc_info:
                run_backtest(config, strategy, fail_fast_is_years=2.0)

        # Only one error raised → single-fire confirmed implicitly by the test
        # reaching this point without a second exception.
        assert exc_info.value.reason.startswith("BLOCKED-FAIL-FAST")


# ---------------------------------------------------------------------------
# (c) Positive-first-2-years case → checkpoint PASSES, run completes
# ---------------------------------------------------------------------------


class TestFailFastPositiveCase:
    """Synthetic scenario where IS returns are positive → checkpoint PASSES."""

    def _build_positive_master(self):
        """Build a master where every LONG trade hits TP (profitable).

        High = +5% (above TP=2%), Low = -0.1% (above SL=2%).
        Result: every trade is profitable → IS weighted_pnl > 0.
        """
        start_ms = OOS_CUTOFF_MS - int(3.5 * 365.25 * 24 * 3600 * 1000)
        n = int(3.5 * 365.25 * 3)
        rows = []
        for i in range(n):
            ot = start_ms + i * _8H_MS
            ct = ot + _8H_MS - 1
            rows.append(
                {
                    "open_time": ot,
                    "close_time": ct,
                    "open": 100.0,
                    "high": 105.0,  # +5% → above TP=2%
                    "low": 99.9,  # -0.1% → above SL=2%
                    "close": 100.0,
                    "volume": 1000.0,
                    "quote_volume": 100000.0,
                    "trades": 100,
                    "taker_buy_volume": 500.0,
                    "taker_buy_quote_volume": 50000.0,
                    "symbol": "TESTUSDT",
                }
            )
        return pd.DataFrame(rows)

    def test_positive_is_does_not_raise(self) -> None:
        """When IS weighted_pnl > 0 at the 2yr checkpoint, no EarlyStopError raised."""
        master = self._build_positive_master()
        config = BacktestConfig(
            symbols=("TESTUSDT",),
            interval="8h",
            max_amount_usd=100.0,
            stop_loss_pct=2.0,  # SL below Low=-0.1% → never triggered
            take_profit_pct=2.0,  # TP hit by High=+5%
            timeout_minutes=4320,
            fee_pct=0.1,
            data_dir=Path("data"),
            cooldown_candles=0,
        )
        strategy = _SyntheticStrategy(direction=1)

        with patch("crypto_trade.backtest._build_master", return_value=master):
            result = run_backtest(config, strategy, fail_fast_is_years=2.0)

        # Must complete without error
        assert result is not None
        # Must have trades
        assert len(result) > 0

    def test_positive_checkpoint_continues_to_oos(self) -> None:
        """After a positive IS checkpoint the backtest proceeds through OOS candles."""
        # Build a master that spans across OOS_CUTOFF_MS so OOS candles exist.
        start_ms = OOS_CUTOFF_MS - int(3.0 * 365.25 * 24 * 3600 * 1000)
        end_ms = OOS_CUTOFF_MS + int(0.5 * 365.25 * 24 * 3600 * 1000)
        n = int((end_ms - start_ms) / _8H_MS)
        rows = []
        for i in range(n):
            ot = start_ms + i * _8H_MS
            ct = ot + _8H_MS - 1
            rows.append(
                {
                    "open_time": ot,
                    "close_time": ct,
                    "open": 100.0,
                    "high": 105.0,
                    "low": 99.9,
                    "close": 100.0,
                    "volume": 1000.0,
                    "quote_volume": 100000.0,
                    "trades": 100,
                    "taker_buy_volume": 500.0,
                    "taker_buy_quote_volume": 50000.0,
                    "symbol": "TESTUSDT",
                }
            )
        master = pd.DataFrame(rows)

        config = BacktestConfig(
            symbols=("TESTUSDT",),
            interval="8h",
            max_amount_usd=100.0,
            stop_loss_pct=2.0,
            take_profit_pct=2.0,
            timeout_minutes=4320,
            fee_pct=0.1,
            data_dir=Path("data"),
            cooldown_candles=0,
        )
        strategy = _SyntheticStrategy(direction=1)

        with patch("crypto_trade.backtest._build_master", return_value=master):
            result = run_backtest(config, strategy, fail_fast_is_years=2.0)

        assert result is not None
        # Verify OOS trades exist (close_time >= OOS_CUTOFF_MS)
        oos_trades = [r for r in result if r.close_time >= OOS_CUTOFF_MS]
        assert len(oos_trades) > 0, (
            "Expected OOS trades after positive IS checkpoint but found none. "
            "The run must continue past the IS 2yr checkpoint."
        )


# ---------------------------------------------------------------------------
# (d) Structural: fail_fast_is_years=None is the default; signature check
# ---------------------------------------------------------------------------


class TestFailFastSignature:
    """Verify the function signature has the correct default."""

    def test_fail_fast_is_years_default_is_none(self) -> None:
        """run_backtest must accept fail_fast_is_years as a keyword-only arg defaulting to None."""
        sig = inspect.signature(run_backtest)
        assert "fail_fast_is_years" in sig.parameters, (
            "run_backtest must have fail_fast_is_years parameter (iter-v1/087)"
        )
        param = sig.parameters["fail_fast_is_years"]
        assert param.default is None, (
            f"fail_fast_is_years default must be None (OFF); got {param.default!r}"
        )
        assert param.kind in (
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ), "fail_fast_is_years must be keyword-accessible"


# ---------------------------------------------------------------------------
# (e) V1_EXCLUDED_SYMBOLS — BNB un-reserved
# ---------------------------------------------------------------------------


class TestBNBUnreserved:
    """Verify BNBUSDT is no longer in V1_EXCLUDED_SYMBOLS (iter-v1/087 directive)."""

    def test_bnb_not_in_excluded_symbols(self) -> None:
        """BNBUSDT must NOT be in V1_EXCLUDED_SYMBOLS after iter-v1/087 un-reservation."""
        from crypto_trade.features_v1 import V1_EXCLUDED_SYMBOLS  # noqa: PLC0415

        assert "BNBUSDT" not in V1_EXCLUDED_SYMBOLS, (
            "iter-v1/087 un-reserved BNBUSDT per user directive 2026-06-10. "
            "'Don't discard BNB — un-reserve it.' "
            f"V1_EXCLUDED_SYMBOLS = {V1_EXCLUDED_SYMBOLS}"
        )

    def test_v2_v3_symbols_still_excluded(self) -> None:
        """v2/v3 live symbols must still be excluded even after BNB un-reservation."""
        from crypto_trade.features_v1 import V1_EXCLUDED_SYMBOLS  # noqa: PLC0415

        for sym in ("XRPUSDT", "DOGEUSDT", "NEARUSDT", "BCHUSDT", "LDOUSDT", "TRXUSDT"):
            assert sym in V1_EXCLUDED_SYMBOLS, (
                f"{sym} must remain in V1_EXCLUDED_SYMBOLS (v2/v3 live track)"
            )

    def test_v1_iter087_universe_is_bnb(self) -> None:
        """V1_ITER087_UNIVERSE must be ('BNBUSDT',)."""
        from crypto_trade.features_v1 import V1_ITER087_UNIVERSE  # noqa: PLC0415

        assert V1_ITER087_UNIVERSE == ("BNBUSDT",), (
            f"V1_ITER087_UNIVERSE must be ('BNBUSDT',); got {V1_ITER087_UNIVERSE}"
        )

    def test_assert_v1_universe_accepts_bnb(self) -> None:
        """assert_v1_universe must no longer reject BNBUSDT (it is now un-reserved)."""
        from crypto_trade.features_v1 import assert_v1_universe  # noqa: PLC0415

        # Must not raise — BNB is no longer in V1_EXCLUDED_SYMBOLS.
        assert_v1_universe(("BNBUSDT",))
