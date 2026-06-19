"""carry-iteration EXPLORATION-006 — CASH-AND-CARRY (spot-perp basis) funding harvest.

The perp-perp cross-sectional carry is CLOSED (no clean scalable alpha: beta-confounded,
capacity-killed, squeeze-prone). The funding income's CLEAN capturable form is the basis trade:
when funding > 0 (longs pay shorts), hold LONG SPOT + SHORT PERP, same notional. The price legs
offset ~1:1 (spot hedges the perp — no squeeze, no beta), and the short-perp position COLLECTS the
funding each 8h. Capacity = spot liquidity. This is the textbook funding harvest.

The catch is COST: each basis unit is TWO legs (spot + perp); a full round trip is ~4 x cost_side
(~0.28%), while funding is ~0.01-0.03% / 8h. So the trade only works at LOW TURNOVER — enter when
funding is positive, HOLD while it stays positive, exit when it flips. We test the funding-trailing
window and the entry threshold for that hold behavior, IS-emphasis (OOS shown), realistic execution
(decide close[t] -> fill open[t+1] both legs -> hold candle t+1 -> collect funding over t+1).
"""

from __future__ import annotations

import glob
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis")
import pair_engine as pe  # noqa: E402

LO0 = pd.Timestamp("2000-01-01")
HI1 = pd.Timestamp("2100-01-01")


def load_basis_coin(sym: str):
    """Return df[perp_open, spot_open, funding] aligned on open_time, or None if no usable spot."""
    perp = pe.load_coin(sym)
    if perp is None:
        return None
    spath = f"data/spot/{sym}/8h.csv"
    if not os.path.exists(spath):
        return None
    sp = pd.read_csv(spath)
    if len(sp) < 1000:
        return None
    spot_open = sp.set_index("open_time")["open"].astype(float)
    df = pd.DataFrame({"perp_open": perp["open"].astype(float), "funding": perp["funding_rate"]})
    df["spot_open"] = spot_open.reindex(df.index)
    df = df.dropna(subset=["spot_open", "perp_open"])
    return df if len(df) >= 1000 else None


def load_basis_universe() -> dict:
    syms = sorted(os.path.basename(p) for p in glob.glob("data/spot/*USDT")
                  if os.path.exists(f"{p}/8h.csv"))
    out = {}
    for s in syms:
        d = load_basis_coin(s)
        if d is not None:
            out[s] = d
    return out


def build_basis_book(coins: dict, m_fund: int = 3, thresh: float = 0.0,
                     cost_side: float = pe.COST_SIDE):
    """Long spot / short perp on coins with trailing funding > thresh; equal weight; earn funding.

    Returns (net, price_leg, funding_leg, weights). Cost = cost_side * 2 * turnover (TWO legs).
    """
    perp = pd.DataFrame({s: d["perp_open"] for s, d in coins.items()}).sort_index()
    spot = pd.DataFrame({s: d["spot_open"] for s, d in coins.items()}).reindex(perp.index)
    fund = pd.DataFrame({s: d["funding"] for s, d in coins.items()}).reindex(perp.index)
    r_perp = perp.shift(-2) / perp.shift(-1) - 1.0          # short perp over hold candle t+1
    r_spot = spot.shift(-2) / spot.shift(-1) - 1.0          # long spot over hold candle t+1
    fund_earn = fund.shift(-1)                              # short-perp earns funding over t+1
    ftrail = fund.rolling(m_fund).mean()
    active = ((ftrail > thresh) & r_perp.notna() & r_spot.notna()
              & fund_earn.notna() & spot.shift(-1).notna() & perp.shift(-1).notna())
    n = active.sum(axis=1).replace(0, np.nan)
    w = active.div(n, axis=0).fillna(0.0)                   # equal-weight basis units
    price = (w * (r_spot - r_perp)).sum(axis=1)             # basis convergence (hedged ~0)
    funding = (w * fund_earn).sum(axis=1)                   # the income
    cost = cost_side * 2.0 * (w - w.shift(1)).abs().sum(axis=1)
    net = (price + funding - cost)
    idx = pd.to_datetime(perp.index, unit="ms")
    for s in (net, price, funding):
        s.index = idx
    w.index = idx
    return net.dropna(), price, funding, w


def msh(s: pd.Series, lo, hi) -> float:
    return pe.monthly_sharpe(s, lo, hi)


def report(label: str, net: pd.Series, price: pd.Series, funding: pd.Series, w) -> None:
    eq = (1 + net).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    turn = float((w - w.shift(1)).abs().sum(axis=1).mean())
    held = (w != 0).sum(axis=1)
    med = int(held[held > 0].median()) if (held > 0).any() else 0
    print(f"  {label:24} net IS={msh(net, LO0, pe.OOS_CUTOFF):+.2f} "
          f"OOS={msh(net, pe.OOS_CUTOFF, HI1):+.2f} | DD={dd*100:4.0f}% "
          f"turn={turn:.2f} medCoins={med}")
    print(f"      decomp: funding IS={msh(funding, LO0, pe.OOS_CUTOFF):+.2f}"
          f" OOS={msh(funding, pe.OOS_CUTOFF, HI1):+.2f} | basis(price) "
          f"IS={msh(price, LO0, pe.OOS_CUTOFF):+.2f} OOS={msh(price, pe.OOS_CUTOFF, HI1):+.2f}")


def main() -> None:
    coins = load_basis_universe()
    print(f"CASH-AND-CARRY (spot-perp basis) — {len(coins)} coins with spot+perp+funding")
    for m, th in [(1, 0.0), (3, 0.0), (3, 0.0001), (9, 0.0), (9, 0.0001)]:
        net, price, funding, w = build_basis_book(coins, m_fund=m, thresh=th)
        report(f"M={m} thresh={th}", net, price, funding, w)


if __name__ == "__main__":
    main()
