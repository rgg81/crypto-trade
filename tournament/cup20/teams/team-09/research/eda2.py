"""Second EDA pass: the mandate's own questions.

  * is the informative quantity the LEVEL of taker imbalance, its CHANGE, or the RESIDUAL after
    removing the price move it should have caused?
  * does imbalance mean something different when the same USDT arrived in many small prints
    versus few large ones (trade count / average print size)?
  * does flow that fails to move price behave differently from price that moves without flow?

Every measure is reported twice: raw, and purged cross-sectionally of the contemporaneous price
move and of the coin's slow size/liquidity class. The purged column is the one that has to carry a
book, because the raw column contains a size premium this window happens to pay.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from flow import Flow, cs_residual, prev_mean, prev_std, prev_sum, rank_rows
from ic import fold_edges, forward_returns, rank_ic
from panel import Panel


def summarise(ics, times, fe, block):
    v = ics[np.isfinite(ics)]
    if v.size < 60:
        return {"ic": np.nan, "t": np.nan}
    b = v[: (v.size // block) * block].reshape(-1, block).mean(axis=1)
    t = b.mean() / (b.std(ddof=1) / np.sqrt(len(b))) if len(b) > 3 else np.nan
    row = {"ic": float(v.mean()), "t": float(t)}
    for name, lo, hi in fe:
        w = ics[(times >= lo) & (times < hi)]
        w = w[np.isfinite(w)]
        row[name] = float(w.mean()) if w.size > 10 else np.nan
    row["minF"] = min(row[k] for k in ("F1", "F2", "F3", "F4"))
    return row


def build(p: Panel, f: Flow, E):
    cut = lambda a: a[p.d0 : p.dn]  # noqa: E731
    M = {}
    for w in (9, 21, 42, 90):
        nq = f.net_quote
        qv = f.qv
        # LEVEL: volume-weighted imbalance
        M[f"lvl_{w}"] = cut(f.netflow(w))
        # PERSISTENCE: fraction of bars with a positive imbalance (outlier-insensitive)
        pos = np.where(np.isfinite(f.imb), (f.imb > 0).astype(float), np.nan)
        M[f"per_{w}"] = cut(prev_mean(pos, w))
        # SCALE-FREE: net flow z-scored against the symbol's own longer-run net-flow scale
        s = prev_std(nq, 90)
        with np.errstate(invalid="ignore", divide="ignore"):
            zz = np.where(s > 0, prev_mean(nq, w) / s, np.nan)
        M[f"zfl_{w}"] = cut(zz)
        # CHANGE: this window's imbalance minus the preceding longer baseline
        M[f"chg_{w}"] = cut(f.netflow(w) - f.netflow(90))
        # BIG-PRINT flow: net flow weighted toward bars whose average print was unusually large
        big = f.log_ats - prev_mean(f.log_ats, 90)
        wgt = np.where(np.isfinite(big), np.clip(big, -3, 3), 0.0)
        with np.errstate(invalid="ignore", divide="ignore"):
            num = prev_sum(np.nan_to_num(f.imb) * wgt * np.nan_to_num(qv), w)
            den = prev_sum(qv, w)
            M[f"bigp_{w}"] = cut(np.where(den > 0, num / den, np.nan))
        # SMALL-PRINT flow: the same, weighted toward many-small-print bars
        M[f"smlp_{w}"] = -M[f"bigp_{w}"]
        # EFFICIENCY: price move delivered per unit of net taker flow (signed)
        nfw = f.netflow(w)
        rw = f.ret_w(w)
        with np.errstate(invalid="ignore", divide="ignore"):
            M[f"eff_{w}"] = cut(np.where(np.abs(nfw) > 0.005, rw / np.abs(nfw), np.nan))
    for w in (9, 21, 42):
        M[f"atssh_{w}"] = cut(f.ats_shock(w, 90))
        M[f"ntsh_{w}"] = cut(f.nt_shock(w, 90))
        M[f"vsh_{w}"] = cut(f.vol_shock(w, 90))
    return M


def main():
    p = Panel()
    f = Flow(p)
    E = p.eligible[p.d0 : p.dn]
    times = p.times
    fe = fold_edges(times)
    cut = lambda a: a[p.d0 : p.dn]  # noqa: E731
    size = rank_rows(cut(prev_mean(f.log_ats, 90)), E)
    liq = rank_rows(cut(prev_mean(f.log_qv, 90)), E)
    M = build(p, f, E)
    rows = []
    for h in (9, 21, 42):
        fwd = forward_returns(p, h)
        block = max(30, 3 * h)
        for name, sig in M.items():
            r0 = rank_rows(sig, E)
            rw = None
            if "_" in name and name.split("_")[-1].isdigit():
                w = int(name.split("_")[-1])
                if w in (9, 21, 42, 90):
                    rw = rank_rows(cut(f.ret_w(w)), E)
            if rw is None:
                rw = rank_rows(cut(f.ret_w(21)), E)
            pur = cs_residual(r0, [rw, size, liq], E)
            a = summarise(rank_ic(r0, fwd, E), times, fe, block)
            b = summarise(rank_ic(pur, fwd, E), times, fe, block)
            rows.append(
                {
                    "m": name,
                    "h": h,
                    "ic_raw": a["ic"],
                    "t_raw": a.get("t"),
                    "ic_pur": b["ic"],
                    "t_pur": b.get("t"),
                    "minF_pur": b.get("minF"),
                    "F1": b.get("F1"),
                    "F2": b.get("F2"),
                    "F3": b.get("F3"),
                    "F4": b.get("F4"),
                }
            )
    df = pd.DataFrame(rows)
    df.to_csv("ic_eda2.csv", index=False)
    pd.set_option("display.width", 240)
    for h in (9, 21, 42):
        d = df[df.h == h].copy()
        d["a"] = d.ic_pur.abs()
        print(f"=== h={h}  (sorted by |purged IC|)")
        print(d.sort_values("a", ascending=False).head(16).drop(columns=["a", "h"]).to_string(index=False))


if __name__ == "__main__":
    main()
