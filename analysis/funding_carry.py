"""FUNDING-RATE CARRY (market-neutral) — BTC-ETH pair + cross-sectional — 2026-06-18.

User idea: market-neutral pairs (equal $ long/short), harvest the FUNDING-RATE differential (carry).
Why this is different from the momentum that failed: the carry income is OBSERVED, not predicted.
Perp funding settles every 8h; when funding>0 LONGS PAY SHORTS. So SHORT the high-funding (crowded
long) coins and LONG the low/negative-funding coins, dollar-neutral → price hedged, harvest the
funding spread. The question shifts from "predict price" (hard, failed) to "does the funding spread
survive the price-hedge noise + costs" (structural, favorable).

NO MAGIC NUMBERS / NO CHEATING / HONEST WALK-FORWARD:
  - Signal at candle t = trailing mean funding over [t-M, t-1] (PAST-ONLY, .shift(1)).
  - The position set at t (from past signal) earns the funding SETTLED during the held candle
    [t, t+1) = funding[t+1] (f.shift(-1)) and the price move close[t]->close[t+1]. No look-ahead.
  - funding P&L of position i = -w_i * f_earned_i  (long pays +f, short receives +f).
  - price P&L = w_i * r1_i (dollar-neutral → ~0 mean, the hedge noise).
  - No fitted parameters except M (trailing window) + k (book width) — both standard, not tuned.

EVALUATION (anti-hype gauntlet): IS/OOS monthly Sharpe; per-period returns are NON-overlapping
(each 8h period's funding+price realized that period → no overlap inflation); decomposition into
funding-income vs price-hedge P&L (shows WHERE the edge is); a shuffled-signal null (randomize which
coins are long/short → a random dollar-neutral book collects ~0 net funding) to prove the funding
RANKING is the source, not chance.
"""

from __future__ import annotations

import glob

import numpy as np
import pandas as pd

OOS_CUTOFF = pd.Timestamp("2025-03-24")
M_TRAIL = 9    # trailing-funding signal window (9 x 8h = 3 days)
K_SIDE = 5     # cross-sectional: short top-5 funding, long bottom-5 (dollar-neutral)
COST_SIDE = 0.07 / 100
RNG = np.random.default_rng(42)
N_NULL = 250


def load_coin(sym: str) -> pd.DataFrame | None:
    """Merge 8h klines + funding on the 8h grid → open_time, close, funding."""
    try:
        k = pd.read_csv(f"data/{sym}/8h.csv", usecols=["open_time", "close"])
        fr = pd.read_csv(f"data/funding_rates/{sym}.csv")
    except (FileNotFoundError, ValueError):
        return None
    k = k.dropna().drop_duplicates("open_time").sort_values("open_time")
    # floor funding_time to the 8h grid → align to candle open_time
    step = 8 * 60 * 60 * 1000
    fr = fr.dropna(subset=["funding_time", "funding_rate"]).copy()
    fr["open_time"] = (fr["funding_time"] // step) * step
    fr = fr.groupby("open_time", as_index=False)["funding_rate"].mean()
    d = k.merge(fr, on="open_time", how="left").sort_values("open_time").reset_index(drop=True)
    d["funding_rate"] = d["funding_rate"].fillna(0.0)
    return d if len(d) > 1000 else None


def build_panel(universe: list[str]):
    frames = []
    for sym in universe:
        d = load_coin(sym)
        if d is None:
            continue
        c = d["close"].astype(float)
        f = d["funding_rate"].astype(float)
        g = pd.DataFrame({"open_time": d["open_time"].to_numpy(), "coin": sym})
        g["signal"] = f.rolling(M_TRAIL).mean().shift(1)   # PAST-ONLY trailing funding
        g["f_earned"] = f.shift(-1)                         # funding settled over the held candle
        g["r1"] = c.shift(-1) / c - 1.0                     # price move over the held candle
        frames.append(g)
    return pd.concat(frames, ignore_index=True)


def carry_book(panel: pd.DataFrame, weight_fn) -> pd.DataFrame:
    """Per-period funding-income, price-pnl, net (after cost). weight_fn(group)->w_i Series."""
    rows = []
    prev = None
    for ot, g in panel.dropna(subset=["signal", "f_earned", "r1"]).groupby("open_time"):
        w = weight_fn(g)
        if w is None:
            continue
        w = w.reindex(g["coin"].to_numpy()).fillna(0.0)
        f = pd.Series(g["f_earned"].to_numpy(), index=g["coin"].to_numpy())
        r = pd.Series(g["r1"].to_numpy(), index=g["coin"].to_numpy())
        fund_pnl = float(-(w * f).sum())     # long pays +f, short receives +f
        price_pnl = float((w * r).sum())     # dollar-neutral hedge noise
        if prev is None:
            turn = w.abs().sum()
        else:
            allc = w.index.union(prev.index)
            turn = (w.reindex(allc).fillna(0.0) - prev.reindex(allc).fillna(0.0)).abs().sum()
        rows.append((ot, fund_pnl, price_pnl, fund_pnl + price_pnl - COST_SIDE * turn))
        prev = w
    cols = ["open_time", "fund_pnl", "price_pnl", "net"]
    return pd.DataFrame(rows, columns=cols).set_index("open_time")


def xsec_weights(g: pd.DataFrame):
    if len(g) < 2 * K_SIDE:
        return None
    gg = g.sort_values("signal")
    w = pd.Series(0.0, index=g["coin"].to_numpy())
    w[gg["coin"].to_numpy()[:K_SIDE]] = 1.0 / K_SIDE       # lowest funding → LONG
    w[gg["coin"].to_numpy()[-K_SIDE:]] = -1.0 / K_SIDE     # highest funding → SHORT
    return w


def pair_weights(g: pd.DataFrame):
    g = g[g["coin"].isin(("BTCUSDT", "ETHUSDT"))]
    if set(g["coin"]) != {"BTCUSDT", "ETHUSDT"}:
        return None
    s = g.set_index("coin")["signal"]
    hi = s.idxmax()
    lo = s.idxmin()
    return pd.Series({hi: -1.0, lo: 1.0})  # short higher-funding, long lower-funding (equal $)


def monthly_sharpe(ret: pd.Series, lo, hi) -> tuple[float, int]:
    if ret.empty:
        return float("nan"), 0
    idx = pd.to_datetime(ret.index, unit="ms")
    m = pd.Series(ret.to_numpy(), index=idx)
    m = m[(m.index >= lo) & (m.index < hi)]
    g = m.groupby(m.index.to_period("M")).sum()
    sh = g.mean() / g.std() * np.sqrt(12) if len(g) > 1 and g.std() > 0 else float("nan")
    return sh, len(m)


def report(name: str, book: pd.DataFrame, panel: pd.DataFrame, weight_fn) -> None:
    lo0, hi1 = pd.Timestamp("2000-01-01"), pd.Timestamp("2100-01-01")
    is_sh, n_is = monthly_sharpe(book["net"], lo0, OOS_CUTOFF)
    oos_sh, n_oos = monthly_sharpe(book["net"], OOS_CUTOFF, hi1)
    idx = pd.to_datetime(book.index, unit="ms")
    oos = book.loc[idx >= OOS_CUTOFF]
    # annualized contribution decomposition (per-period mean x periods/yr, OOS)
    ppy = 365.25 * 3
    print(f"\n========= FUNDING CARRY: {name} — ANTI-HYPE SCORECARD =========")
    print(f"OOS funding income  = {oos['fund_pnl'].mean()*ppy*100:+.1f}%/yr (harvested spread)")
    print(f"OOS price-hedge P&L = {oos['price_pnl'].mean()*ppy*100:+.1f}%/yr (~0 = the noise)")
    print(f"OOS net (after cost)= {oos['net'].mean()*ppy*100:+.1f}%/yr")
    print(f"IS  monthly Sharpe (net) = {is_sh:+.3f} (periods={n_is})")
    print(f"OOS monthly Sharpe (net) = {oos_sh:+.3f} (periods={n_oos})")
    # NULL: shuffle the signal within each period → random dollar-neutral book
    null_oos = []
    base = panel.dropna(subset=["signal", "f_earned", "r1"]).copy()
    for _ in range(N_NULL):
        sh = base.copy()
        sh["signal"] = sh.groupby("open_time")["signal"].transform(
            lambda x: RNG.permutation(x.to_numpy()))
        nb = carry_book(sh, weight_fn)
        s, _ = monthly_sharpe(nb["net"], OOS_CUTOFF, hi1)
        if np.isfinite(s):
            null_oos.append(s)
    null_oos = np.array(null_oos)
    p_null = (float((null_oos >= oos_sh).mean())
              if (np.isfinite(oos_sh) and len(null_oos)) else float("nan"))
    print(f"NULL (shuffled funding signal) OOS Sharpe 95th pct = "
          f"{np.quantile(null_oos, 0.95):+.3f}  ->  p_null = {p_null:.3f}")
    real = bool(np.isfinite(oos_sh) and oos_sh > 0 and np.isfinite(p_null) and p_null < 0.05)
    print(f"VERDICT: {'PASSES (real funding-carry edge)' if real else 'FAILS (not significant)'}")


def main() -> None:
    funding_syms = sorted(p.split("/")[-1][:-4] for p in glob.glob("data/funding_rates/*USDT.csv"))
    panel = build_panel(funding_syms)
    n = panel["coin"].nunique()
    print(f"funding-carry panel: {n} coins, {len(panel)} rows")
    # 1) BTC-ETH pair
    pair_book = carry_book(panel, pair_weights)
    report("BTC-ETH PAIR", pair_book, panel, pair_weights)
    # 2) cross-sectional carry across the funding universe
    xs_book = carry_book(panel, xsec_weights)
    label = f"CROSS-SECTIONAL ({n} coins, short-top{K_SIDE}/long-bottom{K_SIDE})"
    report(label, xs_book, panel, xsec_weights)


if __name__ == "__main__":
    main()
