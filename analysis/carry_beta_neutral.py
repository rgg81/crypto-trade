"""carry-iteration EXPLORATION-005 — per-coin BETA-NEUTRAL funding harvest (the decisive last test).

EXPLORATION-004 showed the carry's OOS returns are ALT-BETA, not funding-selection alpha, and the
dollar-neutral book is NOT beta-neutral. The last intellectually-honest question: if we remove the
market beta PROPERLY — hedge the book's net beta with BTC each candle, using PAST-ONLY per-coin
rolling betas — does the real, regime-stable funding INCOME survive as a clean, beta-neutral edge?
(The risk-engineer's CRUDE static BTC/ETH hedge killed the net; this is the proper time-varying,
per-coin-beta version.)

Method: beta_i[t] = past-only rolling cov(r_i, r_btc)/var(r_btc) (window 90, shifted). Portfolio
beta = sum_i w_i beta_i. Hedge return = -port_beta * r_btc (short the net beta in BTC). Beta-neutral
net = carry_net + hedge. If beta-neutral OOS is clearly positive AND survives a floor -> a real
clean edge. If it collapses (like the dollar-neutral net under a floor) -> the carry is just beta +
uncapturable income, and the scalable-alpha axis is closed.
"""

from __future__ import annotations

import sys

import pandas as pd

sys.path.insert(0, "analysis")
import broad_carry as bc  # noqa: E402
import pair_engine as pe  # noqa: E402

LO0 = pd.Timestamp("2000-01-01")
HI1 = pd.Timestamp("2100-01-01")
BETA_WIN = 90


def stat(net: pd.Series) -> str:
    eq = (1 + net).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    return (f"IS={pe.monthly_sharpe(net, LO0, pe.OOS_CUTOFF):+.2f} "
            f"OOS={pe.monthly_sharpe(net, pe.OOS_CUTOFF, HI1):+.2f} maxDD={dd*100:4.0f}%")


def main() -> None:
    coins = bc.load_universe()
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).sort_index()
    ret = (opens.shift(-2) / opens.shift(-1) - 1.0)
    ret.index = pd.to_datetime(opens.index, unit="ms")
    rb = ret["BTCUSDT"]
    # past-only per-coin rolling beta vs BTC (hold-candle returns; estimated on data <= t-1)
    mb = rb.rolling(BETA_WIN).mean().shift(1)
    varb = (rb.pow(2)).rolling(BETA_WIN).mean().shift(1) - mb.pow(2)
    cov = (ret.mul(rb, axis=0)).rolling(BETA_WIN).mean().shift(1) \
        - ret.rolling(BETA_WIN).mean().shift(1).mul(mb, axis=0)
    beta = cov.div(varb, axis=0)

    print("EXPLORATION-005: per-coin BETA-NEUTRAL funding harvest (hedge net beta with BTC)")
    for label, liq in [("no floor", None), ("$5M floor", 5e6)]:
        book, w = bc.build_book(coins, min_history=1095, min_liquidity=liq)
        w = w.reindex(index=ret.index).fillna(0.0)
        carry_net = book["net"]
        port_beta = (w * beta.reindex(index=w.index, columns=w.columns)).sum(axis=1)
        hedge = -(port_beta * rb)
        bn = (carry_net + hedge.reindex(carry_net.index).fillna(0.0)).dropna()
        print(f"\n  [{label}]  median |port_beta| = {port_beta.abs().median():.2f}")
        print(f"    dollar-neutral (raw carry): {stat(carry_net)}")
        print(f"    BETA-NEUTRAL (BTC-hedged):  {stat(bn)}")


if __name__ == "__main__":
    main()
