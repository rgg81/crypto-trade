"""Generate iter 145 reports with vol-targeted position sizing applied to iter 138 trades.

IS-tuned config: target_vol=1.5, lookback=14 days.
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


def compute_scales(
    trades_raw: list[dict],
    lookback_days: int = 14,
    target_vol: float = 1.5,
    min_scale: float = 0.5,
    max_scale: float = 2.0,
) -> dict:
    """Returns dict[close_time_ms -> scale] for each trade."""
    sorted_trades = sorted(trades_raw, key=lambda t: int(t["open_time"]))
    daily_pnl = defaultdict(float)
    for t in sorted_trades:
        date = datetime.fromtimestamp(
            int(t["close_time"]) / 1000, tz=timezone.utc
        ).date().isoformat()
        daily_pnl[date] += float(t["net_pnl_pct"])

    scales = {}
    for t in sorted_trades:
        trade_open_date = datetime.fromtimestamp(
            int(t["open_time"]) / 1000, tz=timezone.utc
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
        # Key by (open_time, symbol, direction) to identify trade uniquely
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
            symbol=t["symbol"],
            direction=int(t["direction"]),
            entry_price=float(t["entry_price"]),
            exit_price=float(t["exit_price"]),
            weight_factor=scale,
            open_time=int(t["open_time"]),
            close_time=int(t["close_time"]),
            exit_reason=t["exit_reason"],
            pnl_pct=float(t["pnl_pct"]),
            fee_pct=float(t["fee_pct"]),
            net_pnl_pct=net_pnl * scale,  # Apply scaling to PnL
            weighted_pnl=net_pnl * scale,
        ))
    return results


def main() -> None:
    # Load iter 138 trades
    is_raw = load_trades_raw(Path("reports/iteration_138/in_sample/trades.csv"))
    oos_raw = load_trades_raw(Path("reports/iteration_138/out_of_sample/trades.csv"))
    all_raw = is_raw + oos_raw

    print(f"Loaded {len(all_raw)} trades ({len(is_raw)} IS + {len(oos_raw)} OOS)")

    # IS-tuned config from walk-forward analysis
    target_vol = 1.5
    lookback_days = 14
    print(f"\nUsing IS-tuned config: target_vol={target_vol}, lookback={lookback_days}")

    # Compute scales using ALL trades (vol uses past data per trade)
    scales = compute_scales(all_raw, lookback_days=lookback_days, target_vol=target_vol)

    # Apply scales
    scaled_trades = apply_scales(all_raw, scales)
    scaled_trades.sort(key=lambda t: t.close_time)

    avg_scale = sum(scales.values()) / len(scales)
    min_scale_applied = min(scales.values())
    max_scale_applied = max(scales.values())
    print(f"Scales: avg={avg_scale:.2f}, min={min_scale_applied:.2f}, max={max_scale_applied:.2f}")

    # Generate official iter 145 reports
    report_dir = generate_iteration_reports(
        trades=scaled_trades, iteration=145,
        features_dir="data/features", reports_dir="reports", interval="8h",
    )
    print(f"\nReports: {report_dir}")


if __name__ == "__main__":
    main()
