"""EDA 5 -- is the calendar characteristic a CALENDAR effect, or another factor wearing a clock?

The lane's own discipline test. A share-of-activity characteristic is mechanically correlated with
things that are emphatically not calendar: coin size, coin volatility, recent momentum, and the
funding a coin pays. Three of those belong to other lanes. This script residualises the calendar
measure on each control, cross-sectionally, boundary by boundary, and re-measures the IC.

Also runs the two controls the mandate names specifically:
  * conditioning on the funding actually settled at the boundary;
  * the settlement-boundary control that this snapshot can actually identify.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-11/research")
import measures as M  # noqa: E402
import panel  # noqa: E402
from eda_broad import fast_ic  # noqa: E402

IS_START = pd.Timestamp("2020-08-17T00:00:00Z")


def residualise(sig: np.ndarray, ctrls: list[np.ndarray], mask: np.ndarray) -> np.ndarray:
    """Cross-sectional OLS residual of ``sig`` on ``ctrls`` (all rank-standardised), per boundary."""
    out = np.full(sig.shape, np.nan)
    for i in range(sig.shape[0]):
        m = mask[i] & np.isfinite(sig[i])
        for c in ctrls:
            m = m & np.isfinite(c[i])
        n = int(m.sum())
        if n < 10:
            continue
        y = sig[i, m]
        X = np.column_stack([np.ones(n)] + [c[i, m] for c in ctrls])
        try:
            beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        except np.linalg.LinAlgError:  # pragma: no cover
            continue
        out[i, m] = y - X @ beta
    return out


def report(label: str, ic: np.ndarray, half: np.ndarray) -> None:
    v = ic[np.isfinite(ic)]
    t = v.mean() / v.std(ddof=1) * np.sqrt(len(v))
    a = ic[half]
    a = a[np.isfinite(a)]
    b = ic[~half]
    b = b[np.isfinite(b)]
    print(
        f"{label:<52} IC={v.mean():>+.4f}  t={t:>+6.2f}  n={len(v):>5}   "
        f"H1={a.mean():>+.4f}  H2={b.mean():>+.4f}  "
        f"{'STABLE' if np.sign(a.mean()) == np.sign(b.mean()) else 'flips'}"
    )


def main() -> None:
    p = panel.load()
    w = p.times >= IS_START
    times = p.times[w]
    el = p.eligible[w]
    n = len(times)
    half = times < times[n // 2]
    slot = p.slot[w]
    dow = p.dow[w]
    weekend = np.isin(dow, [5, 6])
    close = p.close[w]
    qv = np.where(el, p.quote_volume[w], np.nan)
    clr = M.close_log_return(close)
    absr = np.abs(clr)
    fwd1 = M.cross_section_rank(np.where(el, p.oo_ret[w], np.nan), el)

    W = 126
    cand = {
        "weekend_volat_share_126": M.share_of_activity(absr, weekend, W),
        "weekend_volume_share_126": M.share_of_activity(qv, weekend, W),
        "asia_volume_share_126": M.share_of_activity(qv, slot == 0, W),
        "euro_volume_share_126": M.share_of_activity(qv, slot == 1, W),
        "us_minus_asia_volume_share_126": (
            M.share_of_activity(qv, slot == 2, W) - M.share_of_activity(qv, slot == 0, W)
        ),
    }

    # ---- controls ------------------------------------------------------------------------
    logvol = np.log(np.maximum(M.causal_rolling_sum(qv, W), 1.0))
    rv = np.sqrt(M.causal_rolling_sum(absr**2, W))
    mom = M.causal_rolling_sum(clr, 63)
    fund = M.causal_rolling_sum(np.where(el, p.funding_at_f[w], np.nan), W)
    absfund = M.causal_rolling_sum(np.abs(np.where(el, p.funding_at_f[w], np.nan)), W)
    age = np.cumsum(np.isfinite(close).astype(float), axis=0)

    ctrl = {
        "size(log quote vol 126)": M.cross_section_rank(logvol, el),
        "volatility(rv 126)": M.cross_section_rank(rv, el),
        "momentum(63b)": M.cross_section_rank(mom, el),
        "funding(mean 126)": M.cross_section_rank(fund, el),
        "crowding(|funding| 126)": M.cross_section_rank(absfund, el),
        "listing age": M.cross_section_rank(age, el),
    }

    print("== raw IC of each control, for reference ==")
    for name, c in ctrl.items():
        report(f"CONTROL {name}", fast_ic(c, fwd1), half)

    print("\n== candidate calendar measures: raw, then residualised ==")
    for cname, raw in cand.items():
        sr = M.cross_section_rank(raw, el)
        print()
        report(f"{cname}  [raw]", fast_ic(sr, fwd1), half)
        for ctlname, c in ctrl.items():
            res = residualise(sr, [c], el)
            report(f"   ... residual of {ctlname}", fast_ic(res, fwd1), half)
        allres = residualise(sr, list(ctrl.values()), el)
        report("   ... residual of ALL SIX controls", fast_ic(allres, fwd1), half)

    # ---- reverse direction: do the controls survive residualising on the calendar? --------
    print("\n== reverse: controls residualised on weekend_volat_share_126 ==")
    base = M.cross_section_rank(cand["weekend_volat_share_126"], el)
    for name, c in ctrl.items():
        res = residualise(c, [base], el)
        report(f"{name} | calendar", fast_ic(res, fwd1), half)

    # ---- mandate control 1: funding actually settled AT the boundary ----------------------
    print("\n== does the calendar effect survive conditioning on the funding PAID at the slot? ==")
    fr = np.where(el, p.funding_at_f[w], np.nan)
    frank = M.cross_section_rank(np.abs(fr), el)
    ic = fast_ic(base, fwd1)
    for lo, hi, lab in ((-1.01, -0.34, "low |funding| tercile"),
                        (-0.34, 0.34, "mid |funding| tercile"),
                        (0.34, 1.01, "high |funding| tercile")):
        sel = np.where((frank > lo) & (frank <= hi), base, np.nan)
        report(f"weekend share, {lab}", fast_ic(sel, fwd1), half)
    resf = residualise(base, [M.cross_section_rank(np.abs(fr), el),
                              M.cross_section_rank(fr, el)], el)
    report("weekend share | boundary funding (level+abs)", fast_ic(resf, fwd1), half)
    report("weekend share [unconditional, for comparison]", ic, half)

    # ---- mandate control 2: settlement boundary vs arbitrary boundary --------------------
    print("\n== settlement-boundary identification (see certificate) ==")
    hs = p.has_settlement[w]
    mid = p.mid_settlements[w] > 0
    print(f"eligible symbol-boundaries with a settlement AT the boundary: "
          f"{(el & hs).sum()} / {el.sum()} = {(el & hs).sum() / el.sum():.6f}")
    print(f"eligible bars ALSO carrying a mid-bar (4h/2h regime) settlement: "
          f"{(el & mid).sum()} ({(el & mid).sum() / el.sum():.4%})")
    r = np.where(el, p.oo_ret[w], np.nan)
    a = r[el & mid]
    b = r[el & ~mid]
    print(f"mean |return| on bars WITH an extra mid-bar settlement : "
          f"{np.nanmean(np.abs(a))*1e4:.1f} bp  (n={np.isfinite(a).sum()})")
    print(f"mean |return| on bars WITHOUT one                      : "
          f"{np.nanmean(np.abs(b))*1e4:.1f} bp  (n={np.isfinite(b).sum()})")


if __name__ == "__main__":
    main()
