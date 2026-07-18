"""e06 — post-mortem battery: inverse-vol rescue, equal-weight check, reverse diagnostic."""

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/analysis")
from portfolio_tournament import constants as tc
from portfolio_tournament import engine as te

from common import build_and_move, crank, form_A, form_B, line, panels, score

pn, aux, scoring = panels()
rf = pn["ret_fwd"]
lr1 = np.log(pn["close"].where(pn["close"] > 0)).diff()
sig_vol = lr1.rolling(42, min_periods=30).std()
vol_floor = sig_vol.quantile(0.2, axis=1)
vol_adj = sig_vol.clip(lower=pd.DataFrame(
    np.tile(vol_floor.to_numpy()[:, None], (1, sig_vol.shape[1])),
    index=sig_vol.index, columns=sig_vol.columns))


def form_C(L, q=0.6):
    b, r = build_and_move(pn, aux, L)
    stag = 1.0 - crank((r.abs() / sig_vol).where(b.notna()))
    g = (crank(b) - q).clip(lower=0.0) / (1.0 - q)
    return -(g * np.sign(r) * stag)


def gross_sharpe(sig):
    raw = te.conform_raw(sig.fillna(0.0), pn)
    masked = raw.where(scoring["elig"], 0.0)
    w = te.normalize_and_cap(masked).shift(1)
    pnl = (w * rf.reindex(columns=w.columns)).sum(axis=1)
    return te.msharpe(pnl.dropna(), tc.TRN_IS_START, tc.TRN_IS_HI), pnl


print("== (a) inverse-vol weighted fade ==")
FORMS = {"A": lambda L: form_A(pn, aux, L, 0.6), "B": lambda L: form_B(pn, aux, L),
         "C": lambda L: form_C(L)}
for name, fn in FORMS.items():
    for L in (6, 9, 21, 42):
        s = (fn(L) / vol_adj).fillna(0.0)
        gs, _ = gross_sharpe(s)
        _, _, _, m1 = score(s)
        print(line(f"iv{name} L={L:2d} @1x", m1) + f"  grossS={gs:+.3f}")

print("\n== (b) equal-weight sign-only tercile fade, L=21 ==")
b, r = build_and_move(pn, aux, 21)
cb = crank(b)
s = pd.DataFrame(0.0, index=cb.index, columns=cb.columns)
hi = cb > 2.0 / 3.0
s = (-np.sign(r)).where(hi, 0.0).fillna(0.0)
gs, _ = gross_sharpe(s)
_, _, _, m1 = score(s)
print(line("eqw tercile L=21 @1x", m1) + f"  grossS={gs:+.3f}")

print("\n== (c) DIAGNOSTIC reverse-sign form B (continuation) ==")
for L in (6, 42):
    s = (-form_B(pn, aux, L)).fillna(0.0)
    gs, _ = gross_sharpe(s)
    _, _, _, m1 = score(s)
    _, _, _, m2 = score(s, cost_mult=2.0, slip_mult=2.0)
    print(line(f"revB L={L:2d} @1x", m1) + f"  grossS={gs:+.3f}  S2x={m2.sharpe:+.3f}")

print("\n== (d) active-window Sharpe (2022-01..2024-06) of least-bad fade (B L=42) ==")
s = form_B(pn, aux, 42).fillna(0.0)
net, w, parts, m = score(s)
lo, hi_ts = pd.Timestamp("2022-01-01"), pd.Timestamp("2024-07-01")
print(f"B L=42 active-window S={te.msharpe(net, lo, hi_ts):+.3f} (full-window {m.sharpe:+.3f})")
