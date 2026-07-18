"""e01b — corrected-horizon IC: signal[t] vs ret_fwd[t+1] (engine-held candle) and 3c fwd."""

import numpy as np
import pandas as pd

from common import build_and_move, crank, form_A, form_B, panels

pn, aux, scoring = panels()
elig = aux["eligibility"]
rf = pn["ret_fwd"]
fwd1 = rf.shift(-1)  # held candle for signal at t
fwd3 = rf.shift(-1) + rf.shift(-2) + rf.shift(-3)


def ic_line(sig, fwd):
    s = sig.where(elig)
    ics = s.corrwith(fwd.where(elig), axis=1, method="spearman").dropna()
    mo = ics.groupby(ics.index.to_period("M")).mean()
    t = mo.mean() / mo.std() * np.sqrt(len(mo)) if mo.std() > 0 else float("nan")
    return f"IC={ics.mean():+.4f} t={t:+.2f}"


print("== corrected ICs: signal[t] vs held candle t+1 / next-3 ==")
for L in (3, 6, 9, 21, 42):
    a, b = form_A(pn, aux, L), form_B(pn, aux, L)
    print(
        f"L={L:2d}  A1 {ic_line(a, fwd1)}  A3 {ic_line(a, fwd3)}  "
        f"B1 {ic_line(b, fwd1)}  B3 {ic_line(b, fwd3)}"
    )

print("\n== fwd ret bps over HELD candle (t+1) by build-quintile x sign(r_L), L=9 ==")
b, r = build_and_move(pn, aux, 9)
cb = crank(b)
sgn = np.sign(r)
f1 = fwd1.where(elig)
for lo, hi, tag in [(0.0, 0.2, "Q1"), (0.2, 0.4, "Q2"), (0.4, 0.6, "Q3"), (0.6, 0.8, "Q4"), (0.8, 1.01, "Q5")]:
    m = (cb >= lo) & (cb < hi)
    up = f1[m & (sgn > 0)].stack().mean() * 1e4
    dn = f1[m & (sgn < 0)].stack().mean() * 1e4
    n = int(m.sum().sum())
    print(f"{tag}: after-up {up:+7.1f}  after-down {dn:+7.1f}  (n={n})")

print("\n== same at L=21 ==")
b, r = build_and_move(pn, aux, 21)
cb = crank(b)
sgn = np.sign(r)
for lo, hi, tag in [(0.0, 0.2, "Q1"), (0.2, 0.4, "Q2"), (0.4, 0.6, "Q3"), (0.6, 0.8, "Q4"), (0.8, 1.01, "Q5")]:
    m = (cb >= lo) & (cb < hi)
    up = f1[m & (sgn > 0)].stack().mean() * 1e4
    dn = f1[m & (sgn < 0)].stack().mean() * 1e4
    print(f"{tag}: after-up {up:+7.1f}  after-down {dn:+7.1f}")
