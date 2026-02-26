from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig, Signal, TradeResult
from crypto_trade.backtest_report import aggregate_daily_pnl
from crypto_trade.models import Kline
from crypto_trade.storage import write_klines

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_kline(
    open_time: int,
    open: str,
    high: str,
    low: str,
    close: str,
    close_time: int | None = None,
) -> Kline:
    """Create a Kline with sensible defaults for non-essential fields."""
    if close_time is None:
        close_time = open_time + 3_600_000 - 1  # 1h candle
    return Kline(
        open_time=open_time,
        open=open,
        high=high,
        low=low,
        close=close,
        volume="100.0",
        close_time=close_time,
        quote_volume="10000.0",
        trades=50,
        taker_buy_volume="50.0",
        taker_buy_quote_volume="5000.0",
    )


# Millisecond helpers
H = 3_600_000  # 1 hour in ms
BASE_T = 1_700_000_000_000  # arbitrary epoch-ms starting point


def _write_symbol_data(data_dir: Path, symbol: str, klines: list[Kline]) -> None:
    from crypto_trade.storage import csv_path

    path = csv_path(data_dir, symbol, "1h")
    write_klines(path, klines)


def _default_config(data_dir: Path, symbols: tuple[str, ...] = ("TEST",)) -> BacktestConfig:
    return BacktestConfig(
        symbols=symbols,
        interval="1h",
        max_amount_usd=Decimal("1000"),
        stop_loss_pct=Decimal("2.0"),
        take_profit_pct=Decimal("3.0"),
        timeout_minutes=180,  # 3 hours
        fee_pct=Decimal("0.1"),
        data_dir=data_dir,
    )


# ---------------------------------------------------------------------------
# Test strategies
# ---------------------------------------------------------------------------


class AlwaysBuyStrategy:
    """Emit a buy signal on every kline (weight=100)."""

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        return Signal(direction=1, weight=100)


class AlwaysSellStrategy:
    """Emit a sell signal on every kline (weight=100)."""

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        return Signal(direction=-1, weight=100)


class DoNothingStrategy:
    """Never trade."""

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        return Signal(direction=0, weight=0)


class WeightedBuyStrategy:
    """Emit a buy signal with weight=25."""

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        return Signal(direction=1, weight=25)


class BuyOnceStrategy:
    """Buy only on the first kline."""

    def __init__(self) -> None:
        self._bought: set[str] = set()

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        if symbol not in self._bought:
            self._bought.add(symbol)
            return Signal(direction=1, weight=100)
        return Signal(direction=0, weight=0)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestTakeProfit:
    """1. Single trade hits take profit."""

    def test_long_take_profit(self, tmp_path: Path) -> None:
        # Entry at close=100. TP at 103. Next candle high=104 triggers TP.
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),
            _make_kline(BASE_T + 2 * H, "103", "105", "102", "104"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        assert len(results) >= 1
        r = results[0]
        assert r.exit_reason == "take_profit"
        assert r.exit_price == Decimal("103")  # entry 100 * 1.03
        assert r.pnl_pct > 0
        assert r.net_pnl_pct == r.pnl_pct - r.fee_pct


class TestStopLoss:
    """2. Single trade hits stop loss."""

    def test_long_stop_loss(self, tmp_path: Path) -> None:
        # Entry at close=100. SL at 98. Next candle low=97 triggers SL.
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101", "97", "98"),
            _make_kline(BASE_T + 2 * H, "98", "99", "96", "97"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        assert len(results) >= 1
        r = results[0]
        assert r.exit_reason == "stop_loss"
        assert r.exit_price == Decimal("98")  # entry 100 * 0.98
        assert r.pnl_pct < 0


class TestTimeout:
    """3. Timeout — no SL/TP hit, exits at candle open price."""

    def test_timeout_exit(self, tmp_path: Path) -> None:
        # Timeout = 60 min. Order placed at candle 0 close_time (BASE_T+H-1).
        # timeout_time = BASE_T+H-1+3600000 = BASE_T+2H-1.
        # Candle 1 doesn't trigger SL/TP. Candle 2 open_time (BASE_T+2H) >= timeout_time.
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101.5", "98.5", "100"),
            _make_kline(BASE_T + 2 * H, "99.5", "101.5", "98.5", "100"),
            _make_kline(BASE_T + 3 * H, "100", "101", "99", "100"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=Decimal("1000"),
            stop_loss_pct=Decimal("2.0"),
            take_profit_pct=Decimal("3.0"),
            timeout_minutes=60,
            fee_pct=Decimal("0.1"),
            data_dir=tmp_path,
        )
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.exit_reason == "timeout"
        assert r.exit_price == Decimal("99.5")  # open of the timeout candle


class TestShortOrderTPSL:
    """4. Short order TP/SL — reversed direction logic."""

    def test_short_take_profit(self, tmp_path: Path) -> None:
        # Entry at close=100. Short TP at 97 (100 * 0.97). Next candle low=96 triggers TP.
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "99", "100", "96", "97"),
            _make_kline(BASE_T + 2 * H, "97", "98", "95", "96"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysSellStrategy())

        r = results[0]
        assert r.exit_reason == "take_profit"
        assert r.direction == -1
        assert r.pnl_pct > 0

    def test_short_stop_loss(self, tmp_path: Path) -> None:
        # Entry at close=100. Short SL at 102 (100 * 1.02). Next candle high=103 triggers SL.
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "103", "100", "102"),
            _make_kline(BASE_T + 2 * H, "102", "104", "101", "103"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysSellStrategy())

        r = results[0]
        assert r.exit_reason == "stop_loss"
        assert r.direction == -1
        assert r.pnl_pct < 0


class TestOneOrderPerSymbol:
    """5. One order per symbol — no duplicate orders while one is open."""

    def test_no_duplicate_orders(self, tmp_path: Path) -> None:
        # All candles stay in range, so the first order stays open.
        # AlwaysBuy keeps signalling but shouldn't create duplicates.
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101.5", "98.5", "100.5"),
            _make_kline(BASE_T + 2 * H, "100.5", "102", "99", "101"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        # Only one trade (end-of-data close of the single order)
        assert len(results) == 1
        assert results[0].exit_reason == "end_of_data"


class TestMultipleSymbols:
    """6. Multiple symbols — independent concurrent orders."""

    def test_independent_symbols(self, tmp_path: Path) -> None:
        klines_a = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "104", "99", "103"),
            _make_kline(BASE_T + 2 * H, "103", "105", "102", "104"),
        ]
        klines_b = [
            _make_kline(BASE_T, "50", "51", "49", "50"),
            _make_kline(BASE_T + H, "50", "52", "48", "51"),
            _make_kline(BASE_T + 2 * H, "51", "53", "50", "52"),
        ]
        _write_symbol_data(tmp_path, "SYM_A", klines_a)
        _write_symbol_data(tmp_path, "SYM_B", klines_b)
        config = _default_config(tmp_path, symbols=("SYM_A", "SYM_B"))
        results = run_backtest(config, AlwaysBuyStrategy())

        symbols_in_results = {r.symbol for r in results}
        assert "SYM_A" in symbols_in_results
        assert "SYM_B" in symbols_in_results


class TestSLTPSameCandle:
    """7. SL+TP same candle — worst case (SL) when ambiguous."""

    def test_ambiguous_defaults_to_sl(self, tmp_path: Path) -> None:
        # Long entry at 100. SL=98, TP=103.
        # Next candle: open=100, low=97, high=104 => both hit, open doesn't resolve => SL.
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "104", "97", "101"),
            _make_kline(BASE_T + 2 * H, "101", "102", "100", "101"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.exit_reason == "stop_loss"


class TestSLTPSameCandleResolvable:
    """8. SL+TP same candle — open past barrier resolves unambiguously."""

    def test_open_past_tp_resolves_to_tp(self, tmp_path: Path) -> None:
        # Long entry at 100. TP=103. Next candle: open=103.5, so open >= TP => TP wins.
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "103.5", "105", "97", "104"),
            _make_kline(BASE_T + 2 * H, "104", "105", "103", "104"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.exit_reason == "take_profit"


class TestTimeoutPriority:
    """9. Timeout takes priority over SL/TP on same candle."""

    def test_timeout_before_sltp(self, tmp_path: Path) -> None:
        # Timeout = 60 min. Entry at candle 0 close_time.
        # Candle 1 stays in range. Candle 2 open_time >= timeout_time AND has SL/TP hit.
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101.5", "98.5", "100"),
            # open_time = BASE_T+2H >= timeout_time; also SL/TP both triggered
            _make_kline(BASE_T + 2 * H, "99", "104", "97", "101"),
            _make_kline(BASE_T + 3 * H, "101", "102", "100", "101"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=Decimal("1000"),
            stop_loss_pct=Decimal("2.0"),
            take_profit_pct=Decimal("3.0"),
            timeout_minutes=60,
            fee_pct=Decimal("0.1"),
            data_dir=tmp_path,
        )
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.exit_reason == "timeout"


class TestFeeDeduction:
    """10. Fee deduction — net_pnl = pnl - fee."""

    def test_fee_subtracted(self, tmp_path: Path) -> None:
        # Entry 100, TP hit at 103 => pnl_pct = 3.0, fee = 0.1, net = 2.9
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),
            _make_kline(BASE_T + 2 * H, "103", "105", "102", "104"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.fee_pct == Decimal("0.1")
        assert r.net_pnl_pct == r.pnl_pct - Decimal("0.1")


class TestWeightFactor:
    """11. Weight factor — weight=25 produces weight_factor=0.25."""

    def test_weight_25(self, tmp_path: Path) -> None:
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),
            _make_kline(BASE_T + 2 * H, "103", "105", "102", "104"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, WeightedBuyStrategy())

        r = results[0]
        assert r.weight_factor == Decimal("0.25")
        assert r.weighted_pnl == r.net_pnl_pct * Decimal("0.25")


class TestSignalIgnored:
    """12. Signal direction=0 ignored."""

    def test_no_trades_when_direction_zero(self, tmp_path: Path) -> None:
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101", "99", "100"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, DoNothingStrategy())

        assert len(results) == 0


class TestEndOfData:
    """13. End-of-data closes open orders."""

    def test_end_of_data_close(self, tmp_path: Path) -> None:
        # All candles in range, no SL/TP hit => end_of_data at last close
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101.5", "98.5", "100.5"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        assert len(results) == 1
        r = results[0]
        assert r.exit_reason == "end_of_data"
        assert r.exit_price == Decimal("100.5")


class TestDailyPnL:
    """14. Daily P&L averaging — multiple trades same day."""

    def test_daily_aggregation(self) -> None:
        # Two trades closing on the same UTC day (2023-11-14 00:00 UTC = 1699920000)
        day_start_ms = 1_699_920_000_000
        t1 = TradeResult(
            symbol="A",
            direction=1,
            entry_price=Decimal("100"),
            exit_price=Decimal("103"),
            weight_factor=Decimal("1"),
            open_time=day_start_ms,
            close_time=day_start_ms + 3_600_000,  # +1h, same day
            exit_reason="take_profit",
            pnl_pct=Decimal("3.0"),
            fee_pct=Decimal("0.1"),
            net_pnl_pct=Decimal("2.9"),
            weighted_pnl=Decimal("2.9"),
        )
        t2 = TradeResult(
            symbol="B",
            direction=1,
            entry_price=Decimal("100"),
            exit_price=Decimal("98"),
            weight_factor=Decimal("1"),
            open_time=day_start_ms,
            close_time=day_start_ms + 7_200_000,  # +2h, same day
            exit_reason="stop_loss",
            pnl_pct=Decimal("-2.0"),
            fee_pct=Decimal("0.1"),
            net_pnl_pct=Decimal("-2.1"),
            weighted_pnl=Decimal("-2.1"),
        )
        daily = aggregate_daily_pnl([t1, t2])

        assert len(daily) == 1
        d = daily[0]
        assert d.trade_count == 2
        expected_avg = (Decimal("2.9") + Decimal("-2.1")) / 2
        assert d.avg_weighted_pnl == expected_avg
        assert len(d.trades) == 2


class TestEmptyKlinesRaises:
    """15. Empty klines raises ValueError."""

    def test_no_data_raises(self, tmp_path: Path) -> None:
        config = _default_config(tmp_path)
        with pytest.raises(ValueError, match="No kline data"):
            run_backtest(config, AlwaysBuyStrategy())


class TestEntryAtCloseCheckNextCandle:
    """16. Entry at close, first check at next candle."""

    def test_order_checked_next_candle(self, tmp_path: Path) -> None:
        # Candle 0: close=100 (entry). TP=103.
        # Candle 1: stays in range => order open.
        # Candle 2: high=104 => TP hit.
        klines = [
            _make_kline(BASE_T, "99", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "102", "99", "101"),
            _make_kline(BASE_T + 2 * H, "101", "104", "100", "103"),
            _make_kline(BASE_T + 3 * H, "103", "105", "102", "104"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, BuyOnceStrategy())

        assert len(results) == 1
        r = results[0]
        # Order created at candle 0 close_time, checked starting candle 1
        assert r.open_time == klines[0].close_time
        # TP hit on candle 2 (not candle 0)
        assert r.exit_reason == "take_profit"
        assert r.close_time == klines[2].close_time


# ---------------------------------------------------------------------------
# Additional test strategies
# ---------------------------------------------------------------------------


class ZeroWeightBuyStrategy:
    """Buy signal with weight=0 — should be ignored."""

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        return Signal(direction=1, weight=0)


class NegativeWeightSellStrategy:
    """Sell signal with weight=-10 — should be ignored."""

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        return Signal(direction=-1, weight=-10)


class MinWeightBuyStrategy:
    """Buy signal with weight=1 — minimum valid weight."""

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        return Signal(direction=1, weight=1)


class CustomWeightStrategy:
    """Parametric strategy with configurable direction and weight."""

    def __init__(self, direction: int, weight: int) -> None:
        self._direction = direction
        self._weight = weight

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        return Signal(direction=self._direction, weight=self._weight)


class SellOnceStrategy:
    """Sell only on the first kline per symbol."""

    def __init__(self) -> None:
        self._sold: set[str] = set()

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        if symbol not in self._sold:
            self._sold.add(symbol)
            return Signal(direction=-1, weight=100)
        return Signal(direction=0, weight=0)


class HistoryTrackingStrategy:
    """Records history length on each call."""

    def __init__(self) -> None:
        self.lengths: list[int] = []

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        self.lengths.append(len(history))
        return Signal(direction=0, weight=0)


# ---------------------------------------------------------------------------
# 1. Short-Specific Exit Paths
# ---------------------------------------------------------------------------


class TestShortTimeoutExit:
    def test_short_timeout_exit(self, tmp_path: Path) -> None:
        """Short order times out, exits at candle open."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101.5", "98.5", "100"),
            _make_kline(BASE_T + 2 * H, "99.5", "101.5", "98.5", "100"),
            _make_kline(BASE_T + 3 * H, "100", "101", "99", "100"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=Decimal("1000"),
            stop_loss_pct=Decimal("2.0"),
            take_profit_pct=Decimal("3.0"),
            timeout_minutes=60,
            fee_pct=Decimal("0.1"),
            data_dir=tmp_path,
        )
        results = run_backtest(config, AlwaysSellStrategy())

        r = results[0]
        assert r.exit_reason == "timeout"
        assert r.direction == -1
        assert r.exit_price == Decimal("99.5")
        # Short PnL = (entry - exit) / entry * 100
        expected_pnl = (Decimal("100") - Decimal("99.5")) / Decimal("100") * Decimal("100")
        assert r.pnl_pct == expected_pnl


class TestShortEndOfDataClose:
    def test_short_end_of_data_close(self, tmp_path: Path) -> None:
        """Short order force-closed at last close."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101.5", "98.5", "100.5"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, SellOnceStrategy())

        assert len(results) == 1
        r = results[0]
        assert r.exit_reason == "end_of_data"
        assert r.direction == -1
        assert r.exit_price == Decimal("100.5")
        # Short PnL = (100 - 100.5) / 100 * 100 = -0.5
        expected_pnl = (Decimal("100") - Decimal("100.5")) / Decimal("100") * Decimal("100")
        assert r.pnl_pct == expected_pnl


# ---------------------------------------------------------------------------
# 2. Exact Boundary Hits
# ---------------------------------------------------------------------------


class TestExactBoundaryHits:
    def test_long_sl_exact_boundary(self, tmp_path: Path) -> None:
        """Long SL: low == SL triggers (inclusive <=)."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "102", "98", "101"),  # low=98 == SL
            _make_kline(BASE_T + 2 * H, "101", "102", "100", "101"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.exit_reason == "stop_loss"
        assert r.exit_price == Decimal("98")

    def test_long_tp_exact_boundary(self, tmp_path: Path) -> None:
        """Long TP: high == TP triggers (inclusive >=)."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "103", "99", "102"),  # high=103 == TP
            _make_kline(BASE_T + 2 * H, "102", "103", "101", "102"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.exit_reason == "take_profit"
        assert r.exit_price == Decimal("103")

    def test_short_sl_exact_boundary(self, tmp_path: Path) -> None:
        """Short SL: high == SL triggers."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "102", "99", "101"),  # high=102 == SL
            _make_kline(BASE_T + 2 * H, "101", "102", "100", "101"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysSellStrategy())

        r = results[0]
        assert r.exit_reason == "stop_loss"
        assert r.exit_price == Decimal("102")

    def test_short_tp_exact_boundary(self, tmp_path: Path) -> None:
        """Short TP: low == TP triggers."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "99", "101", "97", "98"),  # low=97 == TP
            _make_kline(BASE_T + 2 * H, "98", "99", "97", "98"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysSellStrategy())

        r = results[0]
        assert r.exit_reason == "take_profit"
        assert r.exit_price == Decimal("97")

    def test_long_price_just_misses_sl(self, tmp_path: Path) -> None:
        """Low = SL + 0.01 does NOT trigger SL."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "102", "98.01", "101"),  # low > SL=98
            _make_kline(BASE_T + 2 * H, "101", "102", "99", "101"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, BuyOnceStrategy())

        assert len(results) == 1
        r = results[0]
        assert r.exit_reason == "end_of_data"

    def test_long_price_just_misses_tp(self, tmp_path: Path) -> None:
        """High = TP - 0.01 does NOT trigger TP."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "102.99", "99", "102"),  # high < TP=103
            _make_kline(BASE_T + 2 * H, "102", "102.99", "100", "101"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, BuyOnceStrategy())

        assert len(results) == 1
        r = results[0]
        assert r.exit_reason == "end_of_data"


# ---------------------------------------------------------------------------
# 3. Reopening After Close
# ---------------------------------------------------------------------------


class TestReopenAfterClose:
    def test_reopen_on_same_candle_after_tp(self, tmp_path: Path) -> None:
        """AlwaysBuy reopens immediately after TP close."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),  # TP hit
            _make_kline(BASE_T + 2 * H, "103", "104", "102", "103"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        assert len(results) >= 2
        assert results[0].exit_reason == "take_profit"
        assert results[1].exit_reason == "end_of_data"

    def test_reopen_on_same_candle_after_sl(self, tmp_path: Path) -> None:
        """AlwaysBuy reopens immediately after SL close."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "99", "101", "97", "98"),  # SL hit
            _make_kline(BASE_T + 2 * H, "98", "99", "97", "98"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        assert len(results) >= 2
        assert results[0].exit_reason == "stop_loss"
        assert results[1].exit_reason == "end_of_data"

    def test_reopen_on_same_candle_after_timeout(self, tmp_path: Path) -> None:
        """AlwaysBuy reopens immediately after timeout."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101.5", "98.5", "100"),
            _make_kline(BASE_T + 2 * H, "99.5", "101.5", "98.5", "100"),
            _make_kline(BASE_T + 3 * H, "100", "101", "99", "100"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=Decimal("1000"),
            stop_loss_pct=Decimal("2.0"),
            take_profit_pct=Decimal("3.0"),
            timeout_minutes=60,
            fee_pct=Decimal("0.1"),
            data_dir=tmp_path,
        )
        results = run_backtest(config, AlwaysBuyStrategy())

        assert len(results) >= 2
        assert results[0].exit_reason == "timeout"
        assert results[1].exit_reason == "end_of_data"


# ---------------------------------------------------------------------------
# 4. Weight/Signal Edge Cases
# ---------------------------------------------------------------------------


class TestWeightSignalEdgeCases:
    def test_nonzero_direction_zero_weight_ignored(self, tmp_path: Path) -> None:
        """Direction=1, weight=0 -> no trade."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101", "99", "100"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, ZeroWeightBuyStrategy())

        assert len(results) == 0

    def test_nonzero_direction_negative_weight_ignored(self, tmp_path: Path) -> None:
        """Direction=-1, weight=-10 -> no trade."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101", "99", "100"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, NegativeWeightSellStrategy())

        assert len(results) == 0

    def test_weight_1_minimum(self, tmp_path: Path) -> None:
        """Weight=1 -> weight_factor=0.01, correct weighted_pnl."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),  # TP hit
            _make_kline(BASE_T + 2 * H, "103", "105", "102", "104"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, MinWeightBuyStrategy())

        r = results[0]
        assert r.weight_factor == Decimal("0.01")
        assert r.weighted_pnl == r.net_pnl_pct * Decimal("0.01")

    def test_weight_100_maximum(self, tmp_path: Path) -> None:
        """Weight=100 -> weight_factor=1.0."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),  # TP hit
            _make_kline(BASE_T + 2 * H, "103", "105", "102", "104"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.weight_factor == Decimal("1")
        assert r.weighted_pnl == r.net_pnl_pct


# ---------------------------------------------------------------------------
# 5. Realistic Price Scenarios
# ---------------------------------------------------------------------------


class TestRealisticPriceScenarios:
    def test_btc_long_take_profit(self, tmp_path: Path) -> None:
        """BTC ~40000, TP at 41200, pnl_pct=3.0."""
        klines = [
            _make_kline(BASE_T, "39800", "40100", "39700", "40000"),
            _make_kline(BASE_T + H, "40100", "41500", "40000", "41200"),
            _make_kline(BASE_T + 2 * H, "41200", "41500", "41000", "41300"),
        ]
        _write_symbol_data(tmp_path, "BTC", klines)
        config = _default_config(tmp_path, symbols=("BTC",))
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.exit_reason == "take_profit"
        assert r.entry_price == Decimal("40000")
        assert r.exit_price == Decimal("41200")
        assert r.pnl_pct == Decimal("3.0")

    def test_eth_short_stop_loss(self, tmp_path: Path) -> None:
        """ETH ~2500, short SL at 2550, pnl_pct=-2.0."""
        klines = [
            _make_kline(BASE_T, "2480", "2510", "2470", "2500"),
            _make_kline(BASE_T + H, "2510", "2560", "2490", "2540"),
            _make_kline(BASE_T + 2 * H, "2540", "2560", "2520", "2550"),
        ]
        _write_symbol_data(tmp_path, "ETH", klines)
        config = _default_config(tmp_path, symbols=("ETH",))
        results = run_backtest(config, AlwaysSellStrategy())

        r = results[0]
        assert r.exit_reason == "stop_loss"
        assert r.direction == -1
        assert r.entry_price == Decimal("2500")
        assert r.exit_price == Decimal("2550")
        assert r.pnl_pct == Decimal("-2.0")

    def test_sol_long_stop_loss(self, tmp_path: Path) -> None:
        """SOL ~100, SL at 98, pnl_pct=-2.0."""
        klines = [
            _make_kline(BASE_T, "99", "101", "99", "100"),
            _make_kline(BASE_T + H, "99", "101", "97", "98"),
            _make_kline(BASE_T + 2 * H, "98", "99", "97", "98"),
        ]
        _write_symbol_data(tmp_path, "SOL", klines)
        config = _default_config(tmp_path, symbols=("SOL",))
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.exit_reason == "stop_loss"
        assert r.entry_price == Decimal("100")
        assert r.exit_price == Decimal("98")
        assert r.pnl_pct == Decimal("-2.0")

    def test_btc_short_take_profit(self, tmp_path: Path) -> None:
        """BTC ~40000, short TP at 38800, pnl_pct=3.0."""
        klines = [
            _make_kline(BASE_T, "40200", "40300", "39900", "40000"),
            _make_kline(BASE_T + H, "39800", "40000", "38500", "38900"),
            _make_kline(BASE_T + 2 * H, "38900", "39000", "38700", "38800"),
        ]
        _write_symbol_data(tmp_path, "BTC", klines)
        config = _default_config(tmp_path, symbols=("BTC",))
        results = run_backtest(config, AlwaysSellStrategy())

        r = results[0]
        assert r.exit_reason == "take_profit"
        assert r.direction == -1
        assert r.entry_price == Decimal("40000")
        assert r.exit_price == Decimal("38800")
        assert r.pnl_pct == Decimal("3.0")


# ---------------------------------------------------------------------------
# 6. Multi-Symbol Advanced
# ---------------------------------------------------------------------------


class TestMultiSymbolAdvanced:
    def test_three_symbols_different_exits(self, tmp_path: Path) -> None:
        """BTC=TP, ETH=SL, SOL=end_of_data simultaneously."""
        # BTC: entry=100, TP=103, candle 1 high=104 -> TP
        klines_btc = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),
            _make_kline(BASE_T + 2 * H, "103", "104", "102", "103"),
        ]
        # ETH: entry=50, SL=49, candle 1 low=48.5 -> SL
        klines_eth = [
            _make_kline(BASE_T, "50", "51", "49", "50"),
            _make_kline(BASE_T + H, "50", "51", "48.5", "49"),
            _make_kline(BASE_T + 2 * H, "49", "50", "48", "49"),
        ]
        # SOL: entry=10, stays in range -> end_of_data
        klines_sol = [
            _make_kline(BASE_T, "10", "10.1", "9.9", "10"),
            _make_kline(BASE_T + H, "10", "10.2", "9.85", "10.1"),
            _make_kline(BASE_T + 2 * H, "10.1", "10.2", "9.9", "10.05"),
        ]
        _write_symbol_data(tmp_path, "BTC", klines_btc)
        _write_symbol_data(tmp_path, "ETH", klines_eth)
        _write_symbol_data(tmp_path, "SOL", klines_sol)
        config = _default_config(tmp_path, symbols=("BTC", "ETH", "SOL"))
        results = run_backtest(config, AlwaysBuyStrategy())

        first_by_sym: dict[str, TradeResult] = {}
        for r in results:
            if r.symbol not in first_by_sym:
                first_by_sym[r.symbol] = r

        assert first_by_sym["BTC"].exit_reason == "take_profit"
        assert first_by_sym["ETH"].exit_reason == "stop_loss"
        assert first_by_sym["SOL"].exit_reason == "end_of_data"

    def test_different_data_lengths_aligned(self, tmp_path: Path) -> None:
        """Symbols with offset time ranges -> correct intersection."""
        klines_a = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101", "99", "100"),
            _make_kline(BASE_T + 2 * H, "100", "101", "99", "100"),
            _make_kline(BASE_T + 3 * H, "100", "101", "99", "100"),
        ]
        klines_b = [
            _make_kline(BASE_T + H, "50", "51", "49", "50"),
            _make_kline(BASE_T + 2 * H, "50", "51", "49", "50"),
            _make_kline(BASE_T + 3 * H, "50", "51", "49", "50"),
            _make_kline(BASE_T + 4 * H, "50", "51", "49", "50"),
        ]
        _write_symbol_data(tmp_path, "SYM_A", klines_a)
        _write_symbol_data(tmp_path, "SYM_B", klines_b)
        config = _default_config(tmp_path, symbols=("SYM_A", "SYM_B"))
        results = run_backtest(config, DoNothingStrategy())

        assert len(results) == 0  # DoNothing produces no trades

    def test_no_overlap_returns_empty(self, tmp_path: Path) -> None:
        """Non-overlapping time ranges -> 0 results."""
        klines_a = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101", "99", "100"),
        ]
        klines_b = [
            _make_kline(BASE_T + 10 * H, "50", "51", "49", "50"),
            _make_kline(BASE_T + 11 * H, "50", "51", "49", "50"),
        ]
        _write_symbol_data(tmp_path, "SYM_A", klines_a)
        _write_symbol_data(tmp_path, "SYM_B", klines_b)
        config = _default_config(tmp_path, symbols=("SYM_A", "SYM_B"))
        results = run_backtest(config, AlwaysBuyStrategy())

        assert len(results) == 0


# ---------------------------------------------------------------------------
# 7. Consecutive Trade Chain
# ---------------------------------------------------------------------------


class TestConsecutiveTradeChain:
    def test_tp_then_sl_then_timeout_chain(self, tmp_path: Path) -> None:
        """Same symbol: TP -> reopen -> SL -> reopen -> timeout (3 trades)."""
        klines = [
            # Candle 0: entry at close=100. TP=103, SL=98.
            _make_kline(BASE_T, "99", "101", "99", "100"),
            # Candle 1: high=104 -> TP hit. Reopen at close=103.
            # New entry=103, TP=106.09, SL=100.94
            _make_kline(BASE_T + H, "101", "104", "100", "103"),
            # Candle 2: low=100 -> SL hit (100 <= 100.94). Reopen at close=101.
            # New entry=101, TP=104.03, SL=98.98.
            _make_kline(BASE_T + 2 * H, "102", "105", "100", "101"),
            # Candle 3: in range (high=103 < 104.03, low=99.5 > 98.98)
            _make_kline(BASE_T + 3 * H, "101", "103", "99.5", "101"),
            # Candle 4: timeout (open_time >= timeout_time)
            _make_kline(BASE_T + 4 * H, "101", "102", "100", "101"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=Decimal("1000"),
            stop_loss_pct=Decimal("2.0"),
            take_profit_pct=Decimal("3.0"),
            timeout_minutes=60,
            fee_pct=Decimal("0.1"),
            data_dir=tmp_path,
        )
        results = run_backtest(config, AlwaysBuyStrategy())

        test_results = [r for r in results if r.symbol == "TEST"]
        assert len(test_results) >= 3
        assert test_results[0].exit_reason == "take_profit"
        assert test_results[1].exit_reason == "stop_loss"
        assert test_results[2].exit_reason == "timeout"


# ---------------------------------------------------------------------------
# 8. PnL Calculation Precision
# ---------------------------------------------------------------------------


class TestPnLCalculationPrecision:
    def test_long_pnl_exact_values(self, tmp_path: Path) -> None:
        """Verify exact Decimal values for long TP."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),
            _make_kline(BASE_T + 2 * H, "103", "105", "102", "104"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.entry_price == Decimal("100")
        assert r.exit_price == Decimal("103")
        assert r.pnl_pct == Decimal("3.0")
        assert r.fee_pct == Decimal("0.1")
        assert r.net_pnl_pct == Decimal("2.9")
        assert r.weight_factor == Decimal("1")
        assert r.weighted_pnl == Decimal("2.9")

    def test_short_pnl_exact_values(self, tmp_path: Path) -> None:
        """Verify exact Decimal values for short SL with weight=50."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "103", "100", "102"),  # high >= SL=102
            _make_kline(BASE_T + 2 * H, "102", "103", "101", "102"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, CustomWeightStrategy(direction=-1, weight=50))

        r = results[0]
        assert r.entry_price == Decimal("100")
        assert r.exit_price == Decimal("102")
        assert r.pnl_pct == Decimal("-2.0")
        assert r.fee_pct == Decimal("0.1")
        assert r.net_pnl_pct == Decimal("-2.1")
        assert r.weight_factor == Decimal("0.5")
        assert r.weighted_pnl == Decimal("-2.1") * Decimal("0.5")

    def test_timeout_pnl_non_round_numbers(self, tmp_path: Path) -> None:
        """Non-round exit price, Decimal precision."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101.5", "98.5", "100"),
            _make_kline(BASE_T + 2 * H, "99.5", "101.5", "98.5", "100"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=Decimal("1000"),
            stop_loss_pct=Decimal("2.0"),
            take_profit_pct=Decimal("3.0"),
            timeout_minutes=60,
            fee_pct=Decimal("0.1"),
            data_dir=tmp_path,
        )
        results = run_backtest(config, BuyOnceStrategy())

        r = results[0]
        assert r.exit_reason == "timeout"
        assert r.exit_price == Decimal("99.5")
        expected_pnl = (Decimal("99.5") - Decimal("100")) / Decimal("100") * Decimal("100")
        assert r.pnl_pct == expected_pnl
        assert r.net_pnl_pct == expected_pnl - Decimal("0.1")

    def test_end_of_data_zero_pnl(self, tmp_path: Path) -> None:
        """Exit == entry -> pnl=0, net_pnl=-fee."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101.5", "98.5", "100"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, BuyOnceStrategy())

        r = results[0]
        assert r.exit_reason == "end_of_data"
        assert r.exit_price == Decimal("100")
        assert r.pnl_pct == Decimal("0")
        assert r.net_pnl_pct == Decimal("-0.1")
        assert r.weighted_pnl == Decimal("-0.1")


# ---------------------------------------------------------------------------
# 9. Daily PnL Report
# ---------------------------------------------------------------------------


class TestDailyPnLReport:
    def test_trades_across_two_days(self) -> None:
        """Trades on different UTC days -> 2 DailyPnL entries."""
        day1_ms = 1_699_920_000_000  # 2023-11-14
        day2_ms = 1_700_006_400_000  # 2023-11-15
        t1 = TradeResult(
            symbol="A",
            direction=1,
            entry_price=Decimal("100"),
            exit_price=Decimal("103"),
            weight_factor=Decimal("1"),
            open_time=day1_ms,
            close_time=day1_ms + 3_600_000,
            exit_reason="take_profit",
            pnl_pct=Decimal("3.0"),
            fee_pct=Decimal("0.1"),
            net_pnl_pct=Decimal("2.9"),
            weighted_pnl=Decimal("2.9"),
        )
        t2 = TradeResult(
            symbol="B",
            direction=1,
            entry_price=Decimal("100"),
            exit_price=Decimal("98"),
            weight_factor=Decimal("1"),
            open_time=day2_ms,
            close_time=day2_ms + 3_600_000,
            exit_reason="stop_loss",
            pnl_pct=Decimal("-2.0"),
            fee_pct=Decimal("0.1"),
            net_pnl_pct=Decimal("-2.1"),
            weighted_pnl=Decimal("-2.1"),
        )
        daily = aggregate_daily_pnl([t1, t2])

        assert len(daily) == 2
        assert daily[0].date == "2023-11-14"
        assert daily[0].trade_count == 1
        assert daily[1].date == "2023-11-15"
        assert daily[1].trade_count == 1

    def test_empty_results_list(self) -> None:
        """aggregate_daily_pnl([]) -> empty list."""
        assert aggregate_daily_pnl([]) == []

    def test_single_trade_day(self) -> None:
        """One trade -> avg equals that trade's weighted_pnl."""
        day_ms = 1_699_920_000_000
        t = TradeResult(
            symbol="A",
            direction=1,
            entry_price=Decimal("100"),
            exit_price=Decimal("103"),
            weight_factor=Decimal("0.5"),
            open_time=day_ms,
            close_time=day_ms + 3_600_000,
            exit_reason="take_profit",
            pnl_pct=Decimal("3.0"),
            fee_pct=Decimal("0.1"),
            net_pnl_pct=Decimal("2.9"),
            weighted_pnl=Decimal("1.45"),
        )
        daily = aggregate_daily_pnl([t])

        assert len(daily) == 1
        assert daily[0].avg_weighted_pnl == Decimal("1.45")
        assert daily[0].trade_count == 1

    def test_integration_with_backtest(self, tmp_path: Path) -> None:
        """End-to-end: backtest -> aggregate -> verify pipeline."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),
            _make_kline(BASE_T + 2 * H, "103", "105", "102", "104"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())
        daily = aggregate_daily_pnl(results)

        assert len(daily) >= 1
        total_trades = sum(d.trade_count for d in daily)
        assert total_trades == len(results)


# ---------------------------------------------------------------------------
# 10. Single Kline Edge
# ---------------------------------------------------------------------------


class TestSingleKlineEdge:
    def test_single_kline_entry_immediate_end_of_data(self, tmp_path: Path) -> None:
        """1 kline -> entry=exit, pnl=0."""
        klines = [_make_kline(BASE_T, "100", "101", "99", "100")]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        assert len(results) == 1
        r = results[0]
        assert r.exit_reason == "end_of_data"
        assert r.entry_price == Decimal("100")
        assert r.exit_price == Decimal("100")
        assert r.pnl_pct == Decimal("0")

    def test_single_kline_no_signal_no_trades(self, tmp_path: Path) -> None:
        """1 kline + DoNothing -> 0 results."""
        klines = [_make_kline(BASE_T, "100", "101", "99", "100")]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, DoNothingStrategy())

        assert len(results) == 0


# ---------------------------------------------------------------------------
# 11. Same-Candle SL/TP Disambiguation
# ---------------------------------------------------------------------------


class TestSameCandleDisambiguation:
    def test_short_ambiguous_defaults_to_sl(self, tmp_path: Path) -> None:
        """Short, both hit, open between TP/SL -> SL."""
        # Short entry=100. SL=102, TP=97.
        # open=99 between TP and SL, high=103 >= SL, low=96 <= TP
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "99", "103", "96", "100"),
            _make_kline(BASE_T + 2 * H, "100", "101", "99", "100"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, SellOnceStrategy())

        r = results[0]
        assert r.exit_reason == "stop_loss"

    def test_short_open_at_tp_resolves_to_tp(self, tmp_path: Path) -> None:
        """Short, open < TP -> TP wins."""
        # Short entry=100. SL=102, TP=97.
        # open=96 < TP, high=103 >= SL, low=95 <= TP
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "96", "103", "95", "100"),
            _make_kline(BASE_T + 2 * H, "100", "101", "99", "100"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, SellOnceStrategy())

        r = results[0]
        assert r.exit_reason == "take_profit"

    def test_short_open_exactly_at_tp_resolves_to_tp(self, tmp_path: Path) -> None:
        """Short, open == TP -> TP wins (<=)."""
        # Short entry=100. SL=102, TP=97.
        # open=97 == TP, high=103 >= SL, low=95 <= TP
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "97", "103", "95", "100"),
            _make_kline(BASE_T + 2 * H, "100", "101", "99", "100"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, SellOnceStrategy())

        r = results[0]
        assert r.exit_reason == "take_profit"

    def test_short_open_exactly_at_sl_resolves_to_sl(self, tmp_path: Path) -> None:
        """Short, open == SL -> SL wins."""
        # Short entry=100. SL=102, TP=97.
        # open=102 == SL, high=103 >= SL, low=96 <= TP
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "102", "103", "96", "100"),
            _make_kline(BASE_T + 2 * H, "100", "101", "99", "100"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, SellOnceStrategy())

        r = results[0]
        assert r.exit_reason == "stop_loss"

    def test_long_open_exactly_at_tp(self, tmp_path: Path) -> None:
        """Long, open == TP -> TP wins (>=)."""
        # Long entry=100. SL=98, TP=103.
        # open=103 == TP, high=105 >= TP, low=97 <= SL
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "103", "105", "97", "101"),
            _make_kline(BASE_T + 2 * H, "101", "102", "100", "101"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, BuyOnceStrategy())

        r = results[0]
        assert r.exit_reason == "take_profit"

    def test_long_open_exactly_at_sl(self, tmp_path: Path) -> None:
        """Long, open == SL -> SL wins."""
        # Long entry=100. SL=98, TP=103.
        # open=98 == SL, high=104 >= TP, low=97 <= SL
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "98", "104", "97", "101"),
            _make_kline(BASE_T + 2 * H, "101", "102", "100", "101"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, BuyOnceStrategy())

        r = results[0]
        assert r.exit_reason == "stop_loss"


# ---------------------------------------------------------------------------
# 12. History Accumulation
# ---------------------------------------------------------------------------


class TestHistoryAccumulation:
    def test_strategy_receives_growing_history(self, tmp_path: Path) -> None:
        """History length = [1, 2, 3, 4] across iterations."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101", "99", "100"),
            _make_kline(BASE_T + 2 * H, "100", "101", "99", "100"),
            _make_kline(BASE_T + 3 * H, "100", "101", "99", "100"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        strat = HistoryTrackingStrategy()
        run_backtest(config, strat)

        assert strat.lengths == [1, 2, 3, 4]


# ---------------------------------------------------------------------------
# 13. Do-Nothing Multi-Symbol
# ---------------------------------------------------------------------------


class TestDoNothingMultiSymbol:
    def test_do_nothing_strategy_multi_symbol(self, tmp_path: Path) -> None:
        """DoNothing + 2 symbols -> 0 results."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101", "99", "100"),
        ]
        _write_symbol_data(tmp_path, "SYM_A", klines)
        _write_symbol_data(tmp_path, "SYM_B", klines)
        config = _default_config(tmp_path, symbols=("SYM_A", "SYM_B"))
        results = run_backtest(config, DoNothingStrategy())

        assert len(results) == 0


# ---------------------------------------------------------------------------
# 14. Results Sorting
# ---------------------------------------------------------------------------


class TestResultsSorting:
    def test_results_sorted_by_close_time(self, tmp_path: Path) -> None:
        """2 symbols, B closes before A -> sorted correctly."""
        # SYM_A: entry=100, TP=103. Candle 1 in range. Candle 2 TP.
        klines_a = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "102", "99", "101"),
            _make_kline(BASE_T + 2 * H, "101", "104", "100", "103"),
        ]
        # SYM_B: entry=50, TP=51.5. Candle 1 TP hit.
        klines_b = [
            _make_kline(BASE_T, "50", "51", "49", "50"),
            _make_kline(BASE_T + H, "50", "52", "49", "51"),
            _make_kline(BASE_T + 2 * H, "51", "53", "50", "52"),
        ]
        _write_symbol_data(tmp_path, "SYM_A", klines_a)
        _write_symbol_data(tmp_path, "SYM_B", klines_b)
        config = _default_config(tmp_path, symbols=("SYM_A", "SYM_B"))
        results = run_backtest(config, BuyOnceStrategy())

        a_results = [r for r in results if r.symbol == "SYM_A"]
        b_results = [r for r in results if r.symbol == "SYM_B"]
        assert len(a_results) >= 1
        assert len(b_results) >= 1
        assert b_results[0].close_time < a_results[0].close_time
        for i in range(len(results) - 1):
            assert results[i].close_time <= results[i + 1].close_time


# ---------------------------------------------------------------------------
# 15. Fee Edge Cases
# ---------------------------------------------------------------------------


class TestFeeEdgeCases:
    def test_zero_fee_pnl_equals_gross(self, tmp_path: Path) -> None:
        """fee=0 -> net == gross."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),
            _make_kline(BASE_T + 2 * H, "103", "105", "102", "104"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=Decimal("1000"),
            stop_loss_pct=Decimal("2.0"),
            take_profit_pct=Decimal("3.0"),
            timeout_minutes=180,
            fee_pct=Decimal("0"),
            data_dir=tmp_path,
        )
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.fee_pct == Decimal("0")
        assert r.net_pnl_pct == r.pnl_pct

    def test_fee_larger_than_pnl_produces_negative_net(self, tmp_path: Path) -> None:
        """fee=5% > TP=3% -> net negative."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),
            _make_kline(BASE_T + 2 * H, "103", "105", "102", "104"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=Decimal("1000"),
            stop_loss_pct=Decimal("2.0"),
            take_profit_pct=Decimal("3.0"),
            timeout_minutes=180,
            fee_pct=Decimal("5.0"),
            data_dir=tmp_path,
        )
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.pnl_pct == Decimal("3.0")
        assert r.fee_pct == Decimal("5.0")
        assert r.net_pnl_pct == Decimal("-2.0")
        assert r.net_pnl_pct < 0


# ---------------------------------------------------------------------------
# 16. Order Creation Verification
# ---------------------------------------------------------------------------


class TestOrderCreationVerification:
    def test_order_prices_long(self, tmp_path: Path) -> None:
        """Verify SL=entry*(1-SL%), TP=entry*(1+TP%), weight_factor correct."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),  # TP hit
            _make_kline(BASE_T + 2 * H, "103", "105", "102", "104"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.entry_price == Decimal("100")
        # TP = 100 * (1 + 0.03) = 103
        assert r.exit_price == Decimal("103")
        assert r.exit_reason == "take_profit"
        assert r.weight_factor == Decimal("1")

    def test_order_prices_short(self, tmp_path: Path) -> None:
        """Verify SL=entry*(1+SL%), TP=entry*(1-TP%) for short."""
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "99", "100", "96", "97"),  # TP hit for short
            _make_kline(BASE_T + 2 * H, "97", "98", "95", "96"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysSellStrategy())

        r = results[0]
        assert r.entry_price == Decimal("100")
        # Short TP = 100 * (1 - 0.03) = 97
        assert r.exit_price == Decimal("97")
        assert r.exit_reason == "take_profit"
        assert r.direction == -1
        assert r.weight_factor == Decimal("1")


# ---------------------------------------------------------------------------
# 17. Start/End Time Filtering
# ---------------------------------------------------------------------------


class TestStartEndTime:
    """start_time / end_time fields on BacktestConfig."""

    def _klines(self) -> list[Kline]:
        """5 hourly klines starting at BASE_T."""
        return [
            _make_kline(BASE_T + i * H, "100", "101", "99", "100")
            for i in range(5)
        ]

    def test_start_time_only(self, tmp_path: Path) -> None:
        """start_time skips early klines."""
        klines = self._klines()
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=Decimal("1000"),
            stop_loss_pct=Decimal("2.0"),
            take_profit_pct=Decimal("3.0"),
            timeout_minutes=180,
            data_dir=tmp_path,
            start_time=BASE_T + 2 * H,
        )
        results = run_backtest(config, AlwaysBuyStrategy())

        # All trades should have open_time >= start_time
        for r in results:
            assert r.open_time >= BASE_T + 2 * H

    def test_end_time_only(self, tmp_path: Path) -> None:
        """end_time skips late klines."""
        klines = self._klines()
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=Decimal("1000"),
            stop_loss_pct=Decimal("2.0"),
            take_profit_pct=Decimal("3.0"),
            timeout_minutes=180,
            data_dir=tmp_path,
            end_time=BASE_T + 2 * H,
        )
        results = run_backtest(config, AlwaysBuyStrategy())

        # All trade entries should come from klines within the range
        for r in results:
            assert r.open_time <= BASE_T + 2 * H + H  # close_time of last included kline

    def test_both_start_and_end_time(self, tmp_path: Path) -> None:
        """Both start_time and end_time restrict to a window."""
        klines = self._klines()
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=Decimal("1000"),
            stop_loss_pct=Decimal("2.0"),
            take_profit_pct=Decimal("3.0"),
            timeout_minutes=180,
            data_dir=tmp_path,
            start_time=BASE_T + 1 * H,
            end_time=BASE_T + 3 * H,
        )
        strat = HistoryTrackingStrategy()
        run_backtest(config, strat)

        # 3 klines in window: indices 1, 2, 3
        assert strat.lengths == [1, 2, 3]

    def test_start_time_after_all_data(self, tmp_path: Path) -> None:
        """start_time beyond last kline -> empty results."""
        klines = self._klines()
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=Decimal("1000"),
            stop_loss_pct=Decimal("2.0"),
            take_profit_pct=Decimal("3.0"),
            timeout_minutes=180,
            data_dir=tmp_path,
            start_time=BASE_T + 100 * H,
        )
        results = run_backtest(config, AlwaysBuyStrategy())

        assert results == []

    def test_end_time_before_all_data(self, tmp_path: Path) -> None:
        """end_time before first kline -> empty results."""
        klines = self._klines()
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=Decimal("1000"),
            stop_loss_pct=Decimal("2.0"),
            take_profit_pct=Decimal("3.0"),
            timeout_minutes=180,
            data_dir=tmp_path,
            end_time=BASE_T - H,
        )
        results = run_backtest(config, AlwaysBuyStrategy())

        assert results == []

    def test_start_after_end_returns_empty(self, tmp_path: Path) -> None:
        """start_time > end_time -> empty results."""
        klines = self._klines()
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=Decimal("1000"),
            stop_loss_pct=Decimal("2.0"),
            take_profit_pct=Decimal("3.0"),
            timeout_minutes=180,
            data_dir=tmp_path,
            start_time=BASE_T + 3 * H,
            end_time=BASE_T + 1 * H,
        )
        results = run_backtest(config, AlwaysBuyStrategy())

        assert results == []

    def test_default_none_uses_full_range(self, tmp_path: Path) -> None:
        """Both None (default) -> all klines used."""
        klines = self._klines()
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        strat = HistoryTrackingStrategy()
        run_backtest(config, strat)

        assert strat.lengths == [1, 2, 3, 4, 5]
