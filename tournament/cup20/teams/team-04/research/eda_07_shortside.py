"""EDA 7 -- can the short sleeve be gross-positive at all?

`short_gross_pnl > 0` at 1x cost is a hard floor and it is not a statement about spread: it asks
whether the names the book shorts actually FALL, funding included, in a window where the top-20
crypto index roughly tripled. This measures the raw material directly -- bucket by bucket, sleeve
width by sleeve width -- before any book is built around it.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-04/research")
from book import build_funding_matrix  # noqa: E402
from eda_03_portfolio import elig, grid, make_signal, opens, start, symbols  # noqa: E402

N = len(grid)
FUND = build_funding_matrix(grid, symbols)


def bucket_returns(sig, K: int, phase: int, m_long: int, m_short: int):
    """Simple-return sum of a held-K-bar equal-weight basket, per side, with funding."""
    long_pnl = short_pnl = 0.0
    long_hits = short_hits = tot = 0
    long_seq, short_seq, when = [], [], []
    for i in range(start, N - K, 1):
        if (i - start) % K != phase % K:
            continue
        s, e = sig[i], elig[i]
        ok = np.isfinite(s) & e
        if ok.sum() < 9:
            continue
        idx = np.where(ok)[0]
        order = idx[np.argsort(s[idx])]
        lo, hi = order[:m_short], order[-m_long:]
        j = min(i + K, N - 1)
        with np.errstate(invalid="ignore", divide="ignore"):
            step = opens[j] / opens[i] - 1.0
        step = np.where(np.isfinite(step), step, 0.0)
        f = FUND[i:j].sum(axis=0)
        lr = float(np.mean(step[hi] - f[hi]))
        sr = float(np.mean(-(step[lo]) + f[lo]))
        long_pnl += lr
        short_pnl += sr
        long_hits += lr > 0
        short_hits += sr > 0
        tot += 1
        long_seq.append(lr)
        short_seq.append(sr)
        when.append(grid[i])
    return long_pnl, short_pnl, long_hits / tot, short_hits / tot, tot, pd.Series(
        short_seq, index=pd.DatetimeIndex(when)
    ), pd.Series(long_seq, index=pd.DatetimeIndex(when))


if __name__ == "__main__":
    kind = sys.argv[1] if len(sys.argv) > 1 else "resid"
    F = int(sys.argv[2]) if len(sys.argv) > 2 else 63
    K = int(sys.argv[3]) if len(sys.argv) > 3 else 21
    sig, _ = make_signal(kind, 270, F, 1)
    print(f"{kind} F={F} K={K}: cumulative simple-return sum per sleeve, funding included, "
          f"phase-averaged over {K} offsets")
    print(f"{'m':>3} | {'long_sum':>9} {'hit':>5} | {'short_sum':>9} {'hit':>5}")
    for m in (1, 2, 3, 4, 5, 6, 7):
        L = S = HL = HS = 0.0
        for p in range(K):
            lp, sp, hl, hs, tot, _, _ = bucket_returns(sig, K, p, m, m)
            L += lp / K
            S += sp / K
            HL += hl / K
            HS += hs / K
        print(f"{m:>3} | {L:>9.3f} {HL:>5.2f} | {S:>9.3f} {HS:>5.2f}")

    print("\nshort-sleeve sum by fold (m=7, phase-averaged):")
    edges = [pd.Timestamp(x, tz="UTC") for x in
             ("2020-08-17", "2021-08-01", "2022-08-01", "2023-08-01", "2024-08-01")]
    acc = None
    for p in range(K):
        _, _, _, _, _, ss, ls = bucket_returns(sig, K, p, 7, 7)
        acc = ss if acc is None else acc.add(ss, fill_value=0.0)
    for a, b in zip(edges[:-1], edges[1:], strict=True):
        seg = acc[(acc.index >= a) & (acc.index < b)]
        print(f"  {a.date()} -> {b.date()}: {seg.sum() / K:+.3f}")
