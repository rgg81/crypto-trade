"""EDA 1 -- does the shock signature condition the reversal, or is magnitude enough?

Question: after a large 8h move, is the subsequent short-horizon reversal LARGER when the move
carried a liquidity-shock signature (range far beyond its own scale, volume/trade-count spike,
elevated impact per unit of flow) than when it did not?

Free research. No trial. No floor is computed here.
"""

from __future__ import annotations

import sys

import numpy as np

sys.path.insert(0, "tournament/cup20/teams/team-05/research")

from panel import build_panel, demean, forward_from_open, summarise  # noqa: E402

P = build_panel(lookback=60)
op = P["open"]
mask = P["tradable"]
fwd = forward_from_open(op, horizons=(1, 2, 3, 6))
# idiosyncratic forward return: remove the equal-weight member basket at each boundary
fwd_i = {h: demean(f, mask) for h, f in fwd.items()}

z = P["z"].where(mask)
rr = P["rr"].where(mask)
vs = P["vspike"].where(mask)
ts = P["tspike"].where(mask)
imp = P["impact"].where(mask)

print("=" * 100)
print("Panel coverage")
print("=" * 100)
print(f"boundaries: {len(op)}  first={op.index[0]}  last={op.index[-1]}")
print(f"tradable symbol-bars: {int(mask.sum().sum())}")
print(f"median members per boundary: {mask.sum(axis=1).median()}")

print()
print("=" * 100)
print("A. Unconditional reversal by |z| bucket (z = 8h return / trailing 60-bar sigma)")
print("   value shown = mean of  -sign(z) * idiosyncratic forward return")
print("=" * 100)
buckets = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 100)]
for h in (1, 2, 3, 6):
    print(f"-- horizon {h} bars ({h * 8}h)")
    for lo, hi in buckets:
        sel = (z.abs() >= lo) & (z.abs() < hi)
        rev = (-np.sign(z) * fwd_i[h]).where(sel)
        print("   " + summarise(f"|z| in [{lo},{hi})", rev.to_numpy().ravel()))

print()
print("=" * 100)
print("B. Conditioning: |z| >= 2.5, split by shock-signature terciles")
print("=" * 100)
big = z.abs() >= 2.5
for label, sig in (("range/scale rr", rr), ("volume spike", vs), ("tradecount spike", ts),
                   ("impact rr/vspike", imp)):
    vals = sig.where(big)
    q1, q2 = np.nanquantile(vals.to_numpy(), [1 / 3, 2 / 3])
    print(f"-- {label}: terciles at {q1:.2f} / {q2:.2f}")
    for tag, sel in (
        ("low   ", big & (sig <= q1)),
        ("mid   ", big & (sig > q1) & (sig <= q2)),
        ("high  ", big & (sig > q2)),
    ):
        for h in (1, 3):
            rev = (-np.sign(z) * fwd_i[h]).where(sel)
            print("   " + summarise(f"{tag} h={h}", rev.to_numpy().ravel()))

print()
print("=" * 100)
print("C. The ablation preview: magnitude-only vs magnitude+signature, matched event count")
print("=" * 100)
for h in (1, 2, 3):
    # magnitude-only: top-N |z| events overall
    zz = z.abs().to_numpy().ravel()
    thresh = np.nanquantile(zz, 0.98)
    sel_mag = z.abs() >= thresh
    n_mag = int(sel_mag.sum().sum())
    rev_mag = (-np.sign(z) * fwd_i[h]).where(sel_mag)
    print("   " + summarise(f"magnitude-only  h={h} (|z|>={thresh:.2f})",
                            rev_mag.to_numpy().ravel()))
    # magnitude+signature: same count, but requires the signature too
    comb = (z.abs() >= 2.0) & (rr >= 1.8) & (vs >= 2.0)
    rev_comb = (-np.sign(z) * fwd_i[h]).where(comb)
    print("   " + summarise(f"mag+signature   h={h} (n target {n_mag})",
                            rev_comb.to_numpy().ravel()))
