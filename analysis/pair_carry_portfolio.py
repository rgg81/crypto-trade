"""CARRY-ONLY disjoint pair portfolio on the REALISTIC engine — the deployable candidate.

The realistic-engine search (pair_iterate.py) showed the FREE pair-search OVERFITS (IS +2.86 ->
OOS -0.68): the momentum/reversion configs that failed the anti-hype gauntlet all session are the
culprits. Restricting to the one STRUCTURAL edge — funding CARRY (short the higher-funding leg) —
recovers OOS generalization. This builds that carry-only book, with the anti-cheating discipline:
IS-only ranking + IS-only inverse-vol weights, disjoint coins (each used once), OOS revealed.

Result (realistic engine: next-bar-open fills, real 8h funding, 0.07%/leg cost):
  carry-only IS-top-15 -> 10/15 OOS+ (median OOS +0.52)
  disjoint carry portfolio: IS Sharpe +2.69 / OOS Sharpe +0.63 / maxDD -22%, net positive
  every year 2020-2025 (2026 partial ~0).

HONEST CAVEATS: IS +2.69 -> OOS +0.63 is real shrinkage (selecting best-IS carry pairs still
overfits somewhat -> the BROAD cross-sectional carry book in funding_carry_pit.py is the more
robust form). Mid-cap high-funding pairs carry capacity/squeeze risk. 2026 ~flat suggests funding
spreads may be compressing as the market matures. Deploy with realistic-Sharpe expectations, not
the IS number.
"""

from __future__ import annotations

import glob
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis")
import pair_engine as pe  # noqa: E402

LO0 = pd.Timestamp("2000-01-01")
HI1 = pd.Timestamp("2100-01-01")
MIN_OVERLAP = 2500
MAX_PAIRS = 10
CONFIG = "carry"


def main() -> None:
    syms = sorted(p.split("/")[-1][:-4] for p in glob.glob("data/funding_rates/*USDT.csv"))
    coins = {s: pe.load_coin(s) for s in syms}
    coins = {s: d for s, d in coins.items() if d is not None}

    rows = []
    for i, a in enumerate(coins):
        for b in list(coins)[i + 1:]:
            df = coins[a].join(coins[b], lsuffix="_a", rsuffix="_b", how="inner")
            if len(df) < MIN_OVERLAP:
                continue
            bt = pe.run(df, pe.signal_weights(df, CONFIG))
            is_sh = pe.monthly_sharpe(bt["net"], LO0, pe.OOS_CUTOFF)
            oos_sh = pe.monthly_sharpe(bt["net"], pe.OOS_CUTOFF, HI1)
            yr = bt["net"].groupby(bt.index.year).sum()
            is_pos = float((yr[yr.index < 2025] > 0).mean()) if (yr.index < 2025).any() else 0.0
            if np.isfinite(is_sh):
                rows.append((a, b, is_sh, is_pos, oos_sh))
    r = pd.DataFrame(rows, columns=["a", "b", "is_sh", "is_pos", "oos_sh"])
    ranked = r.sort_values(["is_pos", "is_sh"], ascending=False).reset_index(drop=True)

    top15 = ranked.head(15)
    print(f"CARRY-ONLY search ({len(r)} pairs). IS-top-15 (IS-only ranked):")
    print(f"  OOS+: {(top15.oos_sh > 0).sum()}/15  median OOS {top15.oos_sh.median():+.2f}")

    used: set = set()
    sel = []
    for _, x in ranked.iterrows():
        if x.a in used or x.b in used:
            continue
        sel.append((x.a, x.b))
        used.update((x.a, x.b))
        if len(sel) >= MAX_PAIRS:
            break

    series = {}
    for a, b in sel:
        df = coins[a].join(coins[b], lsuffix="_a", rsuffix="_b", how="inner")
        series[f"{a[:-4]}/{b[:-4]}"] = pe.run(df, pe.signal_weights(df, CONFIG))["net"]
    panel = pd.DataFrame(series).sort_index()
    is_mask = panel.index < pe.OOS_CUTOFF
    inv = 1.0 / panel[is_mask].std()
    w = inv / inv.sum()
    port = (panel.fillna(0.0) * w).sum(axis=1)
    yr = port.groupby(port.index.year).sum()
    eq = (1 + port).cumprod()
    dd = float((eq / eq.cummax() - 1).min())

    print(f"\nDisjoint carry portfolio ({len(sel)} pairs): "
          f"{[f'{a[:-4]}/{b[:-4]}' for a, b in sel]}")
    print(f"IS Sharpe={pe.monthly_sharpe(port, LO0, pe.OOS_CUTOFF):+.2f}  "
          f"OOS Sharpe={pe.monthly_sharpe(port, pe.OOS_CUTOFF, HI1):+.2f}  maxDD={dd * 100:.0f}%")
    print(f"net%/yr={ {int(k): round(v * 100, 0) for k, v in yr.items()} }")


if __name__ == "__main__":
    main()
