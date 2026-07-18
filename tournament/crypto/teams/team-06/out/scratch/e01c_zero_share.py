"""e01 follow-up 2 — quantify 2022 corruption (zero-share, partial sums) and test whether
the ratio-of-sums (tt_ls_positions / ls_accounts) is count-invariant-clean in 2022."""

import sys

sys.path.insert(
    0,
    "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/tournament/crypto/teams/team-06/out/scratch",
)
import lib06
import numpy as np
import pandas as pd

pn, aux, scoring = lib06.load()
elig = aux["eligibility"]
ls = aux["ls_accounts"]
tt = aux["tt_ls_positions"]

# monthly zero-share among eligible non-NaN cells, 2021-10 .. 2023-06
cells = ls.where(elig)
zero = (cells == 0.0).sum(axis=1)
nn = cells.notna().sum(axis=1)
zs = (zero / nn.where(nn > 0)).loc["2021-10":"2023-06"]
print("monthly mean zero-share of eligible ls_accounts cells:")
print(zs.groupby(zs.index.to_period("M")).mean().round(3).to_string())

# distribution of nonzero ls_accounts in 2022 vs 2023 for BTC (partial-sum smear check)
for yr in ["2022", "2023"]:
    v = ls["BTCUSDT"][yr]
    v = v[v > 0]
    print(f"\nBTC {yr} nonzero: n={len(v)} q05={v.quantile(0.05):.1f} q50={v.median():.1f} "
          f"q95={v.quantile(0.95):.1f}")

# ratio-of-sums validity in 2022: spread = log(tt/ls) where both > 0
spread = np.log(tt.where(tt > 0) / ls.where(ls > 0))
sp_cov = spread.notna().where(elig).sum(axis=1)
print("\nmonthly median eligible coverage of spread log(tt/ls):")
mc = sp_cov.loc["2021-10":"2023-06"]
print(mc.groupby(mc.index.to_period("M")).median().to_string())

# sanity of spread values in 2022 vs 2023 (should be ~log of ratio ~ [-1.5, 1.5])
for yr in ["2022", "2023"]:
    v = spread.loc[yr].stack()
    print(f"spread {yr}: n={len(v)} q01={v.quantile(0.01):.2f} q50={v.median():.2f} "
          f"q99={v.quantile(0.99):.2f}")

# z-coverage of the spread with W=90
zs90 = lib06.zpanel(np.exp(spread), 90)  # zpanel takes ratio>0; exp(log)=tt/ls
cov = zs90.notna().where(elig).sum(axis=1)
qq = cov.groupby(cov.index.to_period("Q")).median()
print("\nquarterly median eligible z90-coverage of spread:")
print(qq.to_string())
