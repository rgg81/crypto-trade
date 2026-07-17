"""team-04 scratch — NON-MATERIAL data inspection (no strategy is run, no PnL is read).

Purpose: ground the pre-registered experiment grid in the panel's actual shape —
name count over time, ragged starts, how many names have >= formation+skip history,
VIX availability. Documented in provenance.md.
"""

import sys

sys.path.insert(0, "analysis/portfolio/tradfi")
from tournament import engine as te  # noqa: E402

pn, aux = te.load_is_panels()
view = te.team_view(pn)

close = view["close"]
print(f"panel shape: {close.shape}  (rows x tickers)")
print(f"date range : {close.index.min().date()} .. {close.index.max().date()}")
print(f"tickers    : {len(close.columns)}")

valid = close.notna()
counts = valid.sum(axis=1)
for y in range(2010, 2025):
    sub = counts[str(y)]
    if len(sub):
        print(f"  {y}: names with a bar — min {int(sub.min())}, median {int(sub.median())}, max {int(sub.max())}")

# names with enough history for a 252+21d formation signal at each year-end
c = close.ffill()
mom_ok = (close.notna() & c.shift(273).notna())
mcounts = mom_ok.sum(axis=1)
print("\nnames with >=273d history (252 formation + 21 skip):")
for y in range(2010, 2025):
    sub = mcounts[str(y)]
    if len(sub):
        print(f"  {y}: min {int(sub.min())}, median {int(sub.median())}, max {int(sub.max())}")

vix = aux["vix"]
print(f"\nVIX: {'present' if vix is not None else 'ABSENT'}", end="")
if vix is not None:
    print(f", {vix.index.min().date()} .. {vix.index.max().date()}, n={len(vix)}")
sectors = sorted(set(aux["sector_map"].values()))
print(f"sectors ({len(sectors)}): {sectors}")
print(f"seed: {aux['seed']}")
