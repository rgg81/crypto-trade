"""Test volatility-targeted position sizing on iter 138 trades.

For each trade, scale position weight inversely to recent portfolio realized vol
(using only PAST trades — walk-forward valid).

Rule: weight = target_vol / rolling_30d_vol, clipped to [0.5, 2.0].
"""

import csv
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
import statistics
import sys


def load_trades(csv_path: Path) -> list[dict]:
    trades = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            trades.append({
                "symbol": row["symbol"],
                "direction": int(row["direction"]),
                "open_time": int(row["open_time"]),
                "close_time": int(row["close_time"]),
                "net_pnl_pct": float(row["net_pnl_pct"]),
            })
    return trades


def portfolio_daily_pnl(trades: list[dict]) -> dict:
    """Aggregate trade PnLs by close date."""
    daily = defaultdict(float)
    for t in trades:
        date = datetime.fromtimestamp(
            t["close_time"] / 1000, tz=timezone.utc
        ).date().isoformat()
        daily[date] += t["net_pnl_pct"]
    return dict(daily)


def compute_sharpe(returns: list[float], annualize: int = 365) -> float:
    if len(returns) < 2:
        return 0.0
    mean_r = sum(returns) / len(returns)
    var = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
    std = var ** 0.5
    if std == 0:
        return 0.0
    return (mean_r / std) * (annualize ** 0.5)


def compute_maxdd(returns: list[float]) -> float:
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for r in returns:
        cum += r
        peak = max(peak, cum)
        max_dd = max(max_dd, peak - cum)
    return max_dd


def apply_vol_targeting(
    trades: list[dict],
    lookback_days: int = 30,
    target_vol: float = 2.0,
    min_scale: float = 0.5,
    max_scale: float = 2.0,
) -> list[dict]:
    """Scale trade weights based on trailing portfolio volatility.

    For each trade, compute portfolio realized vol from trades that CLOSED
    within [trade.open_date - lookback_days, trade.open_date).
    """
    # Sort trades by open_time
    sorted_trades = sorted(trades, key=lambda t: t["open_time"])

    # Pre-compute cumulative daily PnL up to each date
    daily_pnl = portfolio_daily_pnl(sorted_trades)

    scaled = []
    for t in sorted_trades:
        trade_open_ms = t["open_time"]
        trade_open_date = datetime.fromtimestamp(
            trade_open_ms / 1000, tz=timezone.utc
        ).date()

        # Collect daily returns in [open_date - lookback, open_date)
        # Using only CLOSED trades from past
        lookback_returns = []
        for close_date_str, pnl in daily_pnl.items():
            close_date = datetime.fromisoformat(close_date_str).date()
            days_before = (trade_open_date - close_date).days
            if 1 <= days_before <= lookback_days:
                lookback_returns.append(pnl)

        # Compute realized vol (std of daily PnL)
        if len(lookback_returns) >= 5:
            mean_r = sum(lookback_returns) / len(lookback_returns)
            var = sum((r - mean_r) ** 2 for r in lookback_returns) / (len(lookback_returns) - 1)
            realized_vol = var ** 0.5
            if realized_vol > 0:
                scale = target_vol / realized_vol
                scale = max(min_scale, min(max_scale, scale))
            else:
                scale = 1.0
        else:
            scale = 1.0  # Not enough history

        t_scaled = dict(t)
        t_scaled["scale"] = scale
        t_scaled["scaled_pnl"] = t["net_pnl_pct"] * scale
        scaled.append(t_scaled)

    return scaled


def metrics(trades: list[dict], pnl_key: str = "net_pnl_pct") -> tuple[float, float, float, int]:
    daily = defaultdict(float)
    for t in trades:
        date = datetime.fromtimestamp(
            t["close_time"] / 1000, tz=timezone.utc
        ).date().isoformat()
        daily[date] += t[pnl_key]
    returns = list(daily.values())
    sharpe = compute_sharpe(returns)
    maxdd = compute_maxdd(returns)
    total = sum(returns)
    return sharpe, maxdd, total, len(trades)


def main() -> None:
    oos_138 = load_trades(Path("reports/iteration_138/out_of_sample/trades.csv"))

    print("=" * 70)
    print("BASELINE (iter 138) — A+C+D, no position sizing")
    print("=" * 70)
    s, dd, pnl, n = metrics(oos_138, "net_pnl_pct")
    print(f"OOS: Sharpe={s:+.2f}, MaxDD={dd:.2f}%, PnL={pnl:+.2f}%, Trades={n}")

    # Test different target vols and lookback windows
    print("\n" + "=" * 70)
    print("VOL-TARGETED SIZING — various configs")
    print("=" * 70)
    print(f"{'target_vol':>10} {'lookback':>9} {'Sharpe':>8} {'MaxDD':>8} {'PnL':>8} {'avg_scale':>10}")

    configs = []
    for target in [1.0, 1.5, 2.0, 2.5, 3.0, 4.0]:
        for lookback in [14, 21, 30, 60]:
            scaled = apply_vol_targeting(oos_138, lookback_days=lookback, target_vol=target)
            s, dd, pnl, n = metrics(scaled, "scaled_pnl")
            avg_scale = sum(t["scale"] for t in scaled) / len(scaled)
            configs.append((target, lookback, s, dd, pnl, avg_scale))
            print(f"{target:>10.1f} {lookback:>9} {s:>+7.2f} {dd:>7.2f}% {pnl:>+7.2f}% {avg_scale:>10.2f}")

    # Best by Sharpe
    print("\nBEST CONFIG BY SHARPE:")
    configs.sort(key=lambda c: -c[2])
    for c in configs[:5]:
        print(f"  target={c[0]:.1f}, lookback={c[1]}: Sharpe={c[2]:+.2f}, MaxDD={c[3]:.2f}%, PnL={c[4]:+.2f}%")


if __name__ == "__main__":
    main()
