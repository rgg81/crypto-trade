"""EDA 3 — slow carry with cadence + hold; decompose price vs funding leg per fold."""
from __future__ import annotations
import sys, numpy as np, pandas as pd
sys.path.insert(0, "tournament/cup20/teams/team-07/research")
from panel import build_panel
from sim2 import simulate, reference_scalars, metrics, show, G

p = build_panel()
g = p["grid"]; op = p["open"]; el = p["eligible"]; fr = p["funding"]
start = el.sum(axis=1).ge(20).idxmax()
m = g >= start
g = g[m]; op = op.loc[g]; el = el.loc[g]; fr = fr.loc[g]
fwd_price = (op.shift(-1) / op - 1.0)
fwd_fund = fr.shift(-1).fillna(0.0)
ok = (el & fwd_price.notna())
COLS = list(op.columns)

def make_targets(lb, top_n, cadence, phase):
    sig = fr.rolling(lb, min_periods=max(2, lb // 2)).mean().shift(1).where(ok)
    S = sig.to_numpy(); OKa = ok.to_numpy()
    out = []
    for i in range(len(g)):
        if (i % cadence) != (phase % cadence):
            out.append(None); continue
        s = S[i]
        valid = np.isfinite(s) & OKa[i]
        if valid.sum() < 2 * top_n:
            out.append(None); continue
        idxv = np.where(valid)[0]
        order = idxv[np.argsort(s[idxv])]
        w = np.zeros(len(s))
        w[order[:top_n]] = 1.0        # lowest funding -> long
        w[order[-top_n:]] = -1.0      # highest funding -> short
        out.append(w)
    return out

def run_cfg(lb, n, cad, ph, tag=""):
    tl = make_targets(lb, n, cad, ph)
    ref, _ = simulate(tl, fwd_price, fwd_fund, 1.0)
    sc = reference_scalars(ref, g)
    r1, tr = simulate(tl, fwd_price, fwd_fund, 1.0, sc)
    r2, _ = simulate(tl, fwd_price, fwd_fund, 2.0, sc)
    m1, m2 = metrics(r1, tr), metrics(r2, tr)
    if tag: show(tag, m1, m2, tr)
    return m1, m2, r1, tr

print("=== cadence sweep (lb=63, n=6) ===")
for cad in (1, 3, 6, 9, 21):
    for ph in range(min(cad, 3)):
        run_cfg(63, 6, cad, ph, f"lb63 n6 cad={cad} ph={ph}")

print("\n=== lookback x n at cadence 9 (phase 0) ===")
for lb in (21, 42, 63, 126, 189):
    for n in (4, 6, 8):
        run_cfg(lb, n, 9, 0, f"lb{lb} n{n} cad9")

print("\n=== leg decomposition, lb=63 n=6 cad=9 ===")
m1, m2, r1, tr = run_cfg(63, 6, 9, 0)
edges = [r1.index[0], pd.Timestamp("2021-08-01",tz="UTC"), pd.Timestamp("2022-08-01",tz="UTC"),
         pd.Timestamp("2023-08-01",tz="UTC"), r1.index[-1] + pd.Timedelta(hours=8)]
for a, b in zip(edges[:-1], edges[1:]):
    seg = r1[(r1.index >= a) & (r1.index < b)]
    print(f"  {str(a)[:10]}..{str(b)[:10]}  price={seg['price'].sum():+.3f} "
          f"funding={seg['fund'].sum():+.3f} cost={-seg['cost'].sum():+.3f} net={seg['net'].sum():+.3f}")
