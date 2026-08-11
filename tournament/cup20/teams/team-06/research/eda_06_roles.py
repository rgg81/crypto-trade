"""Team 06 EDA 6 -- the long / short / chop role checks.

The organiser's packet reports each sleeve's gross PnL and the four fold Sharpes, which covers the
long and short roles and a coarse regime split. It does not report a return stream, so the CHOP role
has to be measured offline, on the same targets the frozen strategy emits. Disclosed as an offline
diagnostic: the regime label is causal (trailing market return only), but the scoring is this
laboratory's, not the organiser's.

Regimes are terciles of the trailing 63-bar (21-day) equal-weight return of the point-in-time top-20
measured strictly before the bar being attributed.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-06/research")
from lab import BARS_PER_YEAR, _hold_path  # noqa: E402
from signals import load_panel  # noqa: E402

from crypto_trade.tournament.engine_v2 import generate_targets  # noqa: E402
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN  # noqa: E402

IS_START = pd.Timestamp("2020-08-17", tz="UTC")
IS_END = pd.Timestamp("2024-08-01T00:00:00Z")

candidate = sys.argv[1] if len(sys.argv) > 1 else "downside-tercile"
path = Path("tournament/cup20/teams/team-06/candidates") / candidate / "strategy.py"
spec = importlib.util.spec_from_file_location("team06_roles", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

bars = pd.read_parquet("data/cup20/is/bars.parquet")
funding_raw = pd.read_parquet("data/cup20/is/funding.parquet")
membership = pd.read_parquet("data/cup20/is/membership.parquet")
grid = pd.date_range(IS_START, IS_END, freq="8h", inclusive="left")
targets = generate_targets(
    module.build_strategy(), bars, funding_raw, membership, list(grid), seed=20200817
)

P = load_panel()
opens, closes, member, fund = P["opens"], P["closes"], P["member"], P["funding"]
cols = opens.columns
acted = targets[REBALANCE_INSTRUCTION_COLUMN].astype(bool).to_numpy()
W = targets.drop(columns=[REBALANCE_INSTRUCTION_COLUMN]).reindex(columns=cols).astype(float)
vals = W.fillna(0.0).to_numpy().copy()
vals[~acted, :] = np.nan
W = pd.DataFrame(vals, index=W.index, columns=cols)
gross_w = W.abs().sum(axis=1)
W = W.div(gross_w.where(gross_w > 0), axis=0)

fwd = (opens.shift(-1) / opens - 1.0).reindex(columns=cols).loc[W.index]
fundr = fund.shift(-1).reindex(columns=cols).loc[W.index].fillna(0.0)
eff = fwd.fillna(0.0) + fundr
held, turn = _hold_path(W, eff)

pnl = held * eff.to_numpy()
long_pnl = pd.Series(np.where(held > 0, pnl, 0.0).sum(axis=1), index=W.index)
short_pnl = pd.Series(np.where(held < 0, pnl, 0.0).sum(axis=1), index=W.index)
total = long_pnl + short_pnl

lr = np.log(closes).diff()
mkt = lr.where(member).mean(axis=1)
trail = mkt.rolling(63).sum().shift(1).reindex(W.index)
q1, q2 = trail.quantile(1 / 3), trail.quantile(2 / 3)
regime = pd.Series(
    np.where(trail <= q1, "market_down", np.where(trail >= q2, "market_up", "chop")),
    index=W.index,
)

print(f"candidate: {candidate}   ({int(acted.sum())} rebalance boundaries)\n")
print(f"{'regime':12s} {'bars':>6s} {'ann.ret':>9s} {'Sharpe':>8s} {'long PnL':>10s} {'short PnL':>10s}")
for name in ("market_down", "chop", "market_up", "ALL"):
    m = np.ones(len(W), dtype=bool) if name == "ALL" else (regime == name).to_numpy()
    seg = total[m]
    if len(seg) < 10:
        continue
    sharpe = seg.mean() / seg.std() * np.sqrt(BARS_PER_YEAR)
    ann = seg.mean() * BARS_PER_YEAR
    print(
        f"{name:12s} {m.sum():6d} {ann:+9.3f} {sharpe:+8.2f} "
        f"{long_pnl[m].sum():+10.3f} {short_pnl[m].sum():+10.3f}"
    )

print("\nsleeve gross PnL by fold (offline; the packet reports the whole-window figure):")
for name, lo, hi in [
    ("F1", "2020-08-17", "2021-08-01"),
    ("F2", "2021-08-01", "2022-08-01"),
    ("F3", "2022-08-01", "2023-08-01"),
    ("F4", "2023-08-01", "2024-08-01"),
]:
    m = (W.index >= pd.Timestamp(lo, tz="UTC")) & (W.index < pd.Timestamp(hi, tz="UTC"))
    print(f"  {name}  long {long_pnl[m].sum():+.3f}   short {short_pnl[m].sum():+.3f}")

net_exposure = pd.Series(held.sum(axis=1), index=W.index)
print(
    f"\nnet dollar exposure under the beta tilt: mean {net_exposure.mean():+.3f} "
    f"min {net_exposure.min():+.3f} max {net_exposure.max():+.3f}"
)

# --- does the tilt actually neutralise market beta, or just shift dollars? ---
book = total.reindex(W.index)
m = mkt.reindex(W.index).fillna(0.0)
ok = book.notna() & m.notna()
b = np.polyfit(m[ok], book[ok], 1)
resid = book[ok] - (b[0] * m[ok] + b[1])
print(
    f"\nbook return regressed on the equal-weight market: beta {b[0]:+.4f}, "
    f"alpha {b[1] * BARS_PER_YEAR:+.4f}/yr, R^2 {1 - resid.var() / book[ok].var():.4f}"
)
for name, lo, hi in [("F1","2020-08-17","2021-08-01"),("F2","2021-08-01","2022-08-01"),
                     ("F3","2022-08-01","2023-08-01"),("F4","2023-08-01","2024-08-01")]:
    s = (W.index >= pd.Timestamp(lo, tz="UTC")) & (W.index < pd.Timestamp(hi, tz="UTC"))
    sel = ok.to_numpy() & s
    bb = np.polyfit(m[sel], book[sel], 1)
    print(f"  {name} beta {bb[0]:+.4f}")
