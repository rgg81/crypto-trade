"""EDA 04 - the mandate's own question: what separates a break that carries from one that snaps back?

Event set: a coin whose close set a new N-bar high (or low) within the last M bars.
Conditioners tested, all range-structure statements with no rate-of-change analogue:
  C1 coil      - channel width (H_n - L_n) / (ATR_14 * sqrt(n)); a narrow channel is coiled.
  C2 hold      - current channel position u; after an up-breach, u ~ 1 means the break held,
                 u < 0.5 means price fell back inside the range (a FAILED break).
  C3 level age - bars since the breached extreme was originally set.
  C4 breach    - how far past the level, in ATR units, the breach ran at its furthest.
Forward statistic is the total return to a LONG over the next H bars: price return minus funding.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-02/research")
from eda_panel import eligibility_mask, load_panel, true_range, wide  # noqa: E402
from eda_sim import funding_matrix  # noqa: E402

bars, membership, funding = load_panel()
op, hi, lo, cl = (wide(bars, c) for c in ("open", "high", "low", "close"))
index, cols = cl.index, cl.columns
mask = eligibility_mask(membership, index, cols) & op.notna()
fund = funding_matrix(funding, index, cols)
START = pd.Timestamp("2020-08-17T00:00:00Z")
sel = index >= START

atr = true_range(hi, lo, cl).ewm(alpha=1 / 42, min_periods=42).mean()

N = int(sys.argv[1]) if len(sys.argv) > 1 else 126
M = int(sys.argv[2]) if len(sys.argv) > 2 else 9
H = int(sys.argv[3]) if len(sys.argv) > 3 else 9

hh = hi.rolling(N, min_periods=N).max()
ll = lo.rolling(N, min_periods=N).min()
prior_hh = hh.shift(1)
prior_ll = ll.shift(1)
width = (hh - ll)
u = ((cl - ll) / width.where(width > 0)).clip(0, 1)

up_breach = cl > prior_hh                      # close cleared the trailing N-bar high
dn_breach = cl < prior_ll
recent_up = up_breach.rolling(M, min_periods=1).max().astype(bool)
recent_dn = dn_breach.rolling(M, min_periods=1).max().astype(bool)

coil = width / (atr * np.sqrt(N))
# bars since the channel high was last set
argmax_age = hi.rolling(N, min_periods=N).apply(lambda a: len(a) - 1 - int(np.argmax(a)), raw=True)

fwd = op.shift(-(1 + H)) / op.shift(-1) - 1.0
fnd_fwd = fund.shift(-1).rolling(H).sum().shift(-(H - 1))
long_total = fwd - fnd_fwd
ann = 1095 / H

base = mask & sel[:, None] & long_total.notna() & u.notna()
mkt = long_total.where(base).stack().mean() * ann
print(f"N={N} M={M} H={H}.  universe long total return ann = {mkt:.4f} "
      f"(n={int(base.sum().sum())})")


def report(name, cond):
    c = cond & base
    n = int(c.sum().sum())
    if n < 200:
        print(f"  {name:38s} n={n:6d}   --")
        return
    v = long_total.where(c).stack()
    se = v.std() / np.sqrt(len(v)) * ann
    print(f"  {name:38s} n={n:6d}  long_ann={v.mean() * ann: .4f} (+-{se:.3f})  "
          f"vs mkt {v.mean() * ann - mkt:+.4f}")


print(" -- upside breach within last M bars --")
report("all recent up-breach", recent_up)
report("  held  (u >= 0.90)", recent_up & (u >= 0.90))
report("  faded (u <  0.50)  FAILED BREAK", recent_up & (u < 0.50))
report("  faded (u <  0.70)", recent_up & (u < 0.70))
for lo_q, hi_q in ((0, 0.33), (0.33, 0.67), (0.67, 1.01)):
    cq = coil.where(base).stack().quantile([lo_q, min(hi_q, 1.0)]).to_numpy()
    band = (coil >= cq[0]) & (coil < cq[1] if hi_q <= 1 else True)
    report(f"  coil in [{lo_q:.2f},{hi_q:.2f}) tercile", recent_up & band)
for a, b in ((0, N // 4), (N // 4, N // 2), (N // 2, N)):
    report(f"  level age in [{a},{b})", recent_up & (argmax_age >= a) & (argmax_age < b))

print(" -- downside breach within last M bars --")
report("all recent down-breach", recent_dn)
report("  held  (u <= 0.10)", recent_dn & (u <= 0.10))
report("  faded (u >  0.50)  FAILED BREAK", recent_dn & (u > 0.50))
report("  faded (u >  0.30)", recent_dn & (u > 0.30))

print(" -- plain channel-position terciles (no breach condition) --")
report("u < 0.25", u < 0.25)
report("0.25 <= u < 0.75", (u >= 0.25) & (u < 0.75))
report("u >= 0.75", u >= 0.75)
report("u >= 0.95", u >= 0.95)
