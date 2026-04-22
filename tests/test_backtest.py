from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig, Signal, TradeResult
from crypto_trade.backtest_report import (
    aggregate_daily_pnl,
    generate_html_report,
    to_daily_returns_series,
)
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
        max_amount_usd=1000.0,
        stop_loss_pct=2.0,
        take_profit_pct=3.0,
        timeout_minutes=180,  # 3 hours
        fee_pct=0.1,
        data_dir=data_dir,
    )


# ---------------------------------------------------------------------------
# Test strategies
# ---------------------------------------------------------------------------


class AlwaysBuyStrategy:
    """Emit a buy signal on every kline (weight=100)."""

    def compute_features(self, master: pd.DataFrame) -> None:
        pass

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        return Signal(direction=1, weight=100)


class AlwaysSellStrategy:
    """Emit a sell signal on every kline (weight=100)."""

    def compute_features(self, master: pd.DataFrame) -> None:
        pass

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        return Signal(direction=-1, weight=100)


class DoNothingStrategy:
    """Never trade."""

    def compute_features(self, master: pd.DataFrame) -> None:
        pass

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        return Signal(direction=0, weight=0)


class WeightedBuyStrategy:
    """Emit a buy signal with weight=25."""

    def compute_features(self, master: pd.DataFrame) -> None:
        pass

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        return Signal(direction=1, weight=25)


class BuyOnceStrategy:
    """Buy only on the first kline."""

    def __init__(self) -> None:
        self._bought: set[str] = set()

    def compute_features(self, master: pd.DataFrame) -> None:
        self._bought = set()

    def get_signal(self, symbol: str, open_time: int) -> Signal:
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
        assert r.exit_price == pytest.approx(103)
        assert r.pnl_pct > 0
        assert r.net_pnl_pct == pytest.approx(r.pnl_pct - r.fee_pct)


class TestStopLoss:
    """2. Single trade hits stop loss."""

    def test_long_stop_loss(self, tmp_path: Path) -> None:
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
        assert r.exit_price == pytest.approx(98)
        assert r.pnl_pct < 0


class TestTimeout:
    """3. Timeout — no SL/TP hit, exits at candle open price."""

    def test_timeout_exit(self, tmp_path: Path) -> None:
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
            max_amount_usd=1000.0,
            stop_loss_pct=2.0,
            take_profit_pct=3.0,
            timeout_minutes=60,
            fee_pct=0.1,
            data_dir=tmp_path,
        )
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.exit_reason == "timeout"
        assert r.exit_price == pytest.approx(99.5)


class TestShortOrderTPSL:
    """4. Short order TP/SL — reversed direction logic."""

    def test_short_take_profit(self, tmp_path: Path) -> None:
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
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101.5", "98.5", "100.5"),
            _make_kline(BASE_T + 2 * H, "100.5", "102", "99", "101"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

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
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101.5", "98.5", "100"),
            _make_kline(BASE_T + 2 * H, "99", "104", "97", "101"),
            _make_kline(BASE_T + 3 * H, "101", "102", "100", "101"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=1000.0,
            stop_loss_pct=2.0,
            take_profit_pct=3.0,
            timeout_minutes=60,
            fee_pct=0.1,
            data_dir=tmp_path,
        )
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.exit_reason == "timeout"


class TestFeeDeduction:
    """10. Fee deduction — net_pnl = pnl - fee."""

    def test_fee_subtracted(self, tmp_path: Path) -> None:
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),
            _make_kline(BASE_T + 2 * H, "103", "105", "102", "104"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.fee_pct == pytest.approx(0.1)
        assert r.net_pnl_pct == pytest.approx(r.pnl_pct - 0.1)


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
        assert r.weight_factor == pytest.approx(0.25)
        assert r.weighted_pnl == pytest.approx(r.net_pnl_pct * 0.25)


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
        assert r.exit_price == pytest.approx(100.5)


class TestDailyPnL:
    """14. Daily P&L averaging — multiple trades same day."""

    def test_daily_aggregation(self) -> None:
        day_start_ms = 1_699_920_000_000
        t1 = TradeResult(
            symbol="A",
            direction=1,
            entry_price=100.0,
            exit_price=103.0,
            weight_factor=1.0,
            open_time=day_start_ms,
            close_time=day_start_ms + 3_600_000,
            exit_reason="take_profit",
            pnl_pct=3.0,
            fee_pct=0.1,
            net_pnl_pct=2.9,
            weighted_pnl=2.9,
        )
        t2 = TradeResult(
            symbol="B",
            direction=1,
            entry_price=100.0,
            exit_price=98.0,
            weight_factor=1.0,
            open_time=day_start_ms,
            close_time=day_start_ms + 7_200_000,
            exit_reason="stop_loss",
            pnl_pct=-2.0,
            fee_pct=0.1,
            net_pnl_pct=-2.1,
            weighted_pnl=-2.1,
        )
        daily = aggregate_daily_pnl([t1, t2])

        assert len(daily) == 1
        d = daily[0]
        assert d.trade_count == 2
        expected_avg = (2.9 + (-2.1)) / 2
        assert d.avg_weighted_pnl == pytest.approx(expected_avg)
        assert len(d.trades) == 2


class TestEmptyKlinesSkipped:
    """15. Empty/missing klines are skipped gracefully."""

    def test_no_data_returns_empty(self, tmp_path: Path) -> None:
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())
        assert results == []


class TestEntryAtCloseCheckNextCandle:
    """16. Entry at close, first check at next candle."""

    def test_order_checked_next_candle(self, tmp_path: Path) -> None:
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
        assert r.open_time == klines[0].close_time
        assert r.exit_reason == "take_profit"
        assert r.close_time == klines[2].close_time


# ---------------------------------------------------------------------------
# Additional test strategies
# ---------------------------------------------------------------------------


class ZeroWeightBuyStrategy:
    def compute_features(self, master: pd.DataFrame) -> None:
        pass

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        return Signal(direction=1, weight=0)


class NegativeWeightSellStrategy:
    def compute_features(self, master: pd.DataFrame) -> None:
        pass

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        return Signal(direction=-1, weight=-10)


class MinWeightBuyStrategy:
    def compute_features(self, master: pd.DataFrame) -> None:
        pass

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        return Signal(direction=1, weight=1)


class CustomWeightStrategy:
    def __init__(self, direction: int, weight: int) -> None:
        self._direction = direction
        self._weight = weight

    def compute_features(self, master: pd.DataFrame) -> None:
        pass

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        return Signal(direction=self._direction, weight=self._weight)


class SellOnceStrategy:
    def __init__(self) -> None:
        self._sold: set[str] = set()

    def compute_features(self, master: pd.DataFrame) -> None:
        self._sold = set()

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        if symbol not in self._sold:
            self._sold.add(symbol)
            return Signal(direction=-1, weight=100)
        return Signal(direction=0, weight=0)


class HistoryTrackingStrategy:
    """Records call count (1-based) on each get_signal call."""

    def __init__(self) -> None:
        self.lengths: list[int] = []

    def compute_features(self, master: pd.DataFrame) -> None:
        self.lengths = []

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        self.lengths.append(len(self.lengths) + 1)
        return Signal(direction=0, weight=0)


class CallOrderTracker:
    """Records (symbol, open_time) for each get_signal call."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def compute_features(self, master: pd.DataFrame) -> None:
        self.calls = []

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        self.calls.append((symbol, open_time))
        return Signal(direction=0, weight=0)


# ---------------------------------------------------------------------------
# 1. Short-Specific Exit Paths
# ---------------------------------------------------------------------------


class TestShortTimeoutExit:
    def test_short_timeout_exit(self, tmp_path: Path) -> None:
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
            max_amount_usd=1000.0,
            stop_loss_pct=2.0,
            take_profit_pct=3.0,
            timeout_minutes=60,
            fee_pct=0.1,
            data_dir=tmp_path,
        )
        results = run_backtest(config, AlwaysSellStrategy())

        r = results[0]
        assert r.exit_reason == "timeout"
        assert r.direction == -1
        assert r.exit_price == pytest.approx(99.5)
        expected_pnl = (100 - 99.5) / 100 * 100
        assert r.pnl_pct == pytest.approx(expected_pnl)


class TestShortEndOfDataClose:
    def test_short_end_of_data_close(self, tmp_path: Path) -> None:
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
        assert r.exit_price == pytest.approx(100.5)
        expected_pnl = (100 - 100.5) / 100 * 100
        assert r.pnl_pct == pytest.approx(expected_pnl)


# ---------------------------------------------------------------------------
# 2. Exact Boundary Hits
# ---------------------------------------------------------------------------


class TestExactBoundaryHits:
    def test_long_sl_exact_boundary(self, tmp_path: Path) -> None:
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "102", "98", "101"),
            _make_kline(BASE_T + 2 * H, "101", "102", "100", "101"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.exit_reason == "stop_loss"
        assert r.exit_price == pytest.approx(98)

    def test_long_tp_exact_boundary(self, tmp_path: Path) -> None:
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "103", "99", "102"),
            _make_kline(BASE_T + 2 * H, "102", "103", "101", "102"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.exit_reason == "take_profit"
        assert r.exit_price == pytest.approx(103)

    def test_short_sl_exact_boundary(self, tmp_path: Path) -> None:
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "102", "99", "101"),
            _make_kline(BASE_T + 2 * H, "101", "102", "100", "101"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysSellStrategy())

        r = results[0]
        assert r.exit_reason == "stop_loss"
        assert r.exit_price == pytest.approx(102)

    def test_short_tp_exact_boundary(self, tmp_path: Path) -> None:
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "99", "101", "97", "98"),
            _make_kline(BASE_T + 2 * H, "98", "99", "97", "98"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysSellStrategy())

        r = results[0]
        assert r.exit_reason == "take_profit"
        assert r.exit_price == pytest.approx(97)

    def test_long_price_just_misses_sl(self, tmp_path: Path) -> None:
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "102", "98.01", "101"),
            _make_kline(BASE_T + 2 * H, "101", "102", "99", "101"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, BuyOnceStrategy())

        assert len(results) == 1
        r = results[0]
        assert r.exit_reason == "end_of_data"

    def test_long_price_just_misses_tp(self, tmp_path: Path) -> None:
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "102.99", "99", "102"),
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
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),
            _make_kline(BASE_T + 2 * H, "103", "104", "102", "103"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        assert len(results) >= 2
        assert results[0].exit_reason == "take_profit"
        assert results[1].exit_reason == "end_of_data"

    def test_reopen_on_same_candle_after_sl(self, tmp_path: Path) -> None:
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "99", "101", "97", "98"),
            _make_kline(BASE_T + 2 * H, "98", "99", "97", "98"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        assert len(results) >= 2
        assert results[0].exit_reason == "stop_loss"
        assert results[1].exit_reason == "end_of_data"

    def test_reopen_on_same_candle_after_timeout(self, tmp_path: Path) -> None:
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
            max_amount_usd=1000.0,
            stop_loss_pct=2.0,
            take_profit_pct=3.0,
            timeout_minutes=60,
            fee_pct=0.1,
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
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101", "99", "100"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, ZeroWeightBuyStrategy())
        assert len(results) == 0

    def test_nonzero_direction_negative_weight_ignored(self, tmp_path: Path) -> None:
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101", "99", "100"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, NegativeWeightSellStrategy())
        assert len(results) == 0

    def test_weight_1_minimum(self, tmp_path: Path) -> None:
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),
            _make_kline(BASE_T + 2 * H, "103", "105", "102", "104"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, MinWeightBuyStrategy())

        r = results[0]
        assert r.weight_factor == pytest.approx(0.01)
        assert r.weighted_pnl == pytest.approx(r.net_pnl_pct * 0.01)

    def test_weight_100_maximum(self, tmp_path: Path) -> None:
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),
            _make_kline(BASE_T + 2 * H, "103", "105", "102", "104"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.weight_factor == pytest.approx(1.0)
        assert r.weighted_pnl == pytest.approx(r.net_pnl_pct)


# ---------------------------------------------------------------------------
# 5. Realistic Price Scenarios
# ---------------------------------------------------------------------------


class TestRealisticPriceScenarios:
    def test_btc_long_take_profit(self, tmp_path: Path) -> None:
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
        assert r.entry_price == pytest.approx(40000)
        assert r.exit_price == pytest.approx(41200)
        assert r.pnl_pct == pytest.approx(3.0)

    def test_eth_short_stop_loss(self, tmp_path: Path) -> None:
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
        assert r.entry_price == pytest.approx(2500)
        assert r.exit_price == pytest.approx(2550)
        assert r.pnl_pct == pytest.approx(-2.0)

    def test_sol_long_stop_loss(self, tmp_path: Path) -> None:
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
        assert r.entry_price == pytest.approx(100)
        assert r.exit_price == pytest.approx(98)
        assert r.pnl_pct == pytest.approx(-2.0)

    def test_btc_short_take_profit(self, tmp_path: Path) -> None:
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
        assert r.entry_price == pytest.approx(40000)
        assert r.exit_price == pytest.approx(38800)
        assert r.pnl_pct == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# 6. Multi-Symbol Advanced
# ---------------------------------------------------------------------------


class TestMultiSymbolAdvanced:
    def test_three_symbols_different_exits(self, tmp_path: Path) -> None:
        klines_btc = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),
            _make_kline(BASE_T + 2 * H, "103", "104", "102", "103"),
        ]
        klines_eth = [
            _make_kline(BASE_T, "50", "51", "49", "50"),
            _make_kline(BASE_T + H, "50", "51", "48.5", "49"),
            _make_kline(BASE_T + 2 * H, "49", "50", "48", "49"),
        ]
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
        assert len(results) == 0

    def test_no_overlap_produces_independent_results(self, tmp_path: Path) -> None:
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
        symbols_in_results = {r.symbol for r in results}
        assert "SYM_A" in symbols_in_results
        assert "SYM_B" in symbols_in_results


# ---------------------------------------------------------------------------
# 7. Consecutive Trade Chain
# ---------------------------------------------------------------------------


class TestConsecutiveTradeChain:
    def test_tp_then_sl_then_timeout_chain(self, tmp_path: Path) -> None:
        klines = [
            _make_kline(BASE_T, "99", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),
            _make_kline(BASE_T + 2 * H, "102", "105", "100", "101"),
            _make_kline(BASE_T + 3 * H, "101", "103", "99.5", "101"),
            _make_kline(BASE_T + 4 * H, "101", "102", "100", "101"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=1000.0,
            stop_loss_pct=2.0,
            take_profit_pct=3.0,
            timeout_minutes=60,
            fee_pct=0.1,
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
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),
            _make_kline(BASE_T + 2 * H, "103", "105", "102", "104"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.entry_price == pytest.approx(100)
        assert r.exit_price == pytest.approx(103)
        assert r.pnl_pct == pytest.approx(3.0)
        assert r.fee_pct == pytest.approx(0.1)
        assert r.net_pnl_pct == pytest.approx(2.9)
        assert r.weight_factor == pytest.approx(1.0)
        assert r.weighted_pnl == pytest.approx(2.9)

    def test_short_pnl_exact_values(self, tmp_path: Path) -> None:
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "103", "100", "102"),
            _make_kline(BASE_T + 2 * H, "102", "103", "101", "102"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, CustomWeightStrategy(direction=-1, weight=50))

        r = results[0]
        assert r.entry_price == pytest.approx(100)
        assert r.exit_price == pytest.approx(102)
        assert r.pnl_pct == pytest.approx(-2.0)
        assert r.fee_pct == pytest.approx(0.1)
        assert r.net_pnl_pct == pytest.approx(-2.1)
        assert r.weight_factor == pytest.approx(0.5)
        assert r.weighted_pnl == pytest.approx(-2.1 * 0.5)

    def test_timeout_pnl_non_round_numbers(self, tmp_path: Path) -> None:
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101.5", "98.5", "100"),
            _make_kline(BASE_T + 2 * H, "99.5", "101.5", "98.5", "100"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=1000.0,
            stop_loss_pct=2.0,
            take_profit_pct=3.0,
            timeout_minutes=60,
            fee_pct=0.1,
            data_dir=tmp_path,
        )
        results = run_backtest(config, BuyOnceStrategy())

        r = results[0]
        assert r.exit_reason == "timeout"
        assert r.exit_price == pytest.approx(99.5)
        expected_pnl = (99.5 - 100) / 100 * 100
        assert r.pnl_pct == pytest.approx(expected_pnl)
        assert r.net_pnl_pct == pytest.approx(expected_pnl - 0.1)

    def test_end_of_data_zero_pnl(self, tmp_path: Path) -> None:
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101.5", "98.5", "100"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, BuyOnceStrategy())

        r = results[0]
        assert r.exit_reason == "end_of_data"
        assert r.exit_price == pytest.approx(100)
        assert r.pnl_pct == pytest.approx(0)
        assert r.net_pnl_pct == pytest.approx(-0.1)
        assert r.weighted_pnl == pytest.approx(-0.1)


# ---------------------------------------------------------------------------
# 9. Daily PnL Report
# ---------------------------------------------------------------------------


class TestDailyPnLReport:
    def test_trades_across_two_days(self) -> None:
        day1_ms = 1_699_920_000_000
        day2_ms = 1_700_006_400_000
        t1 = TradeResult(
            symbol="A",
            direction=1,
            entry_price=100.0,
            exit_price=103.0,
            weight_factor=1.0,
            open_time=day1_ms,
            close_time=day1_ms + 3_600_000,
            exit_reason="take_profit",
            pnl_pct=3.0,
            fee_pct=0.1,
            net_pnl_pct=2.9,
            weighted_pnl=2.9,
        )
        t2 = TradeResult(
            symbol="B",
            direction=1,
            entry_price=100.0,
            exit_price=98.0,
            weight_factor=1.0,
            open_time=day2_ms,
            close_time=day2_ms + 3_600_000,
            exit_reason="stop_loss",
            pnl_pct=-2.0,
            fee_pct=0.1,
            net_pnl_pct=-2.1,
            weighted_pnl=-2.1,
        )
        daily = aggregate_daily_pnl([t1, t2])
        assert len(daily) == 2
        assert daily[0].date == "2023-11-14"
        assert daily[0].trade_count == 1
        assert daily[1].date == "2023-11-15"
        assert daily[1].trade_count == 1

    def test_empty_results_list(self) -> None:
        assert aggregate_daily_pnl([]) == []

    def test_single_trade_day(self) -> None:
        day_ms = 1_699_920_000_000
        t = TradeResult(
            symbol="A",
            direction=1,
            entry_price=100.0,
            exit_price=103.0,
            weight_factor=0.5,
            open_time=day_ms,
            close_time=day_ms + 3_600_000,
            exit_reason="take_profit",
            pnl_pct=3.0,
            fee_pct=0.1,
            net_pnl_pct=2.9,
            weighted_pnl=1.45,
        )
        daily = aggregate_daily_pnl([t])
        assert len(daily) == 1
        assert daily[0].avg_weighted_pnl == pytest.approx(1.45)
        assert daily[0].trade_count == 1

    def test_integration_with_backtest(self, tmp_path: Path) -> None:
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
        klines = [_make_kline(BASE_T, "100", "101", "99", "100")]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        assert len(results) == 1
        r = results[0]
        assert r.exit_reason == "end_of_data"
        assert r.entry_price == pytest.approx(100)
        assert r.exit_price == pytest.approx(100)
        assert r.pnl_pct == pytest.approx(0)

    def test_single_kline_no_signal_no_trades(self, tmp_path: Path) -> None:
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
# 12. History Accumulation (now index-based)
# ---------------------------------------------------------------------------


class TestHistoryAccumulation:
    def test_strategy_receives_growing_history(self, tmp_path: Path) -> None:
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
        klines_a = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "102", "99", "101"),
            _make_kline(BASE_T + 2 * H, "101", "104", "100", "103"),
        ]
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
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),
            _make_kline(BASE_T + 2 * H, "103", "105", "102", "104"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=1000.0,
            stop_loss_pct=2.0,
            take_profit_pct=3.0,
            timeout_minutes=180,
            fee_pct=0.0,
            data_dir=tmp_path,
        )
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.fee_pct == pytest.approx(0)
        assert r.net_pnl_pct == pytest.approx(r.pnl_pct)

    def test_fee_larger_than_pnl_produces_negative_net(self, tmp_path: Path) -> None:
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),
            _make_kline(BASE_T + 2 * H, "103", "105", "102", "104"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=1000.0,
            stop_loss_pct=2.0,
            take_profit_pct=3.0,
            timeout_minutes=180,
            fee_pct=5.0,
            data_dir=tmp_path,
        )
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.pnl_pct == pytest.approx(3.0)
        assert r.fee_pct == pytest.approx(5.0)
        assert r.net_pnl_pct == pytest.approx(-2.0)
        assert r.net_pnl_pct < 0


# ---------------------------------------------------------------------------
# 16. Order Creation Verification
# ---------------------------------------------------------------------------


class TestOrderCreationVerification:
    def test_order_prices_long(self, tmp_path: Path) -> None:
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "101", "104", "100", "103"),
            _make_kline(BASE_T + 2 * H, "103", "105", "102", "104"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysBuyStrategy())

        r = results[0]
        assert r.entry_price == pytest.approx(100)
        assert r.exit_price == pytest.approx(103)
        assert r.exit_reason == "take_profit"
        assert r.weight_factor == pytest.approx(1.0)

    def test_order_prices_short(self, tmp_path: Path) -> None:
        klines = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "99", "100", "96", "97"),
            _make_kline(BASE_T + 2 * H, "97", "98", "95", "96"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        results = run_backtest(config, AlwaysSellStrategy())

        r = results[0]
        assert r.entry_price == pytest.approx(100)
        assert r.exit_price == pytest.approx(97)
        assert r.exit_reason == "take_profit"
        assert r.direction == -1
        assert r.weight_factor == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 17. Start/End Time Filtering
# ---------------------------------------------------------------------------


class TestStartEndTime:
    def _klines(self) -> list[Kline]:
        return [_make_kline(BASE_T + i * H, "100", "101", "99", "100") for i in range(5)]

    def test_start_time_only(self, tmp_path: Path) -> None:
        klines = self._klines()
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=1000.0,
            stop_loss_pct=2.0,
            take_profit_pct=3.0,
            timeout_minutes=180,
            data_dir=tmp_path,
            start_time=BASE_T + 2 * H,
        )
        results = run_backtest(config, AlwaysBuyStrategy())
        for r in results:
            assert r.open_time >= BASE_T + 2 * H

    def test_end_time_only(self, tmp_path: Path) -> None:
        klines = self._klines()
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=1000.0,
            stop_loss_pct=2.0,
            take_profit_pct=3.0,
            timeout_minutes=180,
            data_dir=tmp_path,
            end_time=BASE_T + 2 * H,
        )
        results = run_backtest(config, AlwaysBuyStrategy())
        for r in results:
            assert r.open_time <= BASE_T + 2 * H + H

    def test_both_start_and_end_time(self, tmp_path: Path) -> None:
        klines = self._klines()
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=1000.0,
            stop_loss_pct=2.0,
            take_profit_pct=3.0,
            timeout_minutes=180,
            data_dir=tmp_path,
            start_time=BASE_T + 1 * H,
            end_time=BASE_T + 3 * H,
        )
        strat = HistoryTrackingStrategy()
        run_backtest(config, strat)
        assert strat.lengths == [1, 2, 3]

    def test_start_time_after_all_data(self, tmp_path: Path) -> None:
        klines = self._klines()
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=1000.0,
            stop_loss_pct=2.0,
            take_profit_pct=3.0,
            timeout_minutes=180,
            data_dir=tmp_path,
            start_time=BASE_T + 100 * H,
        )
        results = run_backtest(config, AlwaysBuyStrategy())
        assert results == []

    def test_end_time_before_all_data(self, tmp_path: Path) -> None:
        klines = self._klines()
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=1000.0,
            stop_loss_pct=2.0,
            take_profit_pct=3.0,
            timeout_minutes=180,
            data_dir=tmp_path,
            end_time=BASE_T - H,
        )
        results = run_backtest(config, AlwaysBuyStrategy())
        assert results == []

    def test_start_after_end_returns_empty(self, tmp_path: Path) -> None:
        klines = self._klines()
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=1000.0,
            stop_loss_pct=2.0,
            take_profit_pct=3.0,
            timeout_minutes=180,
            data_dir=tmp_path,
            start_time=BASE_T + 3 * H,
            end_time=BASE_T + 1 * H,
        )
        results = run_backtest(config, AlwaysBuyStrategy())
        assert results == []

    def test_default_none_uses_full_range(self, tmp_path: Path) -> None:
        klines = self._klines()
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)
        strat = HistoryTrackingStrategy()
        run_backtest(config, strat)
        assert strat.lengths == [1, 2, 3, 4, 5]


# ---------------------------------------------------------------------------
# Chronological Iteration
# ---------------------------------------------------------------------------


class TestChronologicalIteration:
    def test_merged_iteration_in_time_order(self, tmp_path: Path) -> None:
        """Symbols with staggered starts are iterated in timestamp order."""
        # SYM_A: starts at BASE_T
        klines_a = [
            _make_kline(BASE_T, "100", "101", "99", "100"),
            _make_kline(BASE_T + H, "100", "101", "99", "100"),
            _make_kline(BASE_T + 2 * H, "100", "101", "99", "100"),
        ]
        # SYM_B: starts at BASE_T + H (one hour later)
        klines_b = [
            _make_kline(BASE_T + H, "50", "51", "49", "50"),
            _make_kline(BASE_T + 2 * H, "50", "51", "49", "50"),
            _make_kline(BASE_T + 3 * H, "50", "51", "49", "50"),
        ]
        _write_symbol_data(tmp_path, "SYM_A", klines_a)
        _write_symbol_data(tmp_path, "SYM_B", klines_b)
        config = _default_config(tmp_path, symbols=("SYM_A", "SYM_B"))
        strat = CallOrderTracker()
        run_backtest(config, strat)

        # Verify timestamps are non-decreasing
        times = [t for _, t in strat.calls]
        assert times == sorted(times)

        # Both symbols were visited
        symbols_seen = {s for s, _ in strat.calls}
        assert symbols_seen == {"SYM_A", "SYM_B"}


# ---------------------------------------------------------------------------
# Daily Returns Series & HTML Report
# ---------------------------------------------------------------------------

DAY_MS = 86_400_000  # 1 day in ms


def _make_trade(close_time: int, weighted_pnl: float) -> TradeResult:
    """Create a minimal TradeResult for returns tests."""
    return TradeResult(
        symbol="TEST",
        direction=1,
        entry_price=100.0,
        exit_price=101.0,
        weight_factor=1.0,
        open_time=close_time - 3_600_000,
        close_time=close_time,
        exit_reason="take_profit",
        pnl_pct=weighted_pnl,
        fee_pct=0.0,
        net_pnl_pct=weighted_pnl,
        weighted_pnl=weighted_pnl,
    )


class TestDailyReturnsSeries:
    # 2024-01-15 00:00 UTC in ms
    DAY1 = 1_705_276_800_000
    DAY2 = DAY1 + DAY_MS
    DAY3 = DAY1 + 2 * DAY_MS

    def test_basic(self) -> None:
        """Two trades on different days produce correct decimal returns."""
        trades = [
            _make_trade(self.DAY1, 2.0),  # +2%
            _make_trade(self.DAY2, -1.0),  # -1%
        ]
        s = to_daily_returns_series(trades)
        assert len(s) == 2
        assert abs(s.iloc[0] - 0.02) < 1e-9
        assert abs(s.iloc[1] - (-0.01)) < 1e-9

    def test_fills_gaps(self) -> None:
        """Missing days between trades are filled with 0.0."""
        trades = [
            _make_trade(self.DAY1, 1.0),
            _make_trade(self.DAY3, 1.0),
        ]
        s = to_daily_returns_series(trades)
        assert len(s) == 3
        assert s.iloc[1] == 0.0

    def test_sums_same_day(self) -> None:
        """Multiple trades on the same day are summed."""
        trades = [
            _make_trade(self.DAY1, 1.5),
            _make_trade(self.DAY1, 0.5),
        ]
        s = to_daily_returns_series(trades)
        assert len(s) == 1
        assert abs(s.iloc[0] - 0.02) < 1e-9  # (1.5 + 0.5) / 100

    def test_empty(self) -> None:
        """Empty input returns empty Series."""
        s = to_daily_returns_series([])
        assert s.empty

    def test_date_range_extends(self) -> None:
        """start_date/end_date extend the series beyond trade dates."""
        trades = [_make_trade(self.DAY2, 1.0)]
        s = to_daily_returns_series(trades, start_date="2024-01-15", end_date="2024-01-19")
        assert len(s) == 5  # Jan 15-19
        assert s.iloc[0] == 0.0  # Jan 15 (before trade)
        assert abs(s.iloc[1] - 0.01) < 1e-9  # Jan 16 (trade day)
        assert s.iloc[-1] == 0.0  # Jan 19 (after trade)


class TestGenerateHtmlReport:
    def test_creates_file(self, tmp_path: Path) -> None:
        """Integration test: HTML file is created and contains title."""
        import numpy as np

        idx = pd.date_range("2024-01-01", periods=60, freq="D")
        rng = np.random.default_rng(42)
        returns = pd.Series(rng.normal(0.001, 0.02, len(idx)), index=idx, name="Returns")

        out = generate_html_report(returns, tmp_path / "report.html", title="Test Report")
        assert Path(out).exists()
        content = Path(out).read_text()
        assert "Test Report" in content


# ---------------------------------------------------------------------------
# R1 — Consecutive-SL cool-down (iter 173)
# ---------------------------------------------------------------------------


class TestR1ConsecutiveSlCooldown:
    def test_r1_triggers_after_k_consecutive_stop_losses(self, tmp_path: Path) -> None:
        """After K consecutive SLs, new trades on that symbol are suppressed for C candles."""
        # Build a price series that causes 3 consecutive LONG stop-losses then a recovery.
        # Each "trade opens on candle N, gets SL next candle" needs a drop ≥ 2% per SL.
        # Sequence: 100, 100, 98 (SL1), 98, 96 (SL2), 96, 94 (SL3), 94, 92 (would-be SL4),
        # 92, 94, ..., 98 (recovery long after C=5 candles).
        klines = [
            _make_kline(BASE_T + 0 * H, "100", "100", "100", "100"),  # open @ close=100
            _make_kline(BASE_T + 1 * H, "100", "100", "97", "98"),  # SL1 (low 97 < 98)
            _make_kline(BASE_T + 2 * H, "98", "98", "98", "98"),  # open @ 98
            _make_kline(BASE_T + 3 * H, "98", "98", "95", "96"),  # SL2
            _make_kline(BASE_T + 4 * H, "96", "96", "96", "96"),  # open @ 96
            _make_kline(BASE_T + 5 * H, "96", "96", "93", "94"),  # SL3 → triggers R1
            _make_kline(BASE_T + 6 * H, "94", "94", "94", "94"),  # R1 cool-down active
            _make_kline(BASE_T + 7 * H, "94", "94", "94", "94"),
            _make_kline(BASE_T + 8 * H, "94", "94", "94", "94"),
            _make_kline(BASE_T + 9 * H, "94", "94", "94", "94"),
            _make_kline(BASE_T + 10 * H, "94", "94", "94", "94"),  # cool-down ends here
            _make_kline(BASE_T + 11 * H, "94", "98", "94", "97"),  # trading can resume
            _make_kline(BASE_T + 12 * H, "97", "99", "96", "98"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=1000.0,
            stop_loss_pct=2.0,
            take_profit_pct=3.0,
            timeout_minutes=180,
            fee_pct=0.1,
            data_dir=tmp_path,
            cooldown_candles=0,
            risk_consecutive_sl_limit=3,
            risk_consecutive_sl_cooldown_candles=5,
        )
        results = run_backtest(config, AlwaysBuyStrategy())

        # Without R1 we'd have 5+ SL-or-end_of_data trades. With R1, after the third SL
        # there should be a cooldown window with NO new trades opening.
        sl_trades = [r for r in results if r.exit_reason == "stop_loss"]
        assert len(sl_trades) == 3, f"expected exactly 3 SL trades, got {len(sl_trades)}"
        # Verify the candles during the cool-down window produced no new trades
        cooldown_start = sl_trades[-1].close_time
        cooldown_end = cooldown_start + 5 * H
        in_cooldown = [r for r in results if cooldown_start < r.open_time < cooldown_end]
        assert len(in_cooldown) == 0, f"trades opened during the R1 cool-down window: {in_cooldown}"

    def test_r1_disabled_by_default(self, tmp_path: Path) -> None:
        """With risk_consecutive_sl_limit=None, behaviour unchanged from pre-iter-173."""
        klines = [
            _make_kline(BASE_T + 0 * H, "100", "100", "100", "100"),
            _make_kline(BASE_T + 1 * H, "100", "100", "97", "98"),
            _make_kline(BASE_T + 2 * H, "98", "98", "98", "98"),
            _make_kline(BASE_T + 3 * H, "98", "98", "95", "96"),
            _make_kline(BASE_T + 4 * H, "96", "96", "96", "96"),
            _make_kline(BASE_T + 5 * H, "96", "96", "93", "94"),
            _make_kline(BASE_T + 6 * H, "94", "94", "94", "94"),
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = _default_config(tmp_path)  # no R1 by default
        results = run_backtest(config, AlwaysBuyStrategy())
        sl_trades = [r for r in results if r.exit_reason == "stop_loss"]
        # Without R1 we expect 3 SLs in this data (one per down-candle)
        assert len(sl_trades) >= 3

    def test_r1_streak_resets_on_non_sl_exit(self, tmp_path: Path) -> None:
        """Streak counter resets when a trade exits via take_profit or timeout."""
        klines = [
            _make_kline(BASE_T + 0 * H, "100", "100", "100", "100"),  # open at 100
            _make_kline(BASE_T + 1 * H, "100", "100", "97", "98"),  # SL1
            _make_kline(BASE_T + 2 * H, "98", "98", "98", "98"),
            _make_kline(BASE_T + 3 * H, "98", "98", "95", "96"),  # SL2
            _make_kline(BASE_T + 4 * H, "96", "96", "96", "96"),
            _make_kline(
                BASE_T + 5 * H, "96", "100", "96", "99"
            ),  # TP (99/96-1 > 3%) → reset streak
            _make_kline(BASE_T + 6 * H, "99", "99", "99", "99"),
            _make_kline(
                BASE_T + 7 * H, "99", "99", "96", "97"
            ),  # SL3 (but streak reset, so not counted toward K=3)
        ]
        _write_symbol_data(tmp_path, "TEST", klines)
        config = BacktestConfig(
            symbols=("TEST",),
            interval="1h",
            max_amount_usd=1000.0,
            stop_loss_pct=2.0,
            take_profit_pct=3.0,
            timeout_minutes=180,
            fee_pct=0.1,
            data_dir=tmp_path,
            cooldown_candles=0,
            risk_consecutive_sl_limit=3,
            risk_consecutive_sl_cooldown_candles=5,
        )
        results = run_backtest(config, AlwaysBuyStrategy())
        # Should get 2 SL, 1 TP, 1 SL — not in R1 cooldown (streak reset by TP)
        sls = [r for r in results if r.exit_reason == "stop_loss"]
        tps = [r for r in results if r.exit_reason == "take_profit"]
        assert len(tps) >= 1, "expected at least one TP to reset the streak"
        assert len(sls) >= 3, "streak reset should allow the 3rd SL after the TP"
