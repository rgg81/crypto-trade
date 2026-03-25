"""Iteration report generator — splits backtest results at OOS cutoff.

Produces:
    reports/iteration_NNN/in_sample/    (trades with open_time < OOS_CUTOFF_MS)
    reports/iteration_NNN/out_of_sample/ (trades with open_time >= OOS_CUTOFF_MS)
    reports/iteration_NNN/comparison.csv (side-by-side metrics + OOS/IS ratios)
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.backtest_models import TradeResult
from crypto_trade.backtest_report import (
    generate_html_report,
    summarize,
    to_daily_returns_series,
)
from crypto_trade.config import OOS_CUTOFF_MS


@dataclass(frozen=True)
class SplitMetrics:
    """Key metrics for one half (IS or OOS) of the split."""

    sharpe: float
    sortino: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    calmar_ratio: float
    total_net_pnl: float


def _compute_metrics(trades: list[TradeResult]) -> SplitMetrics | None:
    """Compute Sharpe, Sortino, max drawdown, etc. from trade list."""
    if not trades:
        return None

    summary = summarize(trades)
    if summary is None:
        return None

    returns = to_daily_returns_series(trades)
    if returns.empty or returns.std() == 0:
        sharpe = 0.0
        sortino = 0.0
    else:
        mean_r = returns.mean()
        std_r = returns.std()
        sharpe = float(mean_r / std_r * math.sqrt(365)) if std_r > 0 else 0.0
        downside = returns[returns < 0].std()
        sortino = float(mean_r / downside * math.sqrt(365)) if downside > 0 else 0.0

    calmar = (
        abs(summary.total_net_pnl_pct / summary.max_drawdown_pct)
        if summary.max_drawdown_pct > 0
        else 0.0
    )

    return SplitMetrics(
        sharpe=sharpe,
        sortino=sortino,
        max_drawdown=summary.max_drawdown_pct,
        win_rate=summary.win_rate_pct,
        profit_factor=summary.profit_factor,
        total_trades=summary.total_trades,
        calmar_ratio=calmar,
        total_net_pnl=summary.total_net_pnl_pct,
    )


def _write_trades_csv(trades: list[TradeResult], path: Path) -> None:
    """Write trade results to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
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
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for t in trades:
            row = {
                "symbol": t.symbol,
                "direction": t.direction,
                "entry_price": f"{t.entry_price:.6f}",
                "exit_price": f"{t.exit_price:.6f}",
                "weight_factor": f"{t.weight_factor:.4f}",
                "open_time": t.open_time,
                "close_time": t.close_time,
                "exit_reason": t.exit_reason,
                "pnl_pct": f"{t.pnl_pct:.4f}",
                "fee_pct": f"{t.fee_pct:.4f}",
                "net_pnl_pct": f"{t.net_pnl_pct:.4f}",
                "weighted_pnl": f"{t.weighted_pnl:.4f}",
            }
            writer.writerow(row)


def _write_daily_pnl(trades: list[TradeResult], path: Path) -> None:
    """Write daily PnL aggregation."""
    by_day: dict[str, float] = {}
    by_day_count: dict[str, int] = {}
    for t in trades:
        day = datetime.fromtimestamp(t.close_time / 1000, tz=UTC).strftime("%Y-%m-%d")
        by_day[day] = by_day.get(day, 0.0) + t.weighted_pnl
        by_day_count[day] = by_day_count.get(day, 0) + 1

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "pnl_pct", "trade_count"])
        for day in sorted(by_day):
            writer.writerow([day, f"{by_day[day]:.4f}", by_day_count[day]])


def _write_monthly_pnl(trades: list[TradeResult], path: Path) -> None:
    """Write monthly PnL aggregation."""
    by_month: dict[str, float] = {}
    by_month_count: dict[str, int] = {}
    for t in trades:
        month = datetime.fromtimestamp(t.close_time / 1000, tz=UTC).strftime("%Y-%m")
        by_month[month] = by_month.get(month, 0.0) + t.weighted_pnl
        by_month_count[month] = by_month_count.get(month, 0) + 1

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["month", "pnl_pct", "trade_count"])
        for month in sorted(by_month):
            writer.writerow([month, f"{by_month[month]:.4f}", by_month_count[month]])


def _write_per_symbol(trades: list[TradeResult], path: Path) -> None:
    """Write per-symbol PnL attribution."""
    by_sym: dict[str, list[float]] = {}
    for t in trades:
        by_sym.setdefault(t.symbol, []).append(t.net_pnl_pct)

    total_pnl = sum(t.net_pnl_pct for t in trades)
    rows = []
    for sym, pnls in sorted(by_sym.items()):
        net = sum(pnls)
        wins = sum(1 for p in pnls if p > 0)
        pct_of_total = (net / total_pnl * 100) if total_pnl != 0 else 0.0
        rows.append(
            {
                "symbol": sym,
                "trades": len(pnls),
                "wins": wins,
                "win_rate": f"{wins / len(pnls) * 100:.1f}",
                "net_pnl_pct": f"{net:.4f}",
                "avg_pnl_pct": f"{net / len(pnls):.4f}",
                "pct_of_total_pnl": f"{pct_of_total:.2f}",
            }
        )
    rows.sort(key=lambda r: float(r["net_pnl_pct"]), reverse=True)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "symbol",
                "trades",
                "wins",
                "win_rate",
                "net_pnl_pct",
                "avg_pnl_pct",
                "pct_of_total_pnl",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def _classify_regime(
    open_time_ms: int,
    btc_regimes: dict[int, str],
) -> str:
    """Look up the BTC-based regime for a given timestamp."""
    return btc_regimes.get(open_time_ms, "unknown")


def _build_btc_regimes(features_dir: str | Path, interval: str = "8h") -> dict[int, str]:
    """Build a mapping of open_time -> regime from BTC NATR/ADX features.

    Uses IS-period medians as fixed regime boundaries.
    """
    features_path = Path(features_dir)
    btc_path = features_path / f"BTCUSDT_{interval}_features.parquet"
    if not btc_path.exists():
        return {}

    df = pd.read_parquet(btc_path, columns=["open_time", "vol_natr_14", "trend_adx_14"])
    df = df.dropna()

    # Compute medians from IS data only
    is_mask = df["open_time"] < OOS_CUTOFF_MS
    natr_median = float(df.loc[is_mask, "vol_natr_14"].median())
    adx_median = float(df.loc[is_mask, "trend_adx_14"].median())

    regimes: dict[int, str] = {}
    for _, row in df.iterrows():
        ot = int(row["open_time"])
        high_vol = row["vol_natr_14"] > natr_median
        trending = row["trend_adx_14"] > adx_median
        if trending and high_vol:
            regimes[ot] = "trending_volatile"
        elif trending and not high_vol:
            regimes[ot] = "trending_quiet"
        elif not trending and high_vol:
            regimes[ot] = "choppy_volatile"
        else:
            regimes[ot] = "mean_reverting_quiet"

    return regimes


def _write_per_regime(
    trades: list[TradeResult],
    btc_regimes: dict[int, str],
    path: Path,
) -> None:
    """Write per-regime performance breakdown."""
    by_regime: dict[str, list[float]] = {}
    for t in trades:
        regime = _classify_regime(t.open_time, btc_regimes)
        by_regime.setdefault(regime, []).append(t.net_pnl_pct)

    rows = []
    for regime, pnls in sorted(by_regime.items()):
        net = sum(pnls)
        wins = sum(1 for p in pnls if p > 0)
        std = float(np.std(pnls)) if len(pnls) > 1 else 0.0
        sharpe = (np.mean(pnls) / std) if std > 0 else 0.0
        rows.append(
            {
                "regime": regime,
                "trades": len(pnls),
                "wins": wins,
                "win_rate": f"{wins / len(pnls) * 100:.1f}",
                "net_pnl_pct": f"{net:.4f}",
                "avg_pnl_pct": f"{net / len(pnls):.4f}",
                "sharpe": f"{sharpe:.4f}",
            }
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "regime", "trades", "wins", "win_rate",
                "net_pnl_pct", "avg_pnl_pct", "sharpe",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def _write_comparison(
    is_metrics: SplitMetrics | None,
    oos_metrics: SplitMetrics | None,
    path: Path,
) -> None:
    """Write comparison.csv with IS vs OOS side-by-side metrics and ratios."""

    def _fmt(v: float | None) -> str:
        return f"{v:.4f}" if v is not None else "—"

    def _ratio(oos_v: float | None, is_v: float | None) -> str:
        if oos_v is None or is_v is None or is_v == 0:
            return "—"
        return f"{oos_v / is_v:.4f}"

    metrics = [
        "sharpe",
        "sortino",
        "max_drawdown",
        "win_rate",
        "profit_factor",
        "total_trades",
        "calmar_ratio",
        "total_net_pnl",
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "in_sample", "out_of_sample", "ratio"])
        for m in metrics:
            is_v = getattr(is_metrics, m, None) if is_metrics else None
            oos_v = getattr(oos_metrics, m, None) if oos_metrics else None
            if m == "total_trades":
                is_str = str(int(is_v)) if is_v else "—"
                oos_str = str(int(oos_v)) if oos_v else "—"
                writer.writerow([m, is_str, oos_str, _ratio(oos_v, is_v)])
            elif m == "max_drawdown":
                is_str = f"{is_v:.2f}%" if is_v is not None else "—"
                oos_str = f"{oos_v:.2f}%" if oos_v is not None else "—"
                ratio = f"{oos_v / is_v:.4f}" if (is_v and oos_v and is_v != 0) else "—"
                writer.writerow([m, is_str, oos_str, ratio])
            elif m == "win_rate":
                is_str = f"{is_v:.1f}%" if is_v is not None else "—"
                oos_str = f"{oos_v:.1f}%" if oos_v is not None else "—"
                writer.writerow([m, is_str, oos_str, _ratio(oos_v, is_v)])
            else:
                writer.writerow([m, _fmt(is_v), _fmt(oos_v), _ratio(oos_v, is_v)])


def generate_iteration_reports(
    trades: list[TradeResult],
    iteration: int | str,
    features_dir: str | Path = "data/features",
    reports_dir: str | Path = "reports",
    interval: str = "8h",
) -> Path:
    """Generate full IS/OOS split reports for an iteration.

    Returns the iteration report directory path.
    """
    if isinstance(iteration, int):
        iter_dir = Path(reports_dir) / f"iteration_{iteration:03d}"
    else:
        iter_dir = Path(reports_dir) / f"iteration_{iteration}"
    is_dir = iter_dir / "in_sample"
    oos_dir = iter_dir / "out_of_sample"

    # Split trades
    is_trades = [t for t in trades if t.open_time < OOS_CUTOFF_MS]
    oos_trades = [t for t in trades if t.open_time >= OOS_CUTOFF_MS]

    print(f"[report] Splitting {len(trades)} trades: {len(is_trades)} IS, {len(oos_trades)} OOS")

    # Build BTC regimes
    btc_regimes = _build_btc_regimes(features_dir, interval)

    # Generate IS reports
    if is_trades:
        print(f"[report] Generating in-sample reports ({len(is_trades)} trades)...")
        _write_trades_csv(is_trades, is_dir / "trades.csv")
        _write_daily_pnl(is_trades, is_dir / "daily_pnl.csv")
        _write_monthly_pnl(is_trades, is_dir / "monthly_pnl.csv")
        _write_per_symbol(is_trades, is_dir / "per_symbol.csv")
        _write_per_regime(is_trades, btc_regimes, is_dir / "per_regime.csv")
        is_returns = to_daily_returns_series(is_trades)
        if not is_returns.empty:
            generate_html_report(is_returns, is_dir / "quantstats.html", title="IS Report")

    # Generate OOS reports
    if oos_trades:
        print(f"[report] Generating out-of-sample reports ({len(oos_trades)} trades)...")
        _write_trades_csv(oos_trades, oos_dir / "trades.csv")
        _write_daily_pnl(oos_trades, oos_dir / "daily_pnl.csv")
        _write_monthly_pnl(oos_trades, oos_dir / "monthly_pnl.csv")
        _write_per_symbol(oos_trades, oos_dir / "per_symbol.csv")
        _write_per_regime(oos_trades, btc_regimes, oos_dir / "per_regime.csv")
        oos_returns = to_daily_returns_series(oos_trades)
        if not oos_returns.empty:
            generate_html_report(oos_returns, oos_dir / "quantstats.html", title="OOS Report")

    # Comparison
    is_metrics = _compute_metrics(is_trades)
    oos_metrics = _compute_metrics(oos_trades)
    _write_comparison(is_metrics, oos_metrics, iter_dir / "comparison.csv")
    print("[report] comparison.csv written")

    # Print summary
    if is_metrics:
        print(
            f"[report] IS:  Sharpe={is_metrics.sharpe:.4f}"
            f"  Trades={is_metrics.total_trades}"
            f"  WR={is_metrics.win_rate:.1f}%"
            f"  PF={is_metrics.profit_factor:.4f}"
            f"  MaxDD={is_metrics.max_drawdown:.2f}%"
        )
    if oos_metrics:
        print(
            f"[report] OOS: Sharpe={oos_metrics.sharpe:.4f}"
            f"  Trades={oos_metrics.total_trades}"
            f"  WR={oos_metrics.win_rate:.1f}%"
            f"  PF={oos_metrics.profit_factor:.4f}"
            f"  MaxDD={oos_metrics.max_drawdown:.2f}%"
        )
    if is_metrics and oos_metrics and is_metrics.sharpe != 0:
        ratio = oos_metrics.sharpe / is_metrics.sharpe
        print(f"[report] OOS/IS Sharpe ratio: {ratio:.4f}")

    return iter_dir
