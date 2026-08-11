"""Team 06 EDA 1 -- do downside-risk measures separate from plain volatility, and does either
carry cross-sectional information about forward returns in the point-in-time top-20?

Every statistic below is computed from rows strictly earlier than the decision boundary and scored
against the open-to-open return the evaluator would actually have earned. No number here is a
score; this is a laboratory for choosing a mechanism.
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

N = 63  # formation bars = 21 days
H = 21  # forward horizon = 7 days


def rolling_measures(n: int) -> dict[str, pd.DataFrame]:
    r = lr
    mu = r.rolling(n).mean()
    sigma = r.rolling(n).std()
    dev = r.sub(mu)
    neg = dev.where(dev < 0, 0.0)
    semidev = (neg.pow(2).rolling(n).mean()) ** 0.5
    neg0 = r.where(r < 0, 0.0)
    semidev0 = (neg0.pow(2).rolling(n).mean()) ** 0.5
    pos = dev.where(dev > 0, 0.0)
    semiup = (pos.pow(2).rolling(n).mean()) ** 0.5
    skew = r.rolling(n).skew()
    # drawdown depth over the window, from the close path
    logc = np.log(closes)
    runmax = logc.rolling(n).max()
    dd = (logc - runmax).rolling(n).min().abs()
    # underwater fraction: share of window bars below the running window max
    underwater = (logc < runmax).rolling(n).mean()
    mom = logc.diff(n)
    # tail asymmetry from order statistics: mean of worst 10% vs best 10%
    q10 = r.rolling(n).quantile(0.10)
    q90 = r.rolling(n).quantile(0.90)
    out = {
        "sigma": sigma,
        "semidev": semidev,
        "semidev0": semidev0,
        "asym": semidev / sigma,
        "semi_ratio": semidev / semiup,
        "skew": skew,
        "maxdd": dd,
        "underwater": underwater,
        "mom": mom,
        "tailratio": (-q10) / q90,
    }
    return {k: v.shift(1) for k, v in out.items()}  # only rows <= i-1 are visible at boundary i


M = rolling_measures(N)
fwd = opens.shift(-H) / opens - 1.0

grid = opens.index
start = pd.Timestamp("2020-08-17", tz="UTC")
mask_time = grid >= start
sample = grid[mask_time][:: BARS_PER_DAY * 7]  # weekly, to keep the IC sample near-independent


def xs_rank(frame: pd.DataFrame, when) -> pd.Series:
    row = frame.loc[when]
    eligible = member.loc[when]
    row = row[eligible & row.notna()]
    return row


records = []
for t in sample:
    if t not in fwd.index:
        continue
    f = fwd.loc[t]
    elig = member.loc[t]
    names = [c for c in opens.columns if elig[c] and np.isfinite(f.get(c, np.nan))]
    if len(names) < 10:
        continue
    rec = {"t": t}
    fr = f[names].rank(pct=True)
    for key, frame in M.items():
        v = frame.loc[t, names]
        ok = v.notna()
        if ok.sum() < 10:
            rec[key] = np.nan
            continue
        rec[key] = v[ok].rank(pct=True).corr(fr[ok.index[ok]].rank(pct=True))
    records.append(rec)

ic = pd.DataFrame(records).set_index("t")
print("=== cross-sectional Spearman IC vs forward 7d return (weekly samples, n=%d) ===" % len(ic))
summary = pd.DataFrame(
    {
        "mean_IC": ic.mean(),
        "t_stat": ic.mean() / ic.std() * np.sqrt(ic.notna().sum()),
        "hit": (ic > 0).mean(),
    }
)
print(summary.round(4).to_string())

print("\n=== mean IC by fold ===")
rows = {}
for name, m in fold_slices(ic.index):
    rows[name] = ic[m].mean()
print(pd.DataFrame(rows).round(4).to_string())

print("\n=== cross-sectional rank correlation BETWEEN measures (mean over dates) ===")
keys = list(M.keys())
corr = pd.DataFrame(0.0, index=keys, columns=keys)
cnt = 0
for t in sample[::4]:
    elig = member.loc[t]
    names = [c for c in opens.columns if elig[c]]
    block = pd.DataFrame({k: M[k].loc[t, names] for k in keys}).dropna()
    if len(block) < 10:
        continue
    corr += block.rank().corr(method="spearman")
    cnt += 1
print((corr / cnt).round(2).to_string())
