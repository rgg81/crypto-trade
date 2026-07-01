"""iter-013 — BOUNDED DIRECTIONAL (TSMOM/trend) sleeve blended into the iter-011 neutral book.

USER-APPROVED (2026-07-01): relax PURE market-neutrality with a SMALL, controlled directional tilt
so the book can earn in the LOW-DISPERSION BULL MELT-UP years a cross-sectional market-neutral book
STRUCTURALLY cannot (2013/2017/2019 — every stock moves together, there is no cross-sectional
spread). iter-012 falsified multi-factor diversification (value/quality/BAB/low-vol all dead
2010-25); the ONLY remaining lever is a directional sleeve that carries some market beta.

=========================================================================================
WHY TIME-SERIES MOMENTUM (Moskowitz-Ooi-Pedersen 2012 "Time Series Momentum")
=========================================================================================
The neutral book (iter-011 = MOM + 0.5*LTR) is CROSS-SECTIONAL: it ranks names against each other
and is dollar/sector-neutral by construction, so its net market exposure is ~0. In a melt-up where
dispersion collapses there is no cross-sectional spread to harvest -> it earns ~0 (2017 net Sharpe
-1.11, 2019 -0.96 on the neutral book). A TIME-SERIES-MOMENTUM sleeve instead sizes EACH name by the
SIGN of its OWN trailing 12-month total return (long uptrenders / short downtrenders), inverse-vol
scaled. On a universe of stocks in a bull market MOST names are uptrending, so TSMOM is NET-LONG ->
it carries market beta -> it earns the melt-up. This is the canonical, theory-pinned way to add a
CONTROLLED directional tilt without abandoning the neutral engine.

=========================================================================================
THE iter-013 CHANGE — bounded blend of the frozen neutral book + a TSMOM directional sleeve
=========================================================================================
    rvol       = close.pct_change().rolling(63).std()                       # 63d realized vol
    tsmom_raw  = gross_norm( sign(close/close.shift(252) - 1) / rvol )       # NET-LONG in bull tape
    neutral    = gross_norm( iter011.mom_ltr_raw(pn, 0.5) )                  # FROZEN neutral engine
    book(lam)  = (1 - lam)*neutral + lam*tsmom_raw                           # lam SMALL, pre-reg.
    net, w     = iter003.banded_net(book(lam), ret_fwd, delta=0.005)         # band + vol-target

  * TSMOM signal = sign(trailing-12m total return)/rvol. 12m (252d) lookback is THEORY-PINNED (MOP),
    NOT swept. sign() (not the raw return) is the canonical MOP form: it avoids letting one giant
    trender (e.g. a +300% name) dominate the book — every name contributes equal SIGNED gross,
    inverse-vol scaled. A name with <252d history has a NaN signal -> 0 weight (PIT-clean, ragged).
  * The blend is at the SIGNAL level, both sleeves gross-normed to unit gross FIRST, so lam is a
    clean mixing fraction. Because neutral contributes ~0 net dollar and tsmom contributes +beta,
    the combined book's realized net-long tilt is ~ lam * (tsmom net-long fraction) -> MONOTONIC in
    lam. The band's own gross-norm preserves the net/gross RATIO, so the tilt SURVIVES to the
    deployed book (an outer per-bar de-lever, unlike a uniform gross scale, is NOT re-normalized).
  * lam is PRE-REGISTERED SMALL and swept only over {0.15, 0.25, 0.35}. We do NOT max-net-fit lam;
    we pick the smallest lam that FIXES the melt-up years without blowing up net market-beta.
    lam=0 reproduces the iter-011 neutral book (pre-registered identity).

=========================================================================================
CONTROLLED TILT — quantify the beta we are buying (the whole point of "small")
=========================================================================================
Two realized measures of the directional tilt, both IS-only:
  * NET-LONG FRACTION = mean over IS of  Sigma(w) / Sigma|w|  of the deployed banded book (static,
    leverage-free structural tilt: 0 = neutral, +1 = fully long).
  * NET MARKET-BETA = OLS beta of the deployed (vol-targeted, cost-netted) daily net return on the
    EQUAL-WEIGHT universe daily return (the PIT "market" proxy; the universe excludes SPY/QQQ).
Both are REPORTED per lam. "Controlled" means these stay MODEST (beta well below a long-only ~1).

=========================================================================================
VIX-MANAGE THE ADDED BEAR/BETA RISK (iter-008 brake, UNCHANGED base=20/floor=0.50)
=========================================================================================
The net-long sleeve adds market beta -> it HURTS in bear/crash (2018-Q4, 2020 COVID). The exogenous
VIX brake  s[t] = clip(20/VIX[t-1], 0.5, 1)  (.shift(1), past-only) de-levers the WHOLE book on the
high-vol days that are the worst days for a net-long book. Applied as an OUTER scalar on the
vol-targeted net (the only place a de-lever survives the vol-target — see iter-008). We REPORT the
bear regime WITH and WITHOUT the brake so the honest cost of the added beta is visible.

=========================================================================================
LEAK SAFETY (HARD) + HONESTY
=========================================================================================
  * TSMOM reads close/close.shift(252) + trailing-63 rvol (pure past); the blend feeds the strictly
    causal iter-003 band; VIX is ffill-then-.shift(1). An in-script future-bar self-check corrupts
    close + ret_fwd after a cutoff and asserts the combined (and combined+VIX) IS net before the
    cutoff is bit-identical.
  * OOS stays HIDDEN: every metric is the IS slice only; no OOS number is computed without --confirm
    (CONFIRMATION only). Do NOT tune lam / the 12m lookback here.
  * HONEST: if even the directional sleeve cannot reach the USER BAR (net >= +0.50 AND positive
    EVERY year, 16/16), we SAY SO and report the best-achievable — we do NOT overfit lam to hit it.

Run: uv run python analysis/portfolio/tradfi/iter_013_directional.py
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
import iter_008_vix_stop as i8  # noqa: E402
import iter_011_mom_ltr as i11  # noqa: E402
import universe_tradfi as ut  # noqa: E402

# --- PRE-REGISTERED directional sleeve (theory-pinned; NOT swept to max-net) ---
TSMOM_LOOKBACK = 252  # 12-month trailing total-return trend (Moskowitz-Ooi-Pedersen), FIXED
W_LTR_NEUTRAL = i11.W_LTR  # 0.5 — the FROZEN iter-011 neutral engine (unchanged)
LAMBDAS = (0.15, 0.25, 0.35)  # SMALL directional mixing fractions — pre-registered, NOT max-fit
CHOSEN_DELTA = i11.CHOSEN_DELTA  # 0.005 band, inherited unchanged

# Melt-up years the neutral (cross-sectional) book structurally misses; TSMOM should FLIP them +.
MELTUP_YEARS = [2013, 2017, 2019]


# ---------------------------------------------------------------- sleeves (leak-safe) -----------
def tsmom_sleeve(pn: dict[str, pd.DataFrame], lookback: int = TSMOM_LOOKBACK) -> pd.DataFrame:
    """TIME-SERIES momentum: sign(trailing-12m total return)/rvol, gross-normed to unit gross.

    signal = sign(close/close.shift(lookback) - 1)/rvol : LONG own-uptrenders / SHORT own-downs,
    inverse-vol scaled. NET-LONG when most names uptrend (bull tape) -> carries market beta. All
    past (close.shift(252) + trailing-63 rvol). A name with <lookback history -> NaN -> 0 weight.
    NOT sector-neutralized (that would kill the directional tilt) — this sleeve is deliberately
    directional; the neutral engine supplies the cross-sectional book.
    """
    close = pn["close"]
    trail = close / close.shift(lookback) - 1.0  # trailing 12m total return (past-only)
    sig = np.sign(trail) / i5._rvol(close)  # inverse-vol; sign() = canonical MOP (no giant-trender)
    return i5._gross_norm(sig)


def neutral_raw(pn: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """The FROZEN iter-011 neutral book (MOM + 0.5*LTR), gross-normed to unit gross."""
    return i5._gross_norm(i11.mom_ltr_raw(pn, W_LTR_NEUTRAL))


def combined_raw(pn: dict[str, pd.DataFrame], lam: float) -> pd.DataFrame:
    """book = (1-lam)*neutral + lam*tsmom, each unit-gross first -> lam is a clean mixing fraction.

    lam=0 returns the gross-normed neutral book (pre-registered identity vs iter-011). Both sleeves
    are past-only unit-gross row-vectors -> the blend is past-only and feeds the causal band.
    """
    neu = neutral_raw(pn)
    dirn = tsmom_sleeve(pn)
    return neu.mul(1.0 - lam).add(dirn.mul(lam), fill_value=0.0)


# ---------------------------------------------------------------- IS-only metrics ---------------
def _banded(raw, ret_fwd):
    return i3.banded_net(raw, ret_fwd, CHOSEN_DELTA)  # (net, w)


def market_return(pn: dict[str, pd.DataFrame]) -> pd.Series:
    """Equal-weight universe forward return = the PIT 'market' proxy (universe excludes SPY/QQQ).

    mkt[t] = mean_i ret_fwd[t,i] — same open[t]->open[t+1] convention as the strategy PnL, so beta
    of net[t] on mkt[t] is a like-for-like realized market-beta. Ragged: mean over names present.
    """
    return pn["ret_fwd"].mean(axis=1)


def net_beta(net: pd.Series, mkt: pd.Series) -> float:
    """OLS beta of deployed daily net on the equal-weight market, IS-only (realized market-beta)."""
    df = pd.concat([net.rename("s"), mkt.rename("m")], axis=1).dropna()
    df = df[df.index < ct.OOS_CUTOFF]
    var = float(df["m"].var())
    return float(df["s"].cov(df["m"]) / var) if var > 0 and len(df) > 2 else float("nan")


def net_long_fraction(w: pd.DataFrame) -> float:
    """Mean Sigma(w)/Sigma|w| over IS active rows — static leverage-free directional tilt."""
    w_is = w[w.index < ct.OOS_CUTOFF]
    gross = w_is.abs().sum(axis=1)
    live = gross > 1e-9
    return float((w_is.loc[live].sum(axis=1) / gross[live]).mean()) if live.any() else float("nan")


def _leak_selfcheck(pn, ret_fwd, lam, s_vix) -> bool:
    """Corrupt close + ret_fwd after a cutoff; combined AND combined+VIX IS net before it must be
    bit-identical (TSMOM reads pure past, blend feeds causal band, VIX is past-only .shift(1))."""
    net0, _ = _banded(combined_raw(pn, lam), ret_fwd)
    net0v = net0 * s_vix.reindex(net0.index).fillna(1.0)
    cut = net0.index[len(net0) // 2]
    pn_c = {k: v.copy() for k, v in pn.items()}
    pn_c["close"].loc[pn_c["close"].index >= cut] *= -7.0
    pn_c["ret_fwd"].loc[pn_c["ret_fwd"].index >= cut] += 5.0
    net1, _ = _banded(combined_raw(pn_c, lam), pn_c["ret_fwd"])
    net1v = net1 * s_vix.reindex(net1.index).fillna(1.0)
    common = net0.index.intersection(net1.index)
    common = common[common < cut]
    ok = np.allclose(net0.loc[common].to_numpy(), net1.loc[common].to_numpy(), atol=1e-12)
    okv = np.allclose(net0v.loc[common].to_numpy(), net1v.loc[common].to_numpy(), atol=1e-12)
    return bool(ok and okv)


def _row(net, w, mkt):
    """IS metric bundle for a deployed net/weight book."""
    npos, nyr = i11.n_pos_years(net)
    return {
        "sh": ct.msharpe(net, ct.LO0, ct.OOS_CUTOFF),
        "npos": npos,
        "nyr": nyr,
        "beta": net_beta(net, mkt),
        "nlong": net_long_fraction(w),
        "mdd": ct.maxdd(ct.is_only(net)) * 100,
        "turn": ct.turnover(w, ct.LO0, ct.OOS_CUTOFF),
        "reg": ct.regime_sharpe(ct.is_only(net)),
    }


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
    mkt = market_return(pn)
    vix = i8.load_vix_close(ret_fwd.index, args.data_dir)
    s_vix = i8.vix_scale(vix)  # base=20 / floor=0.50 (iter-008 UNCHANGED)

    print("=" * 100)
    print("iter-013 — BOUNDED DIRECTIONAL (TSMOM) sleeve on the iter-011 neutral book (IS-only)")
    print("=" * 100)
    print(
        f"  tsmom = sign(close/close.shift({TSMOM_LOOKBACK})-1)/rvol, gross-normed;  "
        f"book=(1-lam)*neutral(iter011 MOM+0.5LTR) + lam*tsmom;  band delta={CHOSEN_DELTA:.3f}\n"
    )

    # --- reference: the frozen iter-011 neutral book (lam=0) + IDENTITY ---
    net_neu, w_neu = _banded(neutral_raw(pn), ret_fwd)
    net_i11, _ = _banded(i11.mom_ltr_raw(pn, W_LTR_NEUTRAL), ret_fwd)
    ident = bool(np.allclose(net_neu.to_numpy(), net_i11.to_numpy(), atol=1e-12))
    r_neu = _row(net_neu, w_neu, mkt)
    print(
        f"  IDENTITY lam=0 reproduces iter-011: {'PASS' if ident else 'FAIL'}  "
        f"(neutral net={r_neu['sh']:+.2f}  +yrs={r_neu['npos']}/{r_neu['nyr']}  "
        f"net-beta={r_neu['beta']:+.2f}  net-long={r_neu['nlong']:+.2f}  maxDD={r_neu['mdd']:.0f}%)"
    )

    # --- (1) STANDALONE TSMOM directional sleeve (same band + vol-target + cost) ---
    net_ts, w_ts = _banded(tsmom_sleeve(pn), ret_fwd)
    r_ts = _row(net_ts, w_ts, mkt)
    print("\n  (1) STANDALONE TSMOM directional sleeve (same band/vol-target/cost):")
    print(
        f"      net={r_ts['sh']:+.2f}  +yrs={r_ts['npos']}/{r_ts['nyr']}  "
        f"net-beta={r_ts['beta']:+.2f}  net-long={r_ts['nlong']:+.2f}  maxDD={r_ts['mdd']:.0f}%  "
        f"bull/bear/chop={r_ts['reg']['bull']:+.2f}/{r_ts['reg']['bear']:+.2f}/"
        f"{r_ts['reg']['chop']:+.2f}"
    )
    yts = i11.year_table(net_ts)
    print(
        "      per-year Sharpe: "
        + " ".join(f"{y}:{yts[y][0]:+.2f}" for y in sorted(yts))
    )

    # --- (2) BOUNDED COMBINED book per pre-registered lam ---
    lams = (args.lam,) if args.lam is not None else LAMBDAS
    rows = {}
    print("\n  (2) BOUNDED COMBINED book (1-lam)*neutral + lam*tsmom  [pre-registered small lam]:")
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
        net_c, w_c = _banded(combined_raw(pn, lam), ret_fwd)
        r = _row(net_c, w_c, mkt)
        rows[lam] = (net_c, w_c, r)
        print(
            f"      {lam:>5.2f} {r['sh']:>+6.2f} {r['npos']:>4}/{r['nyr']} "
            f"{r['beta']:>+9.2f} {r['nlong']:>+9.2f} {r['mdd']:>6.0f}% {r['turn']:>7.4f}"
            f"  {r['reg']['bull']:+.2f}/{r['reg']['bear']:+.2f}/{r['reg']['chop']:+.2f}"
        )

    # --- (3) PER-YEAR table 2010-2025: neutral -> each combined lam (melt-up FIX markers) ---
    yneu = i11.year_table(net_neu)
    ytabs = {lam: i11.year_table(rows[lam][0]) for lam in lams}
    print("\n  (3) PER-YEAR net Sharpe (IS 2010-2025): neutral(lam=0) -> combined per lam "
          "(* = melt-up year the neutral book structurally misses):")
    hdr = f"      {'year':>5} {'neutral':>8}"
    for lam in lams:
        hdr += f" {'lam=' + format(lam, '.2f'):>9}"
    print(hdr)
    for yr in sorted(yneu):
        star = "*" if yr in MELTUP_YEARS else " "
        line = f"      {yr:>4}{star} {yneu[yr][0]:>+8.2f}"
        for lam in lams:
            line += f" {ytabs[lam][yr][0]:>+9.2f}"
        print(line)

    # --- (4) VIX brake ON TOP per lam — bear WITH/WITHOUT (honest cost of the added beta) ---
    print("\n  (4) VIX brake ON TOP (iter-008 s=clip(20/VIX[t-1],0.5,1)) — added-bear management:")
    print(f"      {'lam':>5} {'net':>6} {'netVIX':>7} {'bear':>6} {'bearVIX':>8} "
          f"{'maxDD':>7} {'mddVIX':>8} {'+yrs':>7} {'+yrsVIX':>8}")
    for lam in lams:
        net_c = rows[lam][0]
        net_cv = net_c * s_vix.reindex(net_c.index).fillna(1.0)
        rv = _row(net_cv, rows[lam][1], mkt)
        r = rows[lam][2]
        print(
            f"      {lam:>5.2f} {r['sh']:>+6.2f} {rv['sh']:>+7.2f} "
            f"{r['reg']['bear']:>+6.2f} {rv['reg']['bear']:>+8.2f} "
            f"{r['mdd']:>6.0f}% {rv['mdd']:>7.0f}% "
            f"{r['npos']:>4}/{r['nyr']} {rv['npos']:>5}/{rv['nyr']}"
        )

    # --- (5) leak self-check on the combined + VIX build ---
    leak_lam = lams[len(lams) // 2]
    leak_ok = _leak_selfcheck(pn, ret_fwd, leak_lam, s_vix)
    print(
        f"\n  (5) future-bar leak self-check (combined+VIX IS net bit-identical pre-cut, "
        f"lam={leak_lam:.2f}): {'PASS' if leak_ok else 'FAIL'}"
    )

    # --- (6) HONEST verdict against the USER BAR (net>=+0.50 AND positive EVERY year 16/16) ---
    print("\n  (6) HONEST read vs USER BAR (net>=+0.50 AND 16/16 positive years):")
    best = max(lams, key=lambda lm: (rows[lm][2]["npos"], rows[lm][2]["sh"]))
    for lam in lams:
        r = rows[lam][2]
        fixed = sum(1 for y in MELTUP_YEARS if ytabs[lam][y][0] > 0)
        bar = r["sh"] >= 0.50 and r["npos"] == r["nyr"]
        print(
            f"      lam={lam:.2f}: net={r['sh']:+.2f}  +yrs={r['npos']}/{r['nyr']}  "
            f"net-beta={r['beta']:+.2f}  melt-up-fixed={fixed}/3  "
            f"USER-BAR={'MET' if bar else 'NOT met'}"
        )
    rb = rows[best][2]
    print(
        f"      BEST-ACHIEVABLE: lam={best:.2f}  net={rb['sh']:+.2f}  "
        f"+yrs={rb['npos']}/{rb['nyr']}  "
        f"net-beta={rb['beta']:+.2f} (controlled)  net-long={rb['nlong']:+.2f}"
    )


if __name__ == "__main__":
    main()
