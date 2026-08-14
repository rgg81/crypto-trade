"""EDA 4 -- broad causal measure sweep, close-based formations only.

Reports, for every measure: rank IC against the 1-bar and the H-bar forward open-to-open return,
conditioned on the harvest slot, split into both halves of the window, with the number of
independent boundaries behind each cell.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-11/research")
import measures as M  # noqa: E402
import panel  # noqa: E402

IS_START = pd.Timestamp("2020-08-17T00:00:00Z")
SLOTN = {0: "Asia", 1: "Euro", 2: "US"}


def fast_ic(sig_rank: np.ndarray, fwd_rank: np.ndarray) -> np.ndarray:
    a = sig_rank
    b = fwd_rank
    ok = np.isfinite(a) & np.isfinite(b)
    n = ok.sum(1)
    a = np.where(ok, a, 0.0)
    b = np.where(ok, b, 0.0)
    ma = a.sum(1) / np.maximum(n, 1)
    mb = b.sum(1) / np.maximum(n, 1)
    a = np.where(ok, a - ma[:, None], 0.0)
    b = np.where(ok, b - mb[:, None], 0.0)
    cov = (a * b).sum(1)
    sa = np.sqrt((a * a).sum(1))
    sb = np.sqrt((b * b).sum(1))
    out = np.where((n >= 8) & (sa > 0) & (sb > 0), cov / np.maximum(sa * sb, 1e-18), np.nan)
    return out


def stat(ic: np.ndarray, sel: np.ndarray, half: np.ndarray) -> dict:
    v = ic[sel]
    v = v[np.isfinite(v)]
    if len(v) < 40:
        return {}
    t = v.mean() / v.std(ddof=1) * np.sqrt(len(v))
    v1 = ic[sel & half]
    v1 = v1[np.isfinite(v1)]
    v2 = ic[sel & ~half]
    v2 = v2[np.isfinite(v2)]
    return {
        "n": len(v),
        "ic": v.mean(),
        "t": t,
        "ic_h1": v1.mean() if len(v1) > 2 else np.nan,
        "ic_h2": v2.mean() if len(v2) > 2 else np.nan,
    }


def main() -> None:
    p = panel.load()
    w = p.times >= IS_START
    times = p.times[w]
    el = p.eligible[w]
    n = len(times)
    half = times < times[n // 2]
    slot = p.slot[w]
    dow = p.dow[w]

    close = np.where(np.isfinite(p.close[w]), p.close[w], np.nan)
    open_ = p.open[w]
    qv = np.where(el, p.quote_volume[w], np.nan)
    clr = M.close_log_return(close)
    ibr = M.intrabar_log_return(open_, close)
    absr = np.abs(clr)
    fwd1 = np.where(el, p.oo_ret[w], np.nan)

    # multi-bar forward (held H bars from boundary t): open[t+H]/open[t]-1
    def fwd(h: int) -> np.ndarray:
        nxt = np.full_like(open_, np.nan)
        nxt[:-h] = open_[h:]
        return np.where(el, nxt / open_ - 1.0, np.nan)

    fwds = {h: M.cross_section_rank(fwd(h), el) for h in (1, 3, 6, 9, 21)}

    slot_masks = {s: slot == s for s in range(3)}
    weekend = np.isin(dow, [5, 6])

    sigs: dict[str, np.ndarray] = {}

    # -------- A. plain reversal / momentum controls (close-based) ------------------------
    for W in (1, 2, 3, 6, 9, 21, 63, 126):
        sigs[f"A_mom_{W}b"] = M.causal_rolling_sum(clr, W)

    # -------- B. slot-decomposed formation returns ---------------------------------------
    for W in (9, 21, 45, 90, 180):
        tot = M.causal_rolling_sum(clr, W)
        for s in range(3):
            part = M.causal_masked_sum(clr, slot_masks[s], W)
            sigs[f"B_slot{s}ret_{W}b"] = part
            sigs[f"B_slot{s}tilt_{W}b"] = part - tot / 3.0
    for W in (21, 63, 126):
        we = M.causal_masked_sum(clr, weekend, W)
        wd = M.causal_masked_sum(clr, ~weekend, W)
        sigs[f"B_weekendret_{W}b"] = we
        sigs[f"B_wetilt_{W}b"] = we - (2.0 / 7.0) * (we + wd)

    # -------- C. WHEN this coin trades: share-of-activity characteristics -----------------
    for W in (21, 63, 126, 252):
        for s in range(3):
            sigs[f"C_volshare_slot{s}_{W}b"] = M.share_of_activity(qv, slot_masks[s], W)
            sigs[f"C_volatshare_slot{s}_{W}b"] = M.share_of_activity(absr, slot_masks[s], W)
        sigs[f"C_volshare_weekend_{W}b"] = M.share_of_activity(qv, weekend, W)
        sigs[f"C_volatshare_weekend_{W}b"] = M.share_of_activity(absr, weekend, W)
        # US minus Asia contrast, the clientele axis
        sigs[f"C_volshare_US_minus_Asia_{W}b"] = M.share_of_activity(
            qv, slot_masks[2], W
        ) - M.share_of_activity(qv, slot_masks[0], W)
        sigs[f"C_volatshare_US_minus_Asia_{W}b"] = M.share_of_activity(
            absr, slot_masks[2], W
        ) - M.share_of_activity(absr, slot_masks[0], W)

    # -------- D. session-conditional realised volatility spread ---------------------------
    for W in (21, 63, 126):
        a = M.causal_masked_sum(absr, slot_masks[0], W)
        u = M.causal_masked_sum(absr, slot_masks[2], W)
        e = M.causal_masked_sum(absr, slot_masks[1], W)
        sigs[f"D_volspread_US_Asia_{W}b"] = (u - a) / np.where(
            np.abs(u + a + e) > 1e-12, u + a + e, np.nan
        )
        sigs[f"D_volspread_wknd_{W}b"] = M.share_of_activity(absr, weekend, W)

    # -------- E. intrabar (open->close) session drift decomposition -----------------------
    for W in (21, 63, 126):
        for s in range(3):
            sigs[f"E_intrabar_slot{s}_{W}b"] = M.causal_masked_sum(ibr, slot_masks[s], W)

    rows = []
    for name, raw in sigs.items():
        sr = M.cross_section_rank(raw, el)
        for h, frank in fwds.items():
            ic = fast_ic(sr, frank)
            base = stat(ic, np.ones(n, dtype=bool), half)
            if base:
                rows.append({"measure": name, "H": h, "harvest": "all", **base})
            if h == 1:
                for s in range(3):
                    r = stat(ic, slot_masks[s], half)
                    if r:
                        rows.append({"measure": name, "H": h, "harvest": SLOTN[s], **r})

    out = pd.DataFrame(rows)
    out["abs_t"] = out["t"].abs()
    out["stable"] = np.sign(out["ic_h1"]) == np.sign(out["ic_h2"])
    out.to_csv("tournament/cup20/teams/team-11/research/eda_broad.csv", index=False)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_rows", 400)
    print(f"measures={len(sigs)}   rows={len(out)}")
    print("\n===== top 40 by |t|, all-harvest, H>1 (tradeable slow horizons) =====")
    sel = out[(out.harvest == "all") & (out.H > 1)]
    print(sel.sort_values("abs_t", ascending=False).head(40).to_string(index=False,
                                                                      float_format="%.4f"))
    print("\n===== top 30 stable, all-harvest, H>=3 =====")
    sel2 = sel[sel.stable & (sel.H >= 3)]
    print(sel2.sort_values("abs_t", ascending=False).head(30).to_string(index=False,
                                                                       float_format="%.4f"))
    print("\n===== characteristics (family C/D) only, all horizons =====")
    selc = out[(out.harvest == "all") & (out.measure.str.startswith(("C_", "D_")))]
    print(selc.sort_values("abs_t", ascending=False).head(30).to_string(index=False,
                                                                       float_format="%.4f"))


if __name__ == "__main__":
    main()
