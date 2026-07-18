"""e01 — EDA: OI coverage, gap artifacts, Spearman IC of forms A/B vs ret_fwd."""

import numpy as np
import pandas as pd

from common import build_and_move, form_A, form_B, panels

pn, aux, scoring = panels()
oi = aux["oi"]
elig = aux["eligibility"]

# --- coverage: eligible names with finite positive oi, by quarter -------------------------
have = (oi > 0) & elig
cov = pd.DataFrame({"elig": elig.sum(axis=1), "with_oi": have.sum(axis=1)})
q = cov.groupby(cov.index.to_period("Q")).mean().round(1)
print("== coverage (mean names/candle by quarter) ==")
print(q.to_string())

# --- gap artifacts: 1-candle |dlog oi| tails ----------------------------------------------
b1 = (np.log(oi.where(oi > 0)) - np.log(oi.where(oi > 0).shift(1))).where(elig)
flat = b1.stack().dropna()
print("\n== 1-candle dlog(oi) distribution ==")
print(flat.describe(percentiles=[0.001, 0.01, 0.99, 0.999]).round(4).to_string())
print(f"|dlog oi,1c| > 0.5: {(flat.abs() > 0.5).mean() * 1e4:.1f} per 10k obs")
print(f"|dlog oi,1c| > 1.0: {(flat.abs() > 1.0).mean() * 1e4:.1f} per 10k obs")

# --- IC scan ------------------------------------------------------------------------------
rf = pn["ret_fwd"]
print("\n== cross-sectional Spearman IC vs ret_fwd (mean, t) ==")
for L in (3, 6, 9, 21, 42):
    row = []
    for name, sig in (("A", form_A(pn, aux, L)), ("B", form_B(pn, aux, L))):
        s = sig.where(elig)
        ics = s.corrwith(rf.where(elig), axis=1, method="spearman")
        ics = ics.dropna()
        mo = ics.groupby(ics.index.to_period("M")).mean()
        t = mo.mean() / mo.std() * np.sqrt(len(mo)) if mo.std() > 0 else float("nan")
        row.append(f"{name}: IC={ics.mean():+.4f} t={t:+.2f} n={len(ics)}")
    print(f"L={L:2d}  " + "   ".join(row))

# --- build-vs-forward-return monotonicity (form-A gating sanity) --------------------------
print("\n== fwd ret (bps/candle) by build-quintile x sign(r), L=9 ==")
b, r = build_and_move(pn, aux, 9)
from common import crank  # noqa: E402

cb = crank(b)
sgn = np.sign(r)
fwd = rf.where(elig)
rows = []
for lo, hi, tag in [(0.0, 0.2, "Q1"), (0.2, 0.4, "Q2"), (0.4, 0.6, "Q3"), (0.6, 0.8, "Q4"), (0.8, 1.01, "Q5")]:
    m = (cb >= lo) & (cb < hi)
    up = fwd[m & (sgn > 0)].stack().mean() * 1e4
    dn = fwd[m & (sgn < 0)].stack().mean() * 1e4
    rows.append(f"{tag}: after-up {up:+7.1f}  after-down {dn:+7.1f}")
print("\n".join(rows))
