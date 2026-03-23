from __future__ import annotations

import datetime
import tracemalloc

import numpy as np
import pandas as pd

from crypto_trade.backtest_models import (
    BacktestConfig,
    BacktestResult,
    Order,
    Signal,
    Strategy,
    TradeResult,
)
from crypto_trade.kline_array import load_kline_array
from crypto_trade.storage import csv_path


def _sync_label_params(strategy: Strategy, config: BacktestConfig) -> None:
    """Push backtest config TP/SL/timeout into ML strategies that use them for labeling.

    Walks through filter wrappers (inner chains) to find the leaf strategy.
    Only overrides attributes that still hold their default values, so explicit
    ``--params label_tp_pct=X`` from the CLI takes precedence.
    """
    # Unwrap filter chain to find the innermost strategy
    target = strategy
    while hasattr(target, "inner") and target.inner is not None:
        target = target.inner

    defaults = {"label_tp_pct": 3.0, "label_sl_pct": 2.0, "label_timeout_minutes": 120}
    mapping = {
        "label_tp_pct": config.take_profit_pct,
        "label_sl_pct": config.stop_loss_pct,
        "label_timeout_minutes": config.timeout_minutes,
    }
    for attr, config_val in mapping.items():
        if hasattr(target, attr) and getattr(target, attr) == defaults[attr]:
            setattr(target, attr, config_val)


def _mem_report(label: str) -> None:
    current, peak = tracemalloc.get_traced_memory()
    print(f"[memory] {label}: current={current / 1e9:.2f} GB, peak={peak / 1e9:.2f} GB")


def _detect_verbose(strategy: Strategy) -> int:
    """Walk the strategy/filter chain to find a ``verbose`` attribute."""
    target = strategy
    while True:
        if hasattr(target, "verbose"):
            return int(target.verbose)
        if hasattr(target, "inner") and target.inner is not None:
            target = target.inner
        else:
            return 0


def _flush_predict_log(strategy: Strategy) -> None:
    """Walk chain, print and clear any stored ``_last_predict_log``."""
    target = strategy
    while True:
        log = getattr(target, "_last_predict_log", None)
        if log is not None:
            print(log)
            target._last_predict_log = None
            return
        if hasattr(target, "inner") and target.inner is not None:
            target = target.inner
        else:
            return


def _fmt_ms(ms: int) -> str:
    """Format epoch milliseconds as 'YYYY-MM-DD HH:MM'."""
    return datetime.datetime.fromtimestamp(ms / 1000, tz=datetime.UTC).strftime("%Y-%m-%d %H:%M")


def _month_of(ms: int) -> str:
    """Return 'YYYY-MM' for an epoch-ms timestamp."""
    return datetime.datetime.fromtimestamp(ms / 1000, tz=datetime.UTC).strftime("%Y-%m")


def _day_of(ms: int) -> str:
    """Return 'YYYY-MM-DD' for an epoch-ms timestamp."""
    return datetime.datetime.fromtimestamp(ms / 1000, tz=datetime.UTC).strftime("%Y-%m-%d")


def _log_trade_open(order: Order) -> None:
    """Print trade open event."""
    direction = "LONG" if order.direction == 1 else "SHORT"
    print(
        f"[trade:open] {_fmt_ms(order.open_time)} {order.symbol} {direction} "
        f"@ {order.entry_price:.2f} | "
        f"SL={order.stop_loss_price:.2f} TP={order.take_profit_price:.2f} | "
        f"timeout={_fmt_ms(order.timeout_time)}"
    )


def _log_trade_close(
    result: TradeResult,
    cum_net_pnl: float,
    month_net_pnl: float,
    month_label: str,
    day_net_pnl: float,
    day_label: str,
) -> None:
    """Print trade close event with cumulative PnL."""
    direction = "LONG" if result.direction == 1 else "SHORT"
    sign = "+" if result.pnl_pct >= 0 else ""
    net_sign = "+" if result.net_pnl_pct >= 0 else ""
    cum_sign = "+" if cum_net_pnl >= 0 else ""
    mo_sign = "+" if month_net_pnl >= 0 else ""
    day_sign = "+" if day_net_pnl >= 0 else ""
    print(
        f"[trade:close] {_fmt_ms(result.close_time)} {result.symbol} {direction} "
        f"→ {result.exit_reason} @ {result.exit_price:.2f} | "
        f"PnL={sign}{result.pnl_pct:.2f}% (net {net_sign}{result.net_pnl_pct:.2f}%) | "
        f"cum={cum_sign}{cum_net_pnl:.2f}% {month_label}={mo_sign}{month_net_pnl:.2f}% "
        f"{day_label}={day_sign}{day_net_pnl:.2f}%"
    )


def run_backtest(
    config: BacktestConfig,
    strategy: Strategy,
    *,
    profile_memory: bool = False,
) -> BacktestResult:
    """Run a backtest over historical kline data using the given strategy."""
    if profile_memory:
        tracemalloc.start()

    # Sync labeling params from backtest config into ML strategies
    _sync_label_params(strategy, config)

    verbose = _detect_verbose(strategy)

    master = _build_master(config)
    if master.empty:
        if profile_memory:
            tracemalloc.stop()
        return BacktestResult([], 0)

    if profile_memory:
        _mem_report(f"after _build_master ({len(master):,} rows)")

    strategy.compute_features(master)

    if profile_memory:
        _mem_report("after compute_features")

    # Extract numpy arrays for fast iteration
    sym_arr = master["symbol"].to_numpy(dtype=str)
    open_time_arr = master["open_time"].values
    close_time_arr = master["close_time"].values
    open_arr = master["open"].values
    high_arr = master["high"].values
    low_arr = master["low"].values
    close_arr = master["close"].values

    open_orders: dict[str, Order] = {}
    results: list[TradeResult] = []
    total_signals = 0

    # Running PnL accumulators for verbose logging
    cum_net_pnl = 0.0
    month_net_pnl = 0.0
    current_month = ""
    day_net_pnl = 0.0
    current_day = ""

    for i in range(len(master)):
        sym = str(sym_arr[i])
        ot = int(open_time_arr[i])

        # (a) Check open order for this symbol
        if sym in open_orders:
            result = _check_order(
                open_orders[sym],
                ot,
                float(open_arr[i]),
                float(high_arr[i]),
                float(low_arr[i]),
                int(close_time_arr[i]),
                config.fee_pct,
            )
            if result is not None:
                results.append(result)
                del open_orders[sym]
                if verbose > 0:
                    month_label = _month_of(result.close_time)
                    if month_label != current_month:
                        month_net_pnl = 0.0
                        current_month = month_label
                    day_label = _day_of(result.close_time)
                    if day_label != current_day:
                        day_net_pnl = 0.0
                        current_day = day_label
                    cum_net_pnl += result.net_pnl_pct
                    month_net_pnl += result.net_pnl_pct
                    day_net_pnl += result.net_pnl_pct
                    _log_trade_close(
                        result,
                        cum_net_pnl,
                        month_net_pnl,
                        current_month,
                        day_net_pnl,
                        current_day,
                    )

        # (b) Ask strategy for signal
        signal = strategy.get_signal(sym, ot)
        if signal.direction != 0 and signal.weight > 0:
            total_signals += 1
            if sym not in open_orders:
                order = _create_order(
                    sym,
                    signal,
                    float(close_arr[i]),
                    int(close_time_arr[i]),
                    config,
                )
                open_orders[sym] = order
                if verbose > 0:
                    _flush_predict_log(strategy)
                    _log_trade_open(order)

    # End-of-data: force-close remaining orders
    last_per_sym: dict[str, int] = {}
    for i in range(len(master) - 1, -1, -1):
        s = str(sym_arr[i])
        if s not in last_per_sym:
            last_per_sym[s] = i
    for sym, order in open_orders.items():
        idx = last_per_sym[sym]
        exit_price = float(close_arr[idx])
        exit_time = int(close_time_arr[idx])
        result = _make_result(order, exit_price, exit_time, "end_of_data", config.fee_pct)
        results.append(result)
        if verbose > 0:
            month_label = _month_of(result.close_time)
            if month_label != current_month:
                month_net_pnl = 0.0
                current_month = month_label
            day_label = _day_of(result.close_time)
            if day_label != current_day:
                day_net_pnl = 0.0
                current_day = day_label
            cum_net_pnl += result.net_pnl_pct
            month_net_pnl += result.net_pnl_pct
            day_net_pnl += result.net_pnl_pct
            _log_trade_close(
                result,
                cum_net_pnl,
                month_net_pnl,
                current_month,
                day_net_pnl,
                current_day,
            )

    results.sort(key=lambda r: r.close_time)

    if profile_memory:
        _mem_report("after backtest loop")
        tracemalloc.stop()

    return BacktestResult(results, total_signals)


def _build_master(config: BacktestConfig) -> pd.DataFrame:
    """Build a single master DataFrame from all symbols, sorted by (open_time, symbol)."""
    frames: list[pd.DataFrame] = []
    lengths: list[int] = []
    syms: list[str] = []
    for symbol in config.symbols:
        path = csv_path(config.data_dir, symbol, config.interval)
        ka = load_kline_array(path)
        if len(ka) == 0:
            continue
        ka = ka.time_slice(config.start_time, config.end_time)
        if len(ka) == 0:
            continue
        frames.append(ka.df.reset_index(drop=True))
        lengths.append(len(ka))
        syms.append(symbol)
    if not frames:
        return pd.DataFrame()
    master = pd.concat(frames, ignore_index=True)
    master["symbol"] = pd.Categorical(np.repeat(syms, lengths))
    master.sort_values(["open_time", "symbol"], kind="mergesort", ignore_index=True, inplace=True)
    return master


def _check_order(
    order: Order,
    open_time: int,
    open_price: float,
    high: float,
    low: float,
    close_time: int,
    fee_pct: float,
) -> TradeResult | None:
    """Check if an order should be closed on this kline."""
    # 1. Timeout check
    if open_time >= order.timeout_time:
        return _make_result(order, open_price, open_time, "timeout", fee_pct)

    # 2. SL/TP check
    if order.direction == 1:  # Long
        sl_hit = low <= order.stop_loss_price
        tp_hit = high >= order.take_profit_price
    else:  # Short
        sl_hit = high >= order.stop_loss_price
        tp_hit = low <= order.take_profit_price

    if not sl_hit and not tp_hit:
        return None

    # 3. Both hit same candle
    if sl_hit and tp_hit:
        if order.direction == 1:
            if open_price >= order.take_profit_price:
                sl_hit = False  # TP wins
            else:
                tp_hit = False  # SL wins (includes ambiguous case)
        else:
            if open_price <= order.take_profit_price:
                sl_hit = False  # TP wins
            else:
                tp_hit = False  # SL wins (includes ambiguous case)

    if sl_hit:
        return _make_result(order, order.stop_loss_price, close_time, "stop_loss", fee_pct)
    return _make_result(order, order.take_profit_price, close_time, "take_profit", fee_pct)


def _create_order(
    symbol: str,
    signal: Signal,
    close_price: float,
    close_time: int,
    config: BacktestConfig,
) -> Order:
    """Create an order from a signal at the current kline's close."""
    entry_price = close_price
    weight_factor = signal.weight / 100.0
    amount_usd = weight_factor * config.max_amount_usd

    sl_pct = config.stop_loss_pct / 100.0
    tp_pct = config.take_profit_pct / 100.0

    if signal.direction == 1:  # Long
        stop_loss_price = entry_price * (1 - sl_pct)
        take_profit_price = entry_price * (1 + tp_pct)
    else:  # Short
        stop_loss_price = entry_price * (1 + sl_pct)
        take_profit_price = entry_price * (1 - tp_pct)

    open_time = close_time
    timeout_time = open_time + config.timeout_minutes * 60 * 1000

    return Order(
        symbol=symbol,
        direction=signal.direction,
        entry_price=entry_price,
        amount_usd=amount_usd,
        weight_factor=weight_factor,
        stop_loss_price=stop_loss_price,
        take_profit_price=take_profit_price,
        open_time=open_time,
        timeout_time=timeout_time,
    )


def _make_result(
    order: Order,
    exit_price: float,
    close_time: int,
    exit_reason: str,
    fee_pct: float,
) -> TradeResult:
    """Build a TradeResult from a closed order."""
    if order.direction == 1:  # Long
        pnl_pct = ((exit_price - order.entry_price) / order.entry_price) * 100.0
    else:  # Short
        pnl_pct = ((order.entry_price - exit_price) / order.entry_price) * 100.0

    net_pnl_pct = pnl_pct - fee_pct
    weighted_pnl = net_pnl_pct * order.weight_factor

    return TradeResult(
        symbol=order.symbol,
        direction=order.direction,
        entry_price=order.entry_price,
        exit_price=exit_price,
        weight_factor=order.weight_factor,
        open_time=order.open_time,
        close_time=close_time,
        exit_reason=exit_reason,
        pnl_pct=pnl_pct,
        fee_pct=fee_pct,
        net_pnl_pct=net_pnl_pct,
        weighted_pnl=weighted_pnl,
    )
