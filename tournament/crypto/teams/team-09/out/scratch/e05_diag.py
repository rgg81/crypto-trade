"""e05 — trades-field / composition-signal diagnostics (no P&L)."""

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/analysis")
from portfolio_tournament import engine as te

pn, aux, scoring = te.load_is_panels()
qv, tr_, close = pn["quote_volume"], pn["trades"], pn["close"]
elig = aux["eligibility"]

# (a) coverage: eligible names with valid trades (>0)
valid = (tr_ > 0) & elig
cov = (valid.sum(axis=1) / elig.sum(axis=1)).resample("QS").median()
print("quarterly median fraction of eligible names with trades>0:")
print(cov.to_string(float_format=lambda v: f"{v:.3f}"))

W, B = 21, 90
mpW, mpB = int(np.ceil(0.8 * W)), int(np.ceil(0.8 * B))
ats_num = qv.rolling(W, min_periods=mpW).sum() / tr_.rolling(W, min_periods=mpW).sum()
ats_den = (qv.rolling(B, min_periods=mpB).sum() / tr_.rolling(B, min_periods=mpB).sum()).shift(W)
comp = np.log(ats_num / ats_den).where(elig)

# (b) distribution + persistence
flat = comp.stack().dropna()
print(f"\ncomp distribution: N={len(flat)} mean={flat.mean():+.4f} sd={flat.std():.4f} "
      f"p1={flat.quantile .__self__.quantile(0.01):+.3f}" if False else
      f"\ncomp distribution: N={len(flat)} mean={flat.mean():+.4f} sd={flat.std():.4f} "
      f"p1={flat.quantile(0.01):+.3f} p99={flat.quantile(0.99):+.3f}")

rank = comp.rank(axis=1)
rank = rank.sub(rank.mean(axis=1), axis=0).div(rank.count(axis=1), axis=0)  # centered
print("\ncross-sectional rank autocorrelation (mean per-name corr of rank_t vs rank_{t-lag}):")
for lag in (1, 3, 9, 21, 63):
    a, b = rank, rank.shift(lag)
    both = a.notna() & b.notna()
    corrs = []
    for c in rank.columns:
        m = both[c]
        if m.sum() > 200:
            corrs.append(np.corrcoef(a[c][m], b[c][m])[0, 1])
    print(f"  lag {lag:3d}: {np.nanmean(corrs):+.3f}   (names={len(corrs)})")

# (c) confound map — cross-sectional Spearman of comp vs candidates, mean over candles
def sums(f, w, mp):
    return f.rolling(w, min_periods=mp).sum()

vol_spike = np.log(sums(qv, W, mpW) / sums(qv, B, mpB).shift(W) * (B / W)).where(elig)
cnt_spike = np.log(sums(tr_, W, mpW) / sums(tr_, B, mpB).shift(W) * (B / W)).where(elig)
ret21 = np.log(close).diff(21).where(elig)
size = np.log(qv.rolling(B, min_periods=mpB).mean()).where(elig)

def mean_xsec_spearman(a, b, min_n=15):
    ra, rb = a.rank(axis=1), b.rank(axis=1)
    both = ra.notna() & rb.notna()
    n = both.sum(axis=1)
    ra, rb = ra.where(both), rb.where(both)
    za = ra.sub(ra.mean(axis=1), axis=0).div(ra.std(axis=1), axis=0)
    zb = rb.sub(rb.mean(axis=1), axis=0).div(rb.std(axis=1), axis=0)
    corr = (za * zb).mean(axis=1)[n >= min_n]
    return float(corr.mean()), int(len(corr))

for name, other in (("vol_spike", vol_spike), ("count_spike", cnt_spike),
                    ("ret_21", ret21), ("size(qv90)", size)):
    c, n = mean_xsec_spearman(comp, other)
    print(f"xsec Spearman(comp, {name:11s}) = {c:+.3f}   over {n} candles")
