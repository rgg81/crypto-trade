from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Protocol

from crypto_trade.models import Kline


class Strategy(Protocol):
    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal: ...


@dataclass(frozen=True)
class Signal:
    direction: int  # 1=buy, -1=sell, 0=do nothing
    weight: int  # 0-100


@dataclass(frozen=True)
class BacktestConfig:
    symbols: tuple[str, ...]
    interval: str
    max_amount_usd: Decimal
    stop_loss_pct: Decimal
    take_profit_pct: Decimal
    timeout_minutes: int
    fee_pct: Decimal = Decimal("0.1")
    data_dir: Path = Path("data")
    start_time: int | None = None  # epoch ms, default=first row
    end_time: int | None = None  # epoch ms, default=last row


@dataclass(frozen=True)
class Order:
    symbol: str
    direction: int
    entry_price: Decimal
    amount_usd: Decimal
    weight_factor: Decimal
    stop_loss_price: Decimal
    take_profit_price: Decimal
    open_time: int
    timeout_time: int


@dataclass(frozen=True)
class TradeResult:
    symbol: str
    direction: int
    entry_price: Decimal
    exit_price: Decimal
    weight_factor: Decimal
    open_time: int
    close_time: int
    exit_reason: str  # "stop_loss" | "take_profit" | "timeout" | "end_of_data"
    pnl_pct: Decimal
    fee_pct: Decimal
    net_pnl_pct: Decimal
    weighted_pnl: Decimal


@dataclass(frozen=True)
class DailyPnL:
    date: str  # "YYYY-MM-DD"
    avg_weighted_pnl: Decimal
    trade_count: int
    trades: tuple[TradeResult, ...]
