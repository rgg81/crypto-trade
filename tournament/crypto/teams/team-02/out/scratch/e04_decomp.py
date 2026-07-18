"""e04 — failure decomposition: gross (cost-free, funding-off) alpha; leg split; yearly."""

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/analysis")
from portfolio_tournament import constants as tc
from portfolio_tournament import engine as te

from common import form_A, form_B, panels

pn, aux, scoring = panels()
rf = pn["ret_fwd"]


def gross_stats(sig, tag):
    raw = te.conform_raw(sig.fillna(0.0), pn)
    masked = raw.where(scoring["elig"], 0.0)
    w = te.normalize_and_cap(masked).shift(1)
    r = rf.reindex(columns=w.columns)
    pnl = (w * r).sum(axis=1)  # gross price pnl, no cost, no funding, no vol-target
    wl = w.clip(lower=0.0)
    ws = w.clip(upper=0.0)
    pl = (wl * r).sum(axis=1)
    ps = (ws * r).sum(axis=1)
    # monthly sharpe of gross, active period only for readability (msharpe uses full window)
    ms = te.msharpe(pnl.dropna(), tc.TRN_IS_START, tc.TRN_IS_HI)
    print(
        f"{tag:12s} grossS={ms:+.3f} cumPnl={pnl.sum():+.3f} "
        f"long={pl.sum():+.3f} short={ps.sum():+.3f}"
    )
    yr = pnl.groupby(pnl.index.year).sum().round(3)
    yl = pl.groupby(pl.index.year).sum().round(3)
    ys = ps.groupby(ps.index.year).sum().round(3)
    df = pd.DataFrame({"pnl": yr, "long": yl, "short": ys})
    print(df.T.to_string())
    print()


for L in (6, 21, 42):
    gross_stats(form_A(pn, aux, L, 0.6), f"A L={L}")
for L in (6, 21, 42):
    gross_stats(form_B(pn, aux, L), f"B L={L}")

# how much of the 1x loss is cost? reprint one config with parts
from common import score  # noqa: E402

for tag, sig in (("A L=21", form_A(pn, aux, 21, 0.6)), ("B L=42", form_B(pn, aux, 42))):
    net, w, parts, m = score(sig)
    print(
        f"{tag}: 1x S={m.sharpe:+.3f}  sum pnl={parts['pnl'].sum():+.3f} "
        f"fpnl={parts['fpnl'].sum():+.3f} cost={parts['cost'].sum():+.3f} "
        f"raw_net={parts['raw_net'].sum():+.3f}"
    )
