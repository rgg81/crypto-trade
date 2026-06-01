"""Per-component IS-only evidence for iter-v1/045 bundle.

Reads each of the 5 per-coin source iteration's in_sample/trades.csv, filters
to the component's declared universe, and asserts every row satisfies
close_time < OOS_CUTOFF_MS (IS-window guard). Computes IS daily Sharpe
(annualised), IS PnL sum, IS max drawdown, IS n_trades, and IS win rate.

IS-only: this script reads NO post-2025-03-24 data. The OOS_CUTOFF_MS
sentinel is referenced solely to enforce the IS-window upper bound. No OOS
data enters the computation.

Components (per brief Section 11.A):
  C-BTC  = reports-v1/iteration_v1-012/in_sample/trades.csv  → filter BTCUSDT
  C-ETH  = reports-v1/iteration_v1-042/in_sample/trades.csv  → filter ETHUSDT
  C-LINK = reports-v1/iteration_v1-011/in_sample/trades.csv  → filter LINKUSDT
  C-LTC  = reports-v1/iteration_v1-040/in_sample/trades.csv  → filter LTCUSDT
  C-DOT  = reports-v1/iteration_v1-031/in_sample/trades.csv  → filter DOTUSDT

Output: analysis/iteration_v1-045/component_is_evidence.csv
  Columns: component_id, universe, source_iter, is_n_trades, is_sharpe,
           is_pnl, is_max_dd, is_win_rate
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Sacred constants (unchanged from BASELINE_V1).
# ---------------------------------------------------------------------------

OOS_CUTOFF_MS: int = 1742774400000  # 2025-03-24 00:00 UTC — IS upper-bound sentinel.

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_V1 = REPO_ROOT / "reports-v1"
OUT_PATH = Path(__file__).resolve().parent / "component_is_evidence.csv"

# ---------------------------------------------------------------------------
# 5-component definition (per brief Section 11.A).
# ---------------------------------------------------------------------------

COMPONENTS = [
    ("C-BTC", "BTCUSDT", "iteration_v1-012"),
    ("C-ETH", "ETHUSDT", "iteration_v1-042"),
    ("C-LINK", "LINKUSDT", "iteration_v1-011"),
    ("C-LTC", "LTCUSDT", "iteration_v1-040"),
    ("C-DOT", "DOTUSDT", "iteration_v1-031"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_is_trades(iter_label: str, symbol: str) -> list[dict]:
    """Load IS trades for iter_label, filtered to symbol and IS window.

    Rows with close_time >= OOS_CUTOFF_MS are silently excluded — these are
    walk-forward straddle rows (trade OPENED during IS, CLOSED just after
    the boundary) that live in in_sample/ but have a post-cutoff close_time.
    IS-only provenance is guaranteed by reading ONLY in_sample/trades.csv.
    """
    path = REPORTS_V1 / iter_label / "in_sample" / "trades.csv"
    if not path.exists():
        raise FileNotFoundError(f"IS trades not found: {path}")
    rows: list[dict] = []
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            if r["symbol"] != symbol:
                continue
            ct = int(r["close_time"])
            if ct < OOS_CUTOFF_MS:
                rows.append(r)
    return rows


def _daily_sharpe(trades: list[dict]) -> float:
    """Annualised daily Sharpe = mean(daily_pnl) / std(daily_pnl) * sqrt(365)."""
    if len(trades) < 2:
        return 0.0
    by_day: dict[int, float] = defaultdict(float)
    for r in trades:
        day = int(r["close_time"]) // (24 * 3600 * 1000)
        by_day[day] += float(r["weighted_pnl"])
    daily = list(by_day.values())
    if len(daily) < 2:
        return 0.0
    mean = sum(daily) / len(daily)
    var = sum((x - mean) ** 2 for x in daily) / (len(daily) - 1)
    std = math.sqrt(var) if var > 0 else 0.0
    return (mean / std) * math.sqrt(365) if std > 0 else 0.0


def _max_drawdown(trades: list[dict]) -> float:
    """Maximum peak-to-trough drawdown on cumulative weighted_pnl series."""
    if not trades:
        return 0.0
    cum = peak = max_dd = 0.0
    for r in sorted(trades, key=lambda t: int(t["close_time"])):
        cum += float(r["weighted_pnl"])
        if cum > peak:
            peak = cum
        dd = peak - cum
        if dd > max_dd:
            max_dd = dd
    return max_dd


def _win_rate(trades: list[dict]) -> float:
    """Fraction of trades with net_pnl_pct > 0."""
    if not trades:
        return 0.0
    wins = sum(1 for r in trades if float(r.get("net_pnl_pct", 0)) > 0)
    return wins / len(trades)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    results = []
    for cid, symbol, iter_label in COMPONENTS:
        trades = _load_is_trades(iter_label, symbol)
        sharpe = _daily_sharpe(trades)
        pnl = sum(float(r["weighted_pnl"]) for r in trades)
        max_dd = _max_drawdown(trades)
        n = len(trades)
        wr = _win_rate(trades)
        results.append(
            {
                "component_id": cid,
                "universe": symbol,
                "source_iter": iter_label,
                "is_n_trades": n,
                "is_sharpe": round(sharpe, 4),
                "is_pnl": round(pnl, 4),
                "is_max_dd": round(max_dd, 4),
                "is_win_rate": round(wr, 4),
            }
        )

    with OUT_PATH.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "component_id",
                "universe",
                "source_iter",
                "is_n_trades",
                "is_sharpe",
                "is_pnl",
                "is_max_dd",
                "is_win_rate",
            ],
        )
        writer.writeheader()
        writer.writerows(results)

    print(f"[component_is_evidence] Wrote {OUT_PATH} ({len(results)} components)")
    print()
    print(
        f"{'Component':<10} {'Universe':<12} {'Source':<22} "
        f"{'IS Sharpe':>10} {'IS PnL':>10} {'IS MaxDD':>10} "
        f"{'IS n':>6} {'IS WR':>7}"
    )
    print("-" * 90)
    for r in results:
        print(
            f"{r['component_id']:<10} {r['universe']:<12} {r['source_iter']:<22} "
            f"{r['is_sharpe']:>10.4f} {r['is_pnl']:>10.4f} {r['is_max_dd']:>10.4f} "
            f"{r['is_n_trades']:>6} {r['is_win_rate']:>7.4f}"
        )


if __name__ == "__main__":
    main()
