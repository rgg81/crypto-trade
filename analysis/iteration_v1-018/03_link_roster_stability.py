"""LINK trade roster stability across iterations — iter-v1/018 EDA.

Tests the "LINK structural OOS edge" claim by measuring trade roster overlap
of LINK trades across /011-/017. If LINK trades are highly stable (same trade
roster, same direction, similar PnL) across 7 iterations spanning multiple
axis families (sample-weighting, universe, R5, labeling, etc.), then LINK's
OOS performance is NOT being lifted by any axis specifically — it is the
unperturbed signal-discovery dimension that pool training has bought into.

If LINK trades VARY a lot across iterations, then LINK's profit isn't
structural — it's noise that happens to land positive.

The HYPOTHESIS-DEFINING question:
- structural edge → high roster overlap + consistent OOS positive
- noise → low roster overlap + variable PnL with positive mean

Outputs:
- link_roster_overlap.csv : pairwise LINK trade-roster overlap across iters
- link_pnl_consistency.csv : LINK PnL per iter vs trade-count
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis" / "iteration_v1-018"

# Iterations to compare. Baseline = /011-/017 + iter-baseline.
ITERS = [
    ("baseline", "iteration_v1-baseline"),
    ("011", "iteration_v1-011"),
    ("012", "iteration_v1-012"),
    ("013", "iteration_v1-013"),
    ("014", "iteration_v1-014"),
    ("015", "iteration_v1-015"),
    ("016", "iteration_v1-016"),
    ("017", "iteration_v1-017"),
]


def load_link(iter_path: Path) -> pd.DataFrame | None:
    p_oos = iter_path / "out_of_sample" / "trades.csv"
    if not p_oos.exists():
        return None
    d = pd.read_csv(p_oos)
    return d[d["symbol"] == "LINKUSDT"].copy()


def main() -> None:
    iter_data: dict[str, pd.DataFrame] = {}
    for label, dirname in ITERS:
        ip = ROOT / "reports-v1" / dirname
        link_df = load_link(ip)
        if link_df is not None:
            iter_data[label] = link_df

    print("LINK OOS trade rosters loaded:")
    for label, df in iter_data.items():
        print(f"  {label}: n={len(df)}  net_pnl={df['net_pnl_pct'].sum():+.4f}  "
              f"longs={(df['direction']==1).sum()}  shorts={(df['direction']==-1).sum()}")

    # 1. Pairwise roster overlap (open_time-based, since open_time is the
    #    "trade identity" — same open_time = same trade execution candle).
    # Quantify roster-stability against the baseline.
    rows = []
    base_open_times = set(iter_data["baseline"]["open_time"].tolist())
    for label, df in iter_data.items():
        this_open_times = set(df["open_time"].tolist())
        n_baseline = len(base_open_times)
        n_this = len(this_open_times)
        intersect = base_open_times & this_open_times
        union = base_open_times | this_open_times
        overlap_pct = len(intersect) / max(n_baseline, 1)
        jaccard = len(intersect) / max(len(union), 1)
        rows.append(
            dict(
                iter=label,
                n_trades_baseline=n_baseline,
                n_trades_this=n_this,
                overlap_with_baseline=len(intersect),
                overlap_pct_of_baseline=round(overlap_pct, 4),
                jaccard=round(jaccard, 4),
                net_pnl_this=round(df["net_pnl_pct"].sum(), 4),
                avg_pnl_this=round(df["net_pnl_pct"].mean(), 4),
                win_rate_this=round((df["net_pnl_pct"] > 0).mean(), 4),
            )
        )
    overlap_df = pd.DataFrame(rows)
    op = OUT / "link_roster_overlap.csv"
    overlap_df.to_csv(op, index=False)
    print(f"\n[1] LINK OOS roster overlap vs baseline → {op}")
    print(overlap_df.to_string(index=False))

    # 2. Coefficient of variation of LINK PnL across iters
    pnls = [df["net_pnl_pct"].sum() for _, df in iter_data.items()]
    import statistics
    mean_pnl = statistics.mean(pnls)
    std_pnl = statistics.stdev(pnls) if len(pnls) > 1 else 0
    cv = std_pnl / abs(mean_pnl) if mean_pnl else float("nan")
    print(f"\n[Stats] LINK OOS PnL across {len(pnls)} iters: "
          f"mean={mean_pnl:+.4f}  std={std_pnl:.4f}  CV={cv:.4f}  "
          f"min={min(pnls):+.4f}  max={max(pnls):+.4f}")
    print(f"        ALL positive: {all(p > 0 for p in pnls)}")
    print(f"        Sign consistency: {sum(p > 0 for p in pnls)}/{len(pnls)} positive")


if __name__ == "__main__":
    main()
