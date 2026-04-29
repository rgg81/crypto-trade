"""Tests for order_manager — SL/TP parity with backtest, dry-run exits, timeouts."""

import httpx
import pytest

from crypto_trade.backtest import create_order
from crypto_trade.backtest_models import BacktestConfig, Signal
from crypto_trade.live.auth_client import AuthenticatedBinanceClient
from crypto_trade.live.models import LiveConfig, LiveTrade
from crypto_trade.live.order_manager import OrderManager, compute_sl_tp
from crypto_trade.live.state_store import StateStore


@pytest.fixture
def state(tmp_path):
    s = StateStore(tmp_path / "test.db")
    yield s
    s.close()


def _default_config(**overrides) -> LiveConfig:
    defaults = dict(
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        timeout_minutes=10080,
        fee_pct=0.1,
        max_amount_usd=1000.0,
        cooldown_candles=2,
        dry_run=True,
    )
    defaults.update(overrides)
    return LiveConfig(**defaults)


class TestSLTPParity:
    """SL/TP prices from live must exactly match backtest._create_order."""

    def test_long_fixed_barriers(self):
        signal = Signal(direction=1, weight=100)
        entry = 60000.0
        config = _default_config()

        sl, tp = compute_sl_tp(signal, entry, config)

        # backtest formula: sl = 60000 * (1 - 0.04) = 57600
        #                   tp = 60000 * (1 + 0.08) = 64800
        assert sl == pytest.approx(57600.0)
        assert tp == pytest.approx(64800.0)

    def test_short_fixed_barriers(self):
        signal = Signal(direction=-1, weight=100)
        entry = 60000.0
        config = _default_config()

        sl, tp = compute_sl_tp(signal, entry, config)

        # Short: sl = 60000 * (1 + 0.04) = 62400
        #        tp = 60000 * (1 - 0.08) = 55200
        assert sl == pytest.approx(62400.0)
        assert tp == pytest.approx(55200.0)

    def test_dynamic_atr_barriers(self):
        """Signal with tp_pct/sl_pct (from LightGBM ATR) overrides config."""
        signal = Signal(direction=1, weight=100, tp_pct=5.8, sl_pct=2.9)
        entry = 60000.0
        config = _default_config()

        sl, tp = compute_sl_tp(signal, entry, config)

        # Should use signal values, not config
        assert sl == pytest.approx(60000 * (1 - 0.029))
        assert tp == pytest.approx(60000 * (1 + 0.058))

    def test_parity_with_backtest_create_order(self):
        """Exact numeric parity: live compute_sl_tp == backtest create_order."""
        signal = Signal(direction=1, weight=100, tp_pct=5.8, sl_pct=2.9)
        entry = 63542.17
        close_time = 1700000000000

        config = _default_config()
        sl_live, tp_live = compute_sl_tp(signal, entry, config)

        # Create equivalent backtest config and order
        bt_config = BacktestConfig(
            symbols=("BTCUSDT",),
            interval="8h",
            max_amount_usd=1000.0,
            stop_loss_pct=4.0,
            take_profit_pct=8.0,
            timeout_minutes=10080,
            fee_pct=0.1,
        )
        bt_order = create_order("BTCUSDT", signal, entry, close_time, bt_config)

        assert sl_live == pytest.approx(bt_order.stop_loss_price)
        assert tp_live == pytest.approx(bt_order.take_profit_price)


class TestDryRunOpen:
    def test_open_trade_creates_record(self, state):
        config = _default_config()
        mgr = OrderManager(config, state)

        signal = Signal(direction=1, weight=100, tp_pct=5.0, sl_pct=2.5)
        trade = mgr.open_trade(
            model_name="A",
            symbol="BTCUSDT",
            signal=signal,
            entry_price=60000.0,
            candle_close_time=1000000,
            candle_open_time=999000,
            weight_factor=1.0,
        )

        assert trade.status == "open"
        assert trade.entry_order_id.startswith("DRY-")
        assert trade.sl_order_id.startswith("DRY-")
        assert trade.tp_order_id.startswith("DRY-")

        # Verify persisted
        stored = state.get_trade(trade.id)
        assert stored is not None
        assert stored.symbol == "BTCUSDT"
        assert stored.direction == 1


class TestDryRunExit:
    def test_sl_hit_on_candle(self, state):
        config = _default_config()
        mgr = OrderManager(config, state)

        trade = LiveTrade(
            id="t1",
            model_name="A",
            symbol="BTCUSDT",
            direction=1,
            entry_price=60000.0,
            amount_usd=1000.0,
            weight_factor=1.0,
            stop_loss_price=57600.0,
            take_profit_price=64800.0,
            open_time=1000000,
            timeout_time=99999999999,
            signal_time=999000,
        )
        state.upsert_trade(trade)

        # Candle where low hits SL
        reason = mgr.check_dry_run_exit(
            trade,
            candle_open_time=2000000,
            candle_open=59000.0,
            candle_high=59500.0,
            candle_low=57000.0,  # below SL=57600
            candle_close_time=2999999,
        )
        assert reason == "stop_loss"
        assert state.get_trade("t1").status == "closed"

    def test_tp_hit_on_candle(self, state):
        config = _default_config()
        mgr = OrderManager(config, state)

        trade = LiveTrade(
            id="t2",
            model_name="C",
            symbol="LINKUSDT",
            direction=1,
            entry_price=20.0,
            amount_usd=1000.0,
            weight_factor=1.0,
            stop_loss_price=19.2,
            take_profit_price=21.6,
            open_time=1000000,
            timeout_time=99999999999,
            signal_time=999000,
        )
        state.upsert_trade(trade)

        reason = mgr.check_dry_run_exit(
            trade,
            candle_open_time=2000000,
            candle_open=20.5,
            candle_high=22.0,  # above TP=21.6
            candle_low=20.0,
            candle_close_time=2999999,
        )
        assert reason == "take_profit"

    def test_no_exit(self, state):
        config = _default_config()
        mgr = OrderManager(config, state)

        trade = LiveTrade(
            id="t3",
            model_name="D",
            symbol="BNBUSDT",
            direction=1,
            entry_price=300.0,
            amount_usd=1000.0,
            weight_factor=1.0,
            stop_loss_price=288.0,
            take_profit_price=324.0,
            open_time=1000000,
            timeout_time=99999999999,
            signal_time=999000,
        )
        state.upsert_trade(trade)

        reason = mgr.check_dry_run_exit(
            trade,
            candle_open_time=2000000,
            candle_open=301.0,
            candle_high=310.0,
            candle_low=295.0,
            candle_close_time=2999999,
        )
        assert reason is None
        assert state.get_trade("t3").status == "open"


class TestTimeout:
    def test_timeout_closes_trade(self, state):
        config = _default_config()
        mgr = OrderManager(config, state)

        trade = LiveTrade(
            id="t4",
            model_name="A",
            symbol="BTCUSDT",
            direction=-1,
            entry_price=60000.0,
            amount_usd=1000.0,
            weight_factor=1.0,
            stop_loss_price=62400.0,
            take_profit_price=55200.0,
            open_time=1000000,
            timeout_time=2000000,
            signal_time=999000,
        )
        state.upsert_trade(trade)

        closed = mgr.check_timeouts(now_ms=3000000)
        assert len(closed) == 1
        assert state.get_trade("t4").status == "closed"
        assert state.get_trade("t4").exit_reason == "timeout"

    def test_no_timeout_before_deadline(self, state):
        config = _default_config()
        mgr = OrderManager(config, state)

        trade = LiveTrade(
            id="t5",
            model_name="A",
            symbol="BTCUSDT",
            direction=1,
            entry_price=60000.0,
            amount_usd=1000.0,
            weight_factor=1.0,
            stop_loss_price=57600.0,
            take_profit_price=64800.0,
            open_time=1000000,
            timeout_time=9999999999,
            signal_time=999000,
        )
        state.upsert_trade(trade)

        closed = mgr.check_timeouts(now_ms=1500000)
        assert len(closed) == 0
        assert state.get_trade("t5").status == "open"


def _live_config() -> LiveConfig:
    return LiveConfig(
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        timeout_minutes=10080,
        fee_pct=0.1,
        max_amount_usd=1000.0,
        cooldown_candles=2,
        dry_run=False,
    )


def _no_call_client() -> AuthenticatedBinanceClient:
    """A client whose transport raises on every call — proves no Binance traffic occurred."""

    def handler(request):
        raise AssertionError(
            f"Unexpected Binance call in --live mode for paper trade: "
            f"{request.method} {request.url.path}?{request.url.params}"
        )

    return AuthenticatedBinanceClient(
        api_key="t",
        api_secret="t",
        transport=httpx.MockTransport(handler),
    )


def _open_paper_trade(state: StateStore, **overrides) -> None:
    defaults = dict(
        id="t",
        model_name="A",
        symbol="BTCUSDT",
        direction=1,
        entry_price=60000.0,
        amount_usd=1000.0,
        weight_factor=1.0,
        stop_loss_price=57600.0,
        take_profit_price=64800.0,
        open_time=1,
        timeout_time=10**13,
        signal_time=0,
        entry_order_id="SEEDED",
        sl_order_id=None,
        tp_order_id=None,
    )
    defaults.update(overrides)
    state.upsert_trade(LiveTrade(**defaults))


class TestLiveModePaperSafety:
    """In --live mode, paper trades must not generate Binance traffic."""

    def test_check_exchange_exits_skips_seeded(self, state):
        _open_paper_trade(
            state, id="seeded-1", entry_order_id="SEEDED", sl_order_id=None, tp_order_id=None
        )
        mgr = OrderManager(_live_config(), state, _no_call_client())
        assert mgr.check_exchange_exits() == []
        assert state.get_trade("seeded-1").status == "open"

    def test_check_exchange_exits_skips_catchup(self, state):
        _open_paper_trade(
            state,
            id="cu-1",
            entry_order_id="CATCHUP-deadbeef",
            sl_order_id="CATCHUP-feedface",
            tp_order_id="CATCHUP-12345678",
        )
        mgr = OrderManager(_live_config(), state, _no_call_client())
        assert mgr.check_exchange_exits() == []

    def test_check_exchange_exits_skips_dry_prefix(self, state):
        _open_paper_trade(
            state,
            id="dry-1",
            entry_order_id="DRY-abc12345",
            sl_order_id="DRY-deadbeef",
            tp_order_id="DRY-feedface",
        )
        mgr = OrderManager(_live_config(), state, _no_call_client())
        assert mgr.check_exchange_exits() == []

    def test_check_exchange_exits_real_id_still_polled(self, state):
        """Regression — real numeric-ID trades still hit Binance."""
        called: list[str] = []

        def handler(request):
            called.append(str(request.url.path))
            return httpx.Response(200, json={"status": "NEW"})

        client = AuthenticatedBinanceClient(
            api_key="t",
            api_secret="t",
            transport=httpx.MockTransport(handler),
        )
        _open_paper_trade(
            state, id="real-1", entry_order_id="9876543210", sl_order_id="111", tp_order_id="222"
        )
        mgr = OrderManager(_live_config(), state, client)
        mgr.check_exchange_exits()
        assert any("/fapi/v1/order" in p for p in called)

    def test_timeout_paper_trade_no_binance_call_but_db_closed(self, state):
        """Paper trade hitting timeout in --live mode must update DB without
        calling place_market_order — that would OPEN a real position!"""
        calls: list[tuple[str, str]] = []
        def handler(request):
            calls.append((request.method, str(request.url.path)))
            return httpx.Response(200, json={"orderId": 999})
        client = AuthenticatedBinanceClient(
            api_key="t", api_secret="t", transport=httpx.MockTransport(handler),
        )
        _open_paper_trade(state, id="seeded-late",
                          entry_order_id="SEEDED",
                          sl_order_id=None, tp_order_id=None,
                          timeout_time=2_000_000)
        mgr = OrderManager(_live_config(), state, client)

        closed = mgr.check_timeouts(now_ms=3_000_000)
        assert len(closed) == 1
        assert state.get_trade("seeded-late").status == "closed"
        assert state.get_trade("seeded-late").exit_reason == "timeout"
        assert calls == [], f"Expected zero Binance calls for paper trade, got: {calls}"

    def test_timeout_catchup_trade_no_binance_call(self, state):
        calls: list[tuple[str, str]] = []
        def handler(request):
            calls.append((request.method, str(request.url.path)))
            return httpx.Response(200, json={"orderId": 999})
        client = AuthenticatedBinanceClient(
            api_key="t", api_secret="t", transport=httpx.MockTransport(handler),
        )
        _open_paper_trade(state, id="cu-late", direction=-1,
                          entry_order_id="CATCHUP-deadbeef",
                          sl_order_id="CATCHUP-feedface",
                          tp_order_id="CATCHUP-12345678",
                          stop_loss_price=62400.0, take_profit_price=55200.0,
                          timeout_time=2_000_000)
        mgr = OrderManager(_live_config(), state, client)
        closed = mgr.check_timeouts(now_ms=3_000_000)
        assert len(closed) == 1
        assert state.get_trade("cu-late").status == "closed"
        assert calls == [], f"Expected zero Binance calls for paper trade, got: {calls}"

    def test_timeout_real_id_still_calls_market_order(self, state):
        """Regression — real numeric-ID timeout still goes through Binance close path."""
        calls: list[tuple[str, str]] = []
        def handler(request):
            calls.append((request.method, str(request.url.path)))
            return httpx.Response(200, json={"orderId": 999})
        client = AuthenticatedBinanceClient(
            api_key="t", api_secret="t", transport=httpx.MockTransport(handler),
        )
        _open_paper_trade(state, id="real-late",
                          entry_order_id="9876543210",
                          sl_order_id="111", tp_order_id="222",
                          timeout_time=2_000_000)
        mgr = OrderManager(_live_config(), state, client)
        mgr.check_timeouts(now_ms=3_000_000)

        # Expect: 2 cancels (DELETE) + 1 market close (POST)
        assert any(c == ("POST", "/fapi/v1/order") for c in calls), (
            f"Expected market-close POST among {calls}"
        )
