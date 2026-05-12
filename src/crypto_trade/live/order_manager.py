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
from crypto_trade.live.models import LiveConfig, LiveTrade, is_paper_trade
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


def _try_cancel_algo(auth: AuthenticatedBinanceClient, symbol: str, algo_id: str | None) -> None:
    """Best-effort cancel of an algo (SL/TP) order — logs warning on failure."""
    if not algo_id:
        return
    try:
        auth.cancel_algo_order(symbol, algo_id)
    except Exception as exc:
        log.warning("Failed to cancel algo order %s on %s: %s", algo_id, symbol, exc)


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
        tick_size: dict[str, float] | None = None,
    ) -> None:
        self._config = config
        self._state = state_store
        self._auth = auth_client
        self._qty_prec = quantity_precision or {}
        self._tick_size = tick_size or {}

    def _round_qty(self, symbol: str, quantity: float) -> float:
        prec = self._qty_prec.get(symbol, 3)
        return round(quantity, prec)

    def _round_price(self, symbol: str, price: float) -> float:
        """Round to nearest tickSize (PRICE_FILTER) — Binance enforces this.

        Falls back to 4-decimal rounding if tickSize wasn't loaded (paper mode).
        Uses ``round(price/tick) * tick`` and re-rounds to 8 decimals to dodge
        binary float artifacts (e.g. 0.1 + 0.2 ≠ 0.3).
        """
        tick = self._tick_size.get(symbol)
        if tick is None or tick <= 0:
            return round(price, 4)
        return round(round(price / tick) * tick, 8)

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

        In real mode: places MARKET entry on /fapi/v1/order plus STOP_MARKET SL
        and TAKE_PROFIT_MARKET TP on /fapi/v1/algoOrder (algoType=CONDITIONAL —
        Binance migrated conditional orders off the legacy endpoint on 2025-12-09).
        Atomic: if SL or TP placement fails after the entry fills, the entry is
        rolled back via market close so no naked position is left on-exchange.

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
            try:
                # SL+TP are CONDITIONAL algo orders (Binance moved STOP_MARKET /
                # TAKE_PROFIT_MARKET off /fapi/v1/order on 2025-12-09; the legacy
                # endpoint returns -4120 for these types). Failure here would
                # otherwise leave a naked entry on the exchange.
                sl_resp = self._auth.place_algo_stop_market_order(
                    symbol, close_side, self._round_price(symbol, sl_price), quantity
                )
                trade.sl_order_id = str(sl_resp.get("algoId", ""))

                tp_resp = self._auth.place_algo_take_profit_market_order(
                    symbol, close_side, self._round_price(symbol, tp_price), quantity
                )
                trade.tp_order_id = str(tp_resp.get("algoId", ""))
            except Exception as exc:
                log.error(
                    "SL/TP placement failed after entry %s on %s; "
                    "rolling back entry to avoid naked position: %s",
                    trade.entry_order_id, symbol, exc,
                )
                # Cancel any SL we did manage to place before TP failed.
                _try_cancel_algo(self._auth, symbol, trade.sl_order_id)
                # Close the entry position we just opened.
                try:
                    self._auth.place_market_order(symbol, close_side, quantity)
                except Exception as close_exc:
                    log.critical(
                        "CRITICAL: failed to close naked %s position after SL/TP "
                        "failure (entry order %s): %s — MANUAL INTERVENTION REQUIRED",
                        symbol, trade.entry_order_id, close_exc,
                    )
                raise
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
        """Check if any SL/TP algo orders fired on exchange. Returns closed trades.

        SL/TP are CONDITIONAL algo orders (see auth_client.py); when they
        trigger, ``algoStatus`` flips from ``NEW`` to ``TRIGGERED`` (then
        ``FINISHED``) and ``actualPrice``/``triggerTime`` get populated.

        Paper trades (None / SEEDED / CATCHUP- / DRY-) are skipped — they have
        no Binance counterpart, and querying with sentinel order IDs wastes
        API quota and pollutes logs with 4xx errors.
        """
        if self._config.dry_run or self._auth is None:
            return []

        closed: list[LiveTrade] = []
        for trade in self._state.get_open_trades():
            if is_paper_trade(trade):
                continue

            if trade.sl_order_id:
                sl_status = self._auth.get_algo_order(trade.symbol, trade.sl_order_id)
                if sl_status.get("algoStatus") in ("TRIGGERED", "FINISHED"):
                    fill_price = float(
                        sl_status.get("actualPrice") or trade.stop_loss_price
                    )
                    fill_time = int(
                        sl_status.get("triggerTime")
                        or sl_status.get("updateTime")
                        or int(time.time() * 1000)
                    )
                    self._state.close_trade(trade.id, fill_price, fill_time, "stop_loss")
                    _try_cancel_algo(self._auth, trade.symbol, trade.tp_order_id)
                    closed.append(trade)
                    continue

            if trade.tp_order_id:
                tp_status = self._auth.get_algo_order(trade.symbol, trade.tp_order_id)
                if tp_status.get("algoStatus") in ("TRIGGERED", "FINISHED"):
                    fill_price = float(
                        tp_status.get("actualPrice") or trade.take_profit_price
                    )
                    fill_time = int(
                        tp_status.get("triggerTime")
                        or tp_status.get("updateTime")
                        or int(time.time() * 1000)
                    )
                    self._state.close_trade(trade.id, fill_price, fill_time, "take_profit")
                    _try_cancel_algo(self._auth, trade.symbol, trade.sl_order_id)
                    closed.append(trade)

        return closed

    def check_timeouts(self, now_ms: int) -> list[LiveTrade]:
        """Force-close trades that have exceeded their timeout.

        Real-mode behavior for real numeric-ID trades is unchanged: cancel
        SL+TP, then place a market close in the opposite direction. Paper
        trades (None / SEEDED / CATCHUP- / DRY-) skip the Binance branch —
        place_market_order on a paper trade would OPEN a real position in
        the close direction (no Binance position exists). The DB is still
        closed so timeout accounting (R1/R2) and `_handle_trade_close` fire.
        """
        closed: list[LiveTrade] = []
        for trade in self._state.get_open_trades():
            if now_ms < trade.timeout_time:
                continue

            if (
                not self._config.dry_run
                and self._auth is not None
                and not is_paper_trade(trade)
            ):
                # SL/TP are algo orders; entry was a regular order.
                _try_cancel_algo(self._auth, trade.symbol, trade.sl_order_id)
                _try_cancel_algo(self._auth, trade.symbol, trade.tp_order_id)
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
