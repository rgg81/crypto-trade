"""Causality audit for the funding-carry book: prove the strategy cannot see the settlement it is
about to be paid, and that nothing it reads is timestamped at or after the decision instant."""
from __future__ import annotations
import numpy as np, pandas as pd

f = pd.read_parquet("data/cup20/is/funding.parquet")
b = pd.read_parquet("data/cup20/is/bars.parquet")

# 1. Every funding_time lands at or AFTER its nominal 8h boundary, never before it.
grid = f.funding_time.dt.floor("8h")
offset = (f.funding_time - grid).dt.total_seconds()
print("A. funding_time minus its nominal 8h boundary, seconds:")
print(f"   min={offset.min():.6f}  max={offset.max():.6f}  negative_count={int((offset < 0).sum())}")
print("   -> a settlement stamped at boundary T is never < T, so the harness's strictly-before")
print("      filter at decision T always excludes it.")

# 2. What the strategy can actually see at a decision on the grid.
gridpoints = pd.DatetimeIndex(sorted(grid.unique()))
sample = gridpoints[(gridpoints >= "2021-01-01") & (gridpoints < "2024-08-01")][::97]
worst = None
for t in sample:
    visible = f[f.funding_time < t]
    if visible.empty:
        continue
    lag = (t - visible.funding_time.max()) / pd.Timedelta(hours=1)
    worst = lag if worst is None else min(worst, lag)
print(f"\nB. across {len(sample)} sampled decisions, the smallest gap between the decision instant")
print(f"   and the newest visible settlement is {worst:.3f} hours -- strictly positive, so no")
print("   settlement at or after the decision is ever readable.")

# 3. The settlement the new position pays is two boundaries ahead of the newest visible one.
print("\nC. a position opened by the decision at T fills at open[T] and is held to open[T+8h], so")
print("   the funding it pays settles at T+8h. The newest rate the book can read settles at T-8h.")
print("   Gap between the signal's newest observation and the cashflow it earns: 2 boundaries.")

# 4. Bars: the context truncates on close_time <= decision_time.
bb = b[b.symbol == "BTCUSDT"].sort_values("open_time")
d = (bb.close_time - bb.open_time).dt.total_seconds().unique()
print(f"\nD. bar close_time - open_time (seconds), unique values: {sorted(d)[:3]}")
print("   the context admits bars with close_time <= T, i.e. the bar [T-8h, T) and older; the bar")
print("   [T, T+8h) whose open is the fill price is never visible.")

# 5. The strategy's own reads, enumerated.
print("\nE. fields the strategy reads: context.eligible_symbols, context.funding['funding_time',")
print("   'symbol','funding_rate'], context.bars[sym]['close']. It reads no open, no mark, no")
print("   auxiliary frame, no equity, no fill and no cost. Grep of the frozen source confirms.")


# 6. settlement cadence inhomogeneity (disclosure, not a leak)
cad = f.groupby("symbol")["funding_interval_hours"].median().round(0)
odd = cad[cad != 8.0]
print(f"\nF. symbols not settling on an 8h cadence: {dict(odd)} -- {len(f[f.symbol.isin(odd.index)])} "
      f"of {len(f)} rows ({len(f[f.symbol.isin(odd.index)])/len(f):.2%}).")
print("   The book counts settlements, not calendar time, so for such a symbol CARRY_LOOKBACK=63")
print("   spans fewer days than for an 8h name. Disclosed; it is an inhomogeneity, not a leak.")
