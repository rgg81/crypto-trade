"""EDA 1 -- does a causal market component exist, and is its loading dispersed?

If every top-20 name loaded on the market with the same beta, residualising would be an
elaborate way of cross-sectionally demeaning, and the lane would be a no-op. This measures:
  * the share of pooled 8h return variance the first cross-sectional factor explains;
  * the cross-sectional dispersion of rolling causal betas;
  * how much residualisation actually moves the cross-sectional RANK vector.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-04/research")
from panel import load_panel, log_returns  # noqa: E402

P = load_panel()
grid = P["grid"]
elig = P["eligible"]
r = log_returns(P["closes"])
r[~elig] = np.nan  # only member rows carry information we are allowed to rank on

start = grid.searchsorted(P["is_start"])
print(f"grid {grid[0]} .. {grid[-1]}   rows={len(grid)}  is_start={P['is_start']}")
print(f"members per boundary: min={elig[start:].sum(1).min()} max={elig[start:].sum(1).max()} "
      f"mean={elig[start:].sum(1).mean():.2f}")

# ---- market factor candidates -------------------------------------------------------------
mkt_mean = np.nanmean(np.where(elig, r, np.nan), axis=1)
mkt_med = np.nanmedian(np.where(elig, r, np.nan), axis=1)
btc = r[:, P["symbols"].index("BTCUSDT")]

print("\nfactor pairwise corr (post is_start):")
sl = slice(start, None)
F = pd.DataFrame({"mean": mkt_mean[sl], "median": mkt_med[sl], "btc": btc[sl]})
print(F.corr().round(4).to_string())

# ---- variance share of the equal-weight factor ---------------------------------------------
# pooled R^2 of r_i on the equal-weight market, full window, per symbol (diagnostic only)
rows = []
for j, s in enumerate(P["symbols"]):
    mask = elig[sl, j] & np.isfinite(r[sl, j]) & np.isfinite(mkt_mean[sl])
    if mask.sum() < 500:
        continue
    y = r[sl, j][mask]
    x = mkt_mean[sl][mask]
    b = np.cov(y, x)[0, 1] / np.var(x)
    resid = y - b * (x - x.mean()) - y.mean()
    rows.append((s, int(mask.sum()), b, 1 - resid.var() / y.var(), y.std() * np.sqrt(1095)))
D = pd.DataFrame(rows, columns=["symbol", "n", "beta_full", "r2", "ann_vol"]).sort_values("beta_full")
print(f"\nfull-window betas vs equal-weight market ({len(D)} symbols):")
print(f"  beta: min={D.beta_full.min():.2f} p25={D.beta_full.quantile(.25):.2f} "
      f"med={D.beta_full.median():.2f} p75={D.beta_full.quantile(.75):.2f} max={D.beta_full.max():.2f}")
print(f"  R^2 : med={D.r2.median():.3f}  min={D.r2.min():.3f}  max={D.r2.max():.3f}")
print(D.head(6).to_string(index=False))
print(D.tail(6).to_string(index=False))
