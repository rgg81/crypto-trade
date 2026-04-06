"""Iter 149: Hybrid VT = per-symbol × portfolio scaling.

Tune on IS only, apply to OOS honestly.
"""

import csv
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

from crypto_trade.backtest_models import TradeResult
from crypto_trade.iteration_report import generate_iteration_reports


OOS_CUTOFF_MS = 1742774400000


def load_trades_raw(csv_path: Path) -> list[dict]:
    with open(csv_path) as f:
        return list(csv.DictReader(f))


def compute_hybrid_scales(
    trades_raw: list[dict],
    lookback_days: int,
    target_vol: float,
    min_scale: float = 0.5,
    max_scale: float = 2.0,
) -> dict:
    """Scale = sqrt(per_symbol_scale × portfolio_scale)."""
    # Per-symbol daily PnL
    per_sym_daily = defaultdict(lambda: defaultdict(float))
    # Portfolio-wide daily PnL
    portfolio_daily = defaultdict(float)
    for t in trades_raw:
        date = datetime.fromtimestamp(
            int(t["close_time"]) / 1000, tz=timezone.utc
        ).date().isoformat()
        per_sym_daily[t["symbol"]][date] += float(t["net_pnl_pct"])
        portfolio_daily[date] += float(t["net_pnl_pct"])

    sorted_trades = sorted(trades_raw, key=lambda t: int(t["open_time"]))
    scales = {}
    for t in sorted_trades:
        trade_open_date = datetime.fromtimestamp(
            int(t["open_time"]) / 1000, tz=timezone.utc
        ).date()

        def vol_of(daily_dict):
            rets = []
            for close_date_str, pnl in daily_dict.items():
                close_date = datetime.fromisoformat(close_date_str).date()
                days_before = (trade_open_date - close_date).days
                if 1 <= days_before <= lookback_days:
                    rets.append(pnl)
            if len(rets) >= 5:
                mean_r = sum(rets) / len(rets)
                var = sum((r - mean_r) ** 2 for r in rets) / (len(rets) - 1)
                return var ** 0.5
            return None

        sym_vol = vol_of(per_sym_daily[t["symbol"]])
        port_vol = vol_of(portfolio_daily)

        sym_scale = target_vol / sym_vol if sym_vol and sym_vol > 0 else 1.0
        port_scale = target_vol / port_vol if port_vol and port_vol > 0 else 1.0

        # Hybrid: geometric mean
        hybrid = (sym_scale * port_scale) ** 0.5
        hybrid = max(min_scale, min(max_scale, hybrid))

        key = (int(t["open_time"]), t["symbol"], int(t["direction"]))
        scales[key] = hybrid
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


def compute_sharpe_custom(trades_raw: list[dict], scales: dict) -> float:
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
        return 0.0
    mean_r = sum(returns) / len(returns)
    var = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
    std = var ** 0.5
    return (mean_r / std) * (365 ** 0.5) if std > 0 else 0.0


def main() -> None:
    is_raw = load_trades_raw(Path("reports/iteration_138/in_sample/trades.csv"))
    oos_raw = load_trades_raw(Path("reports/iteration_138/out_of_sample/trades.csv"))
    all_raw = is_raw + oos_raw

    # IS tune on hybrid VT
    print("=" * 70)
    print("Tune hybrid VT on IS only")
    print("=" * 70)
    print(f"{'target':>7} {'lookback':>9} {'IS_Sharpe':>10}")

    results = []
    for target in [0.3, 0.5, 0.75, 1.0, 1.5]:
        for lookback in [14, 21, 30]:
            scales = compute_hybrid_scales(all_raw, lookback, target)
            is_trades = [t for t in all_raw if int(t["open_time"]) < OOS_CUTOFF_MS]
            s = compute_sharpe_custom(is_trades, scales)
            results.append((target, lookback, s))
            print(f"{target:>7.2f} {lookback:>9} {s:>+9.2f}")

    best = max(results, key=lambda r: r[2])
    print(f"\nIS-best: target={best[0]}, lookback={best[1]}, IS Sharpe={best[2]:+.2f}")

    # Apply IS-best to OOS — generate official report
    scales = compute_hybrid_scales(all_raw, best[1], best[0])
    scaled = apply_scales(all_raw, scales)
    scaled.sort(key=lambda t: t.close_time)

    report_dir = generate_iteration_reports(
        trades=scaled, iteration=149,
        features_dir="data/features", reports_dir="reports", interval="8h",
    )
    print(f"\nReports: {report_dir}")


if __name__ == "__main__":
    main()
