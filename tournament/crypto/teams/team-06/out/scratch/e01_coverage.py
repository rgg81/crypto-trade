"""e01 — coverage diagnostic for the 4 positioning-ratio panels (eligible names only)."""

import sys

sys.path.insert(
    0,
    "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/tournament/crypto/teams/team-06/out/scratch",
)
import lib06
import pandas as pd

pn, aux, scoring = lib06.load()
elig = aux["eligibility"]

print("grid:", pn["open"].index[0], "->", pn["open"].index[-1], "candles:", len(pn["open"]))
print("symbols in panel:", pn["open"].shape[1])
print("eligible names/candle: median", float(elig.sum(axis=1).median()))

rows = []
for key in lib06.RATIO_KEYS:
    r = aux[key]
    raw_cov = r.notna().where(elig).sum(axis=1)
    z = lib06.zpanel(r, 90)
    z_cov = z.notna().where(elig).sum(axis=1)
    first_raw = raw_cov[raw_cov > 0].index[0] if (raw_cov > 0).any() else None
    med_roll = z_cov.rolling(90, min_periods=1).median()
    t0_cand = med_roll[med_roll >= 25]
    t0 = t0_cand.index[0] if len(t0_cand) else None
    rows.append((key, str(first_raw), str(t0)))
    qs = raw_cov.groupby(raw_cov.index.to_period("Q")).median()
    zqs = z_cov.groupby(z_cov.index.to_period("Q")).median()
    print(f"\n== {key} ==  first nonzero eligible coverage: {first_raw}   T0(z>=25 sustained): {t0}")
    print(pd.DataFrame({"raw_med": qs, "z90_med": zqs}).to_string())

print("\nsummary:")
for k, f, t in rows:
    print(f"  {k:18s} first={f}  T0={t}")
