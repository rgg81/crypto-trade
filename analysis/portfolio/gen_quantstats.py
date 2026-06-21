"""Generate quantstats HTML tearsheets for baseline-v1 and baseline-v2, split IS / OOS / full.

v1 = trend+carry walk-forward-λ         = banded_net(book, δ=0.0,  "snap")  (δ=0 == iter_005)
v2 = v1 + hysteresis-banding (PROMOTED) = banded_net(book, δ=0.010,"snap")
Per-8h-candle net -> daily compounded returns -> quantstats (periods_per_year=365 crypto).
Output: reports/portfolio/quantstats/<baseline>_<segment>.html
"""

from __future__ import annotations

import os
import sys
import warnings

import pandas as pd
import quantstats as qs

sys.path.insert(0, "analysis/portfolio")
import iter_002_top20 as base  # noqa: E402
import iter_020_hysteresis as hy  # noqa: E402

warnings.filterwarnings("ignore")
OOS_CUTOFF = pd.Timestamp("2025-03-24")
OUT = "reports/portfolio/quantstats"


def to_daily(net: pd.Series) -> pd.Series:
    s = net.dropna().copy()
    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index, unit="ms")
    return ((1 + s).resample("1D").prod() - 1).dropna()


def main() -> None:
    import iter_021_eligexit as ee
    os.makedirs(OUT, exist_ok=True)
    coins = base.load_universe()
    book = hy.canonical_book(coins, hy.build_books(coins))
    elig = ee.eligibility_mask(coins, book["target_w"])
    nets = {
        "baseline_v1_trend_carry": hy.banded_net(book, 0.0, "snap"),
        "baseline_v2_trend_carry_hysteresis": hy.banded_net(book, 0.010, "snap"),
        "baseline_v3_eligibility_exit": ee.eligexit_net(book, elig, 2, 0.010, "snap"),  # K=2
    }
    for name, net in nets.items():
        d = to_daily(net)
        segments = {
            "IS": d[d.index < OOS_CUTOFF],
            "OOS": d[d.index >= OOS_CUTOFF],
            "FULL": d,
        }
        for seg, r in segments.items():
            out = f"{OUT}/{name}_{seg}.html"
            title = f"{name.replace('_', ' ')} — {seg}"
            qs.reports.html(r, benchmark=None, output=out, title=title, periods_per_year=365)
            ann = float(r.mean() / r.std() * (365 ** 0.5)) if r.std() > 0 else float("nan")
            print(f"  wrote {out}  ({len(r)} days {r.index.min().date()}..{r.index.max().date()}, "
                  f"daily-Sharpe(365)={ann:+.2f})")


if __name__ == "__main__":
    main()
