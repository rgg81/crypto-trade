"""Order management for live trading.

Translates strategy Signals into exchange orders (or dry-run simulations).
Monitors SL/TP/timeout. Uses exact same price formulas as backtest.py.
"""

from __future__ import annotations

import logging
import time
import uuid

from crypto_trade.backtest import check_order
from crypto_trade.backtest_models import Order, Signal
from crypto_trade.live.auth_client import AuthenticatedBinanceClient
from crypto_trade.live.models import LiveConfig, LiveTrade
from crypto_trade.live.state_store import StateStore

log = logging.getLogger(__name__)


def compute_sl_tp(signal: Signal, entry_price: float, config: LiveConfig) -> tuple[float, float]:
    """Compute stop-loss and take-profit prices — same formula as backtest.py:create_order."""
    sl_pct = (signal.sl_pct if signal.sl_pct is not None else config.stop_loss_pct) / 100.0
    tp_pct = (signal.tp_pct if signal.tp_pct is not None else config.take_profit_pct) / 100.0

    if signal.direction == 1:
        stop_loss_price = entry_price * (1 - sl_pct)
        take_profit_price = entry_price * (1 + tp_pct)
    else:
        stop_loss_price = entry_price * (1 + sl_pct)
        take_profit_price = entry_price * (1 - tp_pct)

    return stop_loss_price, take_profit_price


def _close_side(direction: int) -> str:
    return "SELL" if direction == 1 else "BUY"


def _entry_side(direction: int) -> str:
    return "BUY" if direction == 1 else "SELL"


def _try_cancel(auth: AuthenticatedBinanceClient, symbol: str, order_id: str | None) -> None:
    """Best-effort cancel — logs warning on failure."""
    if not order_id:
        return
    try:
        auth.cancel_order(symbol, order_id)
    except Exception as exc:
        log.warning("Failed to cancel order %s on %s: %s", order_id, symbol, exc)


def trade_to_order(trade: LiveTrade) -> Order:
    """Convert a LiveTrade to a backtest Order for check_order() reuse."""
    return Order(
        symbol=trade.symbol,
        direction=trade.direction,
        entry_price=trade.entry_price,
        amount_usd=trade.amount_usd,
        weight_factor=trade.weight_factor,
        stop_loss_price=trade.stop_loss_price,
        take_profit_price=trade.take_profit_price,
        open_time=trade.open_time,
        timeout_time=trade.timeout_time,
    )


class OrderManager:
    """Manages order lifecycle for live trades (real and dry-run)."""

    def __init__(
        self,
        config: LiveConfig,
        state_store: StateStore,
        auth_client: AuthenticatedBinanceClient | None = None,
        quantity_precision: dict[str, int] | None = None,
    ) -> None:
        self._config = config
        self._state = state_store
        self._auth = auth_client
        self._qty_prec = quantity_precision or {}

    def _round_qty(self, symbol: str, quantity: float) -> float:
        prec = self._qty_prec.get(symbol, 3)
        return round(quantity, prec)

    def open_trade(
        self,
        model_name: str,
        symbol: str,
        signal: Signal,
        entry_price: float,
        candle_close_time: int,
        candle_open_time: int,
        weight_factor: float = 1.0,
    ) -> LiveTrade:
        """Open a new trade from a signal.

        In real mode: places MARKET entry + STOP_MARKET SL + TAKE_PROFIT_MARKET TP.
        In dry-run: records the trade without exchange calls.
        """
        sl_price, tp_price = compute_sl_tp(signal, entry_price, self._config)
        amount_usd = weight_factor * self._config.max_amount_usd
        quantity = self._round_qty(symbol, amount_usd / entry_price)
        timeout_time = candle_close_time + self._config.timeout_minutes * 60 * 1000

        trade = LiveTrade(
            model_name=model_name,
            symbol=symbol,
            direction=signal.direction,
            entry_price=entry_price,
            amount_usd=amount_usd,
            weight_factor=weight_factor,
            stop_loss_price=sl_price,
            take_profit_price=tp_price,
            open_time=candle_close_time,
            timeout_time=timeout_time,
            signal_time=candle_open_time,
        )

        if not self._config.dry_run and self._auth is not None:
            entry_resp = self._auth.place_market_order(
                symbol, _entry_side(signal.direction), quantity
            )
            trade.entry_order_id = str(entry_resp.get("orderId", ""))

            close_side = _close_side(signal.direction)
            sl_resp = self._auth.place_stop_market_order(symbol, close_side, sl_price, quantity)
            trade.sl_order_id = str(sl_resp.get("orderId", ""))

            tp_resp = self._auth.place_take_profit_market_order(
                symbol, close_side, tp_price, quantity
            )
            trade.tp_order_id = str(tp_resp.get("orderId", ""))
        else:
            trade.entry_order_id = f"DRY-{uuid.uuid4().hex[:8]}"
            trade.sl_order_id = f"DRY-{uuid.uuid4().hex[:8]}"
            trade.tp_order_id = f"DRY-{uuid.uuid4().hex[:8]}"

        self._state.upsert_trade(trade)
        return trade

    def check_dry_run_exit(
        self,
        trade: LiveTrade,
        candle_open_time: int,
        candle_open: float,
        candle_high: float,
        candle_low: float,
        candle_close_time: int,
    ) -> str | None:
        """Check if a dry-run trade should exit — same logic as backtest.check_order."""
        order = trade_to_order(trade)
        result = check_order(
            order,
            candle_open_time,
            candle_open,
            candle_high,
            candle_low,
            candle_close_time,
            self._config.fee_pct,
        )
        if result is not None:
            self._state.close_trade(
                trade.id, result.exit_price, result.close_time, result.exit_reason
            )
            return result.exit_reason
        return None

    def check_exchange_exits(self) -> list[LiveTrade]:
        """Check if any SL/TP orders filled on exchange. Returns closed trades."""
        if self._config.dry_run or self._auth is None:
            return []

        closed: list[LiveTrade] = []
        for trade in self._state.get_open_trades():
            if trade.sl_order_id:
                sl_status = self._auth.get_order(trade.symbol, trade.sl_order_id)
                if sl_status.get("status") == "FILLED":
                    fill_price = float(sl_status.get("avgPrice", trade.stop_loss_price))
                    fill_time = int(sl_status.get("updateTime", int(time.time() * 1000)))
                    self._state.close_trade(trade.id, fill_price, fill_time, "stop_loss")
                    _try_cancel(self._auth, trade.symbol, trade.tp_order_id)
                    closed.append(trade)
                    continue

            if trade.tp_order_id:
                tp_status = self._auth.get_order(trade.symbol, trade.tp_order_id)
                if tp_status.get("status") == "FILLED":
                    fill_price = float(tp_status.get("avgPrice", trade.take_profit_price))
                    fill_time = int(tp_status.get("updateTime", int(time.time() * 1000)))
                    self._state.close_trade(trade.id, fill_price, fill_time, "take_profit")
                    _try_cancel(self._auth, trade.symbol, trade.sl_order_id)
                    closed.append(trade)

        return closed

    def check_timeouts(self, now_ms: int) -> list[LiveTrade]:
        """Force-close trades that have exceeded their timeout."""
        closed: list[LiveTrade] = []
        for trade in self._state.get_open_trades():
            if now_ms < trade.timeout_time:
                continue

            if not self._config.dry_run and self._auth is not None:
                _try_cancel(self._auth, trade.symbol, trade.sl_order_id)
                _try_cancel(self._auth, trade.symbol, trade.tp_order_id)
                quantity = self._round_qty(trade.symbol, trade.amount_usd / trade.entry_price)
                try:
                    self._auth.place_market_order(
                        trade.symbol, _close_side(trade.direction), quantity
                    )
                except Exception as exc:
                    log.warning("Failed to market-close %s on timeout: %s", trade.symbol, exc)

            self._state.close_trade(trade.id, trade.entry_price, now_ms, "timeout")
            closed.append(trade)

        return closed
