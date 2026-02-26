from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from crypto_trade.backtest_models import DailyPnL, TradeResult

_ZERO = Decimal(0)


@dataclass(frozen=True)
class BacktestSummary:
    total_trades: int
    wins: int
    losses: int
    win_rate_pct: Decimal
    avg_pnl_pct: Decimal
    total_net_pnl_pct: Decimal
    max_drawdown_pct: Decimal
    profit_factor: Decimal
    exit_reasons: dict[str, int]
    best_trade_pct: Decimal
    worst_trade_pct: Decimal


def summarize(results: list[TradeResult]) -> BacktestSummary | None:
    """Compute aggregate statistics from a list of trade results."""
    if not results:
        return None

    total = len(results)
    wins = sum(1 for r in results if r.net_pnl_pct > 0)
    losses = total - wins
    win_rate = Decimal(wins) / Decimal(total) * Decimal(100)

    net_pnls = [r.net_pnl_pct for r in results]
    avg_pnl = sum(net_pnls) / Decimal(total)
    total_net = sum(net_pnls)

    best = max(net_pnls)
    worst = min(net_pnls)

    # Max drawdown: largest peak-to-trough decline in cumulative PnL
    cumulative = _ZERO
    peak = _ZERO
    max_dd = _ZERO
    for pnl in net_pnls:
        cumulative += pnl
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd

    # Profit factor: sum(gains) / sum(losses)
    gross_gains = sum(p for p in net_pnls if p > 0)
    gross_losses = sum(-p for p in net_pnls if p < 0)
    profit_factor = gross_gains / gross_losses if gross_losses > 0 else Decimal("Infinity")

    exit_reasons: dict[str, int] = {}
    for r in results:
        exit_reasons[r.exit_reason] = exit_reasons.get(r.exit_reason, 0) + 1

    return BacktestSummary(
        total_trades=total,
        wins=wins,
        losses=losses,
        win_rate_pct=win_rate,
        avg_pnl_pct=avg_pnl,
        total_net_pnl_pct=total_net,
        max_drawdown_pct=max_dd,
        profit_factor=profit_factor,
        exit_reasons=exit_reasons,
        best_trade_pct=best,
        worst_trade_pct=worst,
    )


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
