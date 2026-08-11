"""Team 06 EDA 3 -- from a characteristic to a book.

The question this answers is the one the organiser told me to answer early and cheaply: WHERE DOES
THE BOOK'S REALISED ANNUALISED VOLATILITY SIT RELATIVE TO 0.06 at full unlevered gross, and does a
downside-risk sort behave differently from a plain-volatility sort once it is a portfolio rather
than an IC.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-06/research")
from panel import BARS_PER_DAY, book_stats, load_panel  # noqa: E402

P = load_panel()
opens, closes, member, fund = P["opens"], P["closes"], P["member"], P["funding"]
lr = np.log(closes).diff()
mkt = lr.where(member).mean(axis=1)

START = pd.Timestamp("2020-08-17", tz="UTC")


def features(n: int) -> dict[str, pd.DataFrame]:
    r = lr
    sigma = r.rolling(n).std()
    mu = r.rolling(n).mean()
    dev = r.sub(mu)
    neg = dev.where(dev < 0, 0.0)
    semidev = neg.pow(2).rolling(n).mean() ** 0.5
    q05 = r.rolling(n).quantile(0.05)
    cvar = -r.where(r.le(q05)).rolling(n, min_periods=1).mean()
    logc = np.log(closes)
    dd = (logc - logc.rolling(n).max()).rolling(n).min().abs()
    mfr = pd.DataFrame(
        np.repeat(mkt.to_numpy()[:, None], r.shape[1], axis=1), index=r.index, columns=r.columns
    ).where(r.notna())
    cov = (r.mul(mfr)).rolling(n).mean() - r.rolling(n).mean() * mfr.rolling(n).mean()
    var = (mfr**2).rolling(n).mean() - mfr.rolling(n).mean() ** 2
    beta = cov / var
    return {k: v.shift(1) for k, v in
            {"sigma": sigma, "semidev": semidev, "cvar": cvar, "maxdd": dd, "beta": beta}.items()}


def zscore(row: pd.Series) -> pd.Series:
    s = row.std(ddof=0)
    return (row - row.mean()) / s if s > 0 else row * 0.0


def build(
    score_key: str,
    n: int,
    k: int,
    cadence: int,
    phase: int,
    weighting: str,
    F: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    grid = opens.index
    cols = opens.columns
    W = pd.DataFrame(np.nan, index=grid, columns=cols)
    positions = np.flatnonzero(grid >= START)
    for i in positions:
        if (i - positions[0] - phase) % cadence != 0:
            continue
        t = grid[i]
        elig = member.loc[t]
        names = [c for c in cols if elig[c]]
        if len(names) < 12:
            continue
        if score_key == "blend":
            a = F["cvar"].loc[t, names]
            b = F["sigma"].loc[t, names]
            block = pd.concat([a, b], axis=1).dropna()
            if len(block) < 12:
                continue
            x = zscore(block.iloc[:, 1])
            y = zscore(block.iloc[:, 0])
            slope = np.polyfit(x, y, 1)[0]
            score = y - slope * x + y * 0  # residual only
            score = score + x  # level + residual
        else:
            score = F[score_key].loc[t, names].dropna()
        if len(score) < 12:
            continue
        order = score.sort_values()
        longs = list(order.index[:k])
        shorts = list(order.index[-k:])
        sig = F["sigma"].loc[t]
        bet = F["beta"].loc[t]
        if weighting == "equal":
            wl = pd.Series(1.0, index=longs)
            ws = pd.Series(1.0, index=shorts)
        elif weighting == "invvol":
            wl = 1.0 / sig[longs].clip(lower=1e-6)
            ws = 1.0 / sig[shorts].clip(lower=1e-6)
        else:
            raise ValueError(weighting)
        wl = wl / wl.sum()
        ws = ws / ws.sum()
        if weighting == "equal" and score_key.endswith("_bn"):
            pass
        bl, bs = float((wl * bet[longs]).sum()), float((ws * bet[shorts]).sum())
        if BETA_BALANCE and np.isfinite(bl) and np.isfinite(bs) and (bl + bs) > 0:
            gl = bs / (bl + bs)
        else:
            gl = 0.5
        gl = min(max(gl, 0.2), 0.8)
        row = pd.Series(0.0, index=cols)
        row[longs] = wl * gl
        row[shorts] = -ws * (1 - gl)
        W.loc[t] = row
    return W


def report(tag: str, W: pd.DataFrame) -> dict:
    st = book_stats(W.loc[W.index >= START], opens, fund)
    folds = " ".join(f"{k}={v:+.2f}" for k, v in st["folds"].items())
    print(
        f"{tag:38s} vol={st['vol']:.3f} shp={st['sharpe']:+.2f} ret={st['ann_ret']:+.3f} "
        f"dd={st['maxdd']:.3f} to={st['ann_turnover']:.1f} edge={st['gross_edge_bps']:.0f}bp "
        f"n={st['trades']:5d} | {folds}"
    )
    return st


if __name__ == "__main__":
    for BETA_BALANCE in (False, True):
        print(f"\n########## beta_balance={BETA_BALANCE} ##########")
        for n in (63, 126):
            F = features(n)
            for score in ("sigma", "semidev", "cvar", "maxdd"):
                for weighting in ("equal", "invvol"):
                    W = build(score, n, 6, 21, 0, weighting, F)
                    report(f"n={n} {score:8s} k=6 w={weighting:7s}", W)
