"""EDA 12 -- would a declared position stop help, or would it cut the best bounces?

Drawdown control is 35 of the 100 ranking points and the nominee earns 4.3 of them, so a declared
risk control is the largest single lever left. Two candidates, and they behave oppositely:

  * a DRAWDOWN BRAKE cuts book gross after the book has lost. For this book that is pro-cyclical
    against its own edge -- a cascade IS a drawdown event for a long book, so the brake would
    de-risk precisely when the next opportunity arrives. Rejected on mechanism, before measuring.
  * a POSITION STOP cuts one position that has gone against the entry by more than a fraction,
    and leaves the opportunity set alone. Whether it helps is an empirical question about what
    happens NEXT to a cascade name that is already deeply under water, and that is measurable.

So: for every qualifying event, split by how the first held bar went, and look at what the
remaining held bars did. If the deep losers keep losing, a stop pays. If they bounce hardest, it
does not, and the trial is better spent elsewhere.

Approximation, not a scorer.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-05/research")

from panel import build_panel, summarise  # noqa: E402

P = build_panel(lookback=60)
op, ret, sigma = P["open"], P["ret"], P["sigma"]
mask = P["tradable"]
z = (ret / sigma).where(mask)
ts = P["tspike"].where(mask)
bar = (op.shift(-1) / op - 1.0).where(mask)

qual = ((z <= -2.0) & (ts >= 2.0)).fillna(False)
cascade = qual.sum(axis=1) >= 2
CASC = pd.DataFrame(np.repeat(cascade.to_numpy()[:, None], z.shape[1], axis=1),
                    index=z.index, columns=z.columns)
# the basket is the deepest fallers on a cascade bar, so approximate it with the deep names
depth = (-z).where(z < 0)
rank = depth.where(CASC).rank(axis=1, ascending=False)
sel = CASC & (rank <= 8)

# held bars, relative to the shock bar i: k=2, k=3, k=4 (entry at open of bar i+2)
b2 = bar.shift(-2).where(sel)
b3 = bar.shift(-3).where(sel)
b4 = bar.shift(-4).where(sel)

print("=" * 96)
print("What happens to a cascade name AFTER its first held bar, split by that bar's return")
print("entry at open of bar i+2; the position's return after one bar is exactly bar i+2")
print("=" * 96)
edges = [(-1.0, -0.10), (-0.10, -0.06), (-0.06, -0.03), (-0.03, 0.0), (0.0, 0.03), (0.03, 1.0)]
for lo, hi in edges:
    band = (b2 >= lo) & (b2 < hi)
    rest = (1 + b3.where(band)) * (1 + b4.where(band)) - 1
    print(f"  first bar in [{lo:>6.2f},{hi:>5.2f})  "
          + summarise("remaining 2 bars", rest.to_numpy().ravel()))

print()
print("=" * 96)
print("Same, two bars in: what does bar i+4 do after the position is down over two bars?")
print("=" * 96)
cum2 = (1 + b2) * (1 + b3) - 1
for lo, hi in edges:
    band = (cum2 >= lo) & (cum2 < hi)
    print(f"  two-bar return in [{lo:>6.2f},{hi:>5.2f})  "
          + summarise("final bar", b4.where(band).to_numpy().ravel()))

print()
print("=" * 96)
print("Counterfactual: episode return with and without a stop at various loss fractions")
print("(per-name, equal weight; a stopped name earns nothing further)")
print("=" * 96)
full = ((1 + b2) * (1 + b3) * (1 + b4) - 1)
base = full.to_numpy().ravel()
base = base[np.isfinite(base)]
print(f"  no stop                          mean={base.mean() * 1e4:>8.1f}bp  n={base.size}")
for lf in (0.05, 0.08, 0.10, 0.12, 0.15, 0.20):
    after1 = np.where(b2 <= -lf, b2, np.nan)
    stopped1 = pd.DataFrame(after1, index=b2.index, columns=b2.columns)
    survive1 = b2.where(b2 > -lf)
    cum = (1 + survive1) * (1 + b3) - 1
    stopped2 = cum.where(cum <= -lf)
    survive2 = cum.where(cum > -lf)
    final = (1 + survive2) * (1 + b4) - 1
    combined = stopped1.fillna(0.0) * 0 + np.nan
    combined = pd.concat([stopped1.stack(), stopped2.stack(), final.stack()]).groupby(level=[0, 1]).first()
    arr = combined.to_numpy()
    arr = arr[np.isfinite(arr)]
    hits = int(np.isfinite(stopped1.to_numpy()).sum() + np.isfinite(stopped2.to_numpy()).sum())
    print(f"  stop at -{lf:.2f}                     mean={arr.mean() * 1e4:>8.1f}bp  n={arr.size}"
          f"  stops fired={hits}")
