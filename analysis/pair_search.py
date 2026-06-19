"""PAIR SEARCH — exploration/confirmation to find the best market-neutral (pair, config).

User directive: make the market-neutral pair strategy a skill option, run it as iterations
(EXPLORATION -> CONFIRMATION) to find the best pair AND configuration. This is the search engine.

The prototype proved hand-picking one pair (BTC-ETH) is the wrong unit: no static price signal is
all-weather. So SEARCH the whole universe of pairs x configs, with the anti-cheating discipline that
this session learned the hard way (the bundle selection-bias):

  EXPLORATION  — score every (pair, config) on IN-SAMPLE only (IS Sharpe + regime-consistency =
                 fraction of IS YEARS positive). Rank, take the top-K. NO OOS is touched here.
  CONFIRMATION — reveal OOS (Sharpe + per-year + DD) for the IS-top-K ONLY. The honest test of
                 whether IS-selection generalizes (it usually does NOT for price signals; carry-
                 dominated pairs should hold).

Each candidate = a pair (A,B) x a config (carry / momentum / reversion / momentum+carry /
reversion+carry). Dollar-neutral, per-tick long/short, all signals past-only. Universe = the funding
coins (carry needs funding) with enough history. This is the reusable kernel for a pair-iteration
track; formalizing it into the skill (agents/phases) is the follow-up once it surfaces a winner.
"""

from __future__ import annotations

import glob
from itertools import combinations

import numpy as np
import pandas as pd

OOS_CUTOFF = pd.Timestamp("2025-03-24")
Z_WIN = 90
M_FUND = 9
COST_SIDE = 0.07 / 100
MIN_OVERLAP = 2500          # min shared candles for a pair to be considered
TOP_K = 20                  # IS-top candidates carried to confirmation
CONFIGS = ["carry", "mom", "rev", "mom+carry", "rev+carry"]


def load_coin(sym: str):
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
    return d.set_index("open_time")[["close", "funding_rate"]] if len(d) > 1000 else None


def pair_net(sub: pd.DataFrame, config: str) -> pd.Series:
    ca, cb = np.log(sub["ca"]), np.log(sub["cb"])
    spread = ca - cb
    z = ((spread - spread.rolling(Z_WIN).mean()) / spread.rolling(Z_WIN).std()).shift(1)
    fa_t = sub["fa"].rolling(M_FUND).mean()
    fb_t = sub["fb"].rolling(M_FUND).mean()
    fd = fa_t - fb_t
    fdz = ((fd - fd.rolling(Z_WIN).mean()) / fd.rolling(Z_WIN).std()).shift(1)
    ra = sub["ca"].shift(-1) / sub["ca"] - 1.0
    rb = sub["cb"].shift(-1) / sub["cb"] - 1.0
    fae, fbe = sub["fa"].shift(-1), sub["fb"].shift(-1)
    df = pd.DataFrame({"z": z, "fdz": fdz, "ra": ra, "rb": rb, "fae": fae, "fbe": fbe}).dropna()
    if len(df) < MIN_OVERLAP:
        return pd.Series(dtype=float)
    w_rev, w_carry, rev_sign = {
        "carry": (0.0, 1.0, -1), "mom": (1.0, 0.0, +1), "rev": (1.0, 0.0, -1),
        "mom+carry": (1.0, 1.0, +1), "rev+carry": (1.0, 1.0, -1),
    }[config]
    combo = w_rev * rev_sign * df["z"].to_numpy() + w_carry * (-df["fdz"].to_numpy())
    wa = np.sign(combo)
    wb = -wa
    price = wa * df["ra"].to_numpy() + wb * df["rb"].to_numpy()
    fund = -(wa * df["fae"].to_numpy() + wb * df["fbe"].to_numpy())
    turn = np.abs(np.diff(wa, prepend=0.0)) + np.abs(np.diff(wb, prepend=0.0))
    return pd.Series(price + fund - COST_SIDE * turn,
                     index=pd.to_datetime(df.index.to_numpy(), unit="ms"))


def metrics(net: pd.Series):
    def sh(x):
        g = x.groupby(x.index.to_period("M")).sum()
        return g.mean() / g.std() * np.sqrt(12) if len(g) > 1 and g.std() > 0 else float("nan")
    is_, oos = net[net.index < OOS_CUTOFF], net[net.index >= OOS_CUTOFF]
    yr = is_.groupby(is_.index.year).sum()
    pos_frac = float((yr > 0).mean()) if len(yr) else float("nan")
    return sh(is_), sh(oos), pos_frac


def main() -> None:
    syms = sorted(p.split("/")[-1][:-4] for p in glob.glob("data/funding_rates/*USDT.csv"))
    coins = {s: load_coin(s) for s in syms}
    coins = {s: d for s, d in coins.items() if d is not None}
    print(f"universe: {len(coins)} funding coins -> {len(list(combinations(coins, 2)))} pairs "
          f"x {len(CONFIGS)} configs")

    rows = []
    for a, b in combinations(coins, 2):
        j = coins[a].join(coins[b], lsuffix="_a", rsuffix="_b", how="inner")
        if len(j) < MIN_OVERLAP:
            continue
        sub = pd.DataFrame({"ca": j["close_a"], "cb": j["close_b"],
                            "fa": j["funding_rate_a"], "fb": j["funding_rate_b"]})
        for cfg in CONFIGS:
            net = pair_net(sub, cfg)
            if net.empty:
                continue
            is_sh, oos_sh, pos = metrics(net)
            if np.isfinite(is_sh):
                rows.append((f"{a[:-4]}/{b[:-4]}", cfg, is_sh, pos, oos_sh))
    r = pd.DataFrame(rows, columns=["pair", "config", "is_sh", "is_pos_frac", "oos_sh"])

    # EXPLORATION: rank on IS ONLY — regime-consistency first, then IS Sharpe. NO OOS used.
    expl = r.sort_values(["is_pos_frac", "is_sh"], ascending=False).head(TOP_K)
    expl = expl.reset_index(drop=True)
    print(f"\n=== EXPLORATION (IS-only ranking; {len(r)} candidates) — top {TOP_K} ===")
    print(f"{'pair':>16} {'config':>10} {'IS_Sh':>6} {'IS_yrs+':>7} | {'OOS_Sh(confirm)':>15}")
    for _, x in expl.iterrows():
        print(f"{x['pair']:>16} {x['config']:>10} {x['is_sh']:>+6.2f} {x['is_pos_frac']:>7.2f} | "
              f"{x['oos_sh']:>+15.2f}")
    # CONFIRMATION summary: does IS-selection generalize?
    hold = (expl["oos_sh"] > 0).sum()
    print(f"\n=== CONFIRMATION === IS-top-{TOP_K}: {hold}/{len(expl)} have OOS Sharpe > 0 "
          f"(median OOS {expl['oos_sh'].median():+.2f})")
    print(f"  best IS-selected by OOS: {expl.loc[expl['oos_sh'].idxmax(), 'pair']} "
          f"{expl.loc[expl['oos_sh'].idxmax(), 'config']} OOS={expl['oos_sh'].max():+.2f}")
    # honest cross-check: what the BEST OOS overall was (NOT selectable ex-ante — selection bias)
    print(f"  [ref only, NOT selectable] best OOS in whole grid = {r['oos_sh'].max():+.2f} "
          f"({r.loc[r['oos_sh'].idxmax(), 'pair']} {r.loc[r['oos_sh'].idxmax(), 'config']})")


if __name__ == "__main__":
    main()
