"""exp-002 — data audit / EDA only. No strategy evaluated, no Sharpe read.
Universe shape, ragged starts, sector histogram, eligible-name counts vs history requirement."""

import sys

sys.path.insert(0, "analysis/portfolio/tradfi")
sys.path.insert(0, "tournament/tradfi/teams/team-01")

import pandas as pd

import scratch_common as sc

pn, view, aux = sc.load()
close = view["close"]
print(f"panel shape: {close.shape}  index {close.index[0].date()} .. {close.index[-1].date()}")
print(f"tickers: {len(close.columns)}")

first = close.apply(lambda s: s.first_valid_index())
counts = first.groupby(first.dt.year).count()
print("\nfirst-valid year histogram:")
print(counts.to_string())

late = first[first > pd.Timestamp("2015-01-01")].sort_values()
print(f"\nnames starting after 2015 ({len(late)}):")
print(late.to_string())

sec = pd.Series(aux["sector_map"])
print("\nsector histogram:")
print(sec.value_counts().to_string())

vix = aux["vix"]
print(f"\nVIX: {vix.index[0].date()} .. {vix.index[-1].date()}  n={len(vix)}")

ret = sc.daily_returns(view)
for need in (273, 378, 504):
    elig = (ret.notna().rolling(need, min_periods=need).sum() == need).sum(axis=1)
    q = elig.resample("YE").last()
    print(f"\n#names with >= {need}d continuous return history (year-end):")
    print(q.to_string())
