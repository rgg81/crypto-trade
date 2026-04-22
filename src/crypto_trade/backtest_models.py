from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import pandas as pd


class Strategy(Protocol):
    def compute_features(self, master: pd.DataFrame) -> None:
        """Pre-compute features from master DF. Store internally."""
        ...

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        """Return signal for one candle. Reads from stored features."""
        ...

    def skip(self) -> None:
        """Advance internal position without computing a signal.

        Filters call this on the inner strategy when the candle is blocked,
        avoiding unnecessary computation while keeping ``_pos`` synchronized.
        """
        ...


@dataclass(frozen=True)
class Signal:
    direction: int  # 1=buy, -1=sell, 0=do nothing
    weight: int  # 0-100
    tp_pct: float | None = None  # optional dynamic take-profit %
    sl_pct: float | None = None  # optional dynamic stop-loss %


@dataclass(frozen=True)
class BacktestConfig:
    symbols: tuple[str, ...]
    interval: str
    max_amount_usd: float
    stop_loss_pct: float
    take_profit_pct: float
    timeout_minutes: int
    fee_pct: float = 0.1
    data_dir: Path = Path("data")
    start_time: int | None = None  # epoch ms, default=first row
    end_time: int | None = None  # epoch ms, default=last row
    cooldown_candles: int = 0  # candles to wait after a trade closes before re-entering
    # Per-symbol volatility targeting (iter 147): scale each trade by
    # target_vol / realized_vol of that symbol's past daily PnL.
    vol_targeting: bool = False
    vt_target_vol: float = 0.5
    vt_lookback_days: int = 30
    vt_min_scale: float = 0.5
    vt_max_scale: float = 2.0
    vt_min_history: int = 5  # minimum past daily returns required for scaling
    # Risk mitigation R1 (iter 173): consecutive-loss cool-down.
    # After K consecutive stop-loss closes for a symbol, suppress new
    # trades on that symbol for C candles. Defaults disable the filter.
    risk_consecutive_sl_limit: int | None = None  # K; None disables
    risk_consecutive_sl_cooldown_candles: int = 0  # C


@dataclass(frozen=True)
class Order:
    symbol: str
    direction: int
    entry_price: float
    amount_usd: float
    weight_factor: float
    stop_loss_price: float
    take_profit_price: float
    open_time: int
    timeout_time: int


@dataclass(frozen=True)
class TradeResult:
    symbol: str
    direction: int
    entry_price: float
    exit_price: float
    weight_factor: float
    open_time: int
    close_time: int
    exit_reason: str  # "stop_loss" | "take_profit" | "timeout" | "end_of_data"
    pnl_pct: float
    fee_pct: float
    net_pnl_pct: float
    weighted_pnl: float


@dataclass(frozen=True)
class DailyPnL:
    date: str  # "YYYY-MM-DD"
    avg_weighted_pnl: float
    trade_count: int
    trades: tuple[TradeResult, ...]


class BacktestResult(list):
    """List of TradeResult with extra backtest metadata.

    Extends ``list`` so all existing callers (len, indexing, iteration,
    equality) keep working.  The ``total_signals`` attribute records how
    many times the strategy fired (direction != 0, weight > 0), which may
    exceed ``len(self)`` when signals are skipped because an order is
    already open for that symbol.
    """

    def __init__(self, trades: list[TradeResult], total_signals: int = 0):
        super().__init__(trades)
        self.total_signals = total_signals
