"""Proper walk-forward test of vol-targeting:
1. Tune config on IS trades ONLY
2. Apply IS-best config to OOS trades
3. Compare vs baseline iter 138
"""

import csv
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict


OOS_CUTOFF_MS = 1742774400000  # 2025-03-24


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
            })
    return trades


def apply_vol_targeting(
    trades: list[dict],
    lookback_days: int,
    target_vol: float,
    min_scale: float = 0.5,
    max_scale: float = 2.0,
) -> list[dict]:
    sorted_trades = sorted(trades, key=lambda t: t["open_time"])
    # Daily PnL from all trades (to compute vol from all past)
    daily_pnl = defaultdict(float)
    for t in sorted_trades:
        date = datetime.fromtimestamp(t["close_time"] / 1000, tz=timezone.utc).date().isoformat()
        daily_pnl[date] += t["net_pnl_pct"]

    scaled = []
    for t in sorted_trades:
        trade_open_date = datetime.fromtimestamp(
            t["open_time"] / 1000, tz=timezone.utc
        ).date()
        lookback_returns = []
        for close_date_str, pnl in daily_pnl.items():
            close_date = datetime.fromisoformat(close_date_str).date()
            days_before = (trade_open_date - close_date).days
            if 1 <= days_before <= lookback_days:
                lookback_returns.append(pnl)
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
            scale = 1.0
        t_scaled = dict(t)
        t_scaled["scale"] = scale
        t_scaled["scaled_pnl"] = t["net_pnl_pct"] * scale
        scaled.append(t_scaled)
    return scaled


def compute_sharpe_maxdd(trades: list[dict], pnl_key: str) -> tuple[float, float, float]:
    daily = defaultdict(float)
    for t in trades:
        date = datetime.fromtimestamp(t["close_time"] / 1000, tz=timezone.utc).date().isoformat()
        daily[date] += t[pnl_key]
    returns = list(daily.values())
    n = len(returns)
    if n < 2:
        return 0.0, 0.0, 0.0
    mean_r = sum(returns) / n
    var = sum((r - mean_r) ** 2 for r in returns) / (n - 1)
    std = var ** 0.5
    sharpe = (mean_r / std) * (365 ** 0.5) if std > 0 else 0.0
    # MaxDD
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for r in returns:
        cum += r
        peak = max(peak, cum)
        max_dd = max(max_dd, peak - cum)
    return sharpe, max_dd, sum(returns)


def main() -> None:
    is_trades = load_trades(Path("reports/iteration_138/in_sample/trades.csv"))
    oos_trades = load_trades(Path("reports/iteration_138/out_of_sample/trades.csv"))
    all_trades = is_trades + oos_trades

    print("=" * 80)
    print("STEP 1: Tune vol-targeting on IS trades ONLY")
    print("=" * 80)

    is_baseline_s, is_baseline_dd, is_baseline_pnl = compute_sharpe_maxdd(is_trades, "net_pnl_pct")
    print(f"IS Baseline: Sharpe={is_baseline_s:+.2f}, MaxDD={is_baseline_dd:.2f}%, PnL={is_baseline_pnl:+.2f}%")
    print()
    print(f"{'target':>8} {'lookback':>9} {'IS_Sharpe':>10} {'IS_MaxDD':>10} {'IS_PnL':>10}")

    results = []
    for target in [1.5, 2.0, 2.5, 3.0, 4.0, 5.0]:
        for lookback in [14, 21, 30, 60]:
            # CRITICAL: compute vol-targeting using IS+OOS daily data combined
            # but evaluate only on IS trades
            scaled = apply_vol_targeting(all_trades, lookback_days=lookback, target_vol=target)
            # Filter to IS only for evaluation
            scaled_is = [t for t in scaled if t["open_time"] < OOS_CUTOFF_MS]
            s, dd, pnl = compute_sharpe_maxdd(scaled_is, "scaled_pnl")
            results.append((target, lookback, s, dd, pnl))
            print(f"{target:>8.1f} {lookback:>9} {s:>+9.2f} {dd:>9.2f}% {pnl:>+9.2f}%")

    # Best IS config by Sharpe
    best = max(results, key=lambda r: r[2])
    print(f"\nBEST IS CONFIG: target={best[0]:.1f}, lookback={best[1]}")
    print(f"  IS Sharpe={best[2]:+.2f} (baseline {is_baseline_s:+.2f}, delta={best[2]-is_baseline_s:+.2f})")

    print("\n" + "=" * 80)
    print("STEP 2: Apply IS-best config to OOS — the honest test")
    print("=" * 80)
    best_target, best_lookback = best[0], best[1]

    # Apply same rule to full dataset, then filter OOS
    scaled_all = apply_vol_targeting(all_trades, lookback_days=best_lookback, target_vol=best_target)
    scaled_oos = [t for t in scaled_all if t["open_time"] >= OOS_CUTOFF_MS]

    oos_baseline_s, oos_baseline_dd, oos_baseline_pnl = compute_sharpe_maxdd(oos_trades, "net_pnl_pct")
    oos_scaled_s, oos_scaled_dd, oos_scaled_pnl = compute_sharpe_maxdd(scaled_oos, "scaled_pnl")

    print(f"OOS Baseline:      Sharpe={oos_baseline_s:+.2f}, MaxDD={oos_baseline_dd:.2f}%, PnL={oos_baseline_pnl:+.2f}%")
    print(f"OOS Vol-Targeted:  Sharpe={oos_scaled_s:+.2f}, MaxDD={oos_scaled_dd:.2f}%, PnL={oos_scaled_pnl:+.2f}%")
    print(f"Delta:             Sharpe={oos_scaled_s-oos_baseline_s:+.2f}, MaxDD={oos_scaled_dd-oos_baseline_dd:+.2f}pp, PnL={oos_scaled_pnl-oos_baseline_pnl:+.2f}pp")

    avg_scale = sum(t["scale"] for t in scaled_oos) / len(scaled_oos)
    print(f"\nAvg OOS scale: {avg_scale:.2f}")


if __name__ == "__main__":
    main()
