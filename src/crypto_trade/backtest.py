from __future__ import annotations

import datetime
import tracemalloc
from pathlib import Path

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

    defaults = {"label_tp_pct": 4.0, "label_sl_pct": 2.0, "label_timeout_minutes": 4320}
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


class EarlyStopError(Exception):
    """Raised when fail-fast checkpoint triggers early termination."""

    def __init__(self, reason: str, results: list[TradeResult], total_signals: int):
        self.reason = reason
        self.results = results
        self.total_signals = total_signals
        super().__init__(reason)


def run_backtest(
    config: BacktestConfig,
    strategy: Strategy,
    *,
    profile_memory: bool = False,
    yearly_pnl_check: bool = False,
) -> BacktestResult:
    """Run a backtest over historical kline data using the given strategy.

    If *yearly_pnl_check* is True, checks cumulative PnL at each year
    boundary. Raises EarlyStopError if year-1 PnL is negative.
    """
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

    # Per-symbol daily PnL tracking for vol targeting (iter 147)
    # symbol -> {YYYY-MM-DD -> sum of net_pnl_pct that closed on that day}
    vt_per_sym_daily: dict[str, dict[str, float]] = {}

    # Signal cooldown tracking
    cooldown_until: dict[str, int] = {}  # symbol → earliest open_time for new trade
    candle_duration_ms = 0
    if config.cooldown_candles > 0 and len(master) >= 2:
        # Compute candle duration from first two rows of same symbol
        first_sym = str(sym_arr[0])
        for j in range(1, len(master)):
            if str(sym_arr[j]) == first_sym:
                candle_duration_ms = int(open_time_arr[j] - open_time_arr[0])
                break
        if candle_duration_ms <= 0:
            candle_duration_ms = int(close_time_arr[0] - open_time_arr[0] + 1)

    # Running PnL accumulators for verbose logging
    cum_net_pnl = 0.0
    month_net_pnl = 0.0
    current_month = ""
    day_net_pnl = 0.0
    current_day = ""
    # Yearly fail-fast tracking
    _last_checked_year = 0
    _yearly_pnl: dict[int, float] = {}
    _yearly_trades: dict[int, int] = {}
    _yearly_wins: dict[int, int] = {}

    for i in range(len(master)):
        sym = str(sym_arr[i])
        ot = int(open_time_arr[i])

        # (a) Check open order for this symbol
        if sym in open_orders:
            result = check_order(
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
                # Record per-symbol daily PnL for vol targeting lookback
                if config.vol_targeting:
                    close_date_str = _day_of(result.close_time)
                    sym_daily = vt_per_sym_daily.setdefault(result.symbol, {})
                    sym_daily[close_date_str] = (
                        sym_daily.get(close_date_str, 0.0) + result.net_pnl_pct
                    )
                # Set signal cooldown for this symbol
                if config.cooldown_candles > 0 and candle_duration_ms > 0:
                    cooldown_until[sym] = (
                        result.close_time + config.cooldown_candles * candle_duration_ms
                    )
                # Yearly fail-fast check
                if yearly_pnl_check:
                    yr = datetime.datetime.fromtimestamp(
                        result.close_time / 1000, tz=datetime.UTC
                    ).year
                    _yearly_pnl[yr] = _yearly_pnl.get(yr, 0.0) + result.net_pnl_pct
                    _yearly_trades[yr] = _yearly_trades.get(yr, 0) + 1
                    if result.net_pnl_pct > 0:
                        _yearly_wins[yr] = _yearly_wins.get(yr, 0) + 1
                    # Check at year boundary (when we enter a new year)
                    if yr > _last_checked_year and _last_checked_year > 0:
                        prev = _last_checked_year
                        prev_pnl = _yearly_pnl.get(prev, 0.0)
                        prev_n = _yearly_trades.get(prev, 0)
                        prev_w = _yearly_wins.get(prev, 0)
                        prev_wr = prev_w / prev_n * 100 if prev_n > 0 else 0
                        if prev_n >= 10 and prev_pnl < 0:
                            raise EarlyStopError(
                                f"Year {prev}: PnL={prev_pnl:+.1f}% "
                                f"(WR={prev_wr:.1f}%, {prev_n} trades)",
                                results,
                                total_signals,
                            )
                    _last_checked_year = yr
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
            if sym not in open_orders and ot >= cooldown_until.get(sym, 0):
                vt_scale = 1.0
                if config.vol_targeting:
                    vt_scale = compute_vt_scale(vt_per_sym_daily, sym, ot, config)
                order = create_order(
                    sym,
                    signal,
                    float(close_arr[i]),
                    int(close_time_arr[i]),
                    config,
                    vt_scale=vt_scale,
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
        result = make_result(order, exit_price, exit_time, "end_of_data", config.fee_pct)
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


def build_master(
    symbols: tuple[str, ...] | list[str],
    interval: str,
    data_dir: Path,
    start_time: int | None = None,
    end_time: int | None = None,
) -> pd.DataFrame:
    """Build a single master DataFrame from kline CSVs, sorted by (open_time, symbol).

    Shared by backtest and live modules.
    """
    frames: list[pd.DataFrame] = []
    lengths: list[int] = []
    syms: list[str] = []
    for symbol in symbols:
        path = csv_path(data_dir, symbol, interval)
        ka = load_kline_array(path)
        if len(ka) == 0:
            continue
        if start_time is not None or end_time is not None:
            ka = ka.time_slice(start_time, end_time)
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


def _build_master(config: BacktestConfig) -> pd.DataFrame:
    return build_master(
        config.symbols,
        config.interval,
        config.data_dir,
        config.start_time,
        config.end_time,
    )


def check_order(
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
        return make_result(order, open_price, open_time, "timeout", fee_pct)

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
        return make_result(order, order.stop_loss_price, close_time, "stop_loss", fee_pct)
    return make_result(order, order.take_profit_price, close_time, "take_profit", fee_pct)


def compute_vt_scale(
    per_sym_daily_pnl: dict[str, dict[str, float]],
    symbol: str,
    trade_open_ms: int,
    config: BacktestConfig | object,
) -> float:
    """Compute per-symbol vol-targeting scale for a trade opening at trade_open_ms.

    Looks at the target symbol's past daily aggregate PnL over the last
    ``vt_lookback_days``. Scale = target_vol / realized_vol, clipped to
    [vt_min_scale, vt_max_scale]. Returns 1.0 if history is insufficient
    or realized vol is zero.

    Uses ONLY past data (days_before >= 1) to remain walk-forward valid.
    Accepts any config with vt_* attributes (BacktestConfig or LiveConfig).
    """
    sym_daily = per_sym_daily_pnl.get(symbol, {})
    if not sym_daily:
        return 1.0

    trade_date = datetime.datetime.fromtimestamp(trade_open_ms / 1000, tz=datetime.UTC).date()
    lookback_returns: list[float] = []
    for close_date_str, pnl in sym_daily.items():
        close_date = datetime.date.fromisoformat(close_date_str)
        days_before = (trade_date - close_date).days
        if 1 <= days_before <= config.vt_lookback_days:
            lookback_returns.append(pnl)

    if len(lookback_returns) < config.vt_min_history:
        return 1.0

    n = len(lookback_returns)
    mean_r = sum(lookback_returns) / n
    var = sum((r - mean_r) ** 2 for r in lookback_returns) / (n - 1)
    realized_vol = var**0.5
    # Guard against zero/near-zero vol (numeric noise)
    if realized_vol <= 1e-9:
        return 1.0

    scale = config.vt_target_vol / realized_vol
    return max(config.vt_min_scale, min(config.vt_max_scale, scale))


def create_order(
    symbol: str,
    signal: Signal,
    close_price: float,
    close_time: int,
    config: BacktestConfig,
    vt_scale: float = 1.0,
) -> Order:
    """Create an order from a signal at the current kline's close.

    ``vt_scale`` overrides the signal-derived weight when per-symbol vol
    targeting is enabled.
    """
    entry_price = close_price
    if config.vol_targeting:
        weight_factor = vt_scale
    else:
        weight_factor = signal.weight / 100.0
    amount_usd = weight_factor * config.max_amount_usd

    sl_pct = (signal.sl_pct if signal.sl_pct is not None else config.stop_loss_pct) / 100.0
    tp_pct = (signal.tp_pct if signal.tp_pct is not None else config.take_profit_pct) / 100.0

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


def make_result(
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
