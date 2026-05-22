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
        """Regression — real numeric-ID trades still hit Binance via the algo endpoint."""
        called: list[str] = []

        def handler(request):
            called.append(str(request.url.path))
            return httpx.Response(200, json={"algoStatus": "NEW"})

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
        # SL/TP are algo orders — must hit /fapi/v1/algoOrder, NOT /fapi/v1/order.
        assert any("/fapi/v1/algoOrder" in p for p in called), called

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

        # Expect: 2 algo cancels (DELETE /fapi/v1/algoOrder) + 1 market close (POST)
        assert any(c == ("POST", "/fapi/v1/order") for c in calls), (
            f"Expected market-close POST among {calls}"
        )
        # SL/TP cancels must hit the algo endpoint, not the legacy order endpoint.
        assert any(c == ("DELETE", "/fapi/v1/algoOrder") for c in calls), (
            f"Expected algo cancel among {calls}"
        )


class TestOpenTradeAtomicity:
    """If SL or TP placement fails after entry fills, the entry must be rolled back
    so we never leave a naked position on the exchange."""

    def _capture_with_failures(self, fail_on_paths: set[str]):
        """Mock transport that fails any POST whose path matches `fail_on_paths`."""
        calls: list[tuple[str, str, str]] = []

        def handler(request):
            params = str(request.url.params)
            calls.append((request.method, request.url.path, params))
            if request.method == "POST" and request.url.path in fail_on_paths:
                return httpx.Response(
                    400,
                    json={
                        "code": -4120,
                        "msg": "Order type not supported for this endpoint.",
                    },
                )
            # Default: orderId for /fapi/v1/order, algoId for /fapi/v1/algoOrder
            if "/algoOrder" in request.url.path:
                return httpx.Response(200, json={"algoId": 555, "algoStatus": "NEW"})
            return httpx.Response(200, json={"orderId": 12345, "status": "NEW"})

        return httpx.MockTransport(handler), calls

    def _live_mgr(self, state, transport):
        client = AuthenticatedBinanceClient(
            api_key="t", api_secret="t", transport=transport,
        )
        return OrderManager(
            _live_config(), state, client,
            quantity_precision={"BTCUSDT": 4},
            tick_size={"BTCUSDT": 0.1},
        )

    def test_sl_placement_failure_rolls_back_entry(self, state):
        """Entry succeeds; SL fails → entry must be market-closed and exception re-raised."""
        # Fail every POST to /fapi/v1/algoOrder so SL placement raises.
        transport, calls = self._capture_with_failures({"/fapi/v1/algoOrder"})
        mgr = self._live_mgr(state, transport)

        signal = Signal(direction=1, weight=100, tp_pct=8.0, sl_pct=4.0)
        with pytest.raises(httpx.HTTPStatusError):
            mgr.open_trade(
                model_name="A", symbol="BTCUSDT", signal=signal,
                entry_price=80000.0, candle_close_time=2_000_000,
                candle_open_time=1_000_000, weight_factor=1.0,
            )

        # Sequence must be: entry POST /fapi/v1/order → SL POST /fapi/v1/algoOrder (fails)
        # → close POST /fapi/v1/order with side=SELL.
        order_posts = [c for c in calls if c[0] == "POST" and c[1] == "/fapi/v1/order"]
        assert len(order_posts) == 2, f"Expected entry + close on /fapi/v1/order, got {order_posts}"
        # The second POST should be the rollback close — opposite side.
        close_params = order_posts[1][2]
        assert "side=SELL" in close_params, (
            f"Rollback close should be SELL (closing the long entry); params={close_params}"
        )
        # And no DB record was persisted because the exception bubbled before upsert.
        assert state.get_open_trades() == []

    def test_tp_placement_failure_rolls_back_entry_and_cancels_sl(self, state):
        """Entry + SL succeed; TP fails → SL must be cancelled AND entry market-closed."""
        # Use a stateful handler: succeed for first algoOrder POST (SL), fail for second (TP).
        algo_post_count = [0]

        def handler(request):
            if request.url.path == "/fapi/v1/algoOrder" and request.method == "POST":
                algo_post_count[0] += 1
                if algo_post_count[0] == 1:
                    return httpx.Response(200, json={"algoId": 100, "algoStatus": "NEW"})
                # Second algoOrder POST = TP — fail it.
                return httpx.Response(
                    400, json={"code": -4131, "msg": "PERCENT_PRICE filter violation"},
                )
            if "/algoOrder" in request.url.path and request.method == "DELETE":
                return httpx.Response(200, json={"algoId": 100, "code": "200", "msg": "success"})
            return httpx.Response(200, json={"orderId": 12345, "status": "NEW"})

        # Track all calls separately for assertion.
        all_calls: list[tuple[str, str]] = []

        def trace_handler(request):
            all_calls.append((request.method, request.url.path))
            return handler(request)

        mgr = self._live_mgr(state, httpx.MockTransport(trace_handler))

        signal = Signal(direction=1, weight=100, tp_pct=8.0, sl_pct=4.0)
        with pytest.raises(httpx.HTTPStatusError):
            mgr.open_trade(
                model_name="A", symbol="BTCUSDT", signal=signal,
                entry_price=80000.0, candle_close_time=2_000_000,
                candle_open_time=1_000_000, weight_factor=1.0,
            )

        # Must have: entry POST → SL POST → TP POST (fails) → SL cancel DELETE → close POST.
        kinds = [(m, p) for m, p in all_calls]
        assert ("POST", "/fapi/v1/order") in kinds  # entry + close
        assert kinds.count(("POST", "/fapi/v1/order")) == 2, f"entry+close, got {kinds}"
        assert kinds.count(("POST", "/fapi/v1/algoOrder")) == 2, (
            f"SL + TP attempts, got {kinds}"
        )
        assert ("DELETE", "/fapi/v1/algoOrder") in kinds, (
            f"SL must be cancelled when TP fails; got {kinds}"
        )
        assert state.get_open_trades() == []


class TestAlgoSLTPFillDetection:
    """check_exchange_exits must detect SL/TP fills via algoStatus, not legacy `status`."""

    def test_sl_fill_detected_from_algo_status_triggered(self, state):
        """When the SL algo flips to TRIGGERED, the trade closes as stop_loss."""
        def handler(request):
            # Match SL or TP query
            params = dict(p.split("=") for p in str(request.url.params).split("&") if "=" in p)
            algo_id = params.get("algoId", "")
            if request.method == "GET" and request.url.path == "/fapi/v1/algoOrder":
                if algo_id == "111":  # SL
                    return httpx.Response(200, json={
                        "algoId": 111, "algoStatus": "TRIGGERED",
                        "actualPrice": "57555.5", "triggerTime": 2_500_000,
                    })
                if algo_id == "222":  # TP — still open
                    return httpx.Response(200, json={
                        "algoId": 222, "algoStatus": "NEW",
                        "actualPrice": "0", "triggerTime": 0,
                    })
            if request.method == "DELETE" and request.url.path == "/fapi/v1/algoOrder":
                return httpx.Response(200, json={"code": "200", "msg": "success"})
            return httpx.Response(200, json={})

        client = AuthenticatedBinanceClient(
            api_key="t", api_secret="t", transport=httpx.MockTransport(handler),
        )
        # Numeric (real) SL/TP IDs so is_paper_trade is False.
        trade = LiveTrade(
            id="t-sl", model_name="A", symbol="BTCUSDT", direction=1,
            entry_price=60000.0, amount_usd=1000.0, weight_factor=1.0,
            stop_loss_price=57600.0, take_profit_price=64800.0,
            open_time=1_000_000, timeout_time=10**13, signal_time=999_000,
            entry_order_id="9999", sl_order_id="111", tp_order_id="222",
        )
        state.upsert_trade(trade)
        mgr = OrderManager(_live_config(), state, client)
        closed = mgr.check_exchange_exits()

        assert len(closed) == 1
        stored = state.get_trade("t-sl")
        assert stored.status == "closed"
        assert stored.exit_reason == "stop_loss"
        assert stored.exit_price == pytest.approx(57555.5)
        assert stored.exit_time == 2_500_000

    def test_tp_fill_detected_from_algo_status_finished(self, state):
        """algoStatus=FINISHED is also a fill (Binance flips TRIGGERED→FINISHED)."""
        def handler(request):
            params = dict(p.split("=") for p in str(request.url.params).split("&") if "=" in p)
            algo_id = params.get("algoId", "")
            if request.method == "GET" and request.url.path == "/fapi/v1/algoOrder":
                if algo_id == "333":  # SL — still open
                    return httpx.Response(200, json={
                        "algoId": 333, "algoStatus": "NEW",
                        "actualPrice": "0", "triggerTime": 0,
                    })
                if algo_id == "444":  # TP — finished
                    return httpx.Response(200, json={
                        "algoId": 444, "algoStatus": "FINISHED",
                        "actualPrice": "21.55", "triggerTime": 2_700_000,
                    })
            if request.method == "DELETE" and request.url.path == "/fapi/v1/algoOrder":
                return httpx.Response(200, json={"code": "200", "msg": "success"})
            return httpx.Response(200, json={})

        client = AuthenticatedBinanceClient(
            api_key="t", api_secret="t", transport=httpx.MockTransport(handler),
        )
        trade = LiveTrade(
            id="t-tp", model_name="C", symbol="LINKUSDT", direction=1,
            entry_price=20.0, amount_usd=1000.0, weight_factor=1.0,
            stop_loss_price=19.2, take_profit_price=21.6,
            open_time=1_000_000, timeout_time=10**13, signal_time=999_000,
            entry_order_id="8888", sl_order_id="333", tp_order_id="444",
        )
        state.upsert_trade(trade)
        mgr = OrderManager(_live_config(), state, client)
        closed = mgr.check_exchange_exits()

        assert len(closed) == 1
        stored = state.get_trade("t-tp")
        assert stored.exit_reason == "take_profit"
        assert stored.exit_price == pytest.approx(21.55)
