"""iter-v1/028 Phase 1 — Diagnose iter-027's OOS concentration (the problem to beat).

Reads the COMMITTED iter-027 trades (IS + OOS). The OOS read here is for *post-mortem
diagnosis of the merged baseline's known property*, NOT for design/calibration of the
new model — it quantifies the falsifier the new model must pass. No new model parameter
is tuned on these numbers.

Outputs: diag_027_concentration.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from _common import concentration_stats  # noqa: E402

REPORTS = Path("reports-v1/ETHUSDT/iteration_v1-027")
OUT = Path(__file__).parent


def summarize(trades: pd.DataFrame, tag: str) -> dict:
    net = trades["net_pnl_pct"].values
    cs = concentration_stats(net)
    # per-month concentration
    tr = trades.copy()
    tr["month"] = pd.to_datetime(tr["close_time"], unit="ms").dt.to_period("M").astype(str)
    by_month = tr.groupby("month")["net_pnl_pct"].sum()
    net_sum = net.sum()
    top_month_share = by_month.max() / net_sum if net_sum > 0 else np.nan
    # exit-reason mix (let-winners-run => most exits are timeout)
    exit_mix = tr["exit_reason"].value_counts(normalize=True).to_dict()
    # direction mix
    dir_mix = tr["direction"].value_counts(normalize=True).to_dict()
    row = {"window": tag, **cs, "top_month_share_of_net": top_month_share}
    row["pct_timeout_exit"] = exit_mix.get("timeout", 0.0)
    row["pct_long"] = dir_mix.get("long", dir_mix.get(1, 0.0))
    return row


def main() -> None:
    rows = []
    for tag, sub in [("IS", "in_sample"), ("OOS", "out_of_sample")]:
        p = REPORTS / sub / "trades.csv"
        if not p.exists():
            print(f"missing {p}")
            continue
        trades = pd.read_csv(p)
        rows.append(summarize(trades, tag))
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "diag_027_concentration.csv", index=False)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)
    print("=== iter-027 trade-distribution concentration (the baseline to BEAT) ===")
    print(out.to_string(index=False))
    print()
    print("READ: low WR + high top-1/top-2 share + ~all-timeout exits = let-winners-run.")
    print("The new iter-028 model must INVERT this: higher WR, lower top-1/top-2 share,")
    print("more winners, NOT all-timeout (mean-reversion + meta-filter => many small wins).")


if __name__ == "__main__":
    main()
