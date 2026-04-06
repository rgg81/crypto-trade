"""Iter 154: Temporal stability analysis — rolling OOS performance per quarter.

Applies iter 152 VT config (target=0.3, lookback=45, min_scale=0.33) to iter 138
trades, then breaks OOS into quarterly windows to check stability.
"""

import csv
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict


OOS_CUTOFF_MS = 1742774400000


def load_trades_raw(csv_path):
    with open(csv_path) as f:
        return list(csv.DictReader(f))


def compute_scales(trades_raw, min_scale=0.33, target_vol=0.3, lookback_days=45, max_scale=2.0):
    per_sym_daily = defaultdict(lambda: defaultdict(float))
    for t in trades_raw:
        date = datetime.fromtimestamp(
            int(t["close_time"]) / 1000, tz=timezone.utc
        ).date().isoformat()
        per_sym_daily[t["symbol"]][date] += float(t["net_pnl_pct"])
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
            vol = var ** 0.5
            if vol > 1e-9:
                scale = max(min_scale, min(max_scale, target_vol / vol))
            else:
                scale = 1.0
        else:
            scale = 1.0
        key = (int(t["open_time"]), t["symbol"], int(t["direction"]))
        scales[key] = scale
    return scales


def quarterly_metrics(trades_raw, scales):
    """Group OOS trades by quarter, compute metrics per quarter."""
    quarterly = defaultdict(list)
    for t in trades_raw:
        ot = int(t["open_time"])
        if ot < OOS_CUTOFF_MS:
            continue
        key = (ot, t["symbol"], int(t["direction"]))
        scale = scales.get(key, 1.0)
        weighted_pnl = float(t["net_pnl_pct"]) * scale
        dt = datetime.fromtimestamp(int(t["close_time"]) / 1000, tz=timezone.utc)
        q = f"{dt.year}-Q{(dt.month - 1) // 3 + 1}"
        quarterly[q].append(weighted_pnl)

    print(f"{'Quarter':>8} {'Trades':>7} {'WR':>6} {'PnL':>8} {'Sharpe':>8} {'MaxDD':>8}")
    print("-" * 55)
    for q in sorted(quarterly.keys()):
        pnls = quarterly[q]
        wins = sum(1 for p in pnls if p > 0)
        wr = wins / len(pnls) * 100 if pnls else 0
        total_pnl = sum(pnls)
        # Sharpe from daily aggregation
        daily = defaultdict(float)
        # For per-quarter Sharpe, use trade-count normalization
        if len(pnls) >= 2:
            mean_p = sum(pnls) / len(pnls)
            var = sum((p - mean_p) ** 2 for p in pnls) / (len(pnls) - 1)
            std = var ** 0.5
            sharpe = (mean_p / std) * (len(pnls) ** 0.5) if std > 0 else 0.0
        else:
            sharpe = 0.0
        # MaxDD
        cum = 0.0
        peak = 0.0
        max_dd = 0.0
        for p in pnls:
            cum += p
            peak = max(peak, cum)
            max_dd = max(max_dd, peak - cum)
        print(f"{q:>8} {len(pnls):>7} {wr:>5.1f}% {total_pnl:>+7.2f}% {sharpe:>+7.2f} {max_dd:>7.2f}%")


def main():
    is_raw = load_trades_raw(Path("reports/iteration_138/in_sample/trades.csv"))
    oos_raw = load_trades_raw(Path("reports/iteration_138/out_of_sample/trades.csv"))
    all_raw = is_raw + oos_raw

    print("Applying iter 152 VT config (target=0.3, lookback=45, min_scale=0.33)")
    print("=" * 60)
    scales = compute_scales(all_raw, min_scale=0.33)

    print("\n=== OOS Quarterly Breakdown ===")
    quarterly_metrics(all_raw, scales)

    # Also break down by year + month
    print("\n=== OOS Monthly Breakdown ===")
    monthly = defaultdict(list)
    for t in all_raw:
        ot = int(t["open_time"])
        if ot < OOS_CUTOFF_MS:
            continue
        key = (ot, t["symbol"], int(t["direction"]))
        scale = scales.get(key, 1.0)
        weighted_pnl = float(t["net_pnl_pct"]) * scale
        dt = datetime.fromtimestamp(int(t["close_time"]) / 1000, tz=timezone.utc)
        m = dt.strftime("%Y-%m")
        monthly[m].append(weighted_pnl)

    print(f"{'Month':>8} {'Trades':>7} {'WR':>6} {'PnL':>8}")
    print("-" * 35)
    profitable_months = 0
    total_months = 0
    for m in sorted(monthly.keys()):
        pnls = monthly[m]
        wins = sum(1 for p in pnls if p > 0)
        wr = wins / len(pnls) * 100 if pnls else 0
        total_pnl = sum(pnls)
        status = "+" if total_pnl > 0 else " "
        print(f"{m:>8} {len(pnls):>7} {wr:>5.1f}% {total_pnl:>+7.2f}% {status}")
        total_months += 1
        if total_pnl > 0:
            profitable_months += 1

    print(f"\nProfitable months: {profitable_months}/{total_months} ({100*profitable_months/total_months:.0f}%)")


if __name__ == "__main__":
    main()
