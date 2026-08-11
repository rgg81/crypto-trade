"""Team 06 EDA 2 -- is there a downside-risk characteristic that is NOT plain volatility?

EDA 1 said the level of risk predicts (sigma IC -0.123, t -5.7, negative in all four folds) and the
pure shape of the return distribution does not (semidev/sigma IC +0.009, t 0.47, sign-flipping
across folds). That kills the naive "left-tail asymmetry" story. This step asks the harder version
of the same question: is there a CONDITIONAL downside characteristic -- how a coin behaves when the
market falls, as opposed to how wide its own distribution is -- that carries information plain
volatility does not?
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-06/research")
from panel import BARS_PER_DAY, fold_slices, load_panel  # noqa: E402

P = load_panel()
opens, closes, member = P["opens"], P["closes"], P["member"]
lr = np.log(closes).diff()

N = 63
H = 21

# Equal-weight market return over point-in-time members only.
mkt = (lr.where(member)).mean(axis=1)


def cond_beta(n: int) -> dict[str, pd.DataFrame]:
    r = lr
    m = mkt
    down = (m < 0).astype(float)
    up = (m > 0).astype(float)
    mfr = pd.DataFrame(
        np.repeat(m.to_numpy()[:, None], r.shape[1], axis=1), index=r.index, columns=r.columns
    ).where(r.notna())

    def wmean(x, w):
        num = x.mul(w, axis=0).rolling(n, min_periods=n // 2).sum()
        den = pd.DataFrame(1.0, index=x.index, columns=x.columns).where(x.notna()).mul(
            w, axis=0
        ).rolling(n, min_periods=n // 2).sum()
        return num.div(den.where(den > 0))

    def beta(w):
        mx = wmean(mfr, w)
        rx = wmean(r, w)
        cov = wmean(r.mul(mfr), w) - rx * mx
        var = wmean(mfr**2, w) - mx**2
        return cov / var.where(var > 0)

    dbeta = beta(down)
    ubeta = beta(up)
    # CVaR-style tail measures on own returns
    q05 = r.rolling(n).quantile(0.05)
    q95 = r.rolling(n).quantile(0.95)
    cvar = r.where(r.le(q05)).rolling(n, min_periods=1).mean()
    cvar_up = r.where(r.ge(q95)).rolling(n, min_periods=1).mean()
    sigma = r.rolling(n).std()
    out = {
        "dbeta": dbeta,
        "ubeta": ubeta,
        "beta_asym": dbeta - ubeta,
        "beta_ratio": dbeta / ubeta.abs().clip(lower=0.05),
        "cvar05": -cvar,
        "cvar_asym": (-cvar) / cvar_up.abs().clip(lower=1e-9),
        "sigma": sigma,
        "dbeta_resid": dbeta,  # replaced below by the cross-sectional residual on sigma
    }
    return {k: v.shift(1) for k, v in out.items()}


M = cond_beta(N)
fwd = opens.shift(-H) / opens - 1.0
grid = opens.index
sample = grid[grid >= pd.Timestamp("2020-08-17", tz="UTC")][:: BARS_PER_DAY * 7]

records = []
for t in sample:
    if t not in fwd.index:
        continue
    elig = member.loc[t]
    f = fwd.loc[t]
    names = [c for c in opens.columns if elig[c] and np.isfinite(f.get(c, np.nan))]
    if len(names) < 10:
        continue
    block = pd.DataFrame({k: M[k].loc[t, names] for k in M}).dropna()
    if len(block) < 10:
        continue
    fr = f[block.index].rank(pct=True)
    # residualise dbeta on sigma cross-sectionally (rank space, single regressor)
    x = block["sigma"].rank(pct=True)
    y = block["dbeta"].rank(pct=True)
    beta_hat = np.polyfit(x, y, 1)[0]
    block["dbeta_resid"] = y - beta_hat * x
    block["cvar_resid"] = block["cvar05"].rank(pct=True) - (
        np.polyfit(x, block["cvar05"].rank(pct=True), 1)[0] * x
    )
    rec = {"t": t}
    for k in block.columns:
        rec[k] = block[k].rank(pct=True).corr(fr.rank(pct=True))
    records.append(rec)

ic = pd.DataFrame(records).set_index("t")
print("=== conditional downside measures: IC vs forward 7d return (n=%d) ===" % len(ic))
print(
    pd.DataFrame(
        {
            "mean_IC": ic.mean(),
            "t_stat": ic.mean() / ic.std() * np.sqrt(ic.notna().sum()),
        }
    )
    .round(4)
    .to_string()
)
print("\n=== by fold ===")
print(pd.DataFrame({n: ic[m].mean() for n, m in fold_slices(ic.index)}).round(4).to_string())
