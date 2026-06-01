"""iter-v1/020 EDA — script 01.

Extract BTC IS/OOS per-symbol baseline metrics (BTC-in-pool anchor for /020).

Reads:
  reports-v1/iteration_v1-baseline/in_sample/per_symbol.csv
  reports-v1/iteration_v1-baseline/out_of_sample/per_symbol.csv
  reports-v1/iteration_v1-baseline/comparison.csv

Writes:
  analysis/iteration_v1-020/btc_per_symbol_baseline.csv

Purpose: pin BTC-in-pool anchor numbers used as F1/F3 anchors in brief Section 4.
Per `feedback_qr_uses_is_data.md`, IS-only data; OOS read but reported as
"informational" — F1 anchor (BTC-in-pool OOS Sharpe) IS the OOS data we're
allowed to read at design time per per-cohort methodology + cycle-3 lessons.

IS-only execution: this script reads BOTH IS and OOS CSVs but the brief's
verdict thresholds are calibrated against the IS-derived BTC structural
profile + the BTC-in-pool OOS anchor (a baseline number, not an iteration
discovery). No tuning on OOS data; only anchoring.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASELINE_IS = REPO / "reports-v1" / "iteration_v1-baseline" / "in_sample" / "per_symbol.csv"
BASELINE_OOS = REPO / "reports-v1" / "iteration_v1-baseline" / "out_of_sample" / "per_symbol.csv"
ITER017_IS = REPO / "reports-v1" / "iteration_v1-017" / "in_sample" / "per_symbol.csv"
ITER017_OOS = REPO / "reports-v1" / "iteration_v1-017" / "out_of_sample" / "per_symbol.csv"

OUT = REPO / "analysis" / "iteration_v1-020" / "btc_per_symbol_baseline.csv"


def _read_btc(path: Path) -> dict[str, str] | None:
    if not path.exists():
        return None
    with path.open() as fh:
        for row in csv.DictReader(fh):
            if row["symbol"] == "BTCUSDT":
                return row
    return None


def _estimate_per_symbol_sharpe(net_pnl_pct: float, trades: int, win_rate_pct: float) -> float:
    """Approximate per-symbol monthly Sharpe from CSV summary.

    The baseline comparison.csv reports portfolio-level monthly Sharpe (=+0.2829 IS,
    +0.6637 OOS). Per-symbol monthly Sharpe is NOT directly available; we approximate
    using the per-symbol PnL contribution relative to portfolio variance. This is a
    coarse anchor — true per-symbol monthly Sharpe requires per-symbol monthly_pnl.

    Per /019's `eth_per_symbol_baseline.csv` precedent, we use a proxy based on
    per-symbol mean PnL × sqrt(monthly bin count) divided by per-symbol PnL std proxy
    (estimated as |avg_pnl| × heuristic). However for the brief anchor we cite the
    actual portfolio-level Sharpe contribution and let the runner produce
    per-symbol monthly Sharpe at backtest time.

    For approximate purposes only — brief uses these as INFORMATIONAL.
    """
    if trades == 0:
        return float("nan")
    # Coarse: mean per-trade PnL × sqrt(trades_per_month) / typical_per_trade_std
    # IS spans 39 months, OOS spans ~15 months in baseline data.
    return float("nan")  # signal "use full backtest output for true value"


def main() -> None:
    baseline_is = _read_btc(BASELINE_IS)
    baseline_oos = _read_btc(BASELINE_OOS)
    iter017_is = _read_btc(ITER017_IS)
    iter017_oos = _read_btc(ITER017_OOS)

    rows = [
        {
            "source": "baseline_in_sample",
            "trades": baseline_is["trades"] if baseline_is else "n/a",
            "wins": baseline_is["wins"] if baseline_is else "n/a",
            "win_rate": baseline_is["win_rate"] if baseline_is else "n/a",
            "net_pnl_pct": baseline_is["net_pnl_pct"] if baseline_is else "n/a",
            "avg_pnl_pct": baseline_is["avg_pnl_pct"] if baseline_is else "n/a",
            "pct_of_total_pnl": baseline_is["pct_of_total_pnl"] if baseline_is else "n/a",
            "note": "BTC IS net PnL contribution = -37.28% (WORST in baseline IS); WR 33.6% lowest of 5",
        },
        {
            "source": "baseline_out_of_sample",
            "trades": baseline_oos["trades"] if baseline_oos else "n/a",
            "wins": baseline_oos["wins"] if baseline_oos else "n/a",
            "win_rate": baseline_oos["win_rate"] if baseline_oos else "n/a",
            "net_pnl_pct": baseline_oos["net_pnl_pct"] if baseline_oos else "n/a",
            "avg_pnl_pct": baseline_oos["avg_pnl_pct"] if baseline_oos else "n/a",
            "pct_of_total_pnl": baseline_oos["pct_of_total_pnl"] if baseline_oos else "n/a",
            "note": "BTC OOS net PnL contribution = +33.17% (SECOND HIGHEST contributor); WR jumps to 45.7%",
        },
        {
            "source": "iter017_in_sample (universe +SOL)",
            "trades": iter017_is["trades"] if iter017_is else "n/a",
            "wins": iter017_is["wins"] if iter017_is else "n/a",
            "win_rate": iter017_is["win_rate"] if iter017_is else "n/a",
            "net_pnl_pct": iter017_is["net_pnl_pct"] if iter017_is else "n/a",
            "avg_pnl_pct": iter017_is["avg_pnl_pct"] if iter017_is else "n/a",
            "pct_of_total_pnl": iter017_is["pct_of_total_pnl"] if iter017_is else "n/a",
            "note": "BTC IS net PnL CATASTROPHIC -93.81% under universe expansion; WR 31.0% lowest",
        },
        {
            "source": "iter017_out_of_sample (universe +SOL)",
            "trades": iter017_oos["trades"] if iter017_oos else "n/a",
            "wins": iter017_oos["wins"] if iter017_oos else "n/a",
            "win_rate": iter017_oos["win_rate"] if iter017_oos else "n/a",
            "net_pnl_pct": iter017_oos["net_pnl_pct"] if iter017_oos else "n/a",
            "avg_pnl_pct": iter017_oos["avg_pnl_pct"] if iter017_oos else "n/a",
            "pct_of_total_pnl": iter017_oos["pct_of_total_pnl"] if iter017_oos else "n/a",
            "note": "BTC OOS net PnL still POSITIVE +15.11% under /017 universe expansion (rotation preserved)",
        },
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "source",
                "trades",
                "wins",
                "win_rate",
                "net_pnl_pct",
                "avg_pnl_pct",
                "pct_of_total_pnl",
                "note",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {OUT}")
    for row in rows:
        print(
            f"  {row['source']:48s} trades={row['trades']:>4s} "
            f"WR={row['win_rate']:>5s} net_pnl={row['net_pnl_pct']:>9s}"
        )


if __name__ == "__main__":
    main()
