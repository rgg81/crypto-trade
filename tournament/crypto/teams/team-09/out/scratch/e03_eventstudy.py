"""e03 — (A) e02 center-cell cost/funding decomposition; (B) cascade event study."""

import sys

import numpy as np
import pandas as pd

sys.path.insert(
    0,
    "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/tournament/crypto/teams/team-09/out/scratch",
)
import sig
from portfolio_tournament import constants as tc
from portfolio_tournament import engine as te

pn, aux, scoring = sig.te.load_is_panels()

# ---------- Part A: decomposition of e02 center cell ----------
raw = sig.build_signal(pn, aux, k=2, h=6, gamma=1.0)
raw = te.conform_raw(raw, pn)
for tag, cm, fON in (("cost0_fund0", 0.0, False), ("cost0_fund1", 0.0, True), ("cost1_fund1", 1.0, True)):
    net, w, parts = te.net_series(raw, pn, scoring, cost_mult=cm, slip_mult=cm, apply_funding=fON)
    m = te.evaluate(net, w, parts, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
    print(sig.brief_row(f"A k2h6g1 {tag}", m), flush=True)

# ---------- Part B: event study ----------
close, high, low, qv = pn["close"], pn["high"], pn["low"], pn["quote_volume"]
elig = aux["eligibility"]
k = 2
r1 = np.log(close).diff()
sigma = r1.rolling(42, min_periods=28).std().clip(lower=0.001)
x = r1.rolling(k).sum() / (sigma * np.sqrt(k))
tr = (high - low) / close
rs = tr.rolling(k).mean() / tr.rolling(90, min_periods=60).mean().shift(k)
vs = qv.rolling(k).mean() / qv.rolling(90, min_periods=60).mean().shift(k)
ev = np.sqrt(rs * vs)

rf = pn["ret_fwd"]  # ret_fwd[t] = open[t+1]/open[t]-1  (scoring-only; scratch use is legal)
elig_f = elig.astype(float).where(elig)  # 1.0 where eligible else NaN
mkt = (rf * elig_f).mean(axis=1)  # eligible-universe mean fwd return

# fwd cumulative log-return entering at open[t+1]: sum of log(1+rf) rows t+1 .. t+n
lrf = np.log1p(rf)
lmkt = np.log1p(mkt)

reg = te.regime_of(close.index)

rows = []
for x0 in (2.0, 3.0):
    for ev0 in (1.5, 2.0, 3.0):
        flush = (x <= -x0) & (ev >= ev0) & elig
        squeeze = (x >= x0) & (ev >= ev0) & elig
        for n in (1, 2, 3, 6, 9):
            cum = lrf.shift(-1).rolling(n).sum().shift(-(n - 1))  # rows t+1..t+n
            cumm = lmkt.shift(-1).rolling(n).sum().shift(-(n - 1))
            rel = cum.sub(cumm, axis=0)
            for tag, mask, sgn in (("flushL", flush, +1), ("sqzS", squeeze, -1)):
                vals_rel = rel[mask].stack().dropna()
                vals_abs = cum[mask].stack().dropna()
                if len(vals_rel) < 20:
                    continue
                mu = vals_rel.mean() * sgn
                t_ = mu / (vals_rel.std() / np.sqrt(len(vals_rel)))
                mua = vals_abs.mean() * sgn
                rows.append(
                    dict(x0=x0, ev0=ev0, n=n, side=tag, N=len(vals_rel),
                         rel_mean_bps=mu * 1e4, rel_t=t_, abs_mean_bps=mua * 1e4,
                         hit=float((np.sign(vals_rel * sgn) > 0).mean()))
                )
df = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print("\nEvent study (mean fwd log-ret in bps, signed so + = snap-back profits):")
print(df.to_string(index=False, float_format=lambda v: f"{v:8.2f}"))

# regime split at the center threshold
x0, ev0, n = 2.0, 2.0, 3
flush = (x <= -x0) & (ev >= ev0) & elig
squeeze = (x >= x0) & (ev >= ev0) & elig
cum = lrf.shift(-1).rolling(n).sum().shift(-(n - 1))
cumm = lmkt.shift(-1).rolling(n).sum().shift(-(n - 1))
rel = cum.sub(cumm, axis=0)
print(f"\nregime split @ x0={x0} ev0={ev0} n={n}:")
for label in ("bull", "bear", "chop"):
    rmask = pd.Series(reg == label, index=close.index)
    for tag, mask, sgn in (("flushL", flush, +1), ("sqzS", squeeze, -1)):
        vals = rel[mask & rmask.values[:, None] if False else mask.loc[rmask[rmask].index.intersection(mask.index)]]
        vals = rel.loc[rmask[rmask].index].where(mask.loc[rmask[rmask].index]).stack().dropna()
        if len(vals) < 10:
            print(f"  {label:5s} {tag}: N<10")
            continue
        mu = vals.mean() * sgn
        t_ = mu / (vals.std() / np.sqrt(len(vals)))
        print(f"  {label:5s} {tag}: N={len(vals):5d} rel={mu*1e4:8.2f} bps t={t_:+.2f}")
