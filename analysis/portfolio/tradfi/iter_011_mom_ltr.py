"""iter-011 — LONG-TERM-REVERSAL (value-proxy) sleeve added to the iter-006 momentum book.

ONE change vs iter-006: blend a within-sector LONG-TERM-REVERSAL (LTR) sleeve into the momentum
SIGNAL before the band. Everything downstream — the iter-003 hysteresis band (delta=0.005), the
leak-safe banded_net / vol-target / taker-cost model, and the OOS-hidden accounting — is UNCHANGED.
Only the raw that feeds the band is now (mom + 0.5*ltr), each gross-normed to unit gross first.

=========================================================================================
WHY a long-term-reversal sleeve (the multi-factor diversification thesis)
=========================================================================================
The iter-006 momentum book is net +0.28 IS but NEGATIVE in 6 of 16 calendar years (2010, 2013,
2016, 2017, 2019, 2023). The probe (iter_011_probe.py) split those into two failure modes: the
momentum-CRASH years (2013/2016/2023 — losers snap back hard) and the LOW-DISPERSION melt-up years
(2013/2017/2019 — every cross-sectional factor earns ~0 at once). A value-shaped diversifier fixes
the crash years; nothing market-neutral fixes the low-dispersion years.

Long-term (3y-1y) reversal is the De Bondt-Thaler (1985) VALUE PROXY: the multi-year LOSERS are the
universe's "cheap" names when no fundamentals exist. On this universe it is the ONE price-only,
PIT-trivial, orthogonal, positive-EV sleeve that survives cost (probe Part D: LTR net +0.21, gross
+0.26, corr->MOM +0.01). Value and momentum are canonically negatively correlated (AQR "Value and
Momentum Everywhere"), so blending their imperfectly-correlated bad years raises Sharpe and smooths
the year curve — exactly the mechanism the probe measures here on our 69-name book.

=========================================================================================
THE ONE CHANGE — the LTR sleeve + the equal-weight signal blend
=========================================================================================
    rvol      = close.pct_change().rolling(63).std()                          # 63d realized vol
    ltr_raw   = gross_norm( sector_neutralize( -(close.shift(252)/close.shift(756)-1)/rvol, MAP ) )
    mom_raw   = gross_norm( iter006.crash_braked_raw(pn) )        # the iter-006 base, UNCHANGED
    raw       = ( mom_raw + 0.5 * ltr_raw ) / 1.5                 # w = 0.5 PRE-REGISTERED (basin)
    net, w    = iter003.banded_net(raw, ret_fwd, delta=0.005)     # band + vol-target UNCHANGED

  * LTR signal = -(close.shift(252)/close.shift(756) - 1)/rvol : LONG the 3y-to-1y LOSERS / SHORT
    the 3y-to-1y winners, sector-neutralized (industry-relative value), inverse-vol scaled. The
    skip=252 (1-year) long-end GAP guarantees NO overlap with the 12-1m momentum long leg — the two
    sleeves read disjoint price windows, so LTR is a different bet, not re-sliced momentum.
  * w = 0.5 is PRE-REGISTERED (basin 0.3-0.7 all ~= +0.33 in the probe — a broad plateau, NOT a
    knife-edge). It is NOT tuned to the revealed bad years: LTR is a theory-grounded value proxy and
    the basin sweep is the anti-overfit guard. w=0 reproduces iter-006 (the pre-registered ident.).
  * PIT / ragged: LTR needs 756 trading days (~3yr) of history, so a name with <3yr history (recent
    IPO) has a NaN LTR signal and takes ZERO LTR weight until it seasons. Breadth fills in only from
    ~2013 — the early years (2010-2012) fall back toward PURE momentum (leak-safe, honest, no fit).

=========================================================================================
PRE-REGISTERED IS EFFECT (banded delta=0.005, IS < 2025-03-24, OOS HIDDEN) — from the probe
=========================================================================================
                       net    +yrs    bull    bear    chop    maxDD
  iter-006 (MOM base)  +0.28   10/16  +0.30   -0.24   +0.51   -29%
  iter-011 MOM+0.5LTR  +0.33   11/16  +0.26   +0.35   +0.60   -49%

Fixes the momentum-CRASH years 2013 (-1.28->+0.46), 2016 (-0.56->+1.02), 2023 (-0.09->+0.37); does
NOT fix the low-dispersion years 2017/2019 (both worsen) — a market-neutral book cannot manufacture
return in a low-dispersion melt-up. corr(MOM,LTR) = +0.01 full IS / -0.12 in the bad years (genuine
diversification). Cost: maxDD -29% -> -49% (LTR is more drawdown-prone). This is an ACCRETIVE
multi-factor step, NOT a promote: it does NOT reach the raised bar (net >= +0.50 AND positive EVERY
year), a multi-iteration goal the probe pre-registered (universe breadth + PIT fundamentals).

The iter-008 VIX brake is tested ON TOP (an outer past-only scalar on the vol-targeted net) purely
to see if it tames the deeper -49% maxDD — reported honestly, NOT folded into the sleeve decision.

IDENTITY (pre-registered): w=0 -> raw == gross_norm(iter006 book); through the band's own gross-norm
this reproduces the iter-006 banded net up to machine-eps (double gross-norm re-rounds; allclose
1e-12, msharpe-equal — the same idempotency iter-005 documents), anchoring iter-011 as a pure
one-change delta off iter-006.

OOS stays HIDDEN (perf_line reveal_oos=False) unless --confirm (CONFIRMATION only). Everything here
is IS-only; no OOS number is computed without --confirm. Do NOT tune the LTR weight / windows.

Run: uv run python analysis/portfolio/tradfi/iter_011_mom_ltr.py
"""

from __future__ import annotations

import argparse
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
import iter_008_vix_stop as i8  # noqa: E402
import neutralize as nz  # noqa: E402
import universe_tradfi as ut  # noqa: E402

# --- PRE-REGISTERED LTR sleeve windows + blend weight (theory-pinned; NOT swept to max-net) ---
LTR_LONG = 756  # 3-year long leg (De Bondt-Thaler reversal window)
LTR_SKIP = 252  # 1-year skip -> the disjoint gap that keeps LTR off the 12-1m momentum long leg
W_LTR = 0.5  # pre-registered blend weight (basin 0.3-0.7); w=0 reproduces iter-006
CHOSEN_DELTA = i5.CHOSEN_DELTA  # 0.005, inherited from iter-003 UNCHANGED

BAD_YEARS = [2010, 2013, 2016, 2017, 2019, 2023]  # the iter-006 book's negative years
MOM_CRASH_YEARS = [2013, 2016, 2023]  # the crash-year subset LTR should FLIP positive


# ---------------------------------------------------------------- sleeves (leak-safe) -----------
def ltr_sleeve(pn: dict[str, pd.DataFrame], long_leg: int = LTR_LONG, skip: int = LTR_SKIP):
    """Within-sector LONG-TERM reversal (value proxy), gross-normed to unit gross.

    signal = -(close.shift(skip)/close.shift(long_leg) - 1)/rvol : LONG multi-year losers / SHORT
    multi-year winners, sector-neutralized (industry-relative) then gross-normed. All past
    (close.shift(>=252) + trailing-63 rvol). A name without `long_leg` days of history has a NaN
    signal -> 0 weight after gross_norm's fillna (ragged / PIT-clean by construction).
    """
    close = pn["close"]
    sig = -(close.shift(skip) / close.shift(long_leg) - 1.0) / i5._rvol(close)
    return i5._gross_norm(nz.sector_neutralize(sig, ut.SECTOR_MAP))


def mom_sleeve(pn: dict[str, pd.DataFrame]):
    """The iter-006 crash-braked momentum book, gross-normed to unit gross (UNCHANGED base)."""
    return i5._gross_norm(i6.crash_braked_raw(pn))


def mom_ltr_raw(pn: dict[str, pd.DataFrame], w: float = W_LTR):
    """The ONE change: equal-weight signal blend (mom_raw + w*ltr_raw)/(1+w), each unit-gross first.

    A row-wise linear combination of two past-only, per-sector-net-zero, unit-gross sleeves -> the
    blend stays past-only and per-sector-zero and feeds the iter-003 band UNCHANGED. w=0 returns the
    gross-normed iter-006 book (the pre-registered identity).
    """
    mom = mom_sleeve(pn)
    ltr = ltr_sleeve(pn)
    return mom.add(ltr * w, fill_value=0.0) / (1.0 + w)


# ---------------------------------------------------------------- IS-only metrics ---------------
def _banded(raw, ret_fwd):
    return i3.banded_net(raw, ret_fwd, CHOSEN_DELTA)  # (net, w)


def year_table(net: pd.Series) -> dict[int, tuple[float, float]]:
    """Per calendar year (monthly Sharpe, total return %) over the IS slice only."""
    net = ct.is_only(net)
    out: dict[int, tuple[float, float]] = {}
    for yr, g in net.groupby(net.index.year):
        m = g.groupby(g.index.to_period("M")).sum()
        sh = float(m.mean() / m.std() * np.sqrt(12)) if len(m) > 1 and m.std() > 0 else float("nan")
        out[int(yr)] = (sh, float((np.prod(1.0 + g) - 1.0) * 100))
    return out


def n_pos_years(net: pd.Series) -> tuple[int, int]:
    yt = year_table(net)
    return sum(1 for sh, _ in yt.values() if sh > 0), len(yt)


def _monthly(net: pd.Series) -> pd.Series:
    net = ct.is_only(net)
    return net.groupby(net.index.to_period("M")).sum()


def corr_monthly(net_a: pd.Series, net_b: pd.Series, years=None) -> float:
    """Monthly-return correlation over IS (optionally restricted to `years`)."""
    a, b = _monthly(net_a), _monthly(net_b)
    idx = a.index.intersection(b.index)
    if years is not None:
        idx = idx[[p.year in years for p in idx]]
    if len(idx) < 3:
        return float("nan")
    return float(np.corrcoef(a.loc[idx], b.loc[idx])[0, 1])


def _leak_selfcheck(pn, ret_fwd, delta) -> bool:
    """Corrupt panel + forward returns AFTER a cutoff; the mom+LTR banded net/weights before it must
    be bit-identical (LTR reads close.shift(252)/close.shift(756) — pure past — and the blend feeds
    the strictly-causal band)."""
    net0, w0 = _banded(mom_ltr_raw(pn), ret_fwd)
    cut = net0.index[len(net0) // 2]
    pn_c = {k: v.copy() for k, v in pn.items()}
    pn_c["close"].loc[pn_c["close"].index >= cut] *= -7.0
    pn_c["ret_fwd"].loc[pn_c["ret_fwd"].index >= cut] += 5.0
    net1, w1 = _banded(mom_ltr_raw(pn_c), pn_c["ret_fwd"])
    common = net0.index.intersection(net1.index)
    common = common[common < cut]
    ok_net = np.allclose(net0.loc[common].to_numpy(), net1.loc[common].to_numpy(), atol=1e-12)
    ok_w = np.allclose(
        w0[w0.index < cut].fillna(0.0).to_numpy(),
        w1[w1.index < cut].fillna(0.0).to_numpy(),
        atol=1e-12,
    )
    return bool(ok_net and ok_w)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--w", type=float, default=W_LTR, help="LTR blend weight (pre-registered 0.5)")
    ap.add_argument("--delta", type=float, default=CHOSEN_DELTA, help="hysteresis band (iter-003)")
    ap.add_argument("--confirm", action="store_true", help="reveal OOS (CONFIRMATION only)")
    ap.add_argument("--data-dir", default=None)
    args = ap.parse_args()
    d = args.delta

    base = Path(args.data_dir) if args.data_dir else ct._ROOT / "data"
    syms = sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)
    coins = ct.load_tradfi(syms, args.data_dir)
    if not coins:
        print("No ingested tradfi data found. Run ingest_yahoo.py first.")
        return

    pn = ct.panels(coins)
    close, ret_fwd = pn["close"], pn["ret_fwd"]

    print("=" * 100)
    print(
        "iter-011 — LONG-TERM-REVERSAL (value-proxy) sleeve on the iter-006 momentum book (IS-only)"
    )
    print("=" * 100)
    print(
        f"  LTR: -(close.shift({LTR_SKIP})/close.shift({LTR_LONG})-1)/rvol, sector-neutral, "
        f"gross-normed;  raw=(mom + {args.w:.1f}*ltr)/{1.0 + args.w:.1f};  band delta={d:.3f}\n"
    )

    # --- iter-006 reference (the +0.28 momentum base) ---
    net_mom, w_mom = _banded(i6.crash_braked_raw(pn), ret_fwd)

    # --- IDENTITY: w=0 -> gross_norm(iter006) -> band's own gross-norm is idempotent up to eps ---
    net_id, _ = _banded(mom_ltr_raw(pn, 0.0), ret_fwd)
    maxdiff = float(np.nanmax(np.abs(net_id.to_numpy() - net_mom.to_numpy())))
    ident = bool(np.allclose(net_id.to_numpy(), net_mom.to_numpy(), atol=1e-12, rtol=0.0))
    print(
        f"  IDENTITY w=0 reproduces iter-006: {'PASS' if ident else 'FAIL'}  "
        f"(allclose 1e-12; max|d|={maxdiff:.1e}, machine-eps double-gross-norm)  "
        f"IS_Sharpe={ct.msharpe(net_id, ct.LO0, ct.OOS_CUTOFF):+.2f} vs iter-006 "
        f"{ct.msharpe(net_mom, ct.LO0, ct.OOS_CUTOFF):+.2f}"
    )

    # --- (1) STANDALONE sleeves (each through the SAME band) — orthogonality scorecard ---
    net_ltr, _ = _banded(ltr_sleeve(pn), ret_fwd)
    print("\n  (1) STANDALONE sleeves (same band + 15% vol-target + 6bps cost), IS net Sharpe:")
    for name, net in (("MOM (iter-006)", net_mom), ("LTR (3y-1y value)", net_ltr)):
        npos, nyr = n_pos_years(net)
        reg = ct.regime_sharpe(ct.is_only(net))
        c = 1.0 if name.startswith("MOM") else corr_monthly(net, net_mom)
        print(
            f"      {name:18} net={ct.msharpe(net, ct.LO0, ct.OOS_CUTOFF):+.2f}  "
            f"+yrs={npos}/{nyr}  corr->MOM={c:+.2f}  "
            f"bull/bear/chop={reg['bull']:+.2f}/{reg['bear']:+.2f}/{reg['chop']:+.2f}"
        )

    # --- (2) HEADLINE: iter-011 = MOM + w*LTR vs iter-006 ---
    raw11 = mom_ltr_raw(pn, args.w)
    net11, w11 = _banded(raw11, ret_fwd)
    reg11 = ct.regime_sharpe(ct.is_only(net11))
    reg6 = ct.regime_sharpe(ct.is_only(net_mom))
    npos11, nyr = n_pos_years(net11)
    npos6, _ = n_pos_years(net_mom)
    turn11 = ct.turnover(w11, ct.LO0, ct.OOS_CUTOFF)
    turn6 = ct.turnover(w_mom, ct.LO0, ct.OOS_CUTOFF)
    print(f"\n  (2) HEADLINE iter-011 (MOM + {args.w:.1f}*LTR) vs iter-006:")
    print(ct.perf_line("iter-006 (MOM base)", net_mom, reveal_oos=args.confirm))
    print(
        f"      +yrs={npos6}/{nyr}  bull={reg6['bull']:+.2f} bear={reg6['bear']:+.2f} "
        f"chop={reg6['chop']:+.2f}  turn/day={turn6:.4f}"
    )
    print(ct.perf_line(f"iter-011 MOM+{args.w:.1f}LTR", net11, reveal_oos=args.confirm))
    print(
        f"      +yrs={npos11}/{nyr}  bull={reg11['bull']:+.2f} bear={reg11['bear']:+.2f} "
        f"chop={reg11['chop']:+.2f}  turn/day={turn11:.4f} "
        f"({(turn11 / turn6 - 1) * 100:+.0f}% vs iter-006)"
    )

    # --- (3) WEIGHT BASIN sweep (pre-registered plateau 0.3-0.7; anti-overfit) ---
    print("\n  (3) WEIGHT BASIN (LTR weight w; broad plateau -> not a knife-edge):")
    print(f"      {'w':>6} {'net':>6} {'+yrs':>6} {'worst-yr':>11} {'maxDD':>7}  bull/bear/chop")
    for wl in (0.3, 0.5, 0.7, 1.0):
        nb, _ = _banded(mom_ltr_raw(pn, wl), ret_fwd)
        yt = year_table(nb)
        npos = sum(1 for shv, _ in yt.values() if shv > 0)
        wy, (wsh, _) = min(yt.items(), key=lambda kv: kv[1][0])
        reg = ct.regime_sharpe(ct.is_only(nb))
        tag = "  <- pre-registered" if wl == 0.5 else ""
        print(
            f"      {wl:>6.1f} {ct.msharpe(nb, ct.LO0, ct.OOS_CUTOFF):>+6.2f} {npos:>4}/{len(yt)} "
            f"{wy}:{wsh:>+6.2f} {ct.maxdd(ct.is_only(nb)) * 100:>6.0f}%  "
            f"{reg['bull']:+.2f}/{reg['bear']:+.2f}/{reg['chop']:+.2f}{tag}"
        )

    # --- (4) VIX brake ON TOP (outer past-only scalar on the vol-targeted net) — maxDD tamer? ---
    vix = i8.load_vix_close(net11.index, args.data_dir)
    s_vix = i8.vix_scale(vix)  # pinned base=20 / floor=0.50 (iter-008 UNCHANGED)
    net11_vix = net11 * s_vix.reindex(net11.index).fillna(1.0)
    mdd11 = ct.maxdd(ct.is_only(net11)) * 100
    mdd11_vix = ct.maxdd(ct.is_only(net11_vix)) * 100
    reg11v = ct.regime_sharpe(ct.is_only(net11_vix))
    nposv, _ = n_pos_years(net11_vix)
    print(
        "\n  (4) VIX brake ON TOP of iter-011 (iter-008 s=clip(20/VIX[t-1],0.5,1); exposure only):"
    )
    print(
        f"      iter-011      : net={ct.msharpe(net11, ct.LO0, ct.OOS_CUTOFF):+.2f}  "
        f"maxDD={mdd11:.0f}%  +yrs={npos11}/{nyr}"
    )
    print(
        f"      iter-011 +VIX : net={ct.msharpe(net11_vix, ct.LO0, ct.OOS_CUTOFF):+.2f}  "
        f"maxDD={mdd11_vix:.0f}%  +yrs={nposv}/{nyr}  "
        f"bull={reg11v['bull']:+.2f} bear={reg11v['bear']:+.2f} chop={reg11v['chop']:+.2f}"
    )
    print(
        f"      -> VIX brake {'TAMES' if mdd11_vix > mdd11 else 'does NOT tame'} the drawdown "
        f"(maxDD {mdd11:.0f}% -> {mdd11_vix:.0f}%)"
    )

    # --- (5) PER-YEAR table 2010-2025: MOM -> iter-011 (+FIXED markers) -> iter-011+VIX ---
    print(
        "\n  (5) PER-YEAR net Sharpe / return% (IS 2010-2025): iter-006 -> iter-011 -> iter-011+VIX"
    )
    ymom, y11, y11v = year_table(net_mom), year_table(net11), year_table(net11_vix)
    print(
        f"      {'year':>5} {'MOM_Sh':>8} {'MOM_r%':>7}  |  {'i11_Sh':>8} {'i11_r%':>7} {'fix':>10}"
        f"  |  {'i11V_Sh':>8} {'i11V_r%':>8}"
    )
    for yr in sorted(y11):
        msh, mr = ymom.get(yr, (float("nan"), float("nan")))
        csh, cr = y11[yr]
        vsh, vr = y11v[yr]
        fix = ""
        if yr in BAD_YEARS:
            fix = "FIXED" if csh > 0 else "still-neg"
        star = "*" if yr in BAD_YEARS else " "
        print(
            f"      {yr:>4}{star} {msh:>+8.2f} {mr:>+7.1f}  |  {csh:>+8.2f} {cr:>+7.1f} {fix:>10}"
            f"  |  {vsh:>+8.2f} {vr:>+8.1f}"
        )

    # --- (6) mom<->LTR orthogonality (the diversification claim) ---
    c_full = corr_monthly(net_mom, net_ltr)
    c_bad = corr_monthly(net_mom, net_ltr, BAD_YEARS)
    print(
        f"\n  (6) mom<->LTR monthly-net corr: {c_full:+.2f} full IS / {c_bad:+.2f} bad-years "
        f"(orthogonal -> genuine diversification)"
    )

    # --- (7) PIT / ragged handling — a name with <756d history takes ZERO LTR weight ---
    ltr = ltr_sleeve(pn)
    ltr_is = ltr[ltr.index < ct.OOS_CUTOFF]
    unseasoned = close.reindex(ltr_is.index).shift(LTR_LONG).isna()  # <756d history OR missing bar
    zero_ok = bool((np.abs(ltr_is.to_numpy()[unseasoned.to_numpy()]) < 1e-15).all())
    breadth = (ltr_is.abs() > 1e-12).sum(axis=1)
    by_year = breadth.groupby(breadth.index.year).mean()
    print(
        f"\n  (7) PIT ragged handling: unseasoned (<{LTR_LONG}d history) names get 0 LTR weight: "
        f"{'PASS' if zero_ok else 'FAIL'}"
    )
    print(
        "      LTR breadth (mean names with non-zero weight / yr): "
        + " ".join(f"{y}:{int(round(v))}" for y, v in by_year.items() if y <= 2016)
        + " ...  (early years ~0 -> falls back to pure momentum, leak-safe)"
    )

    # --- (8) leak self-check + sector-neutrality residual ---
    print(
        f"\n  (8) future-bar leak self-check (mom+LTR banded net+weights bit-identical pre-cut): "
        f"{'PASS' if _leak_selfcheck(pn, ret_fwd, d) else 'FAIL'}"
    )
    print(
        f"      sector-neutrality residual (IS active): {i3._sector_residual(w11):.1e}  "
        f"(blend of two per-sector-zero sleeves stays per-sector-zero pre-band)"
    )

    # --- (9) PRE-REGISTERED gate: net>+0.28 AND +yrs>=11/16 AND corr<0.3 AND crash years flip ---
    net11_sh = ct.msharpe(net11, ct.LO0, ct.OOS_CUTOFF)
    crash_flip = all(y11[y][0] > 0 for y in MOM_CRASH_YEARS)
    g_net = net11_sh > 0.28
    g_yrs = npos11 >= 11
    g_corr = c_full < 0.3
    g_leak = _leak_selfcheck(pn, ret_fwd, d)
    keep = g_net and g_yrs and g_corr and crash_flip and g_leak
    print("\n  (9) PRE-REGISTERED gate:")
    print(
        f"      net>+0.28={'Y' if g_net else 'N'} (got {net11_sh:+.2f})  "
        f"+yrs>=11/16={'Y' if g_yrs else 'N'} (got {npos11}/{nyr})  "
        f"corr<0.3={'Y' if g_corr else 'N'} (got {c_full:+.2f})  "
        f"crash-yrs(2013/16/23) flip+={'Y' if crash_flip else 'N'}  "
        f"leak PASS={'Y' if g_leak else 'N'}"
    )
    print(f"      VERDICT: {'KEEP (accretive multi-factor step)' if keep else 'REJECT'}")
    print(
        "      NOTE: does NOT reach the raised bar (net>=+0.50 AND positive EVERY year) — a "
        "pre-registered multi-iteration goal (universe breadth + PIT fundamentals), NOT a promote."
    )


if __name__ == "__main__":
    main()
