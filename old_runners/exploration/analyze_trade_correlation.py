"""Analyze trade correlation across A/C/D/DOGE models from iter 143 data.

Goal: understand why adding DOGE (standalone OOS Sharpe +1.24) didn't improve
the portfolio. Hypothesis: DOGE's losing trades cluster with A/C/D's losing trades.
"""

import csv
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict


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
                "date": datetime.fromtimestamp(
                    int(row["close_time"]) / 1000, tz=timezone.utc
                ).date().isoformat(),
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


def main() -> None:
    # Load iter 143 combined OOS trades
    oos_138 = load_trades(Path("reports/iteration_138/out_of_sample/trades.csv"))
    oos_doge = load_trades(Path("reports/iteration_142_DOGE/out_of_sample/trades.csv"))
    all_oos = oos_138 + oos_doge

    print(f"Total OOS trades: {len(all_oos)}")
    print(f"  A+C+D (iter 138): {len(oos_138)}")
    print(f"  E DOGE (iter 142): {len(oos_doge)}")

    # Per-model monthly PnL
    print("\n=== MONTHLY PnL PER MODEL ===")
    monthly = defaultdict(lambda: defaultdict(float))
    for t in all_oos:
        monthly[t["month"]][model_of(t["symbol"])] += t["net_pnl_pct"]

    print(f"{'Month':<10} {'A':>8} {'C':>8} {'D':>8} {'E':>8} {'Total':>8}")
    print("-" * 55)
    totals = defaultdict(float)
    for month in sorted(monthly.keys()):
        row = monthly[month]
        total = sum(row.values())
        totals["A"] += row["A"]
        totals["C"] += row["C"]
        totals["D"] += row["D"]
        totals["E"] += row["E"]
        totals["T"] += total
        print(f"{month:<10} {row['A']:>+7.2f}% {row['C']:>+7.2f}% {row['D']:>+7.2f}% {row['E']:>+7.2f}% {total:>+7.2f}%")
    print("-" * 55)
    print(f"{'TOTAL':<10} {totals['A']:>+7.2f}% {totals['C']:>+7.2f}% {totals['D']:>+7.2f}% {totals['E']:>+7.2f}% {totals['T']:>+7.2f}%")

    # Monthly correlation matrix
    import statistics
    print("\n=== MONTHLY CORRELATION MATRIX (A/C/D/E PnL) ===")
    months = sorted(monthly.keys())
    models = ["A", "C", "D", "E"]
    series = {m: [monthly[month][m] for month in months] for m in models}

    def correlate(x: list[float], y: list[float]) -> float:
        n = len(x)
        mx = sum(x) / n
        my = sum(y) / n
        num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
        dx = sum((x[i] - mx) ** 2 for i in range(n)) ** 0.5
        dy = sum((y[i] - my) ** 2 for i in range(n)) ** 0.5
        if dx == 0 or dy == 0:
            return 0.0
        return num / (dx * dy)

    print(f"{'':>4} " + " ".join(f"{m:>6}" for m in models))
    for m1 in models:
        row = " ".join(f"{correlate(series[m1], series[m2]):>+6.2f}" for m2 in models)
        print(f"{m1:>4} {row}")

    # Worst months (drawdown analysis)
    print("\n=== WORST 10 MONTHS (by combined PnL) ===")
    ranked = sorted(months, key=lambda m: sum(monthly[m].values()))[:10]
    print(f"{'Month':<10} {'A':>8} {'C':>8} {'D':>8} {'E':>8} {'Total':>8}")
    for month in ranked:
        row = monthly[month]
        total = sum(row.values())
        print(f"{month:<10} {row['A']:>+7.2f}% {row['C']:>+7.2f}% {row['D']:>+7.2f}% {row['E']:>+7.2f}% {total:>+7.2f}%")

    # Correlation of losing months
    print("\n=== LOSING MONTH OVERLAP ===")
    losing = {}
    for m in models:
        losing[m] = {month for month in months if monthly[month][m] < 0}

    print(f"Losing months per model: A={len(losing['A'])}, C={len(losing['C'])}, D={len(losing['D'])}, E={len(losing['E'])}")
    print(f"Total months: {len(months)}")

    for m1 in models:
        for m2 in models:
            if m1 < m2:
                overlap = len(losing[m1] & losing[m2])
                union = len(losing[m1] | losing[m2])
                jaccard = overlap / union if union > 0 else 0.0
                print(f"  {m1} & {m2}: {overlap} overlapping losing months (Jaccard={jaccard:.2f})")

    # Equity curve MaxDD per model
    print("\n=== CUMULATIVE EQUITY PER MODEL (end-of-month) ===")
    cum = {m: 0.0 for m in models}
    peak = {m: 0.0 for m in models}
    dd = {m: 0.0 for m in models}
    print(f"{'Month':<10} " + " ".join(f"{m+'_eq':>8} {m+'_dd':>7}" for m in models))
    for month in months:
        for m in models:
            cum[m] += monthly[month][m]
            peak[m] = max(peak[m], cum[m])
            current_dd = peak[m] - cum[m]
            dd[m] = max(dd[m], current_dd)

    for m in models:
        print(f"{m}: final PnL={cum[m]:+.2f}%, peak={peak[m]:+.2f}%, MaxDD={dd[m]:.2f}%")

    # Combined equity
    cum_total = 0.0
    peak_total = 0.0
    dd_total = 0.0
    for month in months:
        cum_total += sum(monthly[month].values())
        peak_total = max(peak_total, cum_total)
        dd_total = max(dd_total, peak_total - cum_total)
    print(f"Combined: final PnL={cum_total:+.2f}%, peak={peak_total:+.2f}%, MaxDD={dd_total:.2f}%")

    # What if we exclude E?
    cum_acd = 0.0
    peak_acd = 0.0
    dd_acd = 0.0
    for month in months:
        cum_acd += monthly[month]["A"] + monthly[month]["C"] + monthly[month]["D"]
        peak_acd = max(peak_acd, cum_acd)
        dd_acd = max(dd_acd, peak_acd - cum_acd)
    print(f"A+C+D only: final PnL={cum_acd:+.2f}%, peak={peak_acd:+.2f}%, MaxDD={dd_acd:.2f}%")

    # Diff
    print(f"\nMaxDD increase from adding E: {dd_total - dd_acd:.2f}pp")
    print(f"PnL increase from adding E: {cum_total - cum_acd:+.2f}pp")


if __name__ == "__main__":
    main()
