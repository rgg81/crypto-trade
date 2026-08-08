"""Team-01 EDA step 8 -- funding, and whether both sleeves survive it.

Same scope declaration as ``eda_03_shape.py``: gross, cost-free signal diagnostics only. Funding
is included here because it is part of the GROSS return the charter's per-side floor is stated on
(``gross_bar = price_pnl + funding_pnl``), not because a cost model is being applied -- no fee, no
slippage, no cap, no risk unit and no floor is computed in this file.

Mechanism question posed before the numbers: a perpetual-futures trend follower is structurally on
the crowded side of funding. It goes long after the price has risen, which is exactly when the
perpetual trades above spot and longs pay; it goes short after the price has fallen, which is when
the basis inverts and shorts pay. So funding should be a systematic drag on BOTH sleeves rather
than a wash, even on a book whose average net exposure is near zero. If that drag is large enough
to sink the short sleeve below zero, the charter's per-side floor kills the candidate and the lane
does not support a long/short book.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from eda_03_shape import BARS_PER_YEAR
from eda_06_production import prepare
from eda_07_flatness import LADDERS, ir_of, weights
from panel import CONFIG

from crypto_trade.cup20.snapshot import load_snapshot


def funding_panel(grid, symbols):
    snapshot = load_snapshot(CONFIG["data"]["is_root"])
    rate = (
        snapshot.funding.pivot_table(
            index="funding_time", columns="symbol", values="funding_rate", aggfunc="sum"
        ).reindex(columns=symbols)
    )
    edges = pd.DatetimeIndex(list(grid) + [grid[-1] + pd.Timedelta(hours=8)])
    slot = np.searchsorted(edges.to_numpy(), rate.index.to_numpy(), side="left") - 1
    out = np.zeros((len(grid), len(symbols)), dtype=float)
    values = np.nan_to_num(rate.to_numpy(dtype=float))
    keep = (slot >= 0) & (slot < len(grid))
    np.add.at(out, slot[keep], values[keep])
    return out


def main() -> None:
    panel, ret, fwd = prepare()
    folds, elig, grid = panel.fold_of_boundary(), panel.eligible, panel.grid
    fund = funding_panel(grid, panel.symbols)
    price = np.nan_to_num(fwd)

    print("Cumulative GROSS return over the window at unit gross (price + funding), by sleeve.")
    print(f"{'spec':<22} {'Lprice':>7} {'Lfund':>7} {'Lgross':>7} "
          f"{'Sprice':>7} {'Sfund':>7} {'Sgross':>7} {'net IR':>7}")
    for name, ladder in (("3leg", LADDERS["3leg"]), ("4leg", LADDERS["4leg"])):
        for formation, holding, threshold in (
            (45, 3, 0.35), (45, 6, 0.35), (45, 9, 0.35), (54, 6, 0.35), (90, 6, 0.35)
        ):
            w, _ = weights(ret, elig, formation, holding, threshold, ladder)
            _, _, _, live = ir_of(w, fwd, folds, 3 * formation + holding + 5)
            lw = np.where(w > 0, w, 0.0)[live]
            sw = np.where(w < 0, w, 0.0)[live]
            lp, sp = (lw * price[live]).sum(), (sw * price[live]).sum()
            lf, sf = -(lw * fund[live]).sum(), -(sw * fund[live]).sum()
            total = np.nansum((w * price + w * -fund)[live], axis=1)
            ir = total.mean() / total.std(ddof=1) * np.sqrt(BARS_PER_YEAR)
            print(f"{name} F={formation} H={holding} t={threshold:<4} "
                  f"{lp:>7.2f} {lf:>7.2f} {lp + lf:>7.2f} "
                  f"{sp:>7.2f} {sf:>7.2f} {sp + sf:>7.2f} {ir:>7.2f}")

    print()
    print("Fold IR after funding (price + funding, still no fees/slippage/caps/risk unit):")
    print(f"{'spec':<22} {'IR':>6} {'F1':>6} {'F2':>6} {'F3':>6} {'F4':>6} {'+Q':>6}")
    for name, ladder in (("3leg", LADDERS["3leg"]), ("4leg", LADDERS["4leg"])):
        for formation, holding, threshold in (
            (40, 6, 0.35), (45, 3, 0.35), (45, 6, 0.20), (45, 6, 0.35), (45, 6, 0.50),
            (45, 9, 0.35), (50, 6, 0.35), (54, 6, 0.35), (90, 6, 0.35)
        ):
            w, _ = weights(ret, elig, formation, holding, threshold, ladder)
            _, _, _, live = ir_of(w, fwd, folds, 3 * formation + holding + 5)
            total = np.nansum((w * price - w * fund), axis=1)
            x = total[live]
            ir = x.mean() / x.std(ddof=1) * np.sqrt(BARS_PER_YEAR)
            fl = folds[live]
            per = [
                (x[fl == f].mean() / x[fl == f].std(ddof=1) * np.sqrt(BARS_PER_YEAR))
                if (fl == f).sum() > 30 else np.nan for f in range(4)
            ]
            q = pd.Series(
                x, index=pd.PeriodIndex(grid[live].tz_convert("UTC").tz_localize(None), freq="Q")
            ).groupby(level=0).sum()
            print(f"{name} F={formation} H={holding} t={threshold:<4} {ir:>6.2f} "
                  + " ".join(f"{v:>6.2f}" for v in per)
                  + f" {int((q > 0).sum()):>2}/{len(q):<3}")


if __name__ == "__main__":
    main()
