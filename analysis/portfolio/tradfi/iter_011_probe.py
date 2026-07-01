"""iter-011 PROBE — price-only ORTHOGONAL factor sleeves to complement the momentum book.

GOAL (user 2026-07-01): lift the book to net IS Sharpe >= 0.50 AND positive EVERY calendar year
2010-2025 (IS-only). The iter-006 momentum book is +0.28 net but negative in 6 of 16 years
(2010, 2013, 2016, 2017, 2019, 2023) — the low-dispersion melt-up / sharp-cross-sectional-reversal
years cross-sectional stock momentum structurally loses. A single factor CANNOT be positive every
year; the fix is a MULTI-FACTOR market-neutral book whose sleeves have low/negative mutual
correlation so their bad years do not coincide (AQR "Value and Momentum Everywhere"; the classic
value+momentum -0.20 correlation → higher combined Sharpe).

The two textbook momentum diversifiers are VALUE and QUALITY — both need point-in-time fundamentals
(SEC-EDGAR build; see brief §C). This probe asks the honest PRICE-ONLY question first: can
PIT-trivial, price/volume-only orthogonal sleeves get us toward the target without any fundamental
data? Candidates (all leak-safe from daily OHLCV alone):

  MOM   iter-006 sector-relative multi-horizon momentum + crash gate      (the base, +0.28)
  STR1  1-month short-term reversal  -(close/close.shift(21)-1)/rvol      (Jegadeesh 1990; industry-
        relative because sector-neutralized — Da/Liu/Schaumburg: the more powerful, less-crashy)
  STR1W 1-week (5d) short-term reversal                                    (faster reversal sleeve)
  BAB   betting-against-beta: long low-beta / short high-beta             (Frazzini-Pedersen 2014,
        cross-sectional sector-neutral rank form; US BAB Sharpe ~0.75 1926-2009)
  IVOL  low idiosyncratic-vol: short high residual-vol names              (Ang-Hodrick-Xing-Zhang
        2006 low-vol anomaly, residual of a rolling market regression)

Each sleeve is built with the SAME leak-safe machinery as the momentum book: inverse-vol scaled
where a level signal, sector-neutralized (per-sector net-zero → dollar-neutral), gross-normed to
unit gross, run through the iter-003 hysteresis band (delta=0.005) + net_from_raw vol-target (15%
ann) + 6bps/side taker cost. So every sleeve's net Sharpe is directly comparable to the +0.28 book.

COMBINATION: an equal-weight SIGNAL blend (gross-norm each sleeve → average → ONE band → ONE
vol-target) — a single market-neutral book that nets turnover across sleeves (the realistic build).
Equal-weight the unit-gross sleeves ~= risk parity (each is unit-gross, individually ~15%-vol after
the shared vol-target), so NO fitted weights and NO look-ahead. Reported alongside a return-level
inverse-vol blend as a robustness check.

LEAK SAFETY: every sleeve reads only close.shift(>=1)/past returns; betas/idio-vol are past-only
rolling then .shift(1)-lagged; combination weights are equal (no fit) or trailing-vol (past-only).
The combined raw feeds the strictly-causal iter-003 band (single .shift(1) execution lag). OOS is
HIDDEN — every metric on the IS slice (< 2025-03-24); no OOS number is computed. This is a PROBE
(measurement), not a promotion; it prescribes the iter-011 change but does not itself promote.

Run:  uv run python analysis/portfolio/tradfi/iter_011_probe.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import core_tradfi as ct  # noqa: E402
import iter_003_hysteresis as i3  # noqa: E402
import iter_005_multihorizon as i5  # noqa: E402
import iter_006_crashbrake as i6  # noqa: E402
import neutralize as nz  # noqa: E402
import universe_tradfi as ut  # noqa: E402

DELTA = i5.CHOSEN_DELTA  # 0.005 hysteresis band, inherited UNCHANGED
BAD_YEARS = [2010, 2013, 2016, 2017, 2019, 2023]  # momentum book's negative years (Part A)


def _rvol(close):
    return close.pct_change().rolling(ct.VOL_WIN).std()


def _gn(raw):
    """Gross-normalize each row to unit gross (== iter-005 _gross_norm). Leak-free."""
    g = raw.abs().sum(axis=1).replace(0, np.nan)
    return raw.div(g, axis=0).fillna(0.0)


# ---------------------------------------------------------------- sleeves (all leak-safe) -------
def sleeve_mom(pn):
    """iter-006 momentum book raw (multi-horizon + crash gate), gross-normed."""
    return _gn(i6.crash_braked_raw(pn))


def sleeve_str(pn, lookback):
    """Short-term reversal: LONG past-`lookback` losers / SHORT winners, inverse-vol, sector-neut.

    signal = -(close/close.shift(lookback) - 1)/rvol.  Sector-neutralized => industry-relative
    reversal (Da-Liu-Schaumburg: the more powerful, less-crashy reversal). No skip (reversal wants
    the freshest move), but the .shift(1) execution lag is applied downstream by the band.
    """
    close = pn["close"]
    sig = -(close / close.shift(lookback) - 1.0) / _rvol(close)
    return _gn(nz.sector_neutralize(sig, ut.SECTOR_MAP))


def sleeve_bab(pn, beta_win=252):
    """Betting-against-beta (cross-sectional sector-neutral rank form): LONG low-beta / SHORT high.

    beta = rolling cov(asset, EW-mkt)/var(mkt) over beta_win, .shift(1)-lagged (past-only). signal =
    -zscore(beta) within the row; sector-neutralized. This is the sector-neutral cross-sectional
    tilt version of Frazzini-Pedersen (not the leveraged two-portfolio original, which we cannot
    replicate without a risk-free/leverage model) — but it captures the same low-beta-long premium.
    """
    close = pn["close"]
    ret = close.pct_change()
    mkt = ret.mean(axis=1)
    beta = nz.rolling_beta(ret, mkt, win=beta_win).shift(1)
    # cross-sectional z-score of beta per row, then go SHORT it (long low beta)
    z = beta.sub(beta.mean(axis=1), axis=0).div(beta.std(axis=1).replace(0, np.nan), axis=0)
    return _gn(nz.sector_neutralize(-z, ut.SECTOR_MAP))


def sleeve_ltr(pn, long_leg=756, skip=252):
    """LONG-TERM reversal (De Bondt-Thaler 1985) = a PRICE-ONLY VALUE PROXY, sector-neutral.

    signal = -(close.shift(skip)/close.shift(long_leg) - 1)/rvol : LONG the multi-year LOSERS /
    SHORT the multi-year winners, skipping the last 12m so it does NOT cannibalize the 12-1m
    momentum sleeve. 3y-1y (756/252) is the sweet spot here: past-3yr-to-1yr losers are the
    universe's "cheap" names (a price proxy for VALUE when no fundamentals exist). Warm-up is ~3yr,
    so breadth only fills in from ~2013 (early years fall back toward pure momentum) — leak-safe.
    """
    close = pn["close"]
    sig = -(close.shift(skip) / close.shift(long_leg) - 1.0) / _rvol(close)
    return _gn(nz.sector_neutralize(sig, ut.SECTOR_MAP))


def sleeve_ivol(pn, beta_win=252, res_win=63):
    """Low idiosyncratic-vol: SHORT high-residual-vol / LONG low, sector-neutral (Ang et al. 2006).

    residual r_i - beta_i*mkt over a trailing res_win window; idio-vol = std of that residual.
    beta is past-only .shift(1)-lagged; residual + its rolling std are past-only. signal =
    -zscore(idio_vol).
    """
    close = pn["close"]
    ret = close.pct_change()
    mkt = ret.mean(axis=1)
    beta = nz.rolling_beta(ret, mkt, win=beta_win).shift(1)
    resid = ret.sub(beta.mul(mkt, axis=0))
    ivol = resid.rolling(res_win).std()
    z = ivol.sub(ivol.mean(axis=1), axis=0).div(ivol.std(axis=1).replace(0, np.nan), axis=0)
    return _gn(nz.sector_neutralize(-z, ut.SECTOR_MAP))


# ---------------------------------------------------------------- metrics -----------------------
def banded(raw, ret_fwd):
    return i3.banded_net(raw, ret_fwd, DELTA)  # (net, w)


def year_table(net):
    """Per-year (Sharpe, return%) on the IS slice."""
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
    """Monthly-return correlation over IS (optionally restricted to `years`)."""
    a, b = monthly(net_a), monthly(net_b)
    idx = a.index.intersection(b.index)
    if years is not None:
        idx = idx[[p.year in years for p in idx]]
    if len(idx) < 3:
        return float("nan")
    return float(np.corrcoef(a.loc[idx], b.loc[idx])[0, 1])


def bad_year_ret(net):
    """Mean per-year total return% across the momentum book's 6 negative years."""
    yt = year_table(net)
    return float(np.mean([yt[y][1] for y in BAD_YEARS if y in yt]))


def main():
    base = ct._ROOT / "data"
    syms = sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)
    coins = ct.load_tradfi(syms)
    pn = ct.panels(coins)
    ret_fwd = pn["ret_fwd"]

    print("=" * 100)
    print(
        "iter-011 PROBE — price-only orthogonal sleeves vs the momentum book (IS-only, 2010-2025)"
    )
    print("=" * 100)

    sleeves = {
        "MOM (iter-006)": sleeve_mom(pn),
        "STR1 (1m rev)": sleeve_str(pn, 21),
        "STR1W (1w rev)": sleeve_str(pn, 5),
        "BAB (low-beta)": sleeve_bab(pn),
        "IVOL (low idio)": sleeve_ivol(pn),
        "LTR (3y-1y value)": sleeve_ltr(pn),  # the ONE orthogonal, positive-EV price sleeve
    }
    nets = {name: banded(raw, ret_fwd)[0] for name, raw in sleeves.items()}
    mom_net = nets["MOM (iter-006)"]

    # --- (1) standalone sleeve scorecard ---
    print("\n(1) STANDALONE sleeves (same band + 15% vol-target + 6bps cost) — IS net Sharpe:")
    print(
        f"    {'sleeve':16} {'net':>6} {'+yrs':>5} {'corr_MOM':>9} {'corr(bad)':>10} "
        f"{'badYrRet%':>10}  regimes(bull/bear/chop)"
    )
    for name, net in nets.items():
        npos, nyr = n_pos_years(net)
        c_all = corr_to(net, mom_net) if name != "MOM (iter-006)" else 1.0
        c_bad = corr_to(net, mom_net, BAD_YEARS) if name != "MOM (iter-006)" else 1.0
        reg = ct.regime_sharpe(ct.is_only(net))
        sh = ct.msharpe(net, ct.LO0, ct.OOS_CUTOFF)
        print(
            f"    {name:16} {sh:>+6.2f} {npos:>3}/{nyr} {c_all:>+9.2f} {c_bad:>+10.2f} "
            f"{bad_year_ret(net):>+10.1f}  "
            f"{reg['bull']:+.2f}/{reg['bear']:+.2f}/{reg['chop']:+.2f}"
        )

    # --- (2) per-year detail for MOM + the best diversifiers (do the bad years get covered?) ---
    print("\n(2) PER-YEAR net Sharpe — does a sleeve EARN in the momentum book's 6 bad years?")
    show = ["MOM (iter-006)", "STR1 (1m rev)", "BAB (low-beta)", "IVOL (low idio)"]
    yts = {n: year_table(nets[n]) for n in show}
    yrs = sorted(next(iter(yts.values())).keys())
    print(f"    {'year':>5} " + " ".join(f"{n.split()[0]:>8}" for n in show))
    for yr in yrs:
        cells = []
        for n in show:
            sh = yts[n].get(yr, (float("nan"),))[0]
            mark = "*" if (n == "MOM (iter-006)" and yr in BAD_YEARS) else " "
            cells.append(f"{sh:>+7.2f}{mark}")
        print(f"    {yr:>5} " + " ".join(cells))

    # --- (3) COMBINATIONS (signal-level equal-weight blend → one band → one vol-target) ---
    print("\n(3) COMBINED market-neutral books (equal-weight SIGNAL blend, one band+vol-target):")
    combos = {
        "MOM+STR1": ["MOM (iter-006)", "STR1 (1m rev)"],
        "MOM+BAB": ["MOM (iter-006)", "BAB (low-beta)"],
        "MOM+IVOL": ["MOM (iter-006)", "IVOL (low idio)"],
        "MOM+STR1+BAB": ["MOM (iter-006)", "STR1 (1m rev)", "BAB (low-beta)"],
        "MOM+STR1+BAB+IVOL": [
            "MOM (iter-006)",
            "STR1 (1m rev)",
            "BAB (low-beta)",
            "IVOL (low idio)",
        ],
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

    # --- (4) per-year detail for the full combo (the positive-every-year test) ---
    full = combos["MOM+STR1+BAB+IVOL"]
    acc = sleeves[full[0]].copy()
    for m in full[1:]:
        acc = acc.add(sleeves[m], fill_value=0.0)
    acc = acc / len(full)
    full_net, _ = banded(acc, ret_fwd)
    print("\n(4) PER-YEAR — MOM alone vs MOM+STR1+BAB+IVOL combo (the positive-every-year test):")
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
        f"positive years = {npos}/{nyr}  "
        f"(target: net>=+0.50 AND {nyr}/{nyr})"
    )

    # --- (5) return-level inverse-vol blend robustness check (independent sleeves, past-only) --
    print("\n(5) ROBUSTNESS — return-level blend (each sleeve vol-targeted independently):")
    members = full
    ndf = pd.DataFrame({m: ct.is_only(nets[m]) for m in members}).dropna()
    for label, wts in (
        ("equal-weight", pd.Series(1.0, index=members)),
        ("inv-vol (static)", 1.0 / ndf.std()),
    ):
        w = wts / wts.sum()
        blend = (ndf * w).sum(axis=1)
        bm = blend.groupby(blend.index.to_period("M")).sum()
        sh = float(bm.mean() / bm.std() * np.sqrt(12))
        npos = sum(
            1
            for _, g in blend.groupby(blend.index.year)
            if (gm := g.groupby(g.index.to_period("M")).sum()).mean() / gm.std() > 0
        )
        print(
            f"    {label:18} net Sharpe={sh:+.2f}  +years={npos}/{blend.index.year.nunique()}"
        )

    # --- (6) RECOMMENDED iter-011: MOM + w*LTR (the one orthogonal positive-EV price sleeve) ------
    print("\n(6) RECOMMENDED iter-011 — MOM + w*LTR (value-proxy) signal blend (weight BASIN):")
    mom_raw, ltr_raw = sleeves["MOM (iter-006)"], sleeves["LTR (3y-1y value)"]
    print(
        f"    {'weight w':>10} {'net':>6} {'+yrs':>6} {'worst-yr':>9} {'maxDD':>7}  bull/bear/chop"
    )
    for wl in (0.3, 0.5, 0.7, 1.0):
        raw = mom_raw.add(ltr_raw * wl, fill_value=0.0) / (1.0 + wl)
        net, _ = banded(raw, ret_fwd)
        yt = year_table(net)
        npos = sum(1 for shv, _ in yt.values() if shv > 0)
        worst = min(yt.items(), key=lambda kv: kv[1][0])
        reg = ct.regime_sharpe(ct.is_only(net))
        tag = "  <- pre-registered" if wl == 0.5 else ""
        sh_c = ct.msharpe(net, ct.LO0, ct.OOS_CUTOFF)
        mdd_c = ct.maxdd(ct.is_only(net)) * 100
        print(
            f"    MOM+{wl:.1f}*LTR {sh_c:>+6.2f} {npos:>3}/{len(yt)} "
            f"{worst[0]}:{worst[1][0]:>+.2f} {mdd_c:>6.0f}%  "
            f"{reg['bull']:+.2f}/{reg['bear']:+.2f}/{reg['chop']:+.2f}{tag}"
        )

    raw = mom_raw.add(ltr_raw * 0.5, fill_value=0.0) / 1.5
    rec_net, _ = banded(raw, ret_fwd)
    ym, yr_ = year_table(mom_net), year_table(rec_net)
    print("\n    PER-YEAR MOM vs recommended MOM+0.5*LTR (does it fix the momentum-crash years?):")
    for yr in sorted(yr_):
        mk = "*" if yr in BAD_YEARS else " "
        fix = (
            "  FIXED"
            if yr in BAD_YEARS and yr_[yr][0] > 0
            else "  still-neg"
            if yr in BAD_YEARS
            else ""
        )
        print(
            f"    {yr:>5}{mk} MOM {ym[yr][0]:>+6.2f} -> {yr_[yr][0]:>+6.2f} "
            f"({yr_[yr][1]:>+5.1f}%){fix}"
        )
    npos, nyr = n_pos_years(rec_net)
    print(
        f"    net={ct.msharpe(rec_net, ct.LO0, ct.OOS_CUTOFF):+.3f} (vs MOM +0.28)  "
        f"positive years={npos}/{nyr} (vs MOM 10/16)  corr(MOM,LTR)="
        f"{corr_to(mom_net, banded(ltr_raw, ret_fwd)[0]):+.2f} full / "
        f"{corr_to(mom_net, banded(ltr_raw, ret_fwd)[0], BAD_YEARS):+.2f} bad-yrs"
    )
    print(
        "    HONEST: lifts net + fixes the momentum-CRASH years (2013/2016/2023) but NOT the "
        "LOW-DISPERSION years (2017/2019) — target (+0.50 AND 16/16) NOT reached price-only."
    )

    # --- leak self-check on the full combo ---
    net0, w0 = banded(acc, ret_fwd)
    cut = net0.index[len(net0) // 2]
    pn_c = {k: v.copy() for k, v in pn.items()}
    pn_c["close"].loc[pn_c["close"].index >= cut] *= -7.0
    pn_c["ret_fwd"].loc[pn_c["ret_fwd"].index >= cut] += 5.0
    acc_c = sleeve_mom(pn_c).copy()
    for fn, args in ((sleeve_str, (21,)), (sleeve_bab, ()), (sleeve_ivol, ())):
        acc_c = acc_c.add(fn(pn_c, *args), fill_value=0.0)
    acc_c = acc_c / 4
    net1, _ = banded(acc_c, pn_c["ret_fwd"])
    common = net0.index.intersection(net1.index)
    common = common[common < cut]
    ok = np.allclose(net0.loc[common].to_numpy(), net1.loc[common].to_numpy(), atol=1e-10)
    print(
        f"\n  future-bar leak self-check (combo net bit-identical pre-cut): "
        f"{'PASS' if ok else 'FAIL'}"
    )


if __name__ == "__main__":
    main()
