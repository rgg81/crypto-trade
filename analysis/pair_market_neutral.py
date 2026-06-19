"""PAIR MARKET-NEUTRAL strategy (any pair) — spread mean-reversion + funding carry — 2026-06-18.

User spec: for any pair (A,B), run a market-neutral book (one long / one short, equal $),
rebalancing/inverting EVERY tick, profiting from momentum + funding + any other mechanism,
robust across regimes. Start with one pair, then scale.

What the anti-hype gauntlet already taught us shapes the design:
  - directional RELATIVE MOMENTUM (predict which leg rises) failed everywhere -> for a
    market-neutral PAIR the classic edge is SPREAD MEAN-REVERSION (stat-arb): when log(A/B)
    stretches from its rolling mean, bet on reversion. We TEST trend-vs-revert, not assume.
  - FUNDING CARRY is the verified structural edge -> here an income tilt (short higher-funding leg).
Combined per-tick signal -> w_A = sign(combo), w_B = -w_A (dollar-neutral, full long/short, flips
on sign). P&L = price + funding - turnover cost. ALL signals past-only (.shift(1)); walk-forward.

EVALUATION = regime-robustness (per-YEAR Sharpe — the "all regimes" bar, tested not assumed) +
IS/OOS + maxDD. No fitted params except z-window / trailing-funding window / combo weights.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

OOS_CUTOFF = pd.Timestamp("2025-03-24")
Z_WIN = 90        # spread z-score rolling window (30d at 8h)
M_FUND = 9        # trailing-funding window (3d)
COST_SIDE = 0.07 / 100


def load(sym: str) -> pd.DataFrame | None:
    try:
        k = pd.read_csv(f"data/{sym}/8h.csv", usecols=["open_time", "close"])
        fr = pd.read_csv(f"data/funding_rates/{sym}.csv")
    except (FileNotFoundError, ValueError):
        return None
    k = k.dropna().drop_duplicates("open_time").sort_values("open_time")
    step = 8 * 60 * 60 * 1000
    fr = fr.dropna(subset=["funding_time", "funding_rate"]).copy()
    fr["open_time"] = (fr["funding_time"] // step) * step
    fr = fr.groupby("open_time", as_index=False)["funding_rate"].mean()
    d = k.merge(fr, on="open_time", how="left")
    d["funding_rate"] = d["funding_rate"].fillna(0.0)
    return d.sort_values("open_time").reset_index(drop=True)


def build(sym_a: str, sym_b: str, z_win: int, m_fund: int) -> pd.DataFrame:
    a, b = load(sym_a), load(sym_b)
    m = a.merge(b, on="open_time", suffixes=("_a", "_b")).sort_values("open_time")
    m = m.reset_index(drop=True)
    ca, cb = m["close_a"], m["close_b"]
    spread = np.log(ca) - np.log(cb)
    mu = spread.rolling(z_win).mean()
    sd = spread.rolling(z_win).std()
    m["z"] = ((spread - mu) / sd).shift(1)                              # past-only spread z-score
    fa = m["funding_rate_a"].rolling(m_fund).mean()
    fb = m["funding_rate_b"].rolling(m_fund).mean()
    m["fdiff_z"] = ((fa - fb) - (fa - fb).rolling(z_win).mean()).div(
        (fa - fb).rolling(z_win).std()).shift(1)                       # past-only funding-diff z
    m["ra"] = ca.shift(-1) / ca - 1.0                                  # next-candle returns
    m["rb"] = cb.shift(-1) / cb - 1.0
    m["fa_earn"] = m["funding_rate_a"].shift(-1)                       # funding over held candle
    m["fb_earn"] = m["funding_rate_b"].shift(-1)
    return m


def backtest(m: pd.DataFrame, w_rev: float, w_carry: float, rev_sign: int = -1) -> pd.Series:
    """w_A = sign(combo); rev_sign=-1 = mean-reversion (short rich), +1 = momentum (chase)."""
    d = m.dropna(subset=["z", "fdiff_z", "ra", "rb", "fa_earn", "fb_earn"]).copy()
    combo = w_rev * (rev_sign * d["z"]) + w_carry * (-d["fdiff_z"])    # both tilt w_A
    wa = np.sign(combo).to_numpy()
    wb = -wa
    price = wa * d["ra"].to_numpy() + wb * d["rb"].to_numpy()
    fund = -(wa * d["fa_earn"].to_numpy() + wb * d["fb_earn"].to_numpy())
    turn = np.abs(np.diff(wa, prepend=0.0)) + np.abs(np.diff(wb, prepend=0.0))
    net = price + fund - COST_SIDE * turn
    return pd.Series(net, index=pd.to_datetime(d["open_time"].to_numpy(), unit="ms"))


def backtest_adaptive(m: pd.DataFrame, w_carry: float, ac_win: int = 60) -> pd.Series:
    """REGIME-ADAPTIVE: pick momentum vs mean-reversion per tick from the spread's recent
    autocorrelation (past-only). dspread lag-1 autocorr > 0 => trending => momentum (chase z);
    < 0 => ranging => mean-revert (fade z). Plus the carry tilt. The 'all-regimes' attempt.
    """
    d = m.dropna(subset=["z", "fdiff_z", "ra", "rb", "fa_earn", "fb_earn"]).copy()
    # rolling lag-1 autocorrelation of spread first-differences, past-only
    dz = d["z"].diff()
    ac = dz.rolling(ac_win).apply(
        lambda x: pd.Series(x).autocorr(lag=1) if pd.Series(x).std() > 0 else 0.0, raw=False
    ).shift(1)
    rev_sign = np.where(ac.to_numpy() > 0, 1.0, -1.0)  # +1 momentum (trend), -1 reversion (range)
    combo = rev_sign * d["z"].to_numpy() + w_carry * (-d["fdiff_z"].to_numpy())
    wa = np.sign(combo)
    wb = -wa
    price = wa * d["ra"].to_numpy() + wb * d["rb"].to_numpy()
    fund = -(wa * d["fa_earn"].to_numpy() + wb * d["fb_earn"].to_numpy())
    turn = np.abs(np.diff(wa, prepend=0.0)) + np.abs(np.diff(wb, prepend=0.0))
    net = price + fund - COST_SIDE * turn
    return pd.Series(net, index=pd.to_datetime(d["open_time"].to_numpy(), unit="ms"))


def sharpe(s: pd.Series, lo, hi) -> float:
    x = s[(s.index >= lo) & (s.index < hi)]
    g = x.groupby(x.index.to_period("M")).sum()
    return g.mean() / g.std() * np.sqrt(12) if len(g) > 1 and g.std() > 0 else float("nan")


def report(name: str, net: pd.Series) -> None:
    lo0, hi1 = pd.Timestamp("2000-01-01"), pd.Timestamp("2100-01-01")
    yr = net.groupby(net.index.year).sum() * 100
    by_year = {int(k): round(v, 0) for k, v in yr.items()}
    eq = (1 + net).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    is_s, oos_s = sharpe(net, lo0, OOS_CUTOFF), sharpe(net, OOS_CUTOFF, hi1)
    print(f"  {name:26} IS={is_s:+.2f} OOS={oos_s:+.2f} maxDD={dd*100:5.0f}%  net%/yr={by_year}")


def main() -> None:
    pair = ("BTCUSDT", "ETHUSDT")
    m = build(*pair, Z_WIN, M_FUND)
    print(f"PAIR MARKET-NEUTRAL: {pair[0]}/{pair[1]}  (z_win={Z_WIN}, m_fund={M_FUND}); "
          f"{len(m)} candles. Per-year net% = the regime-robustness test.")
    print("\nComponent isolation (IS / OOS monthly Sharpe, maxDD, per-year net%):")
    report("mean-reversion only", backtest(m, 1.0, 0.0, rev_sign=-1))
    report("momentum only", backtest(m, 1.0, 0.0, rev_sign=+1))
    report("carry only", backtest(m, 0.0, 1.0))
    report("mean-rev + carry", backtest(m, 1.0, 1.0, rev_sign=-1))
    report("momentum + carry", backtest(m, 1.0, 1.0, rev_sign=+1))
    report("REGIME-ADAPTIVE + carry", backtest_adaptive(m, 1.0))
    report("REGIME-ADAPTIVE (no carry)", backtest_adaptive(m, 0.0))


if __name__ == "__main__":
    main()
