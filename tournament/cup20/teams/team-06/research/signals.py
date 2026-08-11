"""Team 06 -- the downside-risk characteristics and the book construction, in one place.

Kept separate from the experiment drivers so the offline lab and the frozen ``strategy.py`` are
demonstrably computing the same thing.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

ROOT = "data/cup20/is"


def load_panel() -> dict[str, pd.DataFrame]:
    bars = pd.read_parquet(f"{ROOT}/bars.parquet")
    membership = pd.read_parquet(f"{ROOT}/membership.parquet")
    funding = pd.read_parquet(f"{ROOT}/funding.parquet")
    opens = bars.pivot(index="open_time", columns="symbol", values="open").sort_index()
    closes = bars.pivot(index="open_time", columns="symbol", values="close").sort_index()
    grid = opens.index
    recon = sorted(membership["reconstitution_time"].unique())
    by_time = {t: set(g["symbol"]) for t, g in membership.groupby("reconstitution_time")}
    rows, current, it = [], set(), iter(recon)
    nxt = next(it, None)
    for t in grid:
        while nxt is not None and nxt <= t:
            current = by_time[nxt]
            nxt = next(it, None)
        rows.append([c in current for c in opens.columns])
    member = pd.DataFrame(rows, index=grid, columns=opens.columns) & opens.notna()
    f = funding.copy()
    f["bucket"] = f["funding_time"].dt.floor("8h")
    fund = (
        f.groupby(["bucket", "symbol"])["funding_rate"].sum().unstack("symbol")
        .reindex(index=grid, columns=opens.columns).fillna(0.0)
    )
    return {"opens": opens, "closes": closes, "member": member, "funding": fund}


def characteristics(closes: pd.DataFrame, member: pd.DataFrame, n: int, skip: int) -> dict:
    """Every characteristic is measured on the window ending ``skip`` bars before the decision.

    ``.shift(1 + skip)`` is the causal guard: at boundary i only rows <= i-1 exist, and ``skip``
    additionally discards the most recent ``skip`` bars so the score is the coin's CHRONIC left-tail
    character rather than whatever just happened to it.
    """
    r = np.log(closes).diff()
    lag = 1 + skip
    sigma = r.rolling(n).std()
    mu = r.rolling(n).mean()
    dev = r.sub(mu)
    neg = dev.where(dev < 0, 0.0)
    semidev = neg.pow(2).rolling(n).mean() ** 0.5
    q05 = r.rolling(n).quantile(0.05)
    cvar = -r.where(r.le(q05)).rolling(n, min_periods=1).mean()
    logc = np.log(closes)
    runmax = logc.rolling(n).max()
    maxdd = (logc - runmax).rolling(n).min().abs()
    underwater = (logc < runmax - 1e-12).rolling(n).mean()
    mkt = r.where(member).mean(axis=1)
    mfr = pd.DataFrame(
        np.repeat(mkt.to_numpy()[:, None], r.shape[1], axis=1), index=r.index, columns=r.columns
    ).where(r.notna())
    cov = (r * mfr).rolling(n).mean() - r.rolling(n).mean() * mfr.rolling(n).mean()
    var = (mfr**2).rolling(n).mean() - mfr.rolling(n).mean() ** 2
    beta = cov / var
    out = {
        "sigma": sigma,
        "semidev": semidev,
        "cvar": cvar,
        "maxdd": maxdd,
        "underwater": underwater,
        "beta": beta,
        "mom": logc.diff(n),
    }
    return {k: v.shift(lag) for k, v in out.items()}


def zscore(row: pd.Series) -> pd.Series:
    s = row.std(ddof=0)
    return (row - row.mean()) / s if s > 1e-12 else row * 0.0


def score_row(F: dict, t, names: list[str], family: str) -> pd.Series:
    """The cross-sectional downside-risk score. Higher = riskier = short side."""
    parts = {k: F[k].loc[t, names] for k in ("sigma", "cvar", "maxdd", "underwater", "semidev")}
    block = pd.DataFrame(parts).dropna()
    if len(block) < 10:
        return pd.Series(dtype=float)
    if family == "sigma":
        return zscore(block["sigma"])
    if family == "semidev":
        return zscore(block["semidev"])
    if family == "cvar":
        return zscore(block["cvar"])
    if family == "maxdd":
        return zscore(block["maxdd"])
    if family == "dd_pair":  # depth + time under water
        return zscore(block["maxdd"]) + zscore(block["underwater"])
    if family == "downside":  # left-tail depth + drawdown depth + recovery time
        return zscore(block["cvar"]) + zscore(block["maxdd"]) + zscore(block["underwater"])
    if family == "cvar_dd":
        return zscore(block["cvar"]) + zscore(block["maxdd"])
    if family == "mandate":  # equal-weight composite of every characteristic the mandate names
        return (
            zscore(block["cvar"])
            + zscore(block["semidev"])
            + zscore(block["maxdd"])
            + zscore(block["underwater"])
        )
    if family == "resid":  # the part of left-tail depth NOT explained by total volatility
        x, y = zscore(block["sigma"]), zscore(block["cvar"])
        return y - float(np.polyfit(x, y, 1)[0]) * x
    raise ValueError(family)


def build_book(
    P: dict,
    F: dict,
    *,
    family: str,
    k: int,
    cadence: int,
    phase: int,
    beta_balance: bool,
    start: pd.Timestamp,
) -> pd.DataFrame:
    opens, member = P["opens"], P["member"]
    grid, cols = opens.index, opens.columns
    W = pd.DataFrame(np.nan, index=grid, columns=cols)
    positions = np.flatnonzero(grid >= start)
    if not len(positions):
        return W
    base = positions[0]
    for i in positions:
        if (i - base - phase) % cadence != 0:
            continue
        t = grid[i]
        elig = member.loc[t]
        names = [c for c in cols if elig[c]]
        if len(names) < 12:
            continue
        score = score_row(F, t, names, family)
        if len(score) < 12:
            continue
        order = score.sort_values()
        longs, shorts = list(order.index[:k]), list(order.index[-k:])
        gl = 0.5
        if beta_balance:
            bet = F["beta"].loc[t]
            bl, bs = float(bet[longs].mean()), float(bet[shorts].mean())
            if np.isfinite(bl) and np.isfinite(bs) and (bl + bs) > 1e-6:
                gl = min(max(bs / (bl + bs), 0.20), 0.80)
        row = pd.Series(0.0, index=cols)
        row[longs] = gl / k
        row[shorts] = -(1 - gl) / k
        W.loc[t] = row
    return W
