"""EDA 4 -- fold stability, does the signature beat market stress alone, and what does it cost?

Three questions that decide whether the lane supports a candidate:

  A. Is the snap-back present in all four chronological folds, or only in the bull ones?
  B. Does the per-symbol liquidity signature add anything once market-wide stress is conditioned
     on?  (If not, the honest description is "buy the market after a cascade", not "trade the
     shock signature".)
  C. What does a concrete overlapping-slice book turn over, and what is its gross edge per unit
     of that turnover?

C is an APPROXIMATION of the weight path, not a scorer: no costs, no risk unit, no funding, no
caps, no floors. It exists to rank constructions before spending trials, never to stand in for the
organiser's numbers.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-05/research")

from panel import build_panel, forward_from_open, summarise  # noqa: E402

P = build_panel(lookback=60)
op, ret, sigma = P["open"], P["ret"], P["sigma"]
mask = P["tradable"]
fwd = forward_from_open(op, horizons=(1, 2, 3, 4, 6))
fwd_r = {h: f.where(mask) for h, f in fwd.items()}

z = (ret / sigma).where(mask)
ts = P["tspike"].where(mask)
vs = P["vspike"].where(mask)
rr = P["rr"].where(mask)

mkt_ret = ret.where(mask).mean(axis=1)
mkt_sig = mkt_ret.rolling(60, min_periods=30).std().shift(1)
mkt_z = mkt_ret / mkt_sig
MZ = pd.DataFrame(np.repeat(mkt_z.to_numpy()[:, None], z.shape[1], axis=1),
                  index=z.index, columns=z.columns)

FOLDS = {
    "F1 2020-08..2021-08": ("2020-08-01", "2021-08-01"),
    "F2 2021-08..2022-08": ("2021-08-01", "2022-08-01"),
    "F3 2022-08..2023-08": ("2022-08-01", "2023-08-01"),
    "F4 2023-08..2024-08": ("2023-08-01", "2024-08-01"),
}


def fold_mask(index: pd.DatetimeIndex, lo: str, hi: str) -> np.ndarray:
    return (index >= pd.Timestamp(lo, tz="UTC")) & (index < pd.Timestamp(hi, tz="UTC"))


print("=" * 104)
print("A. Fold stability of the down-shock snap-back (RAW forward, h=3)")
print("   signal:  z <= -2.0  AND  tspike >= 2.0     |   control: z <= -2.0 only")
print("=" * 104)
sig_sel = (z <= -2.0) & (ts >= 2.0)
ctl_sel = z <= -2.0
for name, (lo, hi) in FOLDS.items():
    rows = fold_mask(z.index, lo, hi)
    for tag, sel in (("SIGNATURE", sig_sel), ("control  ", ctl_sel)):
        v = fwd_r[3].where(sel).loc[rows].to_numpy().ravel()
        base = fwd_r[3].loc[rows].to_numpy().ravel()
        base = base[np.isfinite(base)]
        print("   " + summarise(f"{name} {tag}", v)
              + f"   basket-baseline={base.mean() * 1e4:>7.2f}bp")

print()
print("=" * 104)
print("B. Does the signature add WITHIN market-stress buckets? (RAW forward h=3)")
print("=" * 104)
for lo_b, hi_b in [(-99, -2.0), (-2.0, -1.0), (-1.0, 0.0), (0.0, 99)]:
    band = (MZ >= lo_b) & (MZ < hi_b)
    for tag, extra in (
        ("all members       ", band),
        ("z<=-2             ", band & (z <= -2.0)),
        ("z<=-2 & ts>=2     ", band & (z <= -2.0) & (ts >= 2.0)),
        ("z<=-2 & ts>=3     ", band & (z <= -2.0) & (ts >= 3.0)),
        ("z<=-2 & ts<1.5    ", band & (z <= -2.0) & (ts < 1.5)),
    ):
        print("   " + summarise(f"mkt_z[{lo_b},{hi_b}) {tag}",
                                fwd_r[3].where(extra).to_numpy().ravel()))
    print()

print("=" * 104)
print("C. Up-shock short sleeve: is there ANY subset that reverts? (short pays -RAW, h in 1..6)")
print("=" * 104)
up = z >= 2.0
for tag, sel in (
    ("plain up-shock        ", up),
    ("up + tspike>=2        ", up & (ts >= 2.0)),
    ("up + tspike<1.5       ", up & (ts < 1.5)),
    ("up during mkt squeeze ", up & (MZ >= 1.5)),
    ("up in calm market     ", up & (MZ.abs() < 1.0)),
    ("up during mkt stress  ", up & (MZ <= -1.0)),
):
    for h in (1, 2, 3, 6):
        print("   " + summarise(f"{tag} h={h}", (-fwd_r[h]).where(sel).to_numpy().ravel()))

print()
print("=" * 104)
print("D. Book shape: how many names are active, and what does the weight path turn over?")
print("=" * 104)


def simulate(zth: float, tsth: float, hold: int, top_k: int | None = None) -> dict:
    """Approximate weight path of an overlapping-slice long book. Not a scorer."""
    flag = ((z <= zth) & (ts >= tsth)).fillna(False)
    if top_k is not None:
        # keep only the top_k most-shocked names at each boundary
        score = (-z).where(flag)
        rank = score.rank(axis=1, ascending=False)
        flag = flag & (rank <= top_k)
    raw = flag.astype(float)
    active = raw.rolling(hold, min_periods=1).max()  # a name is held for `hold` bars after a shock
    active = active.where(mask.reindex_like(active).fillna(False), 0.0)
    gross = active.sum(axis=1)
    w = active.div(gross.where(gross > 0, np.nan), axis=0).fillna(0.0)
    dw = w.diff().abs().sum(axis=1)
    dw.iloc[0] = w.iloc[0].abs().sum()
    n_bars = len(w)
    years = n_bars / 1095.0
    turn = float(dw.sum()) / years
    # gross arithmetic PnL of the weight path, no costs, entering at next open
    step = (op.shift(-2) / op.shift(-1) - 1.0).where(mask)
    pnl = (w * step.fillna(0.0)).sum(axis=1)
    invested = float((gross > 0).mean())
    names = float(gross[gross > 0].mean()) if (gross > 0).any() else 0.0
    total_turn = float(dw.sum())
    edge_bps = float(pnl.sum()) / total_turn * 1e4 if total_turn > 0 else float("nan")
    daily = pnl.groupby(pd.DatetimeIndex(w.index).floor("D")).sum()
    sharpe = float(daily.mean() / daily.std() * np.sqrt(365)) if daily.std() > 0 else float("nan")
    return {
        "turnover/yr": turn,
        "invested%": invested * 100,
        "avg names": names,
        "gross ann%": float(pnl.sum()) / years * 100,
        "edge bps/turn": edge_bps,
        "gross sharpe": sharpe,
    }


print(f"{'config':<44}" + "".join(f"{k:>15}" for k in
      ["turnover/yr", "invested%", "avg names", "gross ann%", "edge bps/turn", "gross sharpe"]))
for zth in (-1.5, -2.0, -2.5):
    for tsth in (1.0, 1.5, 2.0, 3.0):
        for hold in (2, 3, 4, 6):
            r = simulate(zth, tsth, hold)
            label = f"z<={zth} ts>={tsth} hold={hold}"
            print(f"{label:<44}" + "".join(f"{v:>15.2f}" for v in r.values()))
