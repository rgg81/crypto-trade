"""PAIR ITERATION on the REALISTIC engine — exploration/confirmation + disjoint portfolio.

The skill-loop kernel, now on the deployment-grade pair_engine (next-bar-open fills, real funding,
per-leg cost, leak-tested) instead of the proxy. Anti-cheating discipline (the bundle lesson):
  EXPLORATION  — score every (pair, config) on IN-SAMPLE only (IS Sharpe + regime-consistency =
                 fraction of IS years positive). Rank. NO OOS touched.
  CONFIRMATION — reveal OOS for the IS-top-K only.
  PORTFOLIO    — greedily pick IS-ranked pairs with DISJOINT coins (each coin used once -> no
                 doubled exposure), weight INVERSE-VOL on IS data only, sum the market-neutral
                 books. The portfolio diversifies the single-pair selection noise.
                 Reported IS vs OOS so generalization is honest.
"""

from __future__ import annotations

import glob
import sys
from itertools import combinations

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis")
import pair_engine as pe  # noqa: E402

LO0, HI1 = pd.Timestamp("2000-01-01"), pd.Timestamp("2100-01-01")
MIN_OVERLAP = 2500
TOP_K = 20
MAX_PORTFOLIO = 10


def metrics(bt: pd.DataFrame) -> tuple[float, float, float]:
    is_sh = pe.monthly_sharpe(bt["net"], LO0, pe.OOS_CUTOFF)
    oos_sh = pe.monthly_sharpe(bt["net"], pe.OOS_CUTOFF, HI1)
    yr = bt["net"].groupby(bt.index.year).sum()
    is_pos = float((yr[yr.index < 2025] > 0).mean()) if (yr.index < 2025).any() else float("nan")
    return is_sh, oos_sh, is_pos


def pair_frame(coins: dict, a: str, b: str) -> pd.DataFrame | None:
    df = coins[a].join(coins[b], lsuffix="_a", rsuffix="_b", how="inner")
    return df if len(df) >= MIN_OVERLAP else None


def portfolio_net(selected: list[tuple], coins: dict) -> tuple[pd.Series, dict]:
    series = {}
    for a, b, cfg in selected:
        df = pair_frame(coins, a, b)
        bt = pe.run(df, pe.signal_weights(df, cfg))
        series[f"{a[:-4]}/{b[:-4]}:{cfg}"] = bt["net"]
    panel = pd.DataFrame(series).sort_index()
    is_mask = panel.index < pe.OOS_CUTOFF
    inv = 1.0 / panel[is_mask].std()                 # IS-only inverse-vol weights (no OOS leak)
    w = (inv / inv.sum()).to_dict()
    port = (panel.fillna(0.0) * pd.Series(w)).sum(axis=1)
    return port, w


def main() -> None:
    syms = sorted(p.split("/")[-1][:-4] for p in glob.glob("data/funding_rates/*USDT.csv"))
    coins = {s: pe.load_coin(s) for s in syms}
    coins = {s: d for s, d in coins.items() if d is not None}
    print(f"REALISTIC pair iteration: {len(coins)} funding coins -> "
          f"{len(list(combinations(coins, 2)))} pairs x {len(pe.CONFIGS)} configs")

    rows = []
    for a, b in combinations(coins, 2):
        df = pair_frame(coins, a, b)
        if df is None:
            continue
        for cfg in pe.CONFIGS:
            bt = pe.run(df, pe.signal_weights(df, cfg))
            is_sh, oos_sh, is_pos = metrics(bt)
            if np.isfinite(is_sh):
                rows.append((a, b, cfg, is_sh, is_pos, oos_sh))
    r = pd.DataFrame(rows, columns=["a", "b", "cfg", "is_sh", "is_pos", "oos_sh"])

    # EXPLORATION (IS-only): regime-consistency first, then IS Sharpe.
    ranked = r.sort_values(["is_pos", "is_sh"], ascending=False).reset_index(drop=True)
    expl = ranked.head(TOP_K)
    print(f"\n=== EXPLORATION (IS-only; {len(r)} candidates) — top {TOP_K} ===")
    print(f"{'pair':>16} {'cfg':>10} {'IS_Sh':>6} {'IS_yrs+':>7} | {'OOS_Sh':>7}")
    for _, x in expl.iterrows():
        print(f"{x.a[:-4] + '/' + x.b[:-4]:>16} {x.cfg:>10} {x.is_sh:>+6.2f} "
              f"{x.is_pos:>7.2f} | {x.oos_sh:>+7.2f}")
    hold = int((expl.oos_sh > 0).sum())
    med = expl.oos_sh.median()
    print(f"CONFIRMATION: IS-top-{TOP_K} -> {hold}/{len(expl)} OOS+ (median OOS {med:+.2f})")

    # PORTFOLIO: greedy disjoint over IS-ranked, IS-only inverse-vol weights.
    used: set = set()
    selected = []
    for _, x in ranked.iterrows():
        if x.a in used or x.b in used:
            continue
        selected.append((x.a, x.b, x.cfg))
        used.update((x.a, x.b))
        if len(selected) >= MAX_PORTFOLIO:
            break
    port, w = portfolio_net(selected, coins)
    is_sh = pe.monthly_sharpe(port, LO0, pe.OOS_CUTOFF)
    oos_sh = pe.monthly_sharpe(port, pe.OOS_CUTOFF, HI1)
    yr = port.groupby(port.index.year).sum()
    eq = (1 + port).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    print(f"\n=== PORTFOLIO ({len(selected)} disjoint IS-selected pairs, IS inverse-vol) ===")
    for (a, b, cfg) in selected:
        print(f"   {a[:-4]}/{b[:-4]}:{cfg}  w={w[f'{a[:-4]}/{b[:-4]}:{cfg}']:.2f}")
    print(f"PORTFOLIO: IS Sharpe={is_sh:+.2f}  OOS Sharpe={oos_sh:+.2f}  maxDD={dd*100:.0f}%")
    print(f"  net%/yr={ {int(k): round(v * 100, 0) for k, v in yr.items()} }")


if __name__ == "__main__":
    main()
