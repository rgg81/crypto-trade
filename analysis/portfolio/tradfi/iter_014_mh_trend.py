"""iter-014 — MULTI-HORIZON TSMOM: replace the single-12m trend sleeve with a {3m,6m,12m} blend.

ONE change vs iter-013: the directional sleeve is no longer a single 12-month time-series-momentum
signal — it is an EQUAL-WEIGHT blend of THREE trend speeds {3m, 6m, 12m}, each `sign(own trailing-h
return)/rvol`, gross-normed to unit gross FIRST, then averaged. Everything else is IDENTICAL to
iter-013: the same lam=0.25 combine with the frozen [mom + 0.5*LTR] neutral book, the same
iter-003 band (delta=0.005), the same iter-008 VIX brake, the same OOS-hidden accounting.

=========================================================================================
WHY MULTI-HORIZON TREND (the SAME generalization that helped the cross-sectional book at iter-005)
=========================================================================================
iter-013 (lam=0.25) is net +0.63 / 13-of-16 years, but MISSES three years:
  * 2010 — WARM-UP: the LTR neutral sleeve needs 3y of history (thin pre-2013); the book is barely
    populated. Structural, not a trend problem.
  * 2018 — Q4 Fed-tightening bear: the net-long TSMOM tilt CARRIES market beta and pays for it in a
    net-long bear. Structural cost of the directional tilt (the VIX brake only partly tames it).
  * 2019 — TSMOM WHIPSAW: after the 2018-Q4 V-bottom the SINGLE 12-month trend was STILL SHORT
    (its trailing-12m return was negative deep into 2019), so the sleeve sat under-invested / short
    through the melt-up recovery and could not lift the low-dispersion year the neutral book misses.

A single trend speed is a single bet on ONE persistence timescale, and after a sharp V-bottom the
12m trend is the SLOWEST to flip back long. A FASTER-reacting composite — the 3m and 6m trailing
returns flip positive within a quarter or two of the 2018-12-24 trough — re-enters LONG SOONER, so
the multi-horizon sleeve should catch more of the 2019 melt-up. This is EXACTLY the multi-horizon
generalization that improved the cross-sectional book at iter-005 (single 12-1m momentum ->
EQUAL-WEIGHT {3-1,6-1,12-1} blend): decorrelated speeds of the SAME edge, breadth over a single
timescale bet. It is THEORY-GROUNDED and PRE-REGISTERED — NOT a 2019-specific hack: the horizons
{63,126,252}=iter-005's HORIZONS_MH are copied verbatim, NOT hand-picked to flip 2019, lam is NOT
re-tuned (stays 0.25), and no 2019-specific rule is added. If the blend does not fix 2019/2018 we
SAY SO — 2018 (net-long bear) may be structurally unfixable and 2010 is warm-up.

=========================================================================================
THE iter-014 CHANGE — multi-horizon TSMOM sleeve (leak-safe), everything else frozen
=========================================================================================
    rvol        = close.pct_change().rolling(63).std()                    # 63d realized vol (past)
    sleeve(h)   = gross_norm( sign(close/close.shift(h) - 1) / rvol )     # 1 speed, unit-gross
    mh_tsmom    = ( sleeve(63) + sleeve(126) + sleeve(252) ) / 3          # EW blend {3m,6m,12m}
    neutral     = gross_norm( iter011 MOM + 0.5*LTR )                     # FROZEN neutral engine
    book(lam)   = (1-lam)*neutral + lam*mh_tsmom                          # lam=0.25 UNCHANGED
    net, w      = iter003.banded_net(book(lam), ret_fwd, delta=0.005)     # band + vol-target frozen

  * Each sleeve is sign(trailing-h total return)/rvol — canonical MOP form (sign, not raw return, so
    no giant-trender dominates), inverse-vol scaled, gross-normed. NOT sector-neutralized (the tilt
    is deliberately directional). A name with <h days of history -> NaN -> 0 weight (PIT/ragged).
  * The blend is at the SIGNAL level, each speed unit-gross FIRST, so the three contribute equally
    and the composite is unit-gross. EQUAL-WEIGHT is pre-registered (mirrors iter-005 — NOT
    risk-parity, which over-weights the weak sleeve). Same {63,126,252} as iter-005.
  * lam stays 0.25 (iter-013's pre-registered chosen fraction). The full pre-registered LAMBDAS grid
    {0.15,0.25,0.35} is reported for robustness ONLY (as iter-013 did) — 0.25 is THE headline.

=========================================================================================
PRE-REGISTERED IDENTITY (anchors iter-014 as a pure one-change delta off iter-013)
=========================================================================================
A degenerate one-speed blend mh_tsmom(horizons=(252,)) == iter-013's single-12m tsmom_sleeve
bit-for-bit (averaging one gross-normed sleeve is the identity), so combined_raw(...,(252,))
reproduces the iter-013 combined book -> banded net is allclose(1e-12) to iter-013 at every lam.

=========================================================================================
LEAK SAFETY (HARD) + HONESTY
=========================================================================================
  * Every sleeve reads close/close.shift(h) (h in {63,126,252}, pure past) + trailing-63 rvol; the
    blend is a row-wise linear combination of past-only unit-gross sleeves; it feeds the strictly
    causal iter-003 band; the VIX brake is ffill-then-.shift(1). An in-script future-bar self-check
    corrupts close + ret_fwd after a cutoff and asserts the combined (and combined+VIX) IS net
    before the cutoff is bit-identical.
  * OOS stays HIDDEN: every metric is the IS slice only; no OOS number is computed without --confirm
    (CONFIRMATION only). Do NOT tune the horizons / lam / band here.

Run: uv run python analysis/portfolio/tradfi/iter_014_mh_trend.py
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
import iter_005_multihorizon as i5  # noqa: E402
import iter_008_vix_stop as i8  # noqa: E402
import iter_011_mom_ltr as i11  # noqa: E402
import iter_013_directional as i13  # noqa: E402
import universe_tradfi as ut  # noqa: E402

# --- PRE-REGISTERED multi-horizon trend sleeve (theory-pinned; mirrors iter-005; NOT swept) ---
MH_TREND_HORIZONS = i5.HORIZONS_MH  # (63, 126, 252) = 3m / 6m / 12m — copied verbatim from iter-005
CHOSEN_LAM = 0.25  # iter-013's pre-registered chosen fraction — UNCHANGED (NOT re-tuned)
LAMBDAS = i13.LAMBDAS  # (0.15, 0.25, 0.35) — pre-registered robustness grid (report only)
CHOSEN_DELTA = i13.CHOSEN_DELTA  # 0.005 band, inherited unchanged

MELTUP_YEARS = i13.MELTUP_YEARS  # [2013, 2017, 2019] — the melt-up years the neutral book misses
WARMUP_YEAR = 2010  # LTR needs 3y history (thin pre-2013) -> structural warm-up, not a trend miss
BEAR_YEAR = 2018  # 2018-Q4 net-long bear -> structural cost of the directional tilt


# ---------------------------------------------------------------- sleeves (leak-safe) -----------
def mh_tsmom_sleeve(
    pn: dict[str, pd.DataFrame], horizons: tuple[int, ...] = MH_TREND_HORIZONS
) -> pd.DataFrame:
    """EQUAL-WEIGHT multi-horizon TSMOM: mean_h gross_norm(sign(close/close.shift(h)-1)/rvol).

    Each trend speed = sign(trailing-h total return)/rvol (canonical MOP: sign, inverse-vol scaled),
    gross-normed to unit gross FIRST so no speed dominates, then equal-weight averaged. All past
    (close.shift(h) for h in {63,126,252} + trailing-63 rvol). A name with <h history -> NaN -> 0
    weight after gross_norm. NOT sector-neutralized (deliberately directional). horizons=(252,)
    reproduces iter-013's single-12m tsmom_sleeve (pre-registered identity).
    """
    close = pn["close"]
    rvol = i5._rvol(close)
    sleeves = []
    for h in horizons:
        sig = (
            np.sign(close / close.shift(h) - 1.0) / rvol
        )  # one trend speed, inverse-vol, past-only
        sleeves.append(i5._gross_norm(sig))
    acc = sleeves[0].copy()
    for s in sleeves[1:]:
        acc = acc.add(s, fill_value=0.0)
    return acc / len(sleeves)


def combined_raw(pn: dict[str, pd.DataFrame], lam: float) -> pd.DataFrame:
    """book = (1-lam)*neutral + lam*mh_tsmom, each unit-gross first -> lam a clean mixing fraction.

    Only ONE change vs iter-013.combined_raw: the directional sleeve is the multi-horizon blend
    instead of the single-12m sleeve. lam=0 returns the gross-normed neutral book (iter-011 ident).
    """
    neu = i13.neutral_raw(pn)
    dirn = mh_tsmom_sleeve(pn)
    return neu.mul(1.0 - lam).add(dirn.mul(lam), fill_value=0.0)


# ---------------------------------------------------------------- leak self-check ---------------
def _leak_selfcheck(pn, ret_fwd, lam, s_vix) -> bool:
    """Corrupt close + ret_fwd after a cutoff; combined AND combined+VIX IS net before it must be
    bit-identical (each trend speed reads pure past, blend feeds causal band, VIX .shift(1))."""
    net0, _ = i13._banded(combined_raw(pn, lam), ret_fwd)
    net0v = net0 * s_vix.reindex(net0.index).fillna(1.0)
    cut = net0.index[len(net0) // 2]
    pn_c = {k: v.copy() for k, v in pn.items()}
    pn_c["close"].loc[pn_c["close"].index >= cut] *= -7.0
    pn_c["ret_fwd"].loc[pn_c["ret_fwd"].index >= cut] += 5.0
    net1, _ = i13._banded(combined_raw(pn_c, lam), pn_c["ret_fwd"])
    net1v = net1 * s_vix.reindex(net1.index).fillna(1.0)
    common = net0.index.intersection(net1.index)
    common = common[common < cut]
    ok = np.allclose(net0.loc[common].to_numpy(), net1.loc[common].to_numpy(), atol=1e-12)
    okv = np.allclose(net0v.loc[common].to_numpy(), net1v.loc[common].to_numpy(), atol=1e-12)
    return bool(ok and okv)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lam", type=float, default=None, help="single directional fraction to detail")
    ap.add_argument("--confirm", action="store_true", help="reveal OOS (CONFIRMATION only)")
    ap.add_argument("--data-dir", default=None)
    args = ap.parse_args()

    base = Path(args.data_dir) if args.data_dir else ct._ROOT / "data"
    syms = sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)
    coins = ct.load_tradfi(syms, args.data_dir)
    if not coins:
        print("No ingested tradfi data found. Run ingest_yahoo.py first.")
        return

    pn = ct.panels(coins)
    ret_fwd = pn["ret_fwd"]
    mkt = i13.market_return(pn)
    vix = i8.load_vix_close(ret_fwd.index, args.data_dir)
    s_vix = i8.vix_scale(vix)  # base=20 / floor=0.50 (iter-008 UNCHANGED)

    print("=" * 100)
    print("iter-014 — MULTI-HORIZON TSMOM {3m,6m,12m} sleeve on the neutral book (IS-only)")
    print("=" * 100)
    print(
        f"  mh_tsmom = mean_h gross_norm(sign(close/close.shift(h)-1)/rvol), h={MH_TREND_HORIZONS}"
        f"\n  book=(1-lam)*neutral(MOM+0.5LTR) + lam*mh_tsmom;  band delta={CHOSEN_DELTA:.3f}\n"
    )

    # --- reference: the frozen iter-011 neutral book (lam=0) ---
    net_neu, w_neu = i13._banded(i13.neutral_raw(pn), ret_fwd)
    r_neu = i13._row(net_neu, w_neu, mkt)

    # --- IDENTITY: one-speed blend (252,) reproduces iter-013's single-12m sleeve/combined book ---
    mh_one = mh_tsmom_sleeve(pn, (252,))
    ts_i13 = i13.tsmom_sleeve(pn)
    ident_sleeve = bool(
        np.allclose(mh_one.fillna(0).to_numpy(), ts_i13.fillna(0).to_numpy(), atol=1e-12)
    )
    # combined identity at chosen lam using the degenerate one-speed blend:
    neu = i13.neutral_raw(pn)
    comb_one = neu.mul(1 - CHOSEN_LAM).add(mh_one.mul(CHOSEN_LAM), fill_value=0.0)
    comb_i13 = neu.mul(1 - CHOSEN_LAM).add(ts_i13.mul(CHOSEN_LAM), fill_value=0.0)
    net_one, _ = i13._banded(comb_one, ret_fwd)
    net_i13c, _ = i13._banded(comb_i13, ret_fwd)
    ident_comb = bool(np.allclose(net_one.to_numpy(), net_i13c.to_numpy(), atol=1e-12))
    print(
        f"  IDENTITY one-speed blend (252,) == iter-013 single-12m sleeve: "
        f"{'PASS' if ident_sleeve else 'FAIL'};  combined @lam={CHOSEN_LAM} == iter-013 combined: "
        f"{'PASS' if ident_comb else 'FAIL'}"
    )
    print(
        f"  reference iter-011 neutral (lam=0): net={r_neu['sh']:+.2f}  "
        f"+yrs={r_neu['npos']}/{r_neu['nyr']}  beta={r_neu['beta']:+.2f}  maxDD={r_neu['mdd']:.0f}%"
    )

    # --- (1) STANDALONE multi-horizon TSMOM sleeve vs iter-013's single-12m sleeve ---
    net_mh, w_mh = i13._banded(mh_tsmom_sleeve(pn), ret_fwd)
    r_mh = i13._row(net_mh, w_mh, mkt)
    net_ts, w_ts = i13._banded(ts_i13, ret_fwd)
    r_ts = i13._row(net_ts, w_ts, mkt)
    ymh = i11.year_table(net_mh)
    yts = i11.year_table(net_ts)
    print("\n  (1) STANDALONE directional sleeve (same band/vol-target/cost) — MH vs single-12m:")
    print(
        f"      single-12m (iter-013): net={r_ts['sh']:+.2f}  +yrs={r_ts['npos']}/{r_ts['nyr']}  "
        f"net-beta={r_ts['beta']:+.2f}  net-long={r_ts['nlong']:+.2f}  maxDD={r_ts['mdd']:.0f}%  "
        f"2019={yts[2019][0]:+.2f}  2018={yts[2018][0]:+.2f}"
    )
    print(
        f"      MH{{3,6,12}}m (iter-014): net={r_mh['sh']:+.2f}  +yrs={r_mh['npos']}/{r_mh['nyr']} "
        f"beta={r_mh['beta']:+.2f}  net-long={r_mh['nlong']:+.2f}  maxDD={r_mh['mdd']:.0f}%  "
        f"2019={ymh[2019][0]:+.2f}  2018={ymh[2018][0]:+.2f}"
    )
    print(
        f"      MH regimes(IS): bull={r_mh['reg']['bull']:+.2f} bear={r_mh['reg']['bear']:+.2f} "
        f"chop={r_mh['reg']['chop']:+.2f}   per-year Sharpe:"
    )
    print("      " + " ".join(f"{y}:{ymh[y][0]:+.2f}" for y in sorted(ymh)))

    # --- (2) BOUNDED COMBINED book per pre-registered lam (0.25 = CHOSEN, headline) ---
    lams = (args.lam,) if args.lam is not None else LAMBDAS
    rows = {}
    print(
        "\n  (2) BOUNDED COMBINED (1-lam)*neutral + lam*mh_tsmom  [lam=0.25 CHOSEN; grid=robust]:"
    )
    print(
        f"      {'lam':>5} {'net':>6} {'+yrs':>7} {'net-beta':>9} {'net-long':>9} {'maxDD':>7} "
        f"{'turn':>7}  bull/bear/chop"
    )
    print(
        f"      {0.0:>5.2f} {r_neu['sh']:>+6.2f} {r_neu['npos']:>4}/{r_neu['nyr']} "
        f"{r_neu['beta']:>+9.2f} {r_neu['nlong']:>+9.2f} {r_neu['mdd']:>6.0f}% "
        f"{r_neu['turn']:>7.4f}"
        f"  {r_neu['reg']['bull']:+.2f}/{r_neu['reg']['bear']:+.2f}/{r_neu['reg']['chop']:+.2f}"
        f"   <- iter-011 neutral"
    )
    for lam in lams:
        net_c, w_c = i13._banded(combined_raw(pn, lam), ret_fwd)
        r = i13._row(net_c, w_c, mkt)
        rows[lam] = (net_c, w_c, r)
        tag = "  <- CHOSEN (=iter-013 lam)" if abs(lam - CHOSEN_LAM) < 1e-9 else ""
        print(
            f"      {lam:>5.2f} {r['sh']:>+6.2f} {r['npos']:>4}/{r['nyr']} "
            f"{r['beta']:>+9.2f} {r['nlong']:>+9.2f} {r['mdd']:>6.0f}% {r['turn']:>7.4f}"
            f"  {r['reg']['bull']:+.2f}/{r['reg']['bear']:+.2f}/{r['reg']['chop']:+.2f}{tag}"
        )

    # --- (3) PER-YEAR: iter-013 (single-12m) vs iter-014 (MH) at CHOSEN lam=0.25 (FIX markers) ---
    net13_chosen, _ = i13._banded(i13.combined_raw(pn, CHOSEN_LAM), ret_fwd)
    y13 = i11.year_table(net13_chosen)
    y14 = (
        i11.year_table(rows[CHOSEN_LAM][0])
        if CHOSEN_LAM in rows
        else i11.year_table(i13._banded(combined_raw(pn, CHOSEN_LAM), ret_fwd)[0])
    )
    print(
        f"\n  (3) PER-YEAR net Sharpe @lam={CHOSEN_LAM} (IS 2010-2025): "
        f"iter-013 single-12m -> iter-014 MH  (* melt-up / W warm-up / B bear):"
    )
    print(f"      {'year':>5} {'iter-013':>9} {'iter-014':>9} {'delta':>7}  note")
    for yr in sorted(y14):
        tag = (
            "*"
            if yr in MELTUP_YEARS
            else ("W" if yr == WARMUP_YEAR else ("B" if yr == BEAR_YEAR else " "))
        )
        s13 = y13[yr][0]
        s14 = y14[yr][0]
        note = ""
        if s13 <= 0 < s14:
            note = "FIXED (flipped +)"
        elif s13 <= 0 and s14 <= 0:
            note = "still-neg"
        print(f"      {yr:>4}{tag} {s13:>+9.2f} {s14:>+9.2f} {s14 - s13:>+7.2f}  {note}")

    # --- (4) VIX brake ON TOP per lam — bear WITH/WITHOUT (honest cost of the added beta) ---
    print("\n  (4) VIX brake ON TOP (iter-008 s=clip(20/VIX[t-1],0.5,1)) — added-bear management:")
    print(
        f"      {'lam':>5} {'net':>6} {'netVIX':>7} {'bear':>6} {'bearVIX':>8} "
        f"{'maxDD':>7} {'mddVIX':>8} {'+yrs':>7} {'+yrsVIX':>8}"
    )
    for lam in lams:
        net_c = rows[lam][0]
        net_cv = net_c * s_vix.reindex(net_c.index).fillna(1.0)
        rv = i13._row(net_cv, rows[lam][1], mkt)
        r = rows[lam][2]
        print(
            f"      {lam:>5.2f} {r['sh']:>+6.2f} {rv['sh']:>+7.2f} "
            f"{r['reg']['bear']:>+6.2f} {rv['reg']['bear']:>+8.2f} "
            f"{r['mdd']:>6.0f}% {rv['mdd']:>7.0f}% "
            f"{r['npos']:>4}/{r['nyr']} {rv['npos']:>5}/{rv['nyr']}"
        )

    # --- (5) leak self-check on the combined + VIX build ---
    leak_lam = CHOSEN_LAM if CHOSEN_LAM in lams else lams[len(lams) // 2]
    leak_ok = _leak_selfcheck(pn, ret_fwd, leak_lam, s_vix)
    print(
        f"\n  (5) future-bar leak self-check (combined+VIX IS net bit-identical pre-cut, "
        f"lam={leak_lam:.2f}): {'PASS' if leak_ok else 'FAIL'}"
    )

    # --- (6) HONEST verdict vs iter-013 and the USER BAR (net>=+0.50 AND 16/16 positive years) ---
    print("\n  (6) HONEST read vs iter-013 (+0.63, 13/16) and USER BAR (net>=+0.50 AND 16/16):")
    r_chosen = (
        rows[CHOSEN_LAM][2]
        if CHOSEN_LAM in rows
        else i13._row(*i13._banded(combined_raw(pn, CHOSEN_LAM), ret_fwd), mkt)
    )
    fixed19 = y14[2019][0] > 0
    fixed18 = y14[2018][0] > 0
    neg_years = [yr for yr in sorted(y14) if y14[yr][0] <= 0]
    bar = r_chosen["sh"] >= 0.50 and r_chosen["npos"] == r_chosen["nyr"]
    print(
        f"      iter-014 @lam={CHOSEN_LAM}: net={r_chosen['sh']:+.2f}  "
        f"+yrs={r_chosen['npos']}/{r_chosen['nyr']}  net-beta={r_chosen['beta']:+.2f}  "
        f"maxDD={r_chosen['mdd']:.0f}%  (iter-013: +0.63, 13/16, beta +0.12, maxDD -32%)"
    )
    print(
        f"      2019 FIXED={'YES' if fixed19 else 'NO'} ({y13[2019][0]:+.2f}->{y14[2019][0]:+.2f}) "
        f"2018 FIXED={'YES' if fixed18 else 'NO'} ({y13[2018][0]:+.2f}->{y14[2018][0]:+.2f})  "
        f"still-negative years: {neg_years}"
    )
    print(f"      USER BAR (>=+0.50 AND 16/16): {'MET' if bar else 'NOT met'}")


if __name__ == "__main__":
    main()
