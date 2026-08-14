"""EDA 1 -- the calendar cells themselves: sample size, aggregate drift, dispersion, vol.

Everything here is measured on the IS snapshot only. No scored number is produced.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-11/research")
import panel  # noqa: E402

IS_START = pd.Timestamp("2020-08-17T00:00:00Z")
SLOT_NAME = {0: "00-08 (Asia)", 1: "08-16 (Europe)", 2: "16-24 (US)"}
DOW_NAME = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def main() -> None:
    p = panel.load()
    w = p.times >= IS_START
    times = p.times[w]
    el = p.eligible[w]
    ret = np.where(el, p.oo_ret[w], np.nan)
    slot = p.slot[w]
    dow = p.dow[w]
    half = times < times[len(times) // 2]

    print(f"boundaries={len(times)}  first={times[0]}  last={times[-1]}")
    print(f"mean eligible members per boundary = {el.sum(1).mean():.2f}")

    # ---- equal-weight universe return per boundary (the aggregate 'market') -------------
    mkt = np.nanmean(ret, axis=1)
    print("\n== effective sample per calendar cell ==")
    print("cell type            cells   boundaries/cell   symbol-obs/cell")
    for name, key, n in (("slot", slot, 3), ("day-of-week", dow, 7)):
        per = np.bincount(key, minlength=n)
        print(f"{name:<20} {n:>5}   {per.mean():>15.0f}   {el.sum() / n:>15.0f}")
    inter = slot * 7 + dow
    per = np.bincount(inter, minlength=21)
    print(f"{'dow x slot':<20} {21:>5}   {per.mean():>15.0f}   {el.sum() / 21:>15.0f}")

    def block(label, key, names):
        print(f"\n== aggregate equal-weight return by {label} ==")
        print("cell            n     mean(bp)    t     vol(bp)  disp(bp)   1stHalf(bp) 2ndHalf(bp)")
        for k in sorted(set(key.tolist())):
            m = key == k
            r = mkt[m]
            r = r[np.isfinite(r)]
            t = r.mean() / r.std(ddof=1) * np.sqrt(len(r)) if len(r) > 2 else np.nan
            disp = np.nanmean(np.nanstd(ret[m], axis=1))
            r1 = mkt[m & half]
            r2 = mkt[m & ~half]
            print(
                f"{names[k]:<14}{len(r):>5} {r.mean()*1e4:>10.2f} {t:>6.2f} "
                f"{r.std(ddof=1)*1e4:>9.1f} {disp*1e4:>9.1f} "
                f"{np.nanmean(r1)*1e4:>11.2f} {np.nanmean(r2)*1e4:>11.2f}"
            )

    block("slot", slot, SLOT_NAME)
    block("day-of-week", dow, DOW_NAME)

    print("\n== dow x slot mean (bp), aggregate ==")
    print("        " + "".join(f"{DOW_NAME[d]:>9}" for d in range(7)))
    for s in range(3):
        row = []
        for d in range(7):
            m = (slot == s) & (dow == d)
            row.append(np.nanmean(mkt[m]) * 1e4)
        print(f"{SLOT_NAME[s]:<8}" + "".join(f"{v:>9.1f}" for v in row))

    # ---- cross-sectional dispersion and vol by cell ------------------------------------
    print("\n== realised |return| and cross-sectional dispersion by slot ==")
    for s in range(3):
        m = slot == s
        print(
            f"{SLOT_NAME[s]:<16} mean|r|={np.nanmean(np.abs(ret[m]))*1e4:>7.1f}bp  "
            f"xs-dispersion={np.nanmean(np.nanstd(ret[m], axis=1))*1e4:>7.1f}bp  "
            f"mean quote vol share={np.nansum(np.where(el[m], p.quote_volume[w][m], 0))/np.nansum(np.where(el, p.quote_volume[w], 0)):.4f}"
        )

    # ---- settlement identification ------------------------------------------------------
    print("\n== settlement-boundary identification on this snapshot ==")
    hs = p.has_settlement[w]
    mid = p.mid_settlements[w] > 0
    print(f"eligible symbol-boundaries                 : {el.sum()}")
    print(f"  ... carrying a settlement AT the boundary: {(el & hs).sum()}  "
          f"({(el & hs).sum() / el.sum():.4%})")
    print(f"  ... carrying an EXTRA mid-bar settlement : {(el & mid).sum()}  "
          f"({(el & mid).sum() / el.sum():.4%})")
    fr = p.funding_at_f[w]
    print(f"  |funding| at boundary: mean={np.abs(fr[el]).mean()*1e4:.2f}bp  "
          f"median={np.median(np.abs(fr[el]))*1e4:.2f}bp  zero-rate share="
          f"{(np.abs(fr[el]) < 1e-9).mean():.4f}")


if __name__ == "__main__":
    main()
