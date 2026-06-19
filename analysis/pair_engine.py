"""REALISTIC market-neutral PAIR backtest engine (foundation) — 2026-06-18.

Replaces the close-to-close research proxy with a deployment-grade execution model so the backtest
"reproduces real scenarios" (user requirement). Conventions MATCH the live engine so results are
directly comparable to the deployed strategy.

EXECUTION MODEL (the load-bearing realism):
  - DECIDE on candle t's CLOSE (signal uses data through close[t] only — rolling windows END at t).
  - FILL at candle t+1's OPEN (one-bar execution latency; you cannot trade the close you just used).
  - HOLD candle t+1: price P&L = open[t+2]/open[t+1]-1; funding earned = the funding settled over
    candle t+1 (future of the decision -> earned, not used in the signal -> no leak).
  - COST = 0.07%/side (fee 0.1% round-trip + 2bps/side slippage, live-engine convention) applied
    to per-leg turnover |Δw| at each rebalance.
  - Dollar-neutral pair: w_b = -w_a, |w_a| in {0,1} (full long one / short other, flips on signal).
  - Strictly no look-ahead: the weight at t depends only on data <= close[t] (leak-tested below).

Signals (configurable): carry (short higher-funding) / momentum / mean-reversion of log(A/B) /
combos. All past-only. The engine returns per-candle net + funding/price/cost decomposition.

Self-tests (run on import via pytest tests/test_pair_engine.py): (1) NO-LOOKAHEAD — corrupting data
after t never changes the weight at t; (2) FLAT MARKET — constant prices + zero funding => net is
exactly -turnover cost; (3) PURE FUNDING — constant prices + constant funding diff => funding income
equals the analytic expectation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

OOS_CUTOFF = pd.Timestamp("2025-03-24")
FEE_PCT = 0.1          # round-trip fee %, live-engine convention
SLIP_BPS = 2.0         # slippage bps/side, live-engine convention
COST_SIDE = FEE_PCT / 100 / 2 + SLIP_BPS / 1e4   # per-side fraction = 0.0007 (0.07%)
Z_WIN = 90
M_FUND = 9

CONFIGS = {  # (w_rev, w_carry, rev_sign): rev_sign -1 = mean-reversion, +1 = momentum
    "carry": (0.0, 1.0, -1),
    "mom": (1.0, 0.0, +1),
    "rev": (1.0, 0.0, -1),
    "mom+carry": (1.0, 1.0, +1),
    "rev+carry": (1.0, 1.0, -1),
}


def load_coin(sym: str) -> pd.DataFrame | None:
    """open_time-indexed open/close/funding/quote_volume on the 8h grid (funding NaN->0)."""
    cols = ["open_time", "open", "close", "quote_volume"]
    try:
        k = pd.read_csv(f"data/{sym}/8h.csv", usecols=cols)
        fr = pd.read_csv(f"data/funding_rates/{sym}.csv")
    except (FileNotFoundError, ValueError):
        return None
    k = k.dropna(subset=["open_time", "open", "close"]).drop_duplicates("open_time")
    k = k.sort_values("open_time")
    step = 8 * 60 * 60 * 1000
    fr = fr.dropna(subset=["funding_time", "funding_rate"]).copy()
    fr["open_time"] = (fr["funding_time"] // step) * step
    fr = fr.groupby("open_time", as_index=False)["funding_rate"].mean()
    d = k.merge(fr, on="open_time", how="left")
    d["funding_rate"] = d["funding_rate"].fillna(0.0)
    return d.set_index("open_time")[["open", "close", "funding_rate", "quote_volume"]]


def build_pair(a: str, b: str) -> pd.DataFrame | None:
    da, db = load_coin(a), load_coin(b)
    if da is None or db is None:
        return None
    j = da.join(db, lsuffix="_a", rsuffix="_b", how="inner")
    return j if len(j) > Z_WIN + 10 else None


def signal_weights(df: pd.DataFrame, config: str, z_win: int = Z_WIN,
                   m_fund: int = M_FUND) -> np.ndarray:
    """w_a[t] decided at CLOSE[t] (rolling windows end at t; NO forward shift). w_b = -w_a."""
    w_rev, w_carry, rev_sign = CONFIGS[config]
    spread = np.log(df["close_a"]) - np.log(df["close_b"])
    z = (spread - spread.rolling(z_win).mean()) / spread.rolling(z_win).std()
    fd = df["funding_rate_a"].rolling(m_fund).mean() - df["funding_rate_b"].rolling(m_fund).mean()
    fdz = (fd - fd.rolling(z_win).mean()) / fd.rolling(z_win).std()
    combo = w_rev * rev_sign * z.to_numpy() + w_carry * (-fdz.to_numpy())
    w = np.sign(np.nan_to_num(combo, nan=0.0))
    return w  # length N; entries before warmup are 0 (flat)


def run(df: pd.DataFrame, w_a: np.ndarray, cost_side: float = COST_SIDE) -> pd.DataFrame:
    """Realistic next-bar-open backtest. Returns per-candle (net, price, funding, cost) for the HOLD
    candle, indexed by the hold candle's open_time. close[t] decision -> open[t+1] fill -> hold."""
    oa, ob = df["open_a"].to_numpy(), df["open_b"].to_numpy()
    fa, fb = df["funding_rate_a"].to_numpy(), df["funding_rate_b"].to_numpy()
    ot = df.index.to_numpy()
    n = len(df)
    # decision t (0..n-3): fill at open[t+1], exit at open[t+2], hold candle = t+1
    t = np.arange(0, n - 2)
    wa = w_a[t]
    price = wa * (oa[t + 2] / oa[t + 1] - 1.0) - wa * (ob[t + 2] / ob[t + 1] - 1.0)
    funding = -(wa * fa[t + 1] - wa * fb[t + 1])           # short higher-funding leg collects
    dwa = np.abs(np.diff(w_a[: n - 1], prepend=0.0))[t]    # leg-A turnover at open[t+1] rebalance
    cost = 2.0 * cost_side * dwa                            # two legs, |Δw_b| = |Δw_a|
    net = price + funding - cost
    return pd.DataFrame(
        {"net": net, "price": price, "funding": funding, "cost": cost},
        index=pd.to_datetime(ot[t + 1], unit="ms"),
    )


def monthly_sharpe(s: pd.Series, lo, hi) -> float:
    x = s[(s.index >= lo) & (s.index < hi)]
    g = x.groupby(x.index.to_period("M")).sum()
    return g.mean() / g.std() * np.sqrt(12) if len(g) > 1 and g.std() > 0 else float("nan")


def evaluate(df: pd.DataFrame, config: str) -> dict:
    w = signal_weights(df, config)
    bt = run(df, w)
    lo0, hi1 = pd.Timestamp("2000-01-01"), pd.Timestamp("2100-01-01")
    yr = bt["net"].groupby(bt.index.year).sum()
    return {
        "is_sh": monthly_sharpe(bt["net"], lo0, OOS_CUTOFF),
        "oos_sh": monthly_sharpe(bt["net"], OOS_CUTOFF, hi1),
        "is_yrs_pos": float((yr[yr.index < 2025] > 0).mean()),
        "net_by_year": {int(k): round(v * 100, 1) for k, v in yr.items()},
        "n": len(bt),
    }


def main() -> None:
    print(f"REALISTIC PAIR ENGINE (cost={COST_SIDE*100:.3f}%/leg, next-bar-open, real funding)")
    for a, b in [("AAVEUSDT", "LDOUSDT"), ("BTCUSDT", "ETHUSDT"), ("FTMUSDT", "THETAUSDT")]:
        df = build_pair(a, b)
        if df is None:
            print(f"  {a}/{b}: insufficient data")
            continue
        print(f"\n{a[:-4]}/{b[:-4]} ({len(df)} candles):")
        for cfg in ("carry", "mom", "rev"):
            r = evaluate(df, cfg)
            print(f"  {cfg:>10}: IS={r['is_sh']:+.2f} OOS={r['oos_sh']:+.2f} "
                  f"IS_yrs+={r['is_yrs_pos']:.2f}  net%/yr={r['net_by_year']}")


if __name__ == "__main__":
    main()
