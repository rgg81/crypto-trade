"""iter-012 PROBE — do PIT VALUE + QUALITY factors diversify the momentum book? (IS-only, 2010-2025)

The iter-011 probe showed that PRICE-ONLY orthogonal sleeves (short-term reversal, BAB, low-vol, a
long-term-reversal value PROXY) lift the momentum book and fix the momentum-CRASH years but CANNOT
make every year positive — the low-dispersion melt-up years (2017/2019) still lose. The textbook fix
is the two REAL fundamental momentum diversifiers: VALUE and QUALITY (AQR "Value and Momentum
Everywhere" — value/momentum correlate ~-0.2, so their bad years don't coincide -> higher combined
Sharpe). Those need point-in-time fundamentals, which the SEC-EDGAR build (ingest_edgar.py) now
supplies leak-safe.

This probe asks the honest first question: standalone, on THIS 69-name US-stock universe (IS-only),
  (1) is the VALUE factor (book-to-price) positive-EV? the QUALITY factor (gross-profitability)?
  (2) are they LOW/NEGATIVELY correlated to the momentum book — especially in momentum's 6 bad years
      (2010/2013/2016/2017/2019/2023) — i.e. do they actually DIVERSIFY momentum?
  (3) does adding them (equal-weight signal blend, one band + one vol-target) lift net + the
      positive-year count vs momentum alone?

Every factor is built with the SAME leak-safe machinery as the momentum sleeves: PIT fundamentals
(filed<=t) + close[t] -> cross-sectional z-score -> per-sector demean -> iter-003 hysteresis band
(delta=0.005) -> net_from_raw vol-target (15% ann) + 6bps/side taker cost. So each factor's net
Sharpe is directly comparable to the +0.28/+0.31 momentum book.

LEAK SAFETY: fundamentals are strictly point-in-time (ingest_edgar carries only facts filed<=t); the
combined raw feeds the strictly-causal band (single .shift(1) execution lag). OOS is HIDDEN —
every metric is on the IS slice (< 2025-03-24); no OOS number is computed. This is a PROBE
(measurement), not a promotion.

Run:  uv run python analysis/portfolio/tradfi/iter_012_probe.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import core_tradfi as ct  # noqa: E402
import features_fundamental as ff  # noqa: E402
import iter_003_hysteresis as i3  # noqa: E402
import iter_006_crashbrake as i6  # noqa: E402
import universe_tradfi as ut  # noqa: E402

DELTA = i3.CHOSEN_DELTA  # 0.005 hysteresis band, inherited UNCHANGED
BAD_YEARS = [2010, 2013, 2016, 2017, 2019, 2023]  # the momentum book's negative years (iter-011)


def _gn(raw):
    g = raw.abs().sum(axis=1).replace(0, np.nan)
    return raw.div(g, axis=0).fillna(0.0)


def banded(raw, ret_fwd):
    return i3.banded_net(raw, ret_fwd, DELTA)  # (net, w) — mirrors net_from_raw + causal band


def year_table(net):
    net = ct.is_only(net)
    out = {}
    for yr, g in net.groupby(net.index.year):
        m = g.groupby(g.index.to_period("M")).sum()
        sh = float(m.mean() / m.std() * np.sqrt(12)) if len(m) > 1 and m.std() > 0 else float("nan")
        out[yr] = (sh, float((np.prod(1 + g) - 1) * 100))
    return out


def n_pos_years(net):
    yt = year_table(net)
    return sum(1 for sh, _ in yt.values() if sh > 0), len(yt)


def monthly(net):
    net = ct.is_only(net)
    return net.groupby(net.index.to_period("M")).sum()


def corr_to(net_a, net_b, years=None):
    a, b = monthly(net_a), monthly(net_b)
    idx = a.index.intersection(b.index)
    if years is not None:
        idx = idx[[p.year in years for p in idx]]
    if len(idx) < 3:
        return float("nan")
    return float(np.corrcoef(a.loc[idx], b.loc[idx])[0, 1])


def bad_year_ret(net):
    yt = year_table(net)
    vals = [yt[y][1] for y in BAD_YEARS if y in yt]
    return float(np.mean(vals)) if vals else float("nan")


def _active_names(raw):
    """Names that ever carry a non-zero weight on the IS slice (fundamental actually present)."""
    is_raw = raw[raw.index < ct.OOS_CUTOFF]
    return int((is_raw.abs().sum(axis=0) > 1e-12).sum())


def main():
    base = ct._ROOT / "data"
    syms = sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)
    coins = ct.load_tradfi(syms)
    pn = ct.panels(coins)
    close, ret_fwd = pn["close"], pn["ret_fwd"]

    print("=" * 100)
    print("iter-012 PROBE — PIT VALUE + QUALITY factors vs the momentum book (IS-only, 2010-2025)")
    print("=" * 100)

    # ---- PIT fundamentals (filed<=t) aligned to the price panel ----
    panels = ff.load_panels(close)
    cov = ff.coverage(panels, ct.OOS_CUTOFF)
    print(f"\nPIT fundamental coverage (IS names with >=1 known obs): {cov}")

    # ---- factor raw books (sector-neutral z-scores) ----
    mom_raw = _gn(i6.crash_braked_raw(pn))
    value_raw = ff.value_raw(panels, close)
    quality_raw = ff.quality_raw(panels, close)
    ey_raw = ff.earnings_yield_raw(panels, close)
    roe_raw = ff.roe_raw(panels, close)

    print(
        f"active names (ever non-zero, IS): "
        f"VALUE(B/P)={_active_names(value_raw)}  QUALITY(GP/A)={_active_names(quality_raw)}  "
        f"E/P={_active_names(ey_raw)}  ROE={_active_names(roe_raw)}  (of {len(syms)})"
    )

    sleeves = {
        "MOM (iter-006)": mom_raw,
        "VALUE (book/price)": value_raw,
        "QUALITY (GP/assets)": quality_raw,
        "E/P (earn yield)": ey_raw,
        "ROE": roe_raw,
    }
    nets = {name: banded(raw, ret_fwd)[0] for name, raw in sleeves.items()}
    mom_net = nets["MOM (iter-006)"]

    # ---- (1) standalone scorecard ----
    print("\n(1) STANDALONE factors (same band + 15% vol-target + 6bps cost) — IS net Sharpe:")
    print(
        f"    {'factor':20} {'net':>6} {'+yrs':>6} {'corr_MOM':>9} {'corr(bad)':>10} "
        f"{'badYrRet%':>10}  regimes(bull/bear/chop)"
    )
    for name, net in nets.items():
        npos, nyr = n_pos_years(net)
        c_all = corr_to(net, mom_net) if name != "MOM (iter-006)" else 1.0
        c_bad = corr_to(net, mom_net, BAD_YEARS) if name != "MOM (iter-006)" else 1.0
        reg = ct.regime_sharpe(ct.is_only(net))
        sh = ct.msharpe(net, ct.LO0, ct.OOS_CUTOFF)
        print(
            f"    {name:20} {sh:>+6.2f} {npos:>3}/{nyr} {c_all:>+9.2f} {c_bad:>+10.2f} "
            f"{bad_year_ret(net):>+10.1f}  "
            f"{reg['bull']:+.2f}/{reg['bear']:+.2f}/{reg['chop']:+.2f}"
        )

    # ---- (2) per-year — do VALUE / QUALITY earn in momentum's 6 bad years? ----
    print("\n(2) PER-YEAR net Sharpe — do VALUE / QUALITY EARN in the momentum book's bad years?")
    show = ["MOM (iter-006)", "VALUE (book/price)", "QUALITY (GP/assets)"]
    yts = {n: year_table(nets[n]) for n in show}
    yrs = sorted(next(iter(yts.values())).keys())
    print(f"    {'year':>5} " + " ".join(f"{n.split()[0]:>10}" for n in show))
    for yr in yrs:
        cells = []
        for n in show:
            sh = yts[n].get(yr, (float("nan"),))[0]
            mark = "*" if (n == "MOM (iter-006)" and yr in BAD_YEARS) else " "
            cells.append(f"{sh:>+9.2f}{mark}")
        print(f"    {yr:>5} " + " ".join(cells))

    # ---- (3) combined market-neutral books (equal-weight SIGNAL blend, one band + vol-target) ----
    print("\n(3) COMBINED market-neutral books (equal-weight SIGNAL blend, one band+vol-target):")
    combos = {
        "MOM+VALUE": ["MOM (iter-006)", "VALUE (book/price)"],
        "MOM+QUALITY": ["MOM (iter-006)", "QUALITY (GP/assets)"],
        "MOM+VALUE+QUALITY": ["MOM (iter-006)", "VALUE (book/price)", "QUALITY (GP/assets)"],
        "VALUE+QUALITY": ["VALUE (book/price)", "QUALITY (GP/assets)"],
    }
    print(
        f"    {'book':22} {'net':>6} {'+yrs':>6} {'worst-yr':>9} {'maxDD':>7}  "
        f"regimes(bull/bear/chop)"
    )
    for name, members in combos.items():
        acc = sleeves[members[0]].copy()
        for m in members[1:]:
            acc = acc.add(sleeves[m], fill_value=0.0)
        acc = acc / len(members)
        net, _ = banded(acc, ret_fwd)
        npos, nyr = n_pos_years(net)
        yt = year_table(net)
        worst = min(yt.values(), key=lambda t: t[0])
        reg = ct.regime_sharpe(ct.is_only(net))
        sh = ct.msharpe(net, ct.LO0, ct.OOS_CUTOFF)
        mdd = ct.maxdd(ct.is_only(net)) * 100
        print(
            f"    {name:22} {sh:>+6.2f} {npos:>4}/{nyr} {worst[0]:>+9.2f} {mdd:>6.0f}%  "
            f"{reg['bull']:+.2f}/{reg['bear']:+.2f}/{reg['chop']:+.2f}"
        )

    # ---- (4) per-year — MOM alone vs MOM+VALUE+QUALITY (the positive-every-year test) ----
    full = combos["MOM+VALUE+QUALITY"]
    acc = sleeves[full[0]].copy()
    for m in full[1:]:
        acc = acc.add(sleeves[m], fill_value=0.0)
    acc = acc / len(full)
    full_net, _ = banded(acc, ret_fwd)
    print("\n(4) PER-YEAR — MOM alone vs MOM+VALUE+QUALITY (the positive-every-year test):")
    ym, yc = year_table(mom_net), year_table(full_net)
    print(f"    {'year':>5} {'MOM_Sh':>8} {'MOM_ret%':>9}  |  {'COMBO_Sh':>9} {'COMBO_ret%':>11}")
    for yr in sorted(yc):
        m_sh, m_r = ym.get(yr, (float("nan"), float("nan")))
        c_sh, c_r = yc[yr]
        fix = ""
        if yr in BAD_YEARS:
            fix = "  FIXED" if c_sh > 0 else "  still-neg"
        print(f"    {yr:>5} {m_sh:>+8.2f} {m_r:>+9.1f}  |  {c_sh:>+9.2f} {c_r:>+11.1f}{fix}")
    npos, nyr = n_pos_years(full_net)
    print(
        f"\n    COMBO: net IS Sharpe = {ct.msharpe(full_net, ct.LO0, ct.OOS_CUTOFF):+.3f}  "
        f"positive years = {npos}/{nyr}  (MOM alone: {n_pos_years(mom_net)[0]}/{nyr})"
    )

    # ---- (5) DIVERSIFICATION verdict ----
    v_net, q_net = nets["VALUE (book/price)"], nets["QUALITY (GP/assets)"]
    print("\n(5) DIVERSIFICATION verdict (want positive-EV + low/negative corr to MOM):")
    for label, net in (("VALUE", v_net), ("QUALITY", q_net)):
        sh = ct.msharpe(net, ct.LO0, ct.OOS_CUTOFF)
        npos, nyr = n_pos_years(net)
        c_all = corr_to(net, mom_net)
        c_bad = corr_to(net, mom_net, BAD_YEARS)
        by = bad_year_ret(net)
        ev = "positive-EV" if sh > 0 else "NEGATIVE-EV"
        div = "DIVERSIFIES" if (c_all < 0.2 and by > 0) else "does NOT clearly diversify"
        print(
            f"    {label:8} net={sh:+.2f} ({ev}), +yrs={npos}/{nyr}, corr(MOM)={c_all:+.2f} "
            f"(bad-yrs {c_bad:+.2f}), mean bad-yr ret={by:+.1f}%  -> {div}"
        )

    # ---- leak self-check: corrupt all inputs after a cut; IS net stays bit-identical pre-cut ----
    cut = full_net.index[len(full_net) // 2]
    pn_c = {k: v.copy() for k, v in pn.items()}
    pn_c["close"].loc[pn_c["close"].index >= cut] *= -7.0
    pn_c["ret_fwd"].loc[pn_c["ret_fwd"].index >= cut] += 5.0
    panels_c = {k: v.copy() for k, v in panels.items()}
    for k in panels_c:
        panels_c[k].loc[panels_c[k].index >= cut] *= -3.0
    acc_c = _gn(i6.crash_braked_raw(pn_c)).copy()
    acc_c = acc_c.add(ff.value_raw(panels_c, pn_c["close"]), fill_value=0.0)
    acc_c = acc_c.add(ff.quality_raw(panels_c, pn_c["close"]), fill_value=0.0)
    acc_c = acc_c / 3
    net1, _ = banded(acc_c, pn_c["ret_fwd"])
    common = full_net.index.intersection(net1.index)
    common = common[common < cut]
    ok = np.allclose(full_net.loc[common].to_numpy(), net1.loc[common].to_numpy(), atol=1e-10)
    print(
        f"\n  future-bar leak self-check (combo net bit-identical pre-cut): "
        f"{'PASS' if ok else 'FAIL'}"
    )


if __name__ == "__main__":
    main()
