"""EDA 06 - lane integrity: is channel position just cross-sectional momentum in disguise?

Three tests:
  T1 how correlated, cross-sectionally, is rank(u_N) with rank(N-bar return)?
  T2 does a book built on the part of u_N that is ORTHOGONAL to the N-bar return still work?
  T3 does a book built on the N-bar return alone work, and how do the two compare?
If the whole edge lives in the momentum component, this candidate has drifted out of the lane.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-02/research")
from eda05_designs import cadence, cl, hi, index, lo, mask, rank_weights, show, topk_weights  # noqa: E402
from eda_panel import channel_position  # noqa: E402


def xs_rank(s: pd.DataFrame) -> pd.DataFrame:
    r = s.where(mask).rank(axis=1, pct=True)
    return r.sub(r.mean(axis=1), axis=0)


def residualise(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    """Row-wise OLS residual of rank(a) on rank(b)."""
    ra, rb = xs_rank(a), xs_rank(b)
    cov = (ra * rb).sum(axis=1)
    var = (rb * rb).sum(axis=1)
    beta = cov / var.where(var > 0)
    return ra.sub(rb.mul(beta, axis=0))


for N in (126, 189, 252, 378):
    u = channel_position(hi, lo, cl, N)
    mom = cl / cl.shift(N) - 1.0
    ru, rm = xs_rank(u), xs_rank(mom)
    num = (ru * rm).sum(axis=1)
    den = np.sqrt((ru**2).sum(axis=1) * (rm**2).sum(axis=1))
    rho = (num / den.where(den > 0)).dropna()
    rho = rho[rho.index >= pd.Timestamp("2020-08-17T00:00:00Z")]
    print(f"N={N:3d}  cross-sectional rank corr(u, {N}-bar return): "
          f"mean={rho.mean():.3f} p10={rho.quantile(0.1):.3f} p90={rho.quantile(0.9):.3f}")

print()
for N in (189, 252):
    u = channel_position(hi, lo, cl, N)
    mom = cl / cl.shift(N) - 1.0
    resid = residualise(u, mom)
    for c in (21,):
        show(f"[u]        N={N} cad={c}", rank_weights(u), cadence(c))
        show(f"[mom]      N={N} cad={c}", rank_weights(mom), cadence(c))
        show(f"[u|mom]    N={N} cad={c}", rank_weights(resid), cadence(c))
        show(f"[u]  top3  N={N} cad={c}", topk_weights(u, 3), cadence(c))
        show(f"[mom]top3  N={N} cad={c}", topk_weights(mom, 3), cadence(c))
        show(f"[u|mom]top3 N={N} cad={c}", topk_weights(resid, 3), cadence(c))
    print()
