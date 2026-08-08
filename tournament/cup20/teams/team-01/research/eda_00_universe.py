"""Team-01 EDA step 0 -- characterise the IS snapshot's universe and decision grid.

NOT a scorer. This file computes no return series, no Sharpe, no drawdown and no cost. It
describes the data the organiser's runner will stream, so the strategy is designed against the
right shape of problem. Every performance number team-01 acts on comes from
``scripts/cup20_evaluate.py``.
"""

from __future__ import annotations

import pandas as pd

from crypto_trade.cup20.config import IS_END, load_config
from crypto_trade.cup20.runner import decision_grid
from crypto_trade.cup20.snapshot import load_snapshot, resolve_is_start
from crypto_trade.tournament.data import eligible_at

CONFIG = load_config("tournament/cup20/config.toml").raw


def main() -> None:
    snapshot = load_snapshot(CONFIG["data"]["is_root"])
    membership = snapshot.membership
    bars = snapshot.bars

    is_start = resolve_is_start(membership, target_size=int(CONFIG["universe"]["target_size"]))
    grid = decision_grid(is_start, IS_END, interval_hours=8)
    print(f"IS_START           {is_start}")
    print(f"decision boundaries {len(grid)}  ({len(grid) / (365 * 3):.2f} years)")

    recon = sorted(membership["reconstitution_time"].unique())
    print(f"reconstitutions    {len(recon)}  first {recon[0]}  last {recon[-1]}")
    sizes = membership.groupby("reconstitution_time").size()
    print(f"members per recon  min {sizes.min()} median {sizes.median()} max {sizes.max()}")

    # Eligible = point-in-time member AND has an executable open at the boundary.
    open_syms = {
        pd.Timestamp(t): frozenset(g["symbol"])
        for t, g in bars.groupby("open_time", observed=True, sort=False)
    }
    counts = []
    all_members: set[str] = set()
    prev: frozenset[str] = frozenset()
    churn = 0
    for t in grid:
        elig = frozenset(s for s in eligible_at(membership, t) if s in open_syms.get(t, frozenset()))
        counts.append(len(elig))
        all_members |= elig
        if prev:
            churn += len(elig ^ prev)
        prev = elig
    series = pd.Series(counts, index=pd.DatetimeIndex(grid))
    print(f"eligible per boundary  min {series.min()} median {series.median()} max {series.max()}")
    print(f"distinct symbols ever eligible  {len(all_members)}")
    print(f"total one-sided membership changes across grid  {churn}")
    print("\neligible count, quarterly mean:")
    print(series.groupby(series.index.tz_convert('UTC').tz_localize(None).to_period('Q')).mean())

    # How long does a symbol stay in the universe once it enters?
    spans: dict[str, int] = {}
    for t in grid:
        for s in eligible_at(membership, t):
            spans[s] = spans.get(s, 0) + 1
    tenure = pd.Series(spans).sort_values(ascending=False) / 3.0  # boundaries -> days
    print("\nmember tenure in days (top 25):")
    print(tenure.head(25).to_string())
    print(f"\nsymbols with < 180d tenure: {(tenure < 180).sum()} of {len(tenure)}")


if __name__ == "__main__":
    main()
