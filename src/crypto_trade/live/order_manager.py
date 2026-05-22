"""Order management for live trading.

Translates strategy Signals into exchange orders (or dry-run simulations).
Monitors SL/TP/timeout. Uses exact same price formulas as backtest.py.
"""

from __future__ import annotations

import logging
import time
import uuid

from crypto_trade.backtest import check_order, evaluate_order_with_no_confirm
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


def trade_to_order(
    trade: LiveTrade,
    *,
    enable_no_confirm: bool = False,
    no_confirm_trigger_atr: float = 0.0,
    no_confirm_k_candles: int = 0,
    interval_ms: int = 0,
) -> Order:
    """Convert a LiveTrade to a backtest Order for check_order() reuse.

    iter-v3/132: optionally derive no_confirm_arm_time + no_confirm_threshold_price
    from the trade's open_time and SL distance (Path A — no extra DB columns;
    formula matches backtest.create_order at create-time).

    arm_time = open_time + k_candles * interval_ms
    threshold = entry_price * (1 ± trigger_atr * sl_pct) where sl_pct is
    derived from |entry - stop_loss| / entry (the same SL distance the
    backtest used at create-time).
    """
    no_confirm_arm_time = 0
    no_confirm_threshold_price = 0.0
    if enable_no_confirm and no_confirm_k_candles > 0 and interval_ms > 0:
        # Derive arm_time + threshold_price the same way backtest.create_order
        # does at trade creation. Uses |entry - sl| / entry as the sl_pct.
        sl_pct = abs(trade.entry_price - trade.stop_loss_price) / trade.entry_price
        no_confirm_arm_time = trade.open_time + no_confirm_k_candles * interval_ms
        if trade.direction == 1:
            no_confirm_threshold_price = trade.entry_price * (
                1.0 + no_confirm_trigger_atr * sl_pct
            )
        else:
            no_confirm_threshold_price = trade.entry_price * (
                1.0 - no_confirm_trigger_atr * sl_pct
            )
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
        no_confirm_arm_time=no_confirm_arm_time,
        no_confirm_threshold_price=no_confirm_threshold_price,
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
        *,
        candle_close: float | None = None,
        enable_no_confirm: bool = False,
        no_confirm_trigger_atr: float = 0.0,
        no_confirm_k_candles: int = 0,
        interval_ms: int = 0,
        no_confirm_state: dict | None = None,
        model_name: str = "",
    ) -> str | None:
        """Check if a dry-run trade should exit — same logic as backtest.

        iter-v3/132: optionally threads /116 no_confirm primitive via the
        shared evaluate_order_with_no_confirm helper. When enable_no_confirm
        is True, the caller MUST provide candle_close + interval_ms +
        no_confirm_state. Back-compat: when no_confirm disabled (v1/v2 path),
        falls through to bare check_order.
        """
        if enable_no_confirm:
            assert candle_close is not None, (
                "check_dry_run_exit: candle_close required when enable_no_confirm=True"
            )
            assert interval_ms > 0, (
                "check_dry_run_exit: interval_ms required when enable_no_confirm=True"
            )
            assert no_confirm_state is not None, (
                "check_dry_run_exit: no_confirm_state dict required when enable_no_confirm=True"
            )
            order = trade_to_order(
                trade,
                enable_no_confirm=True,
                no_confirm_trigger_atr=no_confirm_trigger_atr,
                no_confirm_k_candles=no_confirm_k_candles,
                interval_ms=interval_ms,
            )
            # State key for live: (model, symbol, trade.id) because Order objects
            # are rebuilt each call → id() not stable across ticks.
            state_key = (model_name, trade.symbol, trade.id)
            result = evaluate_order_with_no_confirm(
                order,
                candle_open_time,
                candle_open,
                candle_high,
                candle_low,
                candle_close,
                candle_close_time,
                self._config.fee_pct,
                enable_no_confirm=True,
                no_confirm_state=no_confirm_state,
                state_key=state_key,
            )
        else:
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

    def check_no_confirm_exit(
        self,
        trade: LiveTrade,
        candle_high: float,
        candle_low: float,
        candle_close: float,
        candle_close_time: int,
        *,
        no_confirm_trigger_atr: float,
        no_confirm_k_candles: int,
        interval_ms: int,
        no_confirm_state: dict,
        model_name: str,
    ) -> str | None:
        """Real-mode /116 no_confirm exit for non-paper trades.

        iter-v3/132: at each post-entry candle close in live mode, this method:
        1. Computes arm_time and threshold_price from the trade's open_time +
           SL distance (matches trade_to_order formula).
        2. Updates the favorable-excursion state in ``no_confirm_state``
           (mutates in place) — same logic as evaluate_order_with_no_confirm.
        3. If arm_time has elapsed AND favorable excursion never reached the
           threshold:
           a. Cancel any pending SL/TP algo orders (best-effort)
           b. Place MARKET close in opposite direction
           c. Close DB row with exit_reason="no_confirm"
           d. Pop state entry to prevent memory leak

        Critical precedence: callers MUST invoke ``check_exchange_exits()``
        FIRST so SL/TP-already-triggered cases win (Binance algo wins over
        engine-side no_confirm). This method assumes the trade is still open.

        Returns "no_confirm" on close, None otherwise. Paper trades return
        None — the paper path is via ``check_dry_run_exit`` instead.
        """
        if is_paper_trade(trade):
            return None
        if no_confirm_k_candles <= 0 or interval_ms <= 0:
            return None  # disabled

        arm_time = trade.open_time + no_confirm_k_candles * interval_ms
        sl_pct = abs(trade.entry_price - trade.stop_loss_price) / trade.entry_price
        if trade.direction == 1:
            threshold_price = trade.entry_price * (1.0 + no_confirm_trigger_atr * sl_pct)
        else:
            threshold_price = trade.entry_price * (1.0 - no_confirm_trigger_atr * sl_pct)

        state_key = (model_name, trade.symbol, trade.id)
        confirmed = no_confirm_state.get(state_key, False)
        if not confirmed:
            if trade.direction == 1:
                if candle_high >= threshold_price:
                    confirmed = True
            else:
                if candle_low <= threshold_price:
                    confirmed = True
            if confirmed:
                no_confirm_state[state_key] = True

        # Fire no_confirm only when arm_time elapsed AND still unconfirmed
        if confirmed or candle_close_time < arm_time:
            return None

        log.warning(
            "no_confirm exit firing for %s %s (open_time=%d, candle_close_time=%d): "
            "favorable excursion never reached threshold=%.6f",
            trade.symbol,
            trade.id,
            trade.open_time,
            candle_close_time,
            threshold_price,
        )
        # Cancel SL + TP algos (best-effort). Each failure is logged but
        # doesn't abort the close — naked position is worse than orphaned
        # algos (Binance auto-expires them when the position closes).
        if self._auth is not None:
            _try_cancel_algo(self._auth, trade.symbol, trade.sl_order_id)
            _try_cancel_algo(self._auth, trade.symbol, trade.tp_order_id)
            quantity = self._round_qty(trade.symbol, trade.amount_usd / trade.entry_price)
            close_side = _close_side(trade.direction)
            try:
                self._auth.place_market_order(trade.symbol, close_side, quantity)
            except Exception as exc:
                log.error(
                    "no_confirm market-close failed for %s: %s — leaving DB row open; "
                    "next tick will retry",
                    trade.symbol,
                    exc,
                )
                return None
        self._state.close_trade(trade.id, candle_close, candle_close_time, "no_confirm")
        no_confirm_state.pop(state_key, None)

        from crypto_trade import decision_log

        decision_log.log(
            {
                "kind": "no_confirm_trigger",
                "model": model_name,
                "symbol": trade.symbol,
                "trade_id": trade.id,
                "open_time": trade.open_time,
                "candle_close_time": candle_close_time,
                "exit_price": candle_close,
                "threshold_price": threshold_price,
                "arm_time": arm_time,
            }
        )
        return "no_confirm"

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
