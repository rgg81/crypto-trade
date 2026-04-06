"""Test min_scale sensitivity with iter 151 config (target=0.3, lookback=45).

Current production: min_scale=0.5 (no position less than 50% of nominal).
Test min_scale in [0.25, 0.33, 0.5, 0.67, 0.75] to see if risk floor matters.
"""

import csv
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

from crypto_trade.backtest_models import TradeResult
from crypto_trade.iteration_report import generate_iteration_reports


OOS_CUTOFF_MS = 1742774400000


def load_trades_raw(csv_path):
    with open(csv_path) as f:
        return list(csv.DictReader(f))


def compute_scales(trades_raw, min_scale, max_scale=2.0, target_vol=0.3, lookback_days=45):
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


def apply_scales(trades_raw, scales):
    results = []
    for t in trades_raw:
        key = (int(t["open_time"]), t["symbol"], int(t["direction"]))
        scale = scales.get(key, 1.0)
        net_pnl = float(t["net_pnl_pct"])
        results.append(TradeResult(
            symbol=t["symbol"], direction=int(t["direction"]),
            entry_price=float(t["entry_price"]), exit_price=float(t["exit_price"]),
            weight_factor=scale, open_time=int(t["open_time"]),
            close_time=int(t["close_time"]), exit_reason=t["exit_reason"],
            pnl_pct=float(t["pnl_pct"]), fee_pct=float(t["fee_pct"]),
            net_pnl_pct=net_pnl, weighted_pnl=net_pnl * scale,
        ))
    results.sort(key=lambda t: t.close_time)
    return results


def main() -> None:
    is_raw = load_trades_raw(Path("reports/iteration_138/in_sample/trades.csv"))
    oos_raw = load_trades_raw(Path("reports/iteration_138/out_of_sample/trades.csv"))
    all_raw = is_raw + oos_raw

    print(f"{'min_scale':>10} {'max_scale':>10}  candidates")
    print("-" * 60)

    # Grid: min_scale × max_scale combinations
    # Keep target=0.3, lookback=45 (iter 151 IS-best)
    configs = [
        (0.25, 2.0),
        (0.33, 2.0),
        (0.5, 2.0),   # production
        (0.67, 2.0),
        (0.75, 2.0),
        (0.5, 1.5),
        (0.5, 3.0),
        (0.33, 3.0),  # wider range
    ]

    for min_s, max_s in configs:
        name = f"152_min{int(min_s*100):02d}_max{int(max_s*100):03d}"
        scales = compute_scales(all_raw, min_s, max_s)
        scaled = apply_scales(all_raw, scales)
        avg_scale = sum(s for s in scales.values()) / len(scales)
        print(f"{min_s:>10.2f} {max_s:>10.2f}  avg_scale={avg_scale:.2f} → {name}")
        generate_iteration_reports(
            trades=scaled, iteration=name,
            features_dir="data/features", reports_dir="reports", interval="8h",
        )


if __name__ == "__main__":
    main()
