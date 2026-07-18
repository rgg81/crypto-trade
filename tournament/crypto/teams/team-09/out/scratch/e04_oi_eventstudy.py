"""e04 — OI-collapse-conditioned event study on 2022+ (honest OI window), with entry delays."""

import sys

import numpy as np
import pandas as pd

sys.path.insert(
    0,
    "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/tournament/crypto/teams/team-09/out/scratch",
)
import sig  # noqa: F401  (path setup)
from portfolio_tournament import engine as te

pn, aux, scoring = te.load_is_panels()
close, high, low, qv = pn["close"], pn["high"], pn["low"], pn["quote_volume"]
elig = aux["eligibility"]
oi = aux["oi"]

k = 2
r1 = np.log(close).diff()
sigma = r1.rolling(42, min_periods=28).std().clip(lower=0.001)
x = r1.rolling(k).sum() / (sigma * np.sqrt(k))
tr = (high - low) / close
rs = tr.rolling(k).mean() / tr.rolling(90, min_periods=60).mean().shift(k)
vs = qv.rolling(k).mean() / qv.rolling(90, min_periods=60).mean().shift(k)
ev = np.sqrt(rs * vs)
oi_drop = -(oi / oi.shift(k) - 1.0)  # + = collapse fraction

rf = pn["ret_fwd"]
elig_f = elig.astype(float).where(elig)
mkt = (rf * elig_f).mean(axis=1)
lrf = np.log1p(rf)
lmkt = np.log1p(mkt)

WLO = pd.Timestamp("2022-01-01")
in_win = close.index >= WLO

x0, ev0 = 2.0, 1.5
base_flush = (x <= -x0) & (ev >= ev0) & elig
base_sqz = (x >= x0) & (ev >= ev0) & elig

rows = []
for oi_tag, oi_thr in (("noOI", None), ("oi5", 0.05), ("oi10", 0.10)):
    if oi_thr is None:
        flush, sqz = base_flush, base_sqz
    else:
        conf = oi_drop >= oi_thr
        flush, sqz = base_flush & conf, base_sqz & conf
    flush = flush.loc[in_win]
    sqz = sqz.loc[in_win]
    for d in (0, 2, 3, 6):
        for n in (1, 3, 6, 9):
            # hold rows t+d+1 .. t+d+n  (enter open[t+d+1])
            cum = lrf.shift(-(d + 1)).rolling(n).sum().shift(-(n - 1))
            cumm = lmkt.shift(-(d + 1)).rolling(n).sum().shift(-(n - 1))
            rel = cum.sub(cumm, axis=0).loc[in_win]
            for tag, mask, sgn in (("flushL", flush, +1), ("sqzS", sqz, -1)):
                vals = rel.where(mask).stack().dropna()
                if len(vals) < 20:
                    rows.append(dict(oi=oi_tag, d=d, n=n, side=tag, N=len(vals),
                                     rel_bps=np.nan, t=np.nan, hit=np.nan))
                    continue
                mu = vals.mean() * sgn
                t_ = mu / (vals.std() / np.sqrt(len(vals)))
                rows.append(dict(oi=oi_tag, d=d, n=n, side=tag, N=len(vals),
                                 rel_bps=mu * 1e4, t=t_,
                                 hit=float((np.sign(vals * sgn) > 0).mean())))

df = pd.DataFrame(rows)
pd.set_option("display.width", 220)
for side in ("flushL", "sqzS"):
    piv = df[df.side == side].pivot_table(
        index=["oi", "d"], columns="n", values=["rel_bps", "t", "N"], aggfunc="first"
    )
    print(f"\n=== {side} (signed + = snap-back profits), 2022-01..2024-06 ===")
    print(piv.to_string(float_format=lambda v: f"{v:8.1f}"))
