"""e01 follow-up — why are z-scores NaN through 2022 despite raw coverage 40?"""

import sys

sys.path.insert(
    0,
    "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/tournament/crypto/teams/team-06/out/scratch",
)
import lib06
import numpy as np
import pandas as pd

pn, aux, scoring = lib06.load()
r = aux["ls_accounts"]

for sym in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT"]:
    if sym not in r.columns:
        continue
    s = r[sym]
    for yr in ["2021", "2022", "2023"]:
        ss = s[yr]
        if not len(ss):
            continue
        print(
            f"{sym} {yr}: n={len(ss)} nan={ss.isna().sum()} nunique={ss.nunique()}"
            f" min={ss.min():.3f} max={ss.max():.3f}"
        )
    print()

# NaN pattern within 2022 for the cross-section: per-candle NaN count among eligible
elig = aux["eligibility"]
sub = r.loc["2022-01":"2023-02"]
esub = elig.loc["2022-01":"2023-02"]
cov = sub.notna().where(esub).sum(axis=1)
print("2022 weekly eligible coverage (count non-NaN):")
print(cov.resample("W").median().to_string())
