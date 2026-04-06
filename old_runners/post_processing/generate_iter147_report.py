"""Generate iter 147 reports: A+C+D with PER-SYMBOL vol targeting.

IS-tuned config: target=0.5, lookback=30.
"""

import csv
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

from crypto_trade.backtest_models import TradeResult
from crypto_trade.iteration_report import generate_iteration_reports


def load_trades_raw(csv_path: Path) -> list[dict]:
    trades = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            trades.append(dict(row))
    return trades


def compute_scales_per_symbol(
    trades_raw: list[dict],
    lookback_days: int,
    target_vol: float,
    min_scale: float = 0.5,
    max_scale: float = 2.0,
) -> dict:
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


def apply_scales(trades_raw: list[dict], scales: dict) -> list[TradeResult]:
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
            net_pnl_pct=net_pnl * scale, weighted_pnl=net_pnl * scale,
        ))
    return results


def main() -> None:
    is_raw = load_trades_raw(Path("reports/iteration_138/in_sample/trades.csv"))
    oos_raw = load_trades_raw(Path("reports/iteration_138/out_of_sample/trades.csv"))
    all_raw = is_raw + oos_raw

    # IS-tuned per-symbol config
    target_vol = 0.5
    lookback = 30
    print(f"Config: target_vol={target_vol}, lookback={lookback} (per-symbol)")

    scales = compute_scales_per_symbol(all_raw, lookback, target_vol)
    scaled = apply_scales(all_raw, scales)
    scaled.sort(key=lambda t: t.close_time)

    avg_scale = sum(scales.values()) / len(scales)
    print(f"Avg scale: {avg_scale:.2f}")

    report_dir = generate_iteration_reports(
        trades=scaled, iteration=147,
        features_dir="data/features", reports_dir="reports", interval="8h",
    )
    print(f"\nReports: {report_dir}")


if __name__ == "__main__":
    main()
