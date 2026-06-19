"""carry-iteration EXPLORATION-004 — split the carry into LONG vs SHORT leg, test capacity per leg.

The critic BLOCKED the combined short-high/long-low carry on realizability: a liquidity floor
inverts net OOS (premium in untradeable illiquid coins). The QR IS-decomposition showed the LONG
leg (long lowest-funding = crowded shorts) as the +309% IS price HERO; the SHORT leg as the drag.

DECISIVE QUESTION: is the capacity problem confined to the SHORT leg (illiquid high-funding squeeze
magnets), while the LONG leg SURVIVES a liquidity floor? If so, a long-tilted / liquid book is the
deployable direction. We split the book's per-coin weights into long (w>0) and short (w<0) and
evaluate each leg's net across liquidity floors (None / $5M / $20M). IS-ONLY emphasis; OOS shown for
context but NOT used to choose anything.

Also: a long-only book is long beta, so we compare the long leg to longing the WHOLE eligible
universe equal-weight (the alt-beta benchmark) — is long-low-funding ALPHA over beta, or just beta?
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis")
import broad_carry as bc  # noqa: E402
import pair_engine as pe  # noqa: E402

LO0 = pd.Timestamp("2000-01-01")
HI1 = pd.Timestamp("2100-01-01")


def panels(coins: dict):
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).sort_index()
    funds = pd.DataFrame({s: d["funding_rate"] for s, d in coins.items()}).reindex(opens.index)
    ret = opens.shift(-2) / opens.shift(-1) - 1.0
    fund_earn = funds.shift(-1)
    ret.index = pd.to_datetime(opens.index, unit="ms")
    fund_earn.index = ret.index
    return ret, fund_earn


def leg_net(w_leg: pd.DataFrame, ret: pd.DataFrame, fund_earn: pd.DataFrame,
            cost_side: float = pe.COST_SIDE) -> pd.Series:
    r = ret.reindex(index=w_leg.index, columns=w_leg.columns)
    f = fund_earn.reindex(index=w_leg.index, columns=w_leg.columns)
    price = (w_leg * r).sum(axis=1)
    funding = -(w_leg * f).sum(axis=1)
    cost = cost_side * (w_leg - w_leg.shift(1)).abs().sum(axis=1)
    return (price + funding - cost).dropna()


def stat(net: pd.Series) -> str:
    eq = (1 + net).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    return (f"IS={pe.monthly_sharpe(net, LO0, pe.OOS_CUTOFF):+.2f} "
            f"OOS={pe.monthly_sharpe(net, pe.OOS_CUTOFF, HI1):+.2f} maxDD={dd*100:4.0f}%")


def main() -> None:
    coins = bc.load_universe()
    ret, fund_earn = panels(coins)
    print("EXPLORATION-004: per-leg capacity test (long vs short, across liquidity floors)")
    print("  (long-only/short-only legs are NOT market-neutral — long leg carries alt beta)")
    for label, liq in [("no floor", None), ("$5M floor", 5e6), ("$20M floor", 2e7)]:
        _, w = bc.build_book(coins, min_history=1095, min_liquidity=liq)
        long_w = w.clip(lower=0.0)
        short_w = w.clip(upper=0.0)
        ln, sn = leg_net(long_w, ret, fund_earn), leg_net(short_w, ret, fund_earn)
        comb = leg_net(w, ret, fund_earn)
        print(f"\n  [{label}]")
        print(f"    LONG leg  (long lowest-funding): {stat(ln)}")
        print(f"    SHORT leg (short highest-funding): {stat(sn)}")
        print(f"    COMBINED market-neutral:          {stat(comb)}")
    # alt-beta benchmark ($5M floor): long the WHOLE eligible universe equal-weight (no selection)
    _, w = bc.build_book(coins, min_history=1095, min_liquidity=5e6)
    elig = (w != 0)
    n = elig.sum(axis=1).replace(0, np.nan)
    ew = elig.div(n, axis=0).fillna(0.0)                       # equal-weight long-only eligible
    long_low = leg_net(w.clip(lower=0.0), ret, fund_earn)
    short_high = leg_net(w.clip(upper=0.0), ret, fund_earn)
    print("\n  ALPHA-vs-BETA ($5M floor): is each leg better than equal-weight ALL (pure beta)?")
    print(f"    long-low-funding leg:          {stat(long_low)}")
    print(f"    long-ALL equal-weight (+beta): {stat(leg_net(ew, ret, fund_earn))}")
    print(f"    short-high-funding leg:        {stat(short_high)}")
    print(f"    short-ALL equal-weight (-beta):{stat(leg_net(-ew, ret, fund_earn))}")


if __name__ == "__main__":
    main()
