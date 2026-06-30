"""iter-008 — VIX BRAKE + DRAWDOWN STOP: two leak-safe EXPOSURE overlays on the iter-006 book.

USER DIRECTIVE (2026-07-01): fix the catastrophic BEAR of the iter-006 working best (net +0.43 /
bull +0.60 / bear -1.23 / chop +0.56 / maxDD -25.5%) WITHOUT killing the strong bull/chop. Add an
exogenous VIX brake and a stop-loss. OOS HIDDEN — IS-only calibration and evaluation.

=========================================================================================
WHY BOTH OVERLAYS ACT ON THE FINAL VOL-TARGETED NET (the load-bearing design choice)
=========================================================================================
iter-006's net is ALREADY 63d portfolio vol-targeted inside `banded_net` -> `ct.vol_target`. The
iter-006 risk note proved that ANY de-lever applied INSIDE the vol-target (a Barroso constant-vol or
a metals drawdown brake on the raw book) gets UNDONE — the vol-target simply re-levers it back to
target. The same trap kills a VIX brake applied to the raw weights: a uniform per-bar scale on the
gross-normalized book is re-normalized to unit gross and then re-vol-targeted away.

So BOTH overlays here are OUTER scalars on the vol-targeted net return series:

    net6      = iter-006 vol-targeted net (UNCHANGED — signal/gate/band/cost untouched)
    net_vix   = net6 * s_vix          (s_vix = VIX brake scalar, past-only)
    net_stop  = dd_brake(net6)        (dd_brake = causal drawdown stop, past-only)
    net_comb  = dd_brake(net6 * s_vix)  (VIX first as the exogenous outer de-lever, then the
                                          endogenous stop protects the actually-deployed book)

An outer scalar on the vol-targeted net is the ONLY place a de-lever survives — and it is exactly
the right semantics: the book runs at target vol in calm tape and BELOW target (de-risked) in
stress. Because each overlay is a per-bar scalar on the WHOLE book, the sector-/dollar-neutrality
and the unit-gross rebalance schedule (hence turnover) are untouched; only EXPOSURE moves.

=========================================================================================
1. THE VIX BRAKE (exogenous crash de-risk) — PRE-REGISTERED, theory-pinned
=========================================================================================
    s_vix_raw[t] = clip( VIX_BASE / VIX_close[t] , VIX_FLOOR , 1.0 )
    s_vix[t]     = s_vix_raw[t-1]            # .shift(1): yesterday's close (causal/conservative)

  * VIX_BASE = 20.0  — the canonical "calm vs elevated" VIX line (~ the long-run VIX median; IS
    median = 18.0). At VIX <= 20 the brake is INERT (scale clipped to 1.0). NOT IS-tuned to flip a
    window: 20 is a conventional fixed level, pre-registered before reading any net.
  * VIX_FLOOR = 0.50 — never cut the book by more than half (the floor binds only at VIX >= 40,
    ~1.9% of IS days). A round, conservative cap, NOT a max-net pick.
  * VIX is EXOGENOUS — it spiked ~82 in the COVID V-crash and stayed elevated through 2022, so it
    de-risks our two IS bears WITHOUT being fit to them. This is the canonical momentum-crash
    mitigant (Barroso-Santa-Clara use realised vol; VIX is the forward-looking exogenous analog),
    de-levering precisely on the high-vol days that are the worst momentum days (vol clustering).

  HONEST CAVEAT: we have only N=2 IS bears (COVID, 2022). The VIX level is reported as SUGGESTIVE,
  with a sensitivity table over {base, floor} — we deliberately DO NOT select the max-net cell.

=========================================================================================
2. THE STOP-LOSS — portfolio-level causal DRAWDOWN stop (metals iter-007 hysteresis)
=========================================================================================
Form choice (my judgment): a PORTFOLIO-level drawdown stop, NOT a per-name stop. A per-name stop
that zeros an individual blowing-up IPO (COIN/MSTR/RIVN) would BREAK the per-sector dollar-
neutrality the whole book is built on (the sector no longer nets to zero), needing a re-neutralize
that changes the strategy's character. A portfolio-level scalar de-lever preserves sector-/dollar-
neutrality EXACTLY and composes trivially with the VIX overlay.

    eq[t]   = running braked equity ;  dd[t] = eq[t]/peak[t] - 1      # past-only, self-referential
    scale[t] = DD_FLOOR        if dd[t-1] <= -D_TRIP        (trip: book is in a deep drawdown)
             = 1.0             if dd[t-1] >= -D_TRIP/2       (re-arm: recovered halfway back)
             = scale[t-1]      otherwise                     (hysteresis dead-band, no chatter)

  * D_TRIP = 80th-percentile of the iter-006 IS daily drawdown-depth distribution — a pre-registered
    WORST-QUINTILE RULE (the book sits deeper than D_TRIP underwater on its worst ~20% of IS days),
    NOT a max-net fit. Derived in-script from IS-only data and printed.
  * DD_FLOOR = 0.50 (floor > 0 so the de-levered book still earns and its equity can RECOVER to
    re-arm — avoids the self-lock a 0-floor stop suffers).
  * Hysteresis re-arm at -D_TRIP/2 (metals iter-007 style) prevents trip/re-arm chatter.

The iter-006 note already found a metals drawdown brake WORSENS the bear standalone (uniform
de-levering does not change a negative-mean regime's Sharpe). So the stop's job here is TAIL/maxDD
control, not bear-Sharpe — the bear fix is the VIX brake. We report all three honestly.

=========================================================================================
LEAK SAFETY (HARD rule)
=========================================================================================
  * VIX is reindexed to the trading-day grid with a PAST-ONLY ffill, then `.shift(1)` — s_vix[t]
    reads only VIX_close[<t]. No bfill, no forward read.
  * dd_brake is a forward sequential scan: scale[t] depends only on braked returns BEFORE t.
  * Both overlays multiply the iter-006 net (itself future-bar leak-safe). The combined build is
    verified by an in-script future-bar self-check (corrupt panel + VIX + forward returns after a
    cutoff -> combined IS net before the cutoff is bit-identical) and by
    test_iter008_* in tests/test_portfolio_tradfi_foundation.py.
  * IDENTITIES: VIX always <= base -> s_vix == 1 -> net_vix == net6; D_TRIP = +inf -> stop never
    trips -> net_stop == net6. Both pre-registered.

OOS stays HIDDEN: every metric is computed on the IS slice only; no OOS number is ever computed or
printed (there is no --confirm path here — this is an EXPLORATION risk probe).

Run: uv run python analysis/portfolio/tradfi/iter_008_vix_stop.py
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
import iter_006_crashbrake as i6  # noqa: E402
import universe_tradfi as ut  # noqa: E402

# --- PRE-REGISTERED VIX brake (theory-pinned; NOT max-net) ---
VIX_BASE = 20.0  # canonical calm/elevated VIX line (~ long-run median); brake inert at VIX <= 20
VIX_FLOOR = 0.50  # never cut the book below half gross (binds only at VIX >= 40)
VIX_STEP_THR = 30.0  # step-variant threshold ("high fear" line) — robustness cross-check only

# --- PRE-REGISTERED drawdown stop (worst-quintile RULE; NOT max-net) ---
DD_QUANTILE = 0.80  # D_TRIP = 80th pct of IS drawdown depth (worst-quintile rule)
DD_FLOOR = 0.50  # de-levered exposure when tripped (floor > 0 -> can recover to re-arm)


# --------------------------------------------------------------------------------------------------
# VIX brake
# --------------------------------------------------------------------------------------------------
def load_vix_close(index: pd.DatetimeIndex, data_dir: str | None = None) -> pd.Series:
    """^VIX daily close reindexed to the trading-day `index` with a PAST-ONLY ffill.

    ffill (never bfill) carries the last KNOWN VIX close across any grid gap, so the series stays
    causal. Returns NaN before VIX history starts (handled downstream as scale=1.0, no brake).
    """
    base = Path(data_dir) if data_dir else ct._ROOT / "data"
    df = pd.read_csv(base / "VIX" / "1d.csv", usecols=["open_time", "close"])
    df = df.drop_duplicates(subset="open_time", keep="last").set_index("open_time").sort_index()
    s = df["close"].astype(float)
    s.index = pd.to_datetime(s.index, unit="ms")
    return s.reindex(index).ffill()


def vix_scale(vix_close: pd.Series, base: float = VIX_BASE, floor: float = VIX_FLOOR) -> pd.Series:
    """Continuous de-lever s[t] = clip(base/VIX[t-1], floor, 1) — past-only (.shift(1)).

    Inert (==1) at VIX<=base; de-levers toward `floor` as VIX rises; floor binds at VIX>=base/floor.
    The .shift(1) uses yesterday's VIX close (causal); missing readings -> 1 (no brake applied).
    """
    s = (base / vix_close).clip(lower=floor, upper=1.0)
    return s.shift(1).fillna(1.0)


def vix_step_scale(
    vix_close: pd.Series, thr: float = VIX_STEP_THR, floor: float = VIX_FLOOR
) -> pd.Series:
    """Step de-lever: s[t] = floor if VIX[t-1] > thr else 1 — fixed-threshold robustness variant."""
    s = pd.Series(np.where(vix_close > thr, floor, 1.0), index=vix_close.index)
    return s.shift(1).fillna(1.0)


# --------------------------------------------------------------------------------------------------
# drawdown stop
# --------------------------------------------------------------------------------------------------
def dd_trip_level(net_is: pd.Series, q: float = DD_QUANTILE) -> float:
    """Worst-quintile D_TRIP: the q-th percentile of the IS daily drawdown-DEPTH distribution.

    Pre-registered RULE (q=0.80), not a max-net fit. Past-computable from realized equity only.
    """
    eq = (1.0 + net_is).cumprod()
    depth = (eq / eq.cummax() - 1.0).abs()
    return float(depth.quantile(q))


def dd_brake_scale(net: pd.Series, d_trip: float, floor: float, rearm: float) -> pd.Series:
    """Causal hysteresis drawdown stop scalar (metals iter-007 style); strictly past-only.

    scale[t] is set BEFORE bar t is applied, from the braked equity through t-1: trip to `floor`
    when drawdown <= -d_trip, re-arm to 1 when drawdown recovers >= -rearm, else HOLD (dead-band).
    floor>0 keeps the de-levered equity moving so it can recover to re-arm (no self-lock).
    """
    vals = net.to_numpy()
    out = np.empty(len(vals))
    eq, peak, scale = 1.0, 1.0, 1.0
    for i, r in enumerate(vals):
        out[i] = scale  # scale for bar i decided from drawdown through i-1 (past-only)
        eq *= 1.0 + r * scale
        peak = max(peak, eq)
        dd = eq / peak - 1.0
        if dd <= -d_trip:
            scale = floor
        elif dd >= -rearm:
            scale = 1.0
    return pd.Series(out, index=net.index)


def dd_brake(net: pd.Series, d_trip: float, floor: float = DD_FLOOR) -> pd.Series:
    """Apply the causal drawdown stop to a net series (re-arm at -d_trip/2 hysteresis)."""
    return net * dd_brake_scale(net, d_trip, floor, d_trip / 2.0)


# --------------------------------------------------------------------------------------------------
# metrics
# --------------------------------------------------------------------------------------------------
def _metrics(net_is: pd.Series, turn: float) -> dict:
    """IS-only metric bundle for an overlaid net series (already sliced to IS)."""
    reg = ct.regime_sharpe(net_is)
    return {
        "net": ct.msharpe(net_is, ct.LO0, ct.OOS_CUTOFF),
        "bull": reg["bull"],
        "bear": reg["bear"],
        "chop": reg["chop"],
        "n_pos": sum(1 for v in reg.values() if v > 0),
        "mdd": ct.maxdd(net_is) * 100,
        "turn": turn,
    }


def _line(label: str, m: dict) -> str:
    return (
        f"  {label:26} net={m['net']:+.2f}  bull={m['bull']:+.2f} bear={m['bear']:+.2f} "
        f"chop={m['chop']:+.2f} ({m['n_pos']}/3)  maxDD={m['mdd']:5.1f}%  turn={m['turn']:.4f}"
    )


def _exposure(scale_is: pd.Series) -> str:
    """Mean / min exposure of a brake scalar over IS active bars (how hard it de-levers)."""
    s = scale_is.dropna()
    return f"mean={s.mean():.2f} min={s.min():.2f} frac<1={float((s < 0.999).mean()) * 100:.0f}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=None)
    args = ap.parse_args()

    base = Path(args.data_dir) if args.data_dir else ct._ROOT / "data"
    syms = sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)
    coins = ct.load_tradfi(syms, args.data_dir)
    if not coins:
        print("No ingested tradfi data found.")
        return
    pn = ct.panels(coins)
    ret_fwd = pn["ret_fwd"]

    # --- iter-006 working best (UNCHANGED), sliced IS-only ---
    raw6 = i6.crash_braked_raw(pn)
    net6, w6 = i3.banded_net(raw6, ret_fwd, i6.CHOSEN_DELTA)
    net6_is = ct.is_only(net6)
    turn6 = ct.turnover(w6, ct.LO0, ct.OOS_CUTOFF)  # overlays scale exposure -> turn UNCHANGED

    # --- VIX + drawdown inputs (past-only) ---
    vix = load_vix_close(net6.index, args.data_dir)
    vix_is = ct.is_only(vix)
    s_vix = vix_scale(vix)  # pinned base=20 / floor=0.50
    d_trip = dd_trip_level(net6_is)  # worst-quintile rule
    rearm = d_trip / 2.0

    print("=" * 100)
    print("iter-008 — VIX BRAKE + DRAWDOWN STOP on iter-006 (exposure overlays, IS-only)")
    print("=" * 100)
    print(
        f"  VIX brake: s=clip({VIX_BASE:.0f}/VIX[t-1],{VIX_FLOOR:.2f},1)  "
        f"(IS VIX: median={vix_is.median():.1f} max={vix_is.max():.0f}; "
        f"frac>20={float((vix_is > 20).mean()) * 100:.0f}% "
        f"frac>40={float((vix_is > 40).mean()) * 100:.0f}%)"
    )
    print(
        f"  DD stop : D_TRIP={d_trip * 100:.1f}% (worst-quintile q={DD_QUANTILE:.2f} of IS DD), "
        f"floor={DD_FLOOR:.2f}, re-arm at -{rearm * 100:.1f}%\n"
    )

    # --- IDENTITIES (pre-registered) ---
    net_vix_id = net6_is * vix_scale(vix, base=1e9).reindex(net6_is.index)  # VIX<<base -> s==1
    net_dd_id = dd_brake(net6_is, d_trip=1e9)  # never trips -> ==net6
    id_vix = bool(np.allclose(net_vix_id.to_numpy(), net6_is.to_numpy(), atol=1e-12))
    id_dd = bool(np.allclose(net_dd_id.to_numpy(), net6_is.to_numpy(), atol=1e-12))
    print(
        f"  IDENTITY  VIX(base=inf)==iter-006: {'PASS' if id_vix else 'FAIL'}   "
        f"DD(D_trip=inf)==iter-006: {'PASS' if id_dd else 'FAIL'}"
    )

    # --- the three builds (all on the IS net6) ---
    net_vix = net6_is * s_vix.reindex(net6_is.index).fillna(1.0)
    net_stop = dd_brake(net6_is, d_trip)
    net_comb = dd_brake(net6_is * s_vix.reindex(net6_is.index).fillna(1.0), d_trip)

    m6 = _metrics(net6_is, turn6)
    m_vix = _metrics(net_vix, turn6)
    m_stop = _metrics(net_stop, turn6)
    m_comb = _metrics(net_comb, turn6)

    print("\n  --- IS effect (overlays don't change the unit-gross book -> turnover identical) ---")
    print(_line("iter-006 (baseline)", m6) + "   <- working best")
    print(_line("VIX brake ALONE", m_vix))
    print(_line("DD stop ALONE", m_stop))
    print(_line("COMBINED (VIX+stop)", m_comb))

    # --- exposure diagnostics (how hard each overlay de-levers, IS) ---
    s_vix_is = s_vix.reindex(net6_is.index).fillna(1.0)
    s_dd_is = dd_brake_scale(net6_is, d_trip, DD_FLOOR, rearm)
    s_comb_dd = dd_brake_scale(net6_is * s_vix_is, d_trip, DD_FLOOR, rearm)
    print("\n  exposure (IS active bars):")
    print(f"    VIX scalar : {_exposure(s_vix_is)}")
    print(f"    DD  scalar : {_exposure(s_dd_is)}")
    print(f"    combined   : VIX x DD  ({_exposure(s_vix_is * s_comb_dd)})")

    # --- BEAR sub-window decomposition (COVID V-crash vs 2022 grind) ---
    def _seg(net, lo, hi):
        s = net[(net.index >= pd.Timestamp(lo)) & (net.index < pd.Timestamp(hi))]
        g = s.groupby(s.index.to_period("M")).sum()
        sh = float(g.mean() / g.std() * np.sqrt(12)) if len(g) > 1 and g.std() > 0 else float("nan")
        return sh, float((np.prod(1.0 + s) - 1.0) * 100)

    print("\n  BEAR sub-window decomposition (iter-006 -> COMBINED):")
    for lab, lo, hi in (
        ("COVID Vcrash", "2020-02-19", "2020-04-01"),
        ("2022 grind  ", "2022-01-03", "2022-10-13"),
    ):
        s6, t6 = _seg(net6_is, lo, hi)
        sc, tc = _seg(net_comb, lo, hi)
        print(f"    {lab} {lo}..{hi}: Sh {s6:+.2f}/{t6:+.0f}% -> {sc:+.2f}/{tc:+.0f}%")

    # --- SENSITIVITY (report; the PINNED cell is starred — we do NOT pick max-net) ---
    print("\n  VIX-brake sensitivity (continuous; base x floor) — net / bull / bear / chop:")
    for b in (18.0, 20.0, 25.0):
        cells = []
        for fl in (0.33, 0.50, 0.67):
            nb = net6_is * vix_scale(vix, base=b, floor=fl).reindex(net6_is.index).fillna(1.0)
            r = ct.regime_sharpe(nb)
            star = "*" if (b == VIX_BASE and fl == VIX_FLOOR) else " "
            cells.append(
                f"fl={fl:.2f}{star}{ct.msharpe(nb, ct.LO0, ct.OOS_CUTOFF):+.2f}/"
                f"{r['bull']:+.2f}/{r['bear']:+.2f}/{r['chop']:+.2f}"
            )
        print(f"    base={b:>4.0f}: " + "   ".join(cells))
    print("    (* = pre-registered pinned cell base=20/floor=0.50; NOT the max-net cell)")

    print("\n  VIX step-variant sensitivity (VIX>thr -> floor=0.50):")
    for thr in (25.0, 30.0, 35.0):
        nb = net6_is * vix_step_scale(vix, thr=thr).reindex(net6_is.index).fillna(1.0)
        r = ct.regime_sharpe(nb)
        print(
            f"    thr={thr:>4.0f}: net={ct.msharpe(nb, ct.LO0, ct.OOS_CUTOFF):+.2f} "
            f"bull={r['bull']:+.2f} bear={r['bear']:+.2f} chop={r['chop']:+.2f}"
        )

    print("\n  DD-stop sensitivity (D_trip multiple of worst-quintile; floor=0.50):")
    for mult in (0.75, 1.0, 1.5):
        nb = dd_brake(net6_is, d_trip * mult)
        r = ct.regime_sharpe(nb)
        star = "*" if mult == 1.0 else " "
        print(
            f"    D_trip={d_trip * mult * 100:4.1f}%{star} "
            f"net={ct.msharpe(nb, ct.LO0, ct.OOS_CUTOFF):+.2f} bull={r['bull']:+.2f} "
            f"bear={r['bear']:+.2f} chop={r['chop']:+.2f} maxDD={ct.maxdd(nb) * 100:.1f}%"
        )
    print("    (* = pinned worst-quintile cell)")

    # --- FUTURE-BAR LEAK SELF-CHECK on the COMBINED build (panel + VIX corrupted post-cutoff) ---
    leak_ok = _leak_selfcheck(pn, ret_fwd, vix, d_trip)
    print(
        f"\n  future-bar leak self-check (COMBINED, corrupt panel+VIX post-cut): "
        f"{'PASS' if leak_ok else 'FAIL'}"
    )

    # --- CRASH-WATCH: worst IS month/day of the COMBINED book (tail bounded?) ---
    wm = net_comb.groupby(net_comb.index.to_period("M")).sum()
    print("\n  CRASH-WATCH (COMBINED, IS-only):")
    print(
        f"    worst MONTH: {wm.idxmin()}  {wm.min() * 100:+.2f}%   (iter-006 worst month -13.15%)"
    )
    print(
        f"    worst DAY  : {net_comb.idxmin().date()}  {net_comb.min() * 100:+.2f}%   "
        f"(iter-006 worst day -5.77%)"
    )

    # --- VERDICT (task's literal test: fix bear WITHOUT killing bull/chop = KEEP, else REJECT) ---
    bear_fixed = m_comb["bear"] - m6["bear"]
    bull_kept = m_comb["bull"] >= m6["bull"] - 0.10  # preserved within a small tolerance
    chop_kept = m_comb["chop"] >= m6["chop"] - 0.10
    keep = (bear_fixed >= 0.25) and bull_kept and chop_kept and (m_comb["n_pos"] >= m6["n_pos"])
    print("\n  VERDICT (COMBINED vs iter-006):")
    print(
        f"    bear {m6['bear']:+.2f} -> {m_comb['bear']:+.2f} (Δ{bear_fixed:+.2f})  "
        f"bull {m6['bull']:+.2f} -> {m_comb['bull']:+.2f}  "
        f"chop {m6['chop']:+.2f} -> {m_comb['chop']:+.2f}  "
        f"net {m6['net']:+.2f} -> {m_comb['net']:+.2f}  "
        f"maxDD {m6['mdd']:.1f}% -> {m_comb['mdd']:.1f}%"
    )
    print(
        f"    bear_improved>=+0.25={'Y' if bear_fixed >= 0.25 else 'N'}  "
        f"bull_preserved={'Y' if bull_kept else 'N'}  chop_preserved={'Y' if chop_kept else 'N'}  "
        f"-> {'KEEP' if keep else 'REJECT/WASH'}"
    )

    # --- COST STRESS at 2x (12 bps/side) on the COMBINED build, IF it KEEPs ---
    print("\n  COST STRESS (COMBINED; signal/band/overlays UNCHANGED, only per-side cost):")
    orig = ct.COST_SIDE
    try:
        for mult, bps in ((1.0, 6.0), (2.0, 12.0)):
            ct.COST_SIDE = orig * mult
            n6c = ct.is_only(i3.banded_net(raw6, ret_fwd, i6.CHOSEN_DELTA)[0])
            ncomb_c = dd_brake(n6c * s_vix.reindex(n6c.index).fillna(1.0), dd_trip_level(n6c))
            print(
                f"    {bps:4.0f} bps/side ({mult:.0f}x): COMBINED net IS_Sharpe="
                f"{ct.msharpe(ncomb_c, ct.LO0, ct.OOS_CUTOFF):+.2f}"
            )
    finally:
        ct.COST_SIDE = orig


def _leak_selfcheck(pn, ret_fwd, vix, d_trip) -> bool:
    """Corrupt panel + VIX + forward returns post-cutoff; COMBINED IS net before must not move."""
    net6 = ct.is_only(i3.banded_net(i6.crash_braked_raw(pn), ret_fwd, i6.CHOSEN_DELTA)[0])
    s0 = vix_scale(vix).reindex(net6.index).fillna(1.0)
    comb0 = dd_brake(net6 * s0, d_trip)
    cut = comb0.index[len(comb0) // 2]

    pn_c = {k: v.copy() for k, v in pn.items()}
    pn_c["close"].loc[pn_c["close"].index >= cut] *= -7.0
    pn_c["ret_fwd"].loc[pn_c["ret_fwd"].index >= cut] += 5.0
    vix_c = vix.copy()
    vix_c.loc[vix_c.index >= cut] = 999.0  # corrupt VIX after the cutoff
    net6_c = ct.is_only(
        i3.banded_net(i6.crash_braked_raw(pn_c), pn_c["ret_fwd"], i6.CHOSEN_DELTA)[0]
    )
    s1 = vix_scale(vix_c).reindex(net6_c.index).fillna(1.0)
    comb1 = dd_brake(net6_c * s1, d_trip)

    common = comb0.index.intersection(comb1.index)
    common = common[common < cut]
    return bool(np.allclose(comb0.loc[common].to_numpy(), comb1.loc[common].to_numpy(), atol=1e-12))


if __name__ == "__main__":
    main()
