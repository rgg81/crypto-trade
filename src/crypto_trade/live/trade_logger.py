"""CSV trade logger for live trades.

Writes closed trades in a format compatible with backtest TradeResult,
enabling post-hoc comparison between live and backtest results.
"""

from __future__ import annotations

import csv
from pathlib import Path

from crypto_trade.backtest import make_result
from crypto_trade.backtest_models import Order, TradeResult
from crypto_trade.live.models import LiveTrade

_CSV_HEADER = [
    "model_name",
    "symbol",
    "direction",
    "entry_price",
    "exit_price",
    "weight_factor",
    "open_time",
    "close_time",
    "exit_reason",
    "pnl_pct",
    "fee_pct",
    "net_pnl_pct",
    "weighted_pnl",
    "signal_time",
    "dry_run",
]


def to_trade_result(trade: LiveTrade, fee_pct: float) -> TradeResult | None:
    """Convert a closed LiveTrade to a backtest TradeResult for reporting."""
    if trade.exit_price is None or trade.exit_time is None or trade.exit_reason is None:
        return None

    order = Order(
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
    return make_result(order, trade.exit_price, trade.exit_time, trade.exit_reason, fee_pct)


def _dir_label(direction: int) -> str:
    return "LONG" if direction == 1 else "SHORT"


class TradeLogger:
    """Appends closed trades to a CSV file for post-hoc analysis."""

    def __init__(self, log_path: Path, fee_pct: float, dry_run: bool) -> None:
        self.path = log_path
        self._fee_pct = fee_pct
        self._dry_run = dry_run
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with open(self.path, "w", newline="") as f:
                csv.writer(f).writerow(_CSV_HEADER)

    def log_open(self, trade: LiveTrade) -> None:
        print(
            f"[{trade.model_name}:{trade.symbol}] OPEN {_dir_label(trade.direction)} "
            f"@ {trade.entry_price:.2f} | "
            f"SL={trade.stop_loss_price:.2f} TP={trade.take_profit_price:.2f} | "
            f"weight={trade.weight_factor:.2f}"
        )

    def log_close(self, trade: LiveTrade) -> None:
        result = to_trade_result(trade, self._fee_pct)
        if result is None:
            return

        sign = "+" if result.net_pnl_pct >= 0 else ""
        print(
            f"[{trade.model_name}:{trade.symbol}] CLOSE {_dir_label(trade.direction)} "
            f"→ {result.exit_reason} @ {result.exit_price:.2f} | "
            f"PnL={sign}{result.net_pnl_pct:.2f}%"
        )

        with open(self.path, "a", newline="") as f:
            csv.writer(f).writerow(
                [
                    trade.model_name,
                    trade.symbol,
                    trade.direction,
                    trade.entry_price,
                    trade.exit_price,
                    trade.weight_factor,
                    trade.open_time,
                    trade.exit_time,
                    trade.exit_reason,
                    f"{result.pnl_pct:.6f}",
                    f"{self._fee_pct:.4f}",
                    f"{result.net_pnl_pct:.6f}",
                    f"{result.weighted_pnl:.6f}",
                    trade.signal_time,
                    self._dry_run,
                ]
            )
