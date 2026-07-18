"""e01 — coverage diagnostic: OI breadth vs eligible breadth over time."""

import sys

sys.path.insert(0, "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/analysis")
from portfolio_tournament import engine as te

pn, aux, scoring = te.load_is_panels()

elig = aux["eligibility"]
oi = aux["oi"]
close = pn["close"]

n_elig = elig.sum(axis=1)
n_close = (close.notna() & elig).sum(axis=1)
n_oi = (oi.notna() & elig).sum(axis=1)

df = (
    n_elig.to_frame("elig")
    .assign(kline=n_close, oi=n_oi)
    .resample("MS")
    .median()
    .astype(int)
)
print("monthly median counts (eligible / eligible-with-kline / eligible-with-OI):")
print(df.to_string())

frac = (n_oi / n_elig).resample("MS").median()
first_80 = frac[frac >= 0.8]
print("\nfirst month with median OI coverage >= 80% of eligibles:",
      first_80.index[0].date() if len(first_80) else "never")
print("grid span:", close.index[0], "->", close.index[-1], " candles:", len(close))
print("symbols in panel:", close.shape[1])
