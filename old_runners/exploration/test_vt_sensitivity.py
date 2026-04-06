"""VT sensitivity analysis: is iter 147's (target=0.5, lookback=30) robust?

Test a grid of VT configs on IS only (walk-forward valid), then measure OOS
performance of the TOP configs. If OOS is stable across good IS configs, the
production setting is not overfit.
"""

import csv
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict


OOS_CUTOFF_MS = 1742774400000


def load_trades_raw(csv_path: Path) -> list[dict]:
    with open(csv_path) as f:
        return list(csv.DictReader(f))


def compute_scales_per_symbol(
    trades_raw, lookback_days, target_vol,
    min_scale=0.5, max_scale=2.0, min_history=5,
):
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
        if len(lookback_returns) >= min_history:
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


def metrics(trades_raw, scales, period_filter):
    """Returns (sharpe, maxdd, pnl, trades)."""
    daily = defaultdict(float)
    weighted_pnls = []
    for t in trades_raw:
        if not period_filter(int(t["open_time"])):
            continue
        key = (int(t["open_time"]), t["symbol"], int(t["direction"]))
        scale = scales.get(key, 1.0)
        pnl = float(t["net_pnl_pct"]) * scale
        weighted_pnls.append(pnl)
        date = datetime.fromtimestamp(
            int(t["close_time"]) / 1000, tz=timezone.utc
        ).date().isoformat()
        daily[date] += pnl
    returns = list(daily.values())
    if len(returns) < 2:
        return 0.0, 0.0, 0.0, 0
    mean_r = sum(returns) / len(returns)
    var = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
    std = var ** 0.5
    sharpe = (mean_r / std) * (365 ** 0.5) if std > 0 else 0.0
    # MaxDD from cumulative weighted PnL
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for p in weighted_pnls:
        cum += p
        peak = max(peak, cum)
        max_dd = max(max_dd, peak - cum)
    return sharpe, max_dd, sum(weighted_pnls), len(weighted_pnls)


def main() -> None:
    is_raw = load_trades_raw(Path("reports/iteration_138/in_sample/trades.csv"))
    oos_raw = load_trades_raw(Path("reports/iteration_138/out_of_sample/trades.csv"))
    all_raw = is_raw + oos_raw

    is_filter = lambda ot: ot < OOS_CUTOFF_MS
    oos_filter = lambda ot: ot >= OOS_CUTOFF_MS

    # No-VT baseline for reference
    no_vt_scales = {}
    is_s_base, is_dd_base, _, _ = metrics(all_raw, no_vt_scales, is_filter)
    oos_s_base, oos_dd_base, _, _ = metrics(all_raw, no_vt_scales, oos_filter)
    print(f"No-VT baseline:  IS Sharpe={is_s_base:+.2f} MaxDD={is_dd_base:.1f}%  |  OOS Sharpe={oos_s_base:+.2f} MaxDD={oos_dd_base:.1f}%")
    print()

    # Grid search
    targets = [0.3, 0.4, 0.5, 0.6, 0.8, 1.0]
    lookbacks = [14, 21, 30, 45, 60]
    results = []
    for target in targets:
        for lb in lookbacks:
            scales = compute_scales_per_symbol(all_raw, lb, target)
            is_s, is_dd, _, _ = metrics(all_raw, scales, is_filter)
            oos_s, oos_dd, _, _ = metrics(all_raw, scales, oos_filter)
            results.append((target, lb, is_s, is_dd, oos_s, oos_dd))

    # Sort by IS Sharpe descending
    results.sort(key=lambda r: -r[2])

    print(f"{'target':>7} {'lookback':>9} {'IS_Sharpe':>10} {'IS_DD':>7} {'OOS_Sharpe':>11} {'OOS_DD':>8}")
    print("-" * 68)
    for target, lb, is_s, is_dd, oos_s, oos_dd in results:
        marker = " <- PROD" if (target == 0.5 and lb == 30) else ""
        print(f"{target:>7.1f} {lb:>9} {is_s:>+9.2f} {is_dd:>6.1f}% {oos_s:>+10.2f} {oos_dd:>7.1f}%{marker}")

    # Top 5 IS configs — their OOS performance
    top5 = results[:5]
    top5_oos_sharpes = [r[4] for r in top5]
    mean_oos = sum(top5_oos_sharpes) / len(top5_oos_sharpes)
    min_oos = min(top5_oos_sharpes)
    max_oos = max(top5_oos_sharpes)
    print(f"\nTop-5 IS configs, OOS Sharpe: mean={mean_oos:+.2f}, min={min_oos:+.2f}, max={max_oos:+.2f}")
    print(f"Production config (target=0.5, lookback=30) OOS Sharpe: {next(r[4] for r in results if r[0]==0.5 and r[1]==30):+.2f}")


if __name__ == "__main__":
    main()
