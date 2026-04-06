"""Per-symbol vol targeting: each trade scaled by its own symbol's recent vol.

Hypothesis: scaling by the TRADED symbol's vol (not portfolio vol) preserves more
signal because good trades from low-vol symbols aren't dampened by unrelated
high-vol events.
"""

import csv
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict


OOS_CUTOFF_MS = 1742774400000


def load_trades_raw(csv_path: Path) -> list[dict]:
    trades = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            trades.append(dict(row))
    return trades


def compute_per_symbol_daily_pnl(trades_raw: list[dict]) -> dict:
    """Returns dict[symbol][date_iso] -> daily_pnl for that symbol."""
    per_symbol = defaultdict(lambda: defaultdict(float))
    for t in trades_raw:
        date = datetime.fromtimestamp(
            int(t["close_time"]) / 1000, tz=timezone.utc
        ).date().isoformat()
        per_symbol[t["symbol"]][date] += float(t["net_pnl_pct"])
    return per_symbol


def compute_scales_per_symbol(
    trades_raw: list[dict],
    lookback_days: int,
    target_vol: float,
    min_scale: float = 0.5,
    max_scale: float = 2.0,
) -> dict:
    per_sym_daily = compute_per_symbol_daily_pnl(trades_raw)
    sorted_trades = sorted(trades_raw, key=lambda t: int(t["open_time"]))

    scales = {}
    for t in sorted_trades:
        trade_open_date = datetime.fromtimestamp(
            int(t["open_time"]) / 1000, tz=timezone.utc
        ).date()
        sym_daily = per_sym_daily[t["symbol"]]
        lookback_returns = []
        for close_date_str, pnl in sym_daily.items():
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
        key = (int(t["open_time"]), t["symbol"], int(t["direction"]))
        scales[key] = scale
    return scales


def daily_metrics(trades_raw: list[dict], scales: dict) -> tuple[float, float, float]:
    """Compute Sharpe, MaxDD, PnL from scaled trades."""
    daily = defaultdict(float)
    for t in trades_raw:
        key = (int(t["open_time"]), t["symbol"], int(t["direction"]))
        scale = scales.get(key, 1.0)
        date = datetime.fromtimestamp(
            int(t["close_time"]) / 1000, tz=timezone.utc
        ).date().isoformat()
        daily[date] += float(t["net_pnl_pct"]) * scale
    returns = list(daily.values())
    if len(returns) < 2:
        return 0.0, 0.0, 0.0
    mean_r = sum(returns) / len(returns)
    var = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
    std = var ** 0.5
    sharpe = (mean_r / std) * (365 ** 0.5) if std > 0 else 0.0
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for r in returns:
        cum += r
        peak = max(peak, cum)
        max_dd = max(max_dd, peak - cum)
    return sharpe, max_dd, sum(returns)


def main() -> None:
    is_raw = load_trades_raw(Path("reports/iteration_138/in_sample/trades.csv"))
    oos_raw = load_trades_raw(Path("reports/iteration_138/out_of_sample/trades.csv"))
    all_raw = is_raw + oos_raw

    print("=" * 75)
    print("STEP 1: Tune per-symbol vol targeting on IS only")
    print("=" * 75)
    print(f"{'target':>7} {'lookback':>9} {'IS_Sharpe':>10} {'IS_MaxDD':>10} {'IS_PnL':>10}")

    results = []
    for target in [0.5, 1.0, 1.5, 2.0, 3.0]:
        for lookback in [7, 14, 21, 30]:
            scales = compute_scales_per_symbol(all_raw, lookback, target)
            is_trades = [t for t in all_raw if int(t["open_time"]) < OOS_CUTOFF_MS]
            s, dd, pnl = daily_metrics(is_trades, scales)
            results.append((target, lookback, s, dd, pnl, scales))
            print(f"{target:>7.1f} {lookback:>9} {s:>+9.2f} {dd:>9.2f}% {pnl:>+9.2f}%")

    best = max(results, key=lambda r: r[2])
    print(f"\nBEST IS: target={best[0]:.1f}, lookback={best[1]}, IS Sharpe={best[2]:+.2f}")

    print("\n" + "=" * 75)
    print("STEP 2: Apply IS-best to OOS")
    print("=" * 75)
    best_target, best_lookback = best[0], best[1]
    scales = compute_scales_per_symbol(all_raw, best_lookback, best_target)
    oos_trades = [t for t in all_raw if int(t["open_time"]) >= OOS_CUTOFF_MS]
    s, dd, pnl = daily_metrics(oos_trades, scales)
    print(f"OOS: Sharpe={s:+.2f}, MaxDD={dd:.2f}%, PnL={pnl:+.2f}%")

    # Avg scale per symbol in OOS
    print("\nAvg OOS scale per symbol:")
    per_sym_scales = defaultdict(list)
    for t in oos_trades:
        key = (int(t["open_time"]), t["symbol"], int(t["direction"]))
        per_sym_scales[t["symbol"]].append(scales.get(key, 1.0))
    for sym, sc in per_sym_scales.items():
        print(f"  {sym}: {sum(sc)/len(sc):.2f} (n={len(sc)})")


if __name__ == "__main__":
    main()
