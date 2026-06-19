"""BROAD CROSS-SECTIONAL FUNDING CARRY — the canonical market-neutral strategy.

Winner of the head-to-head (analysis/carry_broad_vs_pairs.py): selecting NOTHING and trading the
whole funding cross-section generalizes far better than IS-selected pairs (OOS +2.61 vs +0.63,
positive every year 2020-2026, OOS > IS = genuine edge). This is the deployable strategy, on the
REALISTIC engine (pair_engine conventions: next-bar-open fills, real 8h funding, 0.07%/leg cost).

MECHANISM (market-neutral, all past-only):
  - signal at close[t] = trailing-M-mean funding per coin (data <= t).
  - among coins eligible at t (finite signal + finite next-two opens + finite next funding), rank by
    funding; SHORT the top FRAC (crowded longs pay shorts), LONG the bottom FRAC, equal-weight,
    dollar-neutral (sum w = 0, gross = 2*FRAC*N_eligible normalized to +/-1/k each leg).
  - FILL at open[t+1], HOLD candle t+1: price = open[t+2]/open[t+1]-1; funding settled over t+1;
    cost = 0.07%/side on per-coin turnover.

build_book() returns the per-candle net + (price, funding, cost) decomposition AND the per-coin
weight matrix (needed for the drawdown/capacity work). evaluate() runs the gauntlet.
"""

from __future__ import annotations

import glob
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis")
import pair_engine as pe  # noqa: E402

M_FUND = 9
FRAC = 0.25
LIQ_WIN = 90        # trailing-liquidity window (30d of 8h candles) for the capacity floor
LO0 = pd.Timestamp("2000-01-01")
HI1 = pd.Timestamp("2100-01-01")


def load_universe() -> dict:
    syms = sorted(p.split("/")[-1][:-4] for p in glob.glob("data/funding_rates/*USDT.csv"))
    coins = {s: pe.load_coin(s) for s in syms}
    return {s: d for s, d in coins.items() if d is not None}


def build_book(coins: dict, m_fund: int = M_FUND, frac: float = FRAC,
               cost_side: float = pe.COST_SIDE,
               exclude_top_pctl: float | None = None,
               min_liquidity: float | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Realistic broad cross-sectional carry. Returns (book[net,price,funding,cost], weights).

    exclude_top_pctl: if set (e.g. 0.90), drop coins whose trailing funding is above that per-row
        percentile BEFORE ranking — i.e. don't short the most extreme-funding 'squeeze magnets'.
    min_liquidity: if set (e.g. 5e6), a coin is eligible only when its trailing-30d mean 8h
        quote-volume (past-only) >= this floor — the CAPACITY filter (the headline number is
        optimistic without it; ~$5M roughly halves OOS Sharpe but is realizable-at-size).
    """
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).sort_index()
    funds = pd.DataFrame({s: d["funding_rate"] for s, d in coins.items()}).reindex(opens.index)
    ftrail = funds.rolling(m_fund).mean()                 # signal <= t
    ret = opens.shift(-2) / opens.shift(-1) - 1.0         # hold candle t+1
    fund_earn = funds.shift(-1)                            # funding settled over candle t+1
    elig = ftrail.notna() & ret.notna() & fund_earn.notna()
    if min_liquidity is not None:                          # past-only capacity floor
        qv = pd.DataFrame({s: d["quote_volume"] for s, d in coins.items()}).reindex(opens.index)
        liq = qv.rolling(LIQ_WIN).mean().shift(1)
        elig = elig & (liq >= min_liquidity)
    ft_np, elig_np = ftrail.to_numpy(), elig.to_numpy()
    wvals = np.zeros_like(ft_np)
    for i in range(len(opens.index)):
        ecols = np.where(elig_np[i])[0]
        if exclude_top_pctl is not None and len(ecols) >= 4:
            thr = np.quantile(ft_np[i, ecols], exclude_top_pctl)
            ecols = ecols[ft_np[i, ecols] <= thr]         # drop the extreme-high-funding magnets
        k = int(len(ecols) * frac)
        if len(ecols) < 4 or k < 1:
            continue
        order = ecols[np.argsort(ft_np[i, ecols])]        # ascending funding
        wvals[i, order[:k]] = 1.0 / k                     # lowest funding -> LONG
        wvals[i, order[-k:]] = -1.0 / k                   # highest funding -> SHORT
    w = pd.DataFrame(wvals, index=opens.index, columns=opens.columns)
    price = (w * ret).sum(axis=1)
    funding = -(w * fund_earn).sum(axis=1)
    cost = cost_side * (w - w.shift(1)).abs().sum(axis=1)
    book = pd.DataFrame({"net": price + funding - cost, "price": price,
                         "funding": funding, "cost": cost})
    book.index = pd.to_datetime(opens.index, unit="ms")
    w.index = book.index
    return book.dropna(), w


def evaluate(book: pd.DataFrame, w: pd.DataFrame) -> dict:
    net = book["net"]
    eq = (1 + net).cumprod()
    yr = net.groupby(net.index.year).sum()
    is_idx = book.index[book.index < pe.OOS_CUTOFF]
    fis = book["funding"].loc[is_idx].groupby(is_idx.to_period("M")).sum()
    turnover = (w.diff().abs().sum(axis=1)).mean()
    return {
        "is_sh": pe.monthly_sharpe(net, LO0, pe.OOS_CUTOFF),
        "oos_sh": pe.monthly_sharpe(net, pe.OOS_CUTOFF, HI1),
        "fund_is_sh": pe.monthly_sharpe(book["funding"], LO0, pe.OOS_CUTOFF),
        "fund_oos_sh": pe.monthly_sharpe(book["funding"], pe.OOS_CUTOFF, HI1),
        "fund_is_t": fis.mean() / (fis.std() / np.sqrt(len(fis))) if len(fis) > 1 else float("nan"),
        "max_dd": float((eq / eq.cummax() - 1).min()),
        "net_by_year": {int(k): round(v * 100, 0) for k, v in yr.items()},
        "avg_turnover": float(turnover),
        "n": len(net),
    }


def main() -> None:
    coins = load_universe()
    print(f"BROAD CROSS-SECTIONAL CARRY (realistic engine; {len(coins)} coins, "
          f"M={M_FUND}, FRAC={FRAC})")
    for label, min_liq in [("research (NO capacity floor)", None),
                           ("realizable ($5M liquidity floor)", 5e6)]:
        book, w = build_book(coins, min_liquidity=min_liq)
        r = evaluate(book, w)
        print(f"\n  [{label}]")
        print(f"    net   : IS Sharpe={r['is_sh']:+.2f}  OOS Sharpe={r['oos_sh']:+.2f}  "
              f"maxDD={r['max_dd']*100:.0f}%")
        print(f"    funding-only: IS={r['fund_is_sh']:+.2f} OOS={r['fund_oos_sh']:+.2f} "
              f"(IS monthly t={r['fund_is_t']:+.2f})")
        print(f"    turnover={r['avg_turnover']:.2f} | net%/yr={r['net_by_year']}")
    print("\n  NOTE: the $5M-floor row is the capacity-respecting headline; the no-floor row is "
          "research-only (leans on illiquid coins).")


if __name__ == "__main__":
    main()
