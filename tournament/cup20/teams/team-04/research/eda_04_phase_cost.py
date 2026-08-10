"""EDA 4 -- rebalance phase, cost levels, and horizon composites.

Phase is a first-order axis: a cadence-K result run at one offset is a result about that offset.
Everything here is measured across all K offsets, and the headline is the phase mean, never the
best phase.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-04/research")
from book import fold_sharpes, quarter_fraction, simulate, stats  # noqa: E402
from eda_03_portfolio import FUND, build_book, elig, grid, make_signal, opens, start  # noqa: E402


def one(sig, beta, K, phase, cm=1.0, **kw):
    w, reb = build_book(sig, beta, K, phase, **kw)
    res = simulate(w, reb, opens, FUND, start, cost_mult=cm)
    st = stats(res, grid, start)
    fs = fold_sharpes(res, grid, start)
    st["minfold"] = min(fs)
    st["nposfold"] = sum(1 for x in fs if x > 0)
    st["posq"] = quarter_fraction(res, grid, start)
    st["folds"] = fs
    return st


def composite(kind, B, Fs, S):
    """Cross-sectionally z-scored average of the signal at several formation lengths."""
    acc, cnt = None, 0
    for F in Fs:
        sig, beta = make_signal(kind, B, F, S)
        z = np.full_like(sig, np.nan)
        for i in range(start, sig.shape[0]):
            ok = np.isfinite(sig[i]) & elig[i]
            if ok.sum() < 9:
                continue
            v = sig[i][ok]
            z[i][ok] = (v - v.mean()) / (v.std() + 1e-12)
        acc = z if acc is None else np.nansum(np.dstack([acc, z]), 2)
        cnt += 1
    return acc / cnt, beta


if __name__ == "__main__":
    what = sys.argv[1]
    if what == "phase":
        for kind in ("raw", "resid"):
            for F in (42, 63):
                for K in (21, 42):
                    sig, beta = make_signal(kind, 270, F, 1)
                    rows = [one(sig, beta, K, p) for p in range(K)]
                    sh = np.array([r["sharpe"] for r in rows])
                    mf = np.array([r["minfold"] for r in rows])
                    to = np.array([r["turnover_yr"] for r in rows])
                    dd = np.array([r["maxdd"] for r in rows])
                    ed = np.array([r["gross_edge_bps"] for r in rows])
                    print(f"{kind:<6} F={F:<3} K={K:<3} | Sharpe mean={sh.mean():+.2f} "
                          f"sd={sh.std():.2f} min={sh.min():+.2f} max={sh.max():+.2f} | "
                          f"minfold mean={mf.mean():+.2f} min={mf.min():+.2f} | "
                          f"to={to.mean():.1f} dd={dd.mean():.3f} edge={ed.mean():.0f}")
    elif what == "cost":
        for kind in ("raw", "resid"):
            for F, K in ((42, 21), (42, 42), (63, 21)):
                sig, beta = make_signal(kind, 270, F, 1)
                line = f"{kind:<6} F={F:<3} K={K:<3} |"
                for cm in (1, 2, 3):
                    rows = [one(sig, beta, K, p, cm=cm) for p in range(K)]
                    sh = np.median([r["sharpe"] for r in rows])
                    mf = np.median([r["minfold"] for r in rows])
                    line += f" {cm}x: Sh={sh:+.2f} minfold={mf:+.2f} |"
                print(line)
    elif what == "comp":
        for Fs in ([42], [28, 42, 63], [21, 42, 84], [42, 63], [30, 42, 54]):
            for K in (21, 42):
                sig, beta = composite("resid", 270, Fs, 1)
                rows = [one(sig, beta, K, p) for p in range(K)]
                sh = np.array([r["sharpe"] for r in rows])
                mf = np.array([r["minfold"] for r in rows])
                to = np.array([r["turnover_yr"] for r in rows])
                dd = np.array([r["maxdd"] for r in rows])
                nf = np.array([r["nposfold"] for r in rows])
                print(f"comp {str(Fs):<16} K={K:<3} Sh={sh.mean():+.2f}±{sh.std():.2f} "
                      f"minfold={mf.mean():+.2f}(min {mf.min():+.2f}) posfold={nf.mean():.2f} "
                      f"to={to.mean():.1f} dd={dd.mean():.3f}")
    elif what == "bwin":
        for B in (90, 180, 270, 540):
            for K in (21, 42):
                sig, beta = make_signal("resid", B, 42, 1)
                rows = [one(sig, beta, K, p) for p in range(K)]
                sh = np.array([r["sharpe"] for r in rows])
                mf = np.array([r["minfold"] for r in rows])
                print(f"B={B:<4} K={K:<3} Sh={sh.mean():+.2f}±{sh.std():.2f} "
                      f"minfold={mf.mean():+.2f} to={np.mean([r['turnover_yr'] for r in rows]):.1f} "
                      f"dd={np.mean([r['maxdd'] for r in rows]):.3f}")
    elif what == "skip":
        for S in (0, 1, 2, 3, 6):
            sig, beta = make_signal("resid", 270, 42, S)
            rows = [one(sig, beta, 21, p) for p in range(21)]
            sh = np.array([r["sharpe"] for r in rows])
            print(f"S={S:<2} Sh={sh.mean():+.2f}±{sh.std():.2f} "
                  f"minfold={np.mean([r['minfold'] for r in rows]):+.2f}")
