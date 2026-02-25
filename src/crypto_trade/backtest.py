from __future__ import annotations

from decimal import Decimal

from crypto_trade.backtest_models import (
    BacktestConfig,
    Order,
    Signal,
    Strategy,
    TradeResult,
)
from crypto_trade.models import Kline
from crypto_trade.storage import csv_path, read_klines

_100 = Decimal("100")


def run_backtest(config: BacktestConfig, strategy: Strategy) -> list[TradeResult]:
    """Run a backtest over historical kline data using the given strategy."""
    # 1. Load data
    symbol_klines: dict[str, list[Kline]] = {}
    for symbol in config.symbols:
        path = csv_path(config.data_dir, symbol, config.interval)
        klines = read_klines(path)
        if not klines:
            raise ValueError(f"No kline data for {symbol} at {path}")
        symbol_klines[symbol] = klines

    # 2. Align time ranges
    range_start = max(klines[0].open_time for klines in symbol_klines.values())
    range_end = min(klines[-1].open_time for klines in symbol_klines.values())

    aligned: dict[str, list[Kline]] = {}
    for symbol, klines in symbol_klines.items():
        aligned[symbol] = [k for k in klines if range_start <= k.open_time <= range_end]

    num_steps = min(len(klines) for klines in aligned.values())
    if num_steps == 0:
        return []

    # 3. Main loop
    open_orders: dict[str, Order] = {}
    results: list[TradeResult] = []
    history: dict[str, list[Kline]] = {s: [] for s in config.symbols}

    for i in range(num_steps):
        for symbol in config.symbols:
            kline = aligned[symbol][i]
            history[symbol].append(kline)

            # (a) Check open order
            if symbol in open_orders:
                result = _check_order(open_orders[symbol], kline, config.fee_pct)
                if result is not None:
                    results.append(result)
                    del open_orders[symbol]

            # (b) Generate signal
            if symbol not in open_orders:
                signal = strategy.on_kline(symbol, kline, history[symbol])
                if signal.direction != 0 and signal.weight > 0:
                    order = _create_order(symbol, signal, kline, config)
                    open_orders[symbol] = order

    # 4. End-of-data: force-close remaining orders
    for symbol, order in open_orders.items():
        last_kline = aligned[symbol][-1]
        exit_price = Decimal(last_kline.close)
        result = _make_result(
            order, exit_price, last_kline.close_time, "end_of_data", config.fee_pct
        )
        results.append(result)

    # 5. Sort by close_time
    results.sort(key=lambda r: r.close_time)
    return results


def _check_order(order: Order, kline: Kline, fee_pct: Decimal) -> TradeResult | None:
    """Check if an order should be closed on this kline."""
    # 1. Timeout check
    if kline.open_time >= order.timeout_time:
        exit_price = Decimal(kline.open)
        return _make_result(order, exit_price, kline.open_time, "timeout", fee_pct)

    low = Decimal(kline.low)
    high = Decimal(kline.high)
    open_price = Decimal(kline.open)

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
            # Long: if open <= SL, SL wins; if open >= TP, TP wins; else SL (worst case)
            if open_price >= order.take_profit_price:
                sl_hit = False  # TP wins
            else:
                tp_hit = False  # SL wins (includes ambiguous case)
        else:
            # Short: if open >= SL, SL wins; if open <= TP, TP wins; else SL (worst case)
            if open_price <= order.take_profit_price:
                sl_hit = False  # TP wins
            else:
                tp_hit = False  # SL wins (includes ambiguous case)

    if sl_hit:
        return _make_result(order, order.stop_loss_price, kline.close_time, "stop_loss", fee_pct)
    return _make_result(order, order.take_profit_price, kline.close_time, "take_profit", fee_pct)


def _create_order(symbol: str, signal: Signal, kline: Kline, config: BacktestConfig) -> Order:
    """Create an order from a signal at the current kline's close."""
    entry_price = Decimal(kline.close)
    weight_factor = Decimal(signal.weight) / _100
    amount_usd = weight_factor * config.max_amount_usd

    sl_pct = config.stop_loss_pct / _100
    tp_pct = config.take_profit_pct / _100

    if signal.direction == 1:  # Long
        stop_loss_price = entry_price * (1 - sl_pct)
        take_profit_price = entry_price * (1 + tp_pct)
    else:  # Short
        stop_loss_price = entry_price * (1 + sl_pct)
        take_profit_price = entry_price * (1 - tp_pct)

    open_time = kline.close_time
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
    exit_price: Decimal,
    close_time: int,
    exit_reason: str,
    fee_pct: Decimal,
) -> TradeResult:
    """Build a TradeResult from a closed order."""
    if order.direction == 1:  # Long
        pnl_pct = ((exit_price - order.entry_price) / order.entry_price) * _100
    else:  # Short
        pnl_pct = ((order.entry_price - exit_price) / order.entry_price) * _100

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
