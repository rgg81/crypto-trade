"""ANTI-HYPE SCORECARD — a pre-registered gauntlet so a single lucky coin can't look like an edge.

Motivation (2026-06-18): this session repeatedly got HYPED by a single coin's OOS (deterministic
core ETH +0.41; walk-forward ETH +0.99) and then watched breadth deflate it. The fix is an
evaluation system, not another result. Any strategy that produces per-coin OOS trades is judged on:

  1. BREADTH      — % of coins with OOS mean trade return > 0 (+ binomial p vs coin-flip).
  2. POOLED POWER — pool ALL coins' OOS trades (large N); mean trade return + t-stat (is it really
                    > 0?), and trade-level Sharpe.
  3. NULL         — direction-shuffle: keep the same entries/magnitudes, randomize each trade's
                    sign B times; p_null = P(null pooled Sharpe >= real). If you can't beat random
                    signs, there is NO directional alpha.
  4. BENCHMARK    — buy-and-hold OOS monthly Sharpe per coin (the beta you get for free).

A strategy is "real" ONLY if: breadth majority (>50%, ideally >=60%) AND pooled t-stat significant
AND p_null < 0.05 AND it beats buy-and-hold on a majority. One coin's Sharpe proves nothing.

This module is strategy-agnostic: it imports the top-20 walk-forward sweep to get per-coin trades,
but `score()` accepts any {coin: trades_df} dict, so the SAME gauntlet will judge the pooled
LightGBM next (no re-deriving the bar per approach).
"""

from __future__ import annotations

import os
import sys
from math import comb

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # so the sibling import resolves
import top20_walkforward_sma_sweep as sweep  # noqa: E402  (run from repo root for data/ paths)

S = sweep

RNG = np.random.default_rng(42)
N_NULL = 2000


def pooled_oos(trades_by_coin: dict[str, pd.DataFrame]) -> np.ndarray:
    out = []
    for df in trades_by_coin.values():
        if df is None or df.empty:
            continue
        m = pd.to_datetime(df["close_time"], unit="ms")
        out.append(df.loc[m >= S.OOS_CUTOFF, "ret"].to_numpy())
    return np.concatenate(out) if out else np.array([])


def coin_oos_mean(df: pd.DataFrame) -> float:
    if df is None or df.empty:
        return float("nan")
    m = pd.to_datetime(df["close_time"], unit="ms")
    r = df.loc[m >= S.OOS_CUTOFF, "ret"].to_numpy()
    return float(r.mean()) if len(r) else float("nan")


def buy_hold_oos_sharpe(sym: str) -> float:
    d = S.load_klines(sym)
    if d is None:
        return float("nan")
    c = d[["open_time", "close"]].copy()
    c["m"] = pd.to_datetime(c["open_time"], unit="ms").dt.to_period("M").dt.to_timestamp()
    c = c[c["m"] >= S.OOS_CUTOFF]
    if len(c) < 30:
        return float("nan")
    monthly = c.groupby("m")["close"].last().pct_change().dropna()
    return monthly.mean() / monthly.std() * np.sqrt(12) if monthly.std() > 0 else float("nan")


def score(name: str, trades_by_coin: dict[str, pd.DataFrame], coins: list[str]) -> None:
    # 1. BREADTH
    coin_means = {s: coin_oos_mean(trades_by_coin.get(s)) for s in coins}
    valid = {s: v for s, v in coin_means.items() if not np.isnan(v)}
    n_pos = sum(v > 0 for v in valid.values())
    n = len(valid)
    # binomial tail P(X >= n_pos | p=0.5)
    p_breadth = sum(comb(n, k) for k in range(n_pos, n + 1)) / (2 ** n) if n else float("nan")

    # 2. POOLED POWER
    pr = pooled_oos(trades_by_coin)
    mu, sd, npool = pr.mean(), pr.std(ddof=1), len(pr)
    tstat = mu / (sd / np.sqrt(npool)) if (npool > 1 and sd > 0) else float("nan")
    trade_sharpe = mu / sd if sd > 0 else float("nan")

    # 3. NULL (direction shuffle on pooled trades) — signed move = ret + COST; flip signs.
    move = pr + S.COST
    real_sh = trade_sharpe
    null_sh = np.empty(N_NULL)
    for b in range(N_NULL):
        s = RNG.choice((-1.0, 1.0), size=npool)
        nr = s * move - S.COST
        null_sh[b] = nr.mean() / nr.std(ddof=1) if nr.std(ddof=1) > 0 else 0.0
    p_null = float((null_sh >= real_sh).mean()) if np.isfinite(real_sh) else float("nan")

    # 4. BENCHMARK (buy & hold)
    bh = {s: buy_hold_oos_sharpe(s) for s in coins}
    bh_median = float(np.nanmedian(list(bh.values())))

    verdict_pass = (
        all(np.isfinite([p_breadth, tstat, p_null]))
        and (p_breadth < 0.05) and (tstat > 2) and (p_null < 0.05)
    )
    verdict = (
        "PASSES gauntlet (real edge)" if verdict_pass
        else "FAILS gauntlet (indistinguishable from luck / coin-flip)"
    )
    print(f"\n================ ANTI-HYPE SCORECARD: {name} ================")
    print(f"1. BREADTH  : {n_pos}/{n} coins OOS+  (binomial p vs coin-flip {p_breadth:.3f})")
    print(f"2. POOLED   : N={npool} trades  mean={mu*100:+.3f}%  t-stat={tstat:+.2f}  "
          f"trade-Sharpe={trade_sharpe:+.3f}")
    print(f"3. NULL     : real trade-Sharpe={real_sh:+.3f}  vs direction-shuffle null "
          f"95th pct={np.quantile(null_sh, 0.95):+.3f}  ->  p_null={p_null:.3f}")
    print(f"4. BUY&HOLD : median coin B&H OOS Sharpe = {bh_median:+.2f} (must beat to add value)")
    print(f"VERDICT     : {verdict}")


def main() -> None:
    coins = [s for s in S.TOP20 if s != "MATICUSDT"]  # MATIC has no OOS (POL rename)
    wf, fx = {}, {}
    for sym in coins:
        d = S.load_klines(sym)
        if d is None or len(d) < 1000:
            continue
        ot, close, high, low, natr, grid = S.build_grid(d)
        wf[sym] = S.run_arm(grid, close, high, low, natr, ot, None)
        fx[sym] = S.run_arm(grid, close, high, low, natr, ot, 200)
    score("WALK-FORWARD SMA SELECT (top-20)", wf, coins)
    score("FIXED-200 SMA (top-20)", fx, coins)


if __name__ == "__main__":
    main()
