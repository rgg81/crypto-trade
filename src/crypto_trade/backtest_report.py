from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from crypto_trade.backtest_models import DailyPnL, TradeResult

# Euler-Mascheroni constant for DSR computation (AFML Ch. 14)
_EULER_MASCHERONI = 0.5772156649015328


@dataclass(frozen=True)
class BacktestSummary:
    total_trades: int
    wins: int
    losses: int
    win_rate_pct: float
    avg_pnl_pct: float
    total_net_pnl_pct: float
    max_drawdown_pct: float
    profit_factor: float
    exit_reasons: dict[str, int]
    best_trade_pct: float
    worst_trade_pct: float
    trades_per_month: float


def aggregate_monthly_trades(results: list[TradeResult]) -> dict[str, int]:
    """Group trade results by open-time month (UTC) and count trades per month."""
    monthly: dict[str, int] = {}
    for r in results:
        month_str = datetime.fromtimestamp(r.open_time / 1000, tz=UTC).strftime("%Y-%m")
        monthly[month_str] = monthly.get(month_str, 0) + 1
    return dict(sorted(monthly.items()))


def summarize(results: list[TradeResult]) -> BacktestSummary | None:
    """Compute aggregate statistics from a list of trade results."""
    if not results:
        return None

    total = len(results)
    # Win rate uses trade-level PnL (direction-dependent only, not scaled)
    wins = sum(1 for r in results if r.net_pnl_pct > 0)
    losses = total - wins
    win_rate = wins / total * 100.0

    # Portfolio metrics (MaxDD, PnL, PF) use weighted_pnl to reflect position
    # sizing (e.g. vol targeting). For legacy runs with weight_factor=1.0,
    # weighted_pnl == net_pnl_pct, so this is backward-compatible.
    weighted_pnls = [r.weighted_pnl for r in results]
    net_pnls = [r.net_pnl_pct for r in results]
    avg_pnl = sum(weighted_pnls) / total
    total_net = sum(weighted_pnls)

    best = max(net_pnls)
    worst = min(net_pnls)

    # Max drawdown: largest peak-to-trough decline in cumulative weighted PnL
    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for pnl in weighted_pnls:
        cumulative += pnl
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd

    # Profit factor: sum(gains) / sum(losses) on weighted returns
    gross_gains = sum(p for p in weighted_pnls if p > 0)
    gross_losses = sum(-p for p in weighted_pnls if p < 0)
    profit_factor = gross_gains / gross_losses if gross_losses > 0 else float("inf")

    exit_reasons: dict[str, int] = {}
    for r in results:
        exit_reasons[r.exit_reason] = exit_reasons.get(r.exit_reason, 0) + 1

    monthly = aggregate_monthly_trades(results)
    n_months = len(monthly) if monthly else 1
    tpm = total / n_months

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
        trades_per_month=tpm,
    )


def expected_max_sharpe(n_trials: int) -> float:
    """Expected maximum Sharpe under the null of ``n_trials`` random,
    independent Sharpe estimates (mean 0, unit variance).

    Implements the closed-form approximation from Bailey & López de Prado
    (AFML Ch. 14, equation 14.4):

        E[max(SR_0)] ≈ √(2·ln·N) · (1 − γ/(2·ln·N)) + γ/√(2·ln·N)

    where γ is the Euler-Mascheroni constant.

    Returns 0.0 for ``n_trials <= 1`` (no multiple-testing adjustment).
    """
    if n_trials <= 1:
        return 0.0
    ln_n = math.log(n_trials)
    return math.sqrt(2 * ln_n) * (
        1 - _EULER_MASCHERONI / (2 * ln_n)
    ) + _EULER_MASCHERONI / math.sqrt(2 * ln_n)


def sharpe_standard_error(sharpe: float, returns: list[float]) -> float:
    """Standard error of an annualized Sharpe ratio estimate, accounting
    for the return distribution's skew (γ_3) and kurtosis (γ_4).

    Per AFML Ch. 14:

        SE(SR)² ≈ (1 − γ_3·SR + (γ_4 − 1)/4·SR²) / (T − 1)

    where ``T`` is the number of return observations. Returns 0.0 when
    ``T < 3`` or when the computed variance is non-positive (guards
    against degenerate return series).
    """
    t = len(returns)
    if t < 3:
        return 0.0
    mean = sum(returns) / t
    var = sum((r - mean) ** 2 for r in returns) / (t - 1)
    if var <= 0:
        return 0.0
    std = math.sqrt(var)
    z = [(r - mean) / std for r in returns]
    skew = sum(v**3 for v in z) / t
    kurt = sum(v**4 for v in z) / t  # raw (non-excess) kurtosis
    se_sq = (1 - skew * sharpe + (kurt - 1) / 4 * sharpe**2) / (t - 1)
    if se_sq <= 0:
        return 0.0
    return math.sqrt(se_sq)


def compute_deflated_sharpe_ratio(
    sharpe: float,
    n_trials: int,
    returns: list[float],
) -> float:
    """Deflated Sharpe Ratio (DSR) from AFML Ch. 14.

    DSR = (SR_observed − E[max(SR_0)]) / SE(SR)

    - DSR > 0: observed Sharpe exceeds expected random maximum.
    - DSR > 1: ~84% confidence observed Sharpe isn't multiple-testing noise.
    - DSR < 0: observed Sharpe is within random-chance range.

    Args:
        sharpe: observed annualized Sharpe ratio.
        n_trials: number of independent Sharpe estimates considered.
        returns: daily return observations used to estimate skew/kurtosis.

    Returns 0.0 if the standard error cannot be computed.
    """
    emax = expected_max_sharpe(n_trials)
    se = sharpe_standard_error(sharpe, returns)
    if se <= 0:
        return 0.0
    return (sharpe - emax) / se


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
        avg = total / len(trades)
        daily.append(
            DailyPnL(
                date=date_str,
                avg_weighted_pnl=avg,
                trade_count=len(trades),
                trades=tuple(trades),
            )
        )
    return daily


def to_daily_returns_series(
    results: list[TradeResult],
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.Series:
    """Convert trade results to a daily returns Series for quantstats.

    Groups trades by close_time date (UTC), sums weighted_pnl per day,
    converts percentage to decimal (/ 100), and fills missing calendar
    days with 0.0.

    Args:
        results: List of TradeResult from a backtest run.
        start_date: Optional YYYY-MM-DD to extend series start.
        end_date: Optional YYYY-MM-DD to extend series end.

    Returns:
        pd.Series with DatetimeIndex (daily frequency), values as decimal returns.
    """
    if not results:
        return pd.Series(dtype=float)

    # Sum weighted_pnl per close-date
    by_day: dict[str, float] = {}
    for r in results:
        date_str = datetime.fromtimestamp(r.close_time / 1000, tz=UTC).strftime("%Y-%m-%d")
        by_day[date_str] = by_day.get(date_str, 0.0) + r.weighted_pnl

    series = pd.Series(by_day, dtype=float)
    series.index = pd.to_datetime(series.index)

    # Determine date range
    first = series.index.min()
    last = series.index.max()
    if start_date:
        sd = pd.Timestamp(start_date)
        if sd < first:
            first = sd
    if end_date:
        ed = pd.Timestamp(end_date)
        if ed > last:
            last = ed

    idx = pd.date_range(first, last, freq="D")
    series = series.reindex(idx, fill_value=0.0)
    series = series / 100.0  # pct -> decimal
    series.index.name = "Date"
    series.name = "Returns"
    return series


def generate_html_report(
    returns: pd.Series,
    output_path: str | Path,
    title: str = "Backtest Report",
) -> str:
    """Generate a quantstats HTML tearsheet.

    Uses ``compounded=False`` because each trade allocates a fixed dollar
    amount — daily returns are additive sums, not portfolio growth rates.

    Args:
        returns: Daily returns Series (decimal, DatetimeIndex).
        output_path: Where to write the HTML file.
        title: Report title.

    Returns:
        Absolute path of the generated file.
    """
    import quantstats as qs

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    qs.reports.html(
        returns,
        output=str(output_path),
        title=title,
        periods_per_year=365,
        benchmark=None,
        compounded=False,
    )
    return str(output_path.resolve())
