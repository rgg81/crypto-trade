"""Read the offline sweep CSVs and print the views the design decision actually needs."""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 400)
ROOT = "tournament/cup20/teams/team-11/research/"
COLS = ["config", "sharpe_1x", "sharpe_2x", "vol_1x", "dd_1x", "dd_2x", "turnover", "gross_edge",
        "trades", "F1", "F2", "F3", "F4", "worst", "median_fold", "npos",
        "long_gross", "short_gross"]


def g_score(row) -> float:
    def c(x):
        return min(1.0, max(0.0, x))
    return (30 * c((row.worst + 0.25) / 1.00)
            + 20 * c((row.median_fold - 0.25) / 0.75)
            + 20 * c((0.20 - row.dd_2x) / 0.15)
            + 15 * c((row.ret_2x / row.dd_2x if row.dd_2x > 0 else 0.0) / 1.50))


def main() -> None:
    name = sys.argv[1]
    d = pd.read_csv(ROOT + name)
    d["G_partial"] = [g_score(r) for r in d.itertuples()]
    print(f"{name}: {len(d)} configs")
    print("\n=== top 25 by partial G (85 of 100 points: folds + drawdown + calmar) ===")
    print(d.sort_values("G_partial", ascending=False).head(25)[COLS + ["G_partial"]].to_string(
        index=False, float_format="%.3f"))
    print("\n=== top 20 by worst fold ===")
    print(d.sort_values("worst", ascending=False).head(20)[COLS + ["G_partial"]].to_string(
        index=False, float_format="%.3f"))
    if "variant" in d.columns:
        print("\n=== medians across the phase surface, per variant x window ===")
        print(d.groupby(["variant", "W"])[
            ["sharpe_1x", "sharpe_2x", "dd_1x", "worst", "median_fold", "turnover",
             "gross_edge", "long_gross", "short_gross", "G_partial"]
        ].median().to_string(float_format="%.3f"))
        print("\n=== full weekly phase surface, worst-fold 2x ===")
        for (v, W), g in d[d.cadence == 21].groupby(["variant", "W"]):
            g = g.sort_values("phase")
            print(f"{v:<14} W={W}: " + " ".join(
                f"{int(r.phase):>2}:{r.worst:>+5.2f}" for r in g.itertuples()))
        print("\n=== full weekly phase surface, 1x Sharpe ===")
        for (v, W), g in d[d.cadence == 21].groupby(["variant", "W"]):
            g = g.sort_values("phase")
            print(f"{v:<14} W={W}: " + " ".join(
                f"{int(r.phase):>2}:{r.sharpe_1x:>+5.2f}" for r in g.itertuples()))
            arr = g.sharpe_1x.to_numpy()
            print(f"{'':<14}        mean {arr.mean():+.3f}  sd {arr.std(ddof=1):.3f}  "
                  f"min {arr.min():+.3f}  max {arr.max():+.3f}")
    if "signal" in d.columns:
        print("\n=== medians by signal / quantity / window / power / cadence ===")
        print(d.groupby(["signal", "quantity", "W", "power", "cadence"])[
            ["sharpe_1x", "sharpe_2x", "dd_1x", "worst", "median_fold", "turnover",
             "gross_edge", "short_gross"]
        ].median().to_string(float_format="%.3f"))


if __name__ == "__main__":
    main()
