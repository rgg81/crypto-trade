"""Test which model COMBINATIONS yield the best Sharpe and lowest MaxDD."""

import csv
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from itertools import combinations


def load_trades(csv_path: Path) -> list[dict]:
    trades = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            trades.append({
                "symbol": row["symbol"],
                "open_time": int(row["open_time"]),
                "close_time": int(row["close_time"]),
                "net_pnl_pct": float(row["net_pnl_pct"]),
                "month": datetime.fromtimestamp(
                    int(row["close_time"]) / 1000, tz=timezone.utc
                ).strftime("%Y-%m"),
            })
    return trades


def model_of(symbol: str) -> str:
    mapping = {
        "BTCUSDT": "A", "ETHUSDT": "A",
        "LINKUSDT": "C",
        "BNBUSDT": "D",
        "DOGEUSDT": "E",
    }
    return mapping.get(symbol, "?")


def metrics_for_subset(trades: list[dict], models_active: set) -> tuple[float, float, float, int]:
    """Compute annualized Sharpe, MaxDD, total PnL, trade count for active models only."""
    filtered = [t for t in trades if model_of(t["symbol"]) in models_active]
    if not filtered:
        return 0.0, 0.0, 0.0, 0

    # Daily returns
    daily = defaultdict(float)
    for t in filtered:
        date = datetime.fromtimestamp(
            int(t["close_time"]) / 1000, tz=timezone.utc
        ).date().isoformat()
        daily[date] += t["net_pnl_pct"]

    # Treat as daily return series for Sharpe calc
    returns = list(daily.values())
    n = len(returns)
    if n < 2:
        return 0.0, 0.0, sum(returns), len(filtered)

    mean_ret = sum(returns) / n
    var = sum((r - mean_ret) ** 2 for r in returns) / (n - 1)
    std = var ** 0.5
    sharpe = (mean_ret / std) * (365 ** 0.5) if std > 0 else 0.0

    # MaxDD (cumulative)
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for r in returns:
        cum += r
        peak = max(peak, cum)
        max_dd = max(max_dd, peak - cum)

    total_pnl = sum(returns)
    return sharpe, max_dd, total_pnl, len(filtered)


def main() -> None:
    oos_138 = load_trades(Path("reports/iteration_138/out_of_sample/trades.csv"))
    oos_doge = load_trades(Path("reports/iteration_142_DOGE/out_of_sample/trades.csv"))
    all_oos = oos_138 + oos_doge

    print("=== ALL MODEL COMBINATIONS (OOS) ===")
    print(f"{'Combo':<10} {'Sharpe':>8} {'MaxDD':>8} {'PnL':>10} {'Trades':>7}")
    print("-" * 50)

    models = ["A", "C", "D", "E"]
    for r in range(1, len(models) + 1):
        for combo in combinations(models, r):
            active = set(combo)
            sharpe, maxdd, pnl, trades = metrics_for_subset(all_oos, active)
            print(f"{'+'.join(combo):<10} {sharpe:>+7.2f} {maxdd:>7.2f}% {pnl:>+9.2f}% {trades:>7}")


if __name__ == "__main__":
    main()
