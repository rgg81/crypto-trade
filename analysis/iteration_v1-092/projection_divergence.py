"""
iter-v1/092 — Projection Divergence Forensic
=============================================

Pre-registered projection (rerun_projection.md, committed before corrected run):
  IS: 219 -> 162 trades (-57, 26%), IS Sharpe ~+0.81 gain (net wpnl +5.21)
  OOS: 84 -> 72 trades (-12, 14.3%)

Actual corrected result:
  IS: 219 -> 179 trades (-40 net, 18.3%), IS Sharpe 0.3783 -> 0.3007 (-0.078)
  OOS: 84 -> 75 trades (-9 net), Sharpe 0.5158 -> 0.5952 (+0.079)

This script quantifies EXACTLY why the projection diverged, using only the trade CSVs.

Inputs:
  - Ungated roster = /088 IS/OOS trades.csv  (== void /092 roster, bit-identical)
  - Gated roster  = /092 IS/OOS trades.csv  (corrected run, gate armed)

Outputs:
  - Counts: removed (ungated-only), added (gated-only), kept (both)
  - PnL and WR of each segment
  - Mechanism: sequential slot freeing -> replacement trades
  - IS/OOS summary table

IS data guard: this script reads IS trades via open_time < OOS_CUTOFF_MS.
The ungated file covers both IS and OOS; we split by the sacred cutoff.
The ungated IS file at /088 is already IS-only (the runner writes separate files).
"""

import csv
import sys
from pathlib import Path

# ---- Paths ----------------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent.parent  # repo root
UNGATED_IS = BASE / "reports-v1" / "iteration_v1-088" / "in_sample" / "trades.csv"
GATED_IS = BASE / "reports-v1" / "iteration_v1-092" / "in_sample" / "trades.csv"
UNGATED_OOS = BASE / "reports-v1" / "iteration_v1-088" / "out_of_sample" / "trades.csv"
GATED_OOS = BASE / "reports-v1" / "iteration_v1-092" / "out_of_sample" / "trades.csv"

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC (SACRED, never change)


def load_csv(path: Path) -> list[dict]:
    rows = []
    with open(path) as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def classify(ungated: list[dict], gated: list[dict]) -> tuple[list, list, list]:
    """Split into removed (ungated-only), added (gated-only), kept (both)."""
    u_times = {r["open_time"] for r in ungated}
    g_times = {r["open_time"] for r in gated}
    removed = [r for r in ungated if r["open_time"] not in g_times]
    added = [r for r in gated if r["open_time"] not in u_times]
    kept = [r for r in gated if r["open_time"] in u_times]
    return removed, added, kept


def stats(trades: list[dict]) -> dict:
    if not trades:
        return {"n": 0, "wins": 0, "wr": float("nan"), "total_wpnl": 0.0, "mean_wpnl": float("nan")}
    wins = [r for r in trades if float(r["net_pnl_pct"]) > 0]
    wpnl = [float(r["weighted_pnl"]) for r in trades]
    return {
        "n": len(trades),
        "wins": len(wins),
        "wr": len(wins) / len(trades),
        "total_wpnl": sum(wpnl),
        "mean_wpnl": sum(wpnl) / len(trades),
    }


def print_stats(label: str, s: dict) -> None:
    print(
        f"  {label}: n={s['n']}, wins={s['wins']}, "
        f"WR={s['wr']:.4f}, total_wpnl={s['total_wpnl']:.4f}, "
        f"mean_wpnl={s['mean_wpnl']:.4f}"
    )


def run() -> None:
    # ---- Load ----------------------------------------------------------------
    u_is = load_csv(UNGATED_IS)
    g_is = load_csv(GATED_IS)
    u_oos = load_csv(UNGATED_OOS)
    g_oos = load_csv(GATED_OOS)

    # Data integrity sanity
    assert all(int(r["open_time"]) < OOS_CUTOFF_MS for r in u_is), "IS file contains OOS rows"
    assert all(int(r["open_time"]) < OOS_CUTOFF_MS for r in g_is), "IS file contains OOS rows"
    assert all(int(r["open_time"]) >= OOS_CUTOFF_MS for r in u_oos), "OOS file contains IS rows"
    assert all(int(r["open_time"]) >= OOS_CUTOFF_MS for r in g_oos), "OOS file contains IS rows"

    # ---- IS analysis ---------------------------------------------------------
    print("=" * 70)
    print("IS DIVERGENCE ANALYSIS")
    print("=" * 70)
    is_removed, is_added, is_kept = classify(u_is, g_is)

    s_u = stats(u_is)
    s_g = stats(g_is)
    s_rem = stats(is_removed)
    s_add = stats(is_added)
    s_kept = stats(is_kept)

    print(f"\nUngated IS total: n={s_u['n']}, total_wpnl={s_u['total_wpnl']:.4f}")
    print(f"Gated   IS total: n={s_g['n']}, total_wpnl={s_g['total_wpnl']:.4f}")
    print(f"Net trades change: {s_g['n'] - s_u['n']} ({s_g['n']} - {s_u['n']})")
    print(f"Net wpnl change:   {s_g['total_wpnl'] - s_u['total_wpnl']:.4f}")
    print()
    print("Segment breakdown:")
    print_stats("Removed (ungated-only, gate-suppressed + reshuffled)", s_rem)
    print_stats("Added   (gated-only, sequential slot replacement)", s_add)
    print_stats("Kept    (present in both)", s_kept)

    print()
    print("KEY DIVERGENCE FROM PROJECTION:")
    print("  Projected removed: 57 (BTC_UP only), wpnl=-5.21 -> would ADD +5.21")
    print("  Projected added:   0 (assumed static subtraction)")
    print("  Projected net IS wpnl change: +5.21  (subtraction of losers)")
    print()
    n_rem, wr_rem, wp_rem = s_rem["n"], s_rem["wr"], s_rem["total_wpnl"]
    n_add, wr_add, wp_add = s_add["n"], s_add["wr"], s_add["total_wpnl"]
    print(f"  Actual removed:    {n_rem} trades, WR={wr_rem:.4f}, wpnl={wp_rem:.4f}")
    print(f"  Actual added:      {n_add} trades, WR={wr_add:.4f}, wpnl={wp_add:.4f}")
    print(
        f"  Actual net IS wpnl change: "
        f"{s_add['total_wpnl'] - s_rem['total_wpnl']:.4f}  "
        f"(added {s_add['total_wpnl']:.4f} - removed {s_rem['total_wpnl']:.4f})"
    )
    print(
        f"  Projection error (IS wpnl delta): "
        f"{(s_add['total_wpnl'] - s_rem['total_wpnl']) - 5.21:.4f}"
        f"  (actual minus projected)"
    )

    print()
    print("MECHANISM:")
    print("  The offline projection assumed that suppressing 57 BTC_UP entries is a pure")
    print("  subtraction because 'zero overlapping trades' (all positions non-concurrent).")
    print("  This is WRONG for a SEQUENTIAL position model. Suppressing entry at time T")
    print("  frees the position slot -> the strategy enters a NEW trade that was previously")
    print(f"  blocked. The {n_add} added trades (WR={wr_add:.3f}, wpnl={wp_add:.2f})")
    print("  replaced the freed slots and are NET WORSE than the removed entries.")
    print(f"  The replacement WR ({wr_add:.4f}) is BELOW the removed WR ({wr_rem:.4f}),")
    net_is = wp_add - wp_rem
    print(f"  producing IS wpnl loss of {net_is:.4f}.")

    # ---- OOS analysis --------------------------------------------------------
    print()
    print("=" * 70)
    print("OOS DIVERGENCE ANALYSIS")
    print("=" * 70)
    oos_removed, oos_added, oos_kept = classify(u_oos, g_oos)

    so_u = stats(u_oos)
    so_g = stats(g_oos)
    so_rem = stats(oos_removed)
    so_add = stats(oos_added)

    print(f"\nUngated OOS total: n={so_u['n']}, total_wpnl={so_u['total_wpnl']:.4f}")
    print(f"Gated   OOS total: n={so_g['n']}, total_wpnl={so_g['total_wpnl']:.4f}")
    print(f"Net OOS trades change: {so_g['n'] - so_u['n']}")
    print(f"Net OOS wpnl change:   {so_g['total_wpnl'] - so_u['total_wpnl']:.4f}")
    print()
    print("OOS segment breakdown:")
    print_stats("Removed (ungated-only)", so_rem)
    print_stats("Added   (gated-only, replacements)", so_add)

    print()
    print("  Projected removed: 12, wpnl=-2.78 -> would ADD +2.78")
    n_or, wr_or, wp_or = so_rem["n"], so_rem["wr"], so_rem["total_wpnl"]
    n_oa, wr_oa, wp_oa = so_add["n"], so_add["wr"], so_add["total_wpnl"]
    print(f"  Actual removed:    {n_or}, WR={wr_or:.4f}, wpnl={wp_or:.4f}")
    print(f"  Actual added:      {n_oa}, WR={wr_oa:.4f}, wpnl={wp_oa:.4f}")
    net_oos = wp_oa - wp_or
    print(f"  Actual net OOS wpnl change: {net_oos:.4f}")
    print(
        f"  OOS: gate modestly helped (removed WR {wr_or:.3f} < added WR {wr_oa:.3f}),"
        f" net +{net_oos:.4f} wpnl -> Sharpe 0.5158->0.5952."
        " BUT IS destruction (F1 FAILS) overrides."
    )

    # ---- Summary table -------------------------------------------------------
    print()
    print("=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)
    print()
    print(f"{'Segment':<45} {'IS':>8} {'OOS':>8}")
    print("-" * 65)
    print(f"{'Ungated total trades':<45} {s_u['n']:>8} {so_u['n']:>8}")
    print(f"{'Gated total trades':<45} {s_g['n']:>8} {so_g['n']:>8}")
    print(f"{'Net change':<45} {s_g['n'] - s_u['n']:>8} {so_g['n'] - so_u['n']:>8}")
    print(f"{'Projected net change':<45} {-57:>8} {-12:>8}")
    print(f"{'Gross removed (gate-suppressed)':<45} {n_rem:>8} {n_or:>8}")
    print(f"{'Added (sequential replacements)':<45} {n_add:>8} {n_oa:>8}")
    print(f"{'Removed WR':<45} {wr_rem:>8.4f} {wr_or:>8.4f}")
    print(f"{'Added WR':<45} {wr_add:>8.4f} {wr_oa:>8.4f}")
    print(f"{'Removed total wpnl':<45} {wp_rem:>8.4f} {wp_or:>8.4f}")
    print(f"{'Added total wpnl':<45} {wp_add:>8.4f} {wp_oa:>8.4f}")
    print(f"{'Net wpnl change (added - removed)':<45} {net_is:>8.4f} {net_oos:>8.4f}")
    print(f"{'Projected net wpnl change':<45} {'+5.21':>8} {'+2.78':>8}")
    print()
    print("Root cause: sequential position model; suppressed entries free position slots;")
    print("replacement trades generated; replacements WR < removed WR on IS -> net worse.")
    print("Projection error: stated 'analytically exact' but missed slot-freeing mechanism.")


if __name__ == "__main__":
    run()
    sys.exit(0)
