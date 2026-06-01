"""iter-v1/020 EDA — script 03.

BTC IS+OOS monthly PnL distribution + regime concentration check.

Tests the "BTC IS = bull 2020-2021 vs OOS = chop 2024-2025" intrinsic hypothesis.
If BTC IS catastrophic is concentrated in early bull-cycle months, the
INTRINSIC IS-OOS regime mismatch hypothesis is supported. If BTC IS catastrophic
is spread across IS, the POOL-ANCHOR hypothesis is more likely (pool training
distorts BTC's labels regardless of IS regime).

Reads:
  reports-v1/iteration_v1-baseline/in_sample/trades.csv (filter symbol=BTCUSDT)
  reports-v1/iteration_v1-baseline/out_of_sample/trades.csv (filter symbol=BTCUSDT)

Writes:
  analysis/iteration_v1-020/btc_monthly_pnl.csv
  analysis/iteration_v1-020/btc_regime_concentration.csv

IS-only methodology discipline: per /019 precedent (`eth_monthly_oos_baseline.csv`),
this script reads BTC IS trades + BTC OOS anchor trades. Per-cohort methodology
permits reading the BTC-in-pool anchor at design time; we are NOT tuning OOS
parameters, just characterizing the anchor.
"""

from __future__ import annotations

import csv
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
IS_TRADES = REPO / "reports-v1" / "iteration_v1-baseline" / "in_sample" / "trades.csv"
OOS_TRADES = REPO / "reports-v1" / "iteration_v1-baseline" / "out_of_sample" / "trades.csv"

OUT_MONTHLY = REPO / "analysis" / "iteration_v1-020" / "btc_monthly_pnl.csv"
OUT_REGIME = REPO / "analysis" / "iteration_v1-020" / "btc_regime_concentration.csv"


def _ms_to_month(ms_str: str) -> str:
    ms = int(ms_str)
    dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
    return f"{dt.year:04d}-{dt.month:02d}"


def _load_btc_trades(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open() as fh:
        for row in csv.DictReader(fh):
            if row["symbol"] == "BTCUSDT":
                rows.append(row)
    return rows


def _bucket_monthly(trades: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    buckets: dict[str, list[float]] = {}
    for row in trades:
        month = _ms_to_month(row["open_time"])
        pnl = float(row["net_pnl_pct"])
        buckets.setdefault(month, []).append(pnl)
    return {
        month: {
            "n": len(pnls),
            "wins": sum(1 for p in pnls if p > 0),
            "net_pnl_pct": sum(pnls),
            "avg_pnl_pct": sum(pnls) / len(pnls),
        }
        for month, pnls in sorted(buckets.items())
    }


def main() -> None:
    is_btc = _load_btc_trades(IS_TRADES)
    oos_btc = _load_btc_trades(OOS_TRADES)

    is_monthly = _bucket_monthly(is_btc)
    oos_monthly = _bucket_monthly(oos_btc)

    # Write monthly CSV (both IS and OOS rows; sample tag)
    OUT_MONTHLY.parent.mkdir(parents=True, exist_ok=True)
    with OUT_MONTHLY.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["sample", "month", "n_trades", "n_wins", "net_pnl_pct", "avg_pnl_pct"])
        for month, stats in is_monthly.items():
            writer.writerow(
                [
                    "IS",
                    month,
                    int(stats["n"]),
                    int(stats["wins"]),
                    f"{stats['net_pnl_pct']:.4f}",
                    f"{stats['avg_pnl_pct']:.4f}",
                ]
            )
        for month, stats in oos_monthly.items():
            writer.writerow(
                [
                    "OOS",
                    month,
                    int(stats["n"]),
                    int(stats["wins"]),
                    f"{stats['net_pnl_pct']:.4f}",
                    f"{stats['avg_pnl_pct']:.4f}",
                ]
            )
    print(f"wrote {OUT_MONTHLY}")

    # Regime concentration: split IS into halves by month chronology
    is_months = sorted(is_monthly.keys())
    h1_cutoff = is_months[len(is_months) // 2] if is_months else None
    is_h1 = {m: s for m, s in is_monthly.items() if m < h1_cutoff} if h1_cutoff else {}
    is_h2 = {m: s for m, s in is_monthly.items() if m >= h1_cutoff} if h1_cutoff else {}

    def _summarize(label: str, monthly: dict[str, dict[str, float]]) -> dict[str, str]:
        if not monthly:
            return {"sample_half": label, "n_months": "0", "net_pnl_sum": "n/a",
                    "n_pos_months": "n/a", "n_neg_months": "n/a", "worst_month": "n/a",
                    "best_month": "n/a", "mean_monthly_pnl": "n/a"}
        pnls = [s["net_pnl_pct"] for s in monthly.values()]
        return {
            "sample_half": label,
            "n_months": str(len(monthly)),
            "net_pnl_sum": f"{sum(pnls):+.2f}",
            "n_pos_months": str(sum(1 for p in pnls if p > 0)),
            "n_neg_months": str(sum(1 for p in pnls if p < 0)),
            "worst_month": f"{min(pnls):+.2f}",
            "best_month": f"{max(pnls):+.2f}",
            "mean_monthly_pnl": f"{sum(pnls) / len(pnls):+.4f}",
        }

    rows = [
        _summarize("IS_H1", is_h1),
        _summarize("IS_H2", is_h2),
        _summarize("OOS_full", oos_monthly),
    ]

    with OUT_REGIME.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {OUT_REGIME}")

    print()
    print(f"BTC IS half-1 (early bull 2022-?): {rows[0]}")
    print(f"BTC IS half-2 (late 2024+):        {rows[1]}")
    print(f"BTC OOS (2025-03 to 2026-05):      {rows[2]}")
    print()
    print("Diagnostic: if IS_H1 net << IS_H2 net, BTC IS catastrophic is CONCENTRATED")
    print("            in the bull-cycle half (INTRINSIC regime hypothesis supported).")
    print("            If IS_H1 net ≈ IS_H2 net, BTC catastrophic is UNIFORM across IS")
    print("            (POOL-ANCHOR hypothesis — Model A's pooled training distorts")
    print("             BTC labels regardless of regime; BTC-only isolation should help).")


if __name__ == "__main__":
    main()
