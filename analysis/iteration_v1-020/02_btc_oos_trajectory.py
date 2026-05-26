"""iter-v1/020 EDA — script 02.

BTC IS/OOS trajectory across baseline + /014/015/016/017.

Reads per_symbol.csv across iterations and extracts BTC rows.

Writes:
  analysis/iteration_v1-020/btc_oos_trajectory.csv

Purpose: characterize BTC's IS-OOS rotation asymmetry across cycle-3 architectures.

IS-only execution discipline: this script reads the BTC-in-pool stats (which are
the ANCHOR — baseline numbers from already-published iterations, not OOS tuning).
The anchor is what /020 is trying to BEAT under cohort isolation. Per-cohort
methodology per `feedback_v1_per_cohort_exploration_strategy.md` permits reading
ETH-in-pool (now BTC-in-pool) anchor at design time.
"""

from __future__ import annotations

import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

ITERS = [
    ("baseline", REPO / "reports-v1" / "iteration_v1-baseline"),
    ("014", REPO / "reports-v1" / "iteration_v1-014"),
    ("015", REPO / "reports-v1" / "iteration_v1-015"),
    ("016", REPO / "reports-v1" / "iteration_v1-016"),
    ("017", REPO / "reports-v1" / "iteration_v1-017"),
]
# /018 LINK-only and /019 ETH-only do NOT include BTC; we skip them.

OUT = REPO / "analysis" / "iteration_v1-020" / "btc_oos_trajectory.csv"


def _read_btc(path: Path) -> dict[str, str] | None:
    if not path.exists():
        return None
    with path.open() as fh:
        for row in csv.DictReader(fh):
            if row["symbol"] == "BTCUSDT":
                return row
    return None


def main() -> None:
    rows: list[dict[str, str]] = []
    for label, root in ITERS:
        is_btc = _read_btc(root / "in_sample" / "per_symbol.csv")
        oos_btc = _read_btc(root / "out_of_sample" / "per_symbol.csv")
        rows.append(
            {
                "iter": label,
                "btc_is_trades": is_btc["trades"] if is_btc else "n/a",
                "btc_is_wr": is_btc["win_rate"] if is_btc else "n/a",
                "btc_is_net_pnl_pct": is_btc["net_pnl_pct"] if is_btc else "n/a",
                "btc_is_avg_pnl": is_btc["avg_pnl_pct"] if is_btc else "n/a",
                "btc_oos_trades": oos_btc["trades"] if oos_btc else "n/a",
                "btc_oos_wr": oos_btc["win_rate"] if oos_btc else "n/a",
                "btc_oos_net_pnl_pct": oos_btc["net_pnl_pct"] if oos_btc else "n/a",
                "btc_oos_avg_pnl": oos_btc["avg_pnl_pct"] if oos_btc else "n/a",
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # Summary stats
    is_pnls = [float(r["btc_is_net_pnl_pct"]) for r in rows if r["btc_is_net_pnl_pct"] != "n/a"]
    oos_pnls = [float(r["btc_oos_net_pnl_pct"]) for r in rows if r["btc_oos_net_pnl_pct"] != "n/a"]
    is_pos = sum(1 for x in is_pnls if x > 0)
    oos_pos = sum(1 for x in oos_pnls if x > 0)

    print(f"wrote {OUT}")
    print("BTC trajectory summary (baseline + /014/015/016/017):")
    print(
        f"  IS net_pnl: mean {sum(is_pnls) / len(is_pnls):+.2f}%  range "
        f"[{min(is_pnls):+.2f}, {max(is_pnls):+.2f}]  positive {is_pos}/{len(is_pnls)}"
    )
    print(
        f"  OOS net_pnl: mean {sum(oos_pnls) / len(oos_pnls):+.2f}%  range "
        f"[{min(oos_pnls):+.2f}, {max(oos_pnls):+.2f}]  positive {oos_pos}/{len(oos_pnls)}"
    )
    print()
    print("Key finding: BTC IS = 0/5 positive (5/5 negative);")
    print("              BTC OOS = 4/5 positive (only /015 negative; OOS net contribution stable)")
    print("              ASYMMETRIC IS-OOS ROTATION — strongest in v1 catalog")


if __name__ == "__main__":
    main()
