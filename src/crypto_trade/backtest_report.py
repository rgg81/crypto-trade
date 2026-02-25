from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal

from crypto_trade.backtest_models import DailyPnL, TradeResult


def aggregate_daily_pnl(results: list[TradeResult]) -> list[DailyPnL]:
    """Group trade results by close-time date (UTC) and compute daily averages."""
    by_day: dict[str, list[TradeResult]] = defaultdict(list)
    for r in results:
        date_str = datetime.fromtimestamp(r.close_time / 1000, tz=UTC).strftime("%Y-%m-%d")
        by_day[date_str].append(r)

    daily: list[DailyPnL] = []
    for date_str in sorted(by_day):
        trades = by_day[date_str]
        total = sum(t.weighted_pnl for t in trades)
        avg = total / Decimal(len(trades))
        daily.append(
            DailyPnL(
                date=date_str,
                avg_weighted_pnl=avg,
                trade_count=len(trades),
                trades=tuple(trades),
            )
        )
    return daily
