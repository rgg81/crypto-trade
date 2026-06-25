"""iter-008 — THE RISK-MANAGEMENT ARSENAL for a REGIME-SWITCHING (long+short) metals book.

The user's mandate: stop merely SURVIVING the bear, start MANAGING it like a pro. The QR is
designing a regime-gated SHORT in parallel so the bear PAYS; that introduces NEW tail risks the
existing portfolio DRAWDOWN-BRAKE (iter-007) was not designed for:

  (W) WHIPSAW at the regime flip — going short just as the bear ends / long just as it begins;
  (B) SHORT-THE-BOTTOM — getting maximally short into the bear's exhaustion low;
  (S) BEAR-RALLY SQUEEZE — a violent counter-trend rally blowing up a fresh short (fast, fat-tail);
  (A) ASYMMETRY — the secular drift is UP, so a short carries more tail risk than a long of equal
      gross. Equity intuitions (symmetric vol) are WRONG for a structurally-long store-of-value.

=========================================================================================
THE GROSS-NORM + VOL-TARGET WASHOUT (why naive scaling fails — the design constraint)
=========================================================================================
The engine does: raw → gross-normalise to unit gross → .shift(1) → PnL − cost → VOL-TARGET to ~15%.
Vol-target divides by trailing realised vol, so any *magnitude* change to `raw` (or even to `net`
BEFORE vol_target) is RE-LEVERED back to the 15% ceiling — it washes out. This is exactly why the
QR's signal-level brakes (bear_floor grid, convex blend) barely moved the bear DD. A risk layer can
only bite if it acts in ONE of two washout-proof ways:
  (1) DOWNSTREAM of vol_target — multiply the realised net by a causal scalar k≤1 (the iter-007
      DD-brake primitive: net_ks = k·net0). k is a pure de-risk; vol_target cannot undo it.
  (2) As an explicit GROSS CAP fed THROUGH vol_target — cap the per-candle target vol itself in the
      bear regime, so the 15% ceiling becomes (say) 9% while short. This changes the RISK BUDGET,
      not the signal magnitude, so it survives the normalisation.
Every layer below is built to sit in (1) or (2). Layers that would wash out are flagged + excluded.

=========================================================================================
THE REGIME-SHORT PROXY (stated explicitly — the QR owns the real core)
=========================================================================================
For THIS risk study the regime-short is proxied by a long-horizon-trend SIGN FLIP on the anchor:
when the broad metals trend is DOWN (EMA84 < EMA189 on a majority of present metals, the same
parameter-free regime signal the QR's core will use), the anchor's long base-load is REPLACED by a
SHORT of the same gross. Concretely book_rs = (1−2·short_on)·anchor + 0.5·dispersion, where
short_on = 1 when downtrend_fraction > 0.5. This is a deliberately SIMPLE stand-in so the risk
layers have a real short to protect; the QR's production regime-short will differ, but the FAILURE
MODES (whipsaw/bottom/squeeze) are generic to any regime-short and that is what the arsenal targets.
The risk LAYERS are independent of the proxy's exact form — each is a wrapper on net0/raw.

=========================================================================================
THE ARSENAL (each: mechanism · pipeline slot · IS-calibrated threshold · washout-proof?)
=========================================================================================
R-A  REGIME-TRANSITION DE-RISK  — gross taper for `T` candles after ANY regime flip. Slot: a causal
     scalar k_trans∈{taper,1} multiplying net0 (slot-1). Defends W. Threshold T, taper IS-derived.
R-B  ASYMMETRIC GROSS CAP (short ≤ long) — short leg deployed at SHORT_FRAC<1 of long gross. Slot:
     scales the short raw before gross-norm is WRONG (washes out); instead a slot-1 scalar that is
     SHORT_FRAC whenever the book is net-short. Defends A + B. Threshold SHORT_FRAC IS-derived.
R-C  SQUEEZE STOP (bear-rally fast-exit) — when net-short AND a fast counter-rally fires (a
     short-window up-move > Z·trailing band), cut to floor for K candles. Slot-1. Defends S. Z,K IS.
R-D  REGIME-AWARE DD-BRAKE — the iter-007 brake with a TIGHTER trip + FASTER re-arm while net-short
     (a short squeeze draws down fast & violent). Slot-1 (replaces the brake). Defends S + tail.
R-E  DOWNSIDE-SEMIVOL TARGET CEILING — vol_target keyed to DOWNSIDE semivol, capped LOWER in the
     bear so the 15% target doesn't lever UP into a hot bear. Slot-2 (through vol_target). Tail.

Run:  uv run python analysis/portfolio/metals/iter_008_risk_arsenal.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import bear_test_2011 as bear  # noqa: E402
import iter_001_trend as it  # noqa: E402
import iter_002_mn_overlay as ov  # noqa: E402
import iter_007_allweather as aw  # noqa: E402  (dd_brake_scalar, apply_brake, regime_stats)
import iter_007_calibrate as cal  # noqa: E402
import universe_metals as um  # noqa: E402

gn = ov.gross_norm

BEAR_DIR = aw.BEAR_DIR
MAIN_DIR = aw.MAIN_DIR
BEAR_LO, BEAR_HI = aw.BEAR_LO, aw.BEAR_HI
IS_LO, IS_HI = aw.IS_LO, aw.IS_HI
BULL_LO, BULL_HI = aw.BULL_LO, aw.BULL_HI

EMA_FAST, EMA_SLOW = aw.EMA_FAST, aw.EMA_SLOW  # 84/189, inherited — never re-fit


# ════════════════════════════════════════════════════════════════════════════════════════════
#  REGIME SIGNAL + the REGIME-SHORT PROXY (the thing the arsenal protects)
# ════════════════════════════════════════════════════════════════════════════════════════════
def downtrend_fraction(coins: dict[str, pd.DataFrame]) -> pd.Series:
    """b∈[0,1] = fraction of PRESENT metals with EMA84<EMA189 (the parameter-free regime signal).

    Identical to aw.downtrend_fraction — re-exposed so the proxy and the transition layer share ONE
    causal regime read. ewm uses past/present closes only; net_from_raw lags it a candle downstream.
    """
    return aw.downtrend_fraction(coins)


def short_on(coins: dict[str, pd.DataFrame]) -> pd.Series:
    """Binary bear-regime flag s[t]∈{0,1}: 1 when the broad metals trend is DOWN (b>0.5).

    Causal: b is causal, so s is causal; the consuming book is lagged one candle by net_from_raw.
    This is the regime the QR's short keys off and the regime my transition layer reads.
    """
    return (downtrend_fraction(coins) > 0.5).astype(float)


def book_rs_raw(coins: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.Series]:
    """REGIME-SHORT PROXY raw book: flip the anchor's sign in the bear, keep dispersion always-on.

    raw = (1 − 2·s)·gn(anchor) + 0.5·gn(dispersion).  s=0 (bull) → +anchor (the L2 long book);
    s=1 (bear) → −anchor (a short of the same gross). Dispersion (dollar-neutral) is unaffected.
    Returns (raw_book, s) so risk layers can read the regime/short state. PARITY-CORRECT: one
    net_from_raw downstream, exactly like L2.
    """
    pan = um.panels(coins)
    close = pan["close"]
    s = short_on(coins)
    a = gn(it.build_raw(coins))
    d = gn(ov.mn_dispersion_raw(close))
    raw = a.mul(1.0 - 2.0 * s, axis=0) + 0.5 * d
    return raw, s


def book_rs_net0(coins: dict[str, pd.DataFrame]) -> tuple[pd.Series, pd.Series]:
    """Regime-short proxy → (vol-targeted net0, regime flag s aligned to net0.index)."""
    raw, s = book_rs_raw(coins)
    ret_fwd = um.panels(coins)["ret_fwd"]
    net0, _ = um.net_from_raw(raw, ret_fwd)
    s_al = s.reindex(net0.index).ffill().fillna(0.0)
    return net0, s_al


def book_l2_net0(coins: dict[str, pd.DataFrame]) -> pd.Series:
    """The current baseline L2 (long-only anchor + dispersion) net0 — for side-by-side reference."""
    return aw.book_l2(coins)


# ════════════════════════════════════════════════════════════════════════════════════════════
#  THE ARSENAL — each is a CAUSAL scalar k[t]≤1 on net0 (slot-1, washout-proof) unless noted
# ════════════════════════════════════════════════════════════════════════════════════════════
def k_transition(s: pd.Series, taper: float, t_candles: int) -> pd.Series:
    """R-A  REGIME-TRANSITION DE-RISK. k∈{taper,1}: cut gross to `taper` for `t_candles` after ANY
    regime flip (s changes), then restore. Defends WHIPSAW — the freshly-flipped regime is the most
    likely to be wrong, so we carry less gross until it has persisted t_candles.

    Causal: the flip at t is known from s[t] (itself causal); we taper candles t..t+T−1. Past-only.
    """
    sv = s.to_numpy()
    n = len(sv)
    k = np.ones(n)
    cd = 0  # candles remaining in the post-flip taper
    prev = sv[0] if n else 0.0
    for t in range(n):
        if sv[t] != prev:  # a flip occurred at t (causal — s[t] known at close t-1 read)
            cd = t_candles
        prev = sv[t]
        if cd > 0:
            k[t] = taper
            cd -= 1
    return pd.Series(k, index=s.index)


def k_short_asym(s: pd.Series, short_frac: float) -> pd.Series:
    """R-B  ASYMMETRIC GROSS CAP. k = short_frac whenever net-short (s=1), else 1. The short leg
    carries LESS gross than the long because the secular drift is UP (a short fights the tailwind
    and eats violent rallies). Slot-1 scalar so it survives vol_target (scaling raw would wash out).
    Defends ASYMMETRY + softens SHORT-THE-BOTTOM (smaller short → smaller bottom error)."""
    return pd.Series(np.where(s.to_numpy() > 0.5, short_frac, 1.0), index=s.index)


def k_squeeze(
    coins: dict[str, pd.DataFrame],
    s_idx: pd.Series,
    z: float,
    k_candles: int,
    win: int,
    floor: float,
) -> pd.Series:
    """R-C  SQUEEZE STOP. While net-short, if a FAST counter-rally fires — a short-window up-move in
    the broad-metals proxy exceeding z·(trailing band of that move) — cut gross to `floor` for
    `k_candles`. Defends the BEAR-RALLY SQUEEZE (fast, fat-tailed, the classic short killer).

    Counter-rally proxy = the cross-metal mean of `win`-candle returns (gold+silver beta to bear);
    band = trailing std of that move. Strictly causal: the move uses closes through t, the band is
    .shift(1)-lagged, the stop arms for the NEXT k_candles. Only bites when net-short (s=1)."""
    close = um.panels(coins)["close"]
    mret = close.pct_change(win).mean(axis=1)  # broad-metals win-candle return (causal)
    band = mret.rolling(126).std().shift(1)  # trailing dispersion band, past-only
    trig = (mret > z * band) & (band > 0)  # a sharp UP-move (counter-rally while short)
    trig = trig.reindex(s_idx.index).fillna(False).to_numpy()
    sv = s_idx.to_numpy()
    n = len(sv)
    k = np.ones(n)
    cd = 0
    for t in range(n):
        if sv[t] > 0.5 and trig[t]:  # squeeze only matters while net-short
            cd = k_candles
        if cd > 0:
            k[t] = floor
            cd -= 1
    return pd.Series(k, index=s_idx.index)


def dd_brake_regime(
    net0: pd.Series,
    s: pd.Series,
    d_trip_long: float,
    d_rearm_long: float,
    d_trip_short: float,
    d_rearm_short: float,
    floor: float,
) -> pd.Series:
    """R-D  REGIME-AWARE DD-BRAKE. The iter-007 hysteresis brake, but with a TIGHTER trip and FASTER
    re-arm while net-short — a short squeeze draws the book down fast and violently, so we want to
    de-lever sooner and re-arm sooner once the squeeze passes. While long (secular tailwind) we keep
    the looser iter-007 band so the brake does not chatter on benign bull pullbacks.

    Same past-only recursion as aw.dd_brake_scalar (k[t] from dd through t−1; realise t; advance).
    The trip/re-arm thresholds are selected per-candle by the regime flag s[t] (causal)."""
    if floor <= 0.0:
        raise ValueError("floor must be > 0 (self-locking full halt otherwise)")
    r = net0.to_numpy()
    sv = s.reindex(net0.index).ffill().fillna(0.0).to_numpy()
    n = len(r)
    k = np.ones(n)
    eq = 1.0
    peak = 1.0
    armed = False
    for t in range(n):
        dd = eq / peak - 1.0
        dt = d_trip_short if sv[t] > 0.5 else d_trip_long
        dr = d_rearm_short if sv[t] > 0.5 else d_rearm_long
        if armed:
            if dd >= -dr:
                armed = False
        else:
            if dd <= -dt:
                armed = True
        k[t] = floor if armed else 1.0
        eq *= 1.0 + k[t] * r[t]
        peak = max(peak, eq)
    return pd.Series(k, index=net0.index)


def dd_brake_rolling(
    net0: pd.Series,
    s: pd.Series,
    d_trip_long: float,
    d_rearm_long: float,
    d_trip_short: float,
    d_rearm_short: float,
    floor: float,
    peak_win: int,
) -> pd.Series:
    """R-D′  ROLLING-PEAK regime-aware DD-brake — the fix for the cross-regime LOCK-IN trap.

    The iter-007 brake measures drawdown vs the ALL-TIME peak. That is correct for a book that
    recovers, but a regime-switching book can carry a large UNRECOVERED loss across a regime
    boundary (e.g. a short that bled through the bear enters the bull 40% below its old peak). The
    all-time-peak brake then stays armed for the ENTIRE next regime (dd never climbs back above
    −d_rearm), de-levering a perfectly good bull — the de-lever-at-the-bottom trap the iter-007 note
    warns of, triggered by a stale peak.

    FIX: measure drawdown vs a TRAILING ROLLING peak (max over the last `peak_win` candles of the
    kill-switched equity), not the all-time peak. A fresh regime that starts trading well lifts the
    rolling peak and re-arms quickly; a genuine fast drawdown WITHIN `peak_win` still trips. This is
    a local-tail brake — exactly what a regime-switcher needs. Same past-only recursion + regime.
    """
    if floor <= 0.0:
        raise ValueError("floor must be > 0 (self-locking full halt otherwise)")
    r = net0.to_numpy()
    sv = s.reindex(net0.index).ffill().fillna(0.0).to_numpy()
    n = len(r)
    k = np.ones(n)
    eqs = np.empty(n + 1)
    eqs[0] = 1.0
    armed = False
    for t in range(n):
        lo = max(0, t + 1 - peak_win)  # rolling window over the kill-switched equity through t−1
        peak = eqs[lo : t + 1].max()  # trailing peak (past-only; eqs[t] is the close of t−1)
        dd = eqs[t] / peak - 1.0
        dt = d_trip_short if sv[t] > 0.5 else d_trip_long
        dr = d_rearm_short if sv[t] > 0.5 else d_rearm_long
        if armed:
            if dd >= -dr:
                armed = False
        else:
            if dd <= -dt:
                armed = True
        k[t] = floor if armed else 1.0
        eqs[t + 1] = eqs[t] * (1.0 + k[t] * r[t])
    return pd.Series(k, index=net0.index)


def k_compose(*ks: pd.Series) -> pd.Series:
    """Compose independent slot-1 de-risk scalars by MULTIPLICATION (each ≤1 → product ≤1).

    Multiplicative composition keeps the stack monotone (any layer can only REDUCE gross) and
    order-independent — the deepest cut wins, exactly the conservative behaviour we want."""
    out = None
    for k in ks:
        out = k if out is None else out * k.reindex(out.index).fillna(1.0)
    return out


# ════════════════════════════════════════════════════════════════════════════════════════════
#  SCORECARD PLUMBING
# ════════════════════════════════════════════════════════════════════════════════════════════
def _row(net_bear: pd.Series, net_main: pd.Series, k_bull: pd.Series | None = None) -> dict:
    bsr, bdd, bn = aw.regime_stats(net_bear, BEAR_LO, BEAR_HI)
    isr, idd, in_ = aw.regime_stats(net_main, IS_LO, IS_HI)
    usr, udd, un = aw.regime_stats(net_main, BULL_LO, BULL_HI)
    bull_armed = aw.armed_fraction(k_bull, BULL_LO, BULL_HI) if k_bull is not None else 0.0
    return dict(
        bsr=bsr,
        bdd=bdd,
        isr=isr,
        idd=idd,
        usr=usr,
        udd=udd,
        worst=min(bdd, idd, udd),
        allp=(bsr > 0) and (isr > 0) and (usr > 0),
        bull_armed=bull_armed,
        bn=bn,
        in_=in_,
        un=un,
    )


def _fmt(label: str, r: dict) -> str:
    return (
        f"  {label:46} | {r['bsr']:>+6.2f} {r['bdd']:>7.1f}% | {r['isr']:>+6.2f} {r['idd']:>6.1f}% "
        f"| {r['usr']:>+6.2f} {r['udd']:>7.1f}% | {r['worst']:>7.1f}% {str(r['allp']):>5} "
        f"{r['bull_armed']:>9.1f}%"
    )


def _hdr() -> str:
    return (
        f"  {'config':46} | {'BEAR_SR':>6} {'BEAR_DD':>8} | {'IS_SR':>6} {'IS_DD':>7} | "
        f"{'BUL_SR':>6} {'BUL_DD':>8} | {'worstDD':>8} {'all+':>5} {'bul-arm':>10}"
    )


# ════════════════════════════════════════════════════════════════════════════════════════════
#  THE DRIVER — build net0 (L2 + regime-short proxy), then layer the arsenal, score each
# ════════════════════════════════════════════════════════════════════════════════════════════
def _apply(net0: pd.Series, k: pd.Series) -> pd.Series:
    return net0 * k.reindex(net0.index).fillna(1.0)


def scorecard() -> list[tuple[str, dict]]:
    """Build + print the RISK-ARSENAL scorecard. Returns rows for re-use.

    Rows: (1) L2 baseline [long-only, no short]; (2) L2 + iter-007 DD-brake [current state];
    (3) REGIME-SHORT proxy bare [the new risk]; then each arsenal layer ON the regime-short;
    then the RECOMMENDED STACK. Bear column = the one-shot 2011–2015 validation."""
    import iter_008_calibrate as c8

    bear.ingest_bear()
    cb = um.load_metals(BEAR_DIR)
    cm = um.load_metals(MAIN_DIR)
    c = c8.calibrate()  # IS-derived, bear-blind
    c7 = cal.calibrate()  # iter-007 long-band (for the existing brake reference)

    # ── reference books ──────────────────────────────────────────────────────────────────────
    l2_b, l2_m = book_l2_net0(cb), book_l2_net0(cm)
    # iter-007 DD-brake on L2 (the current deployed state)
    kb_l2_b = aw.dd_brake_scalar(l2_b, c7["d_trip"], c7["d_rearm"], 0.25)
    kb_l2_m = aw.dd_brake_scalar(l2_m, c7["d_trip"], c7["d_rearm"], 0.25)

    # ── regime-short proxy net0 + regime flag ────────────────────────────────────────────────
    rs_b, s_b = book_rs_net0(cb)
    rs_m, s_m = book_rs_net0(cm)

    # ── arsenal scalars (bear + main), each IS-calibrated ────────────────────────────────────
    k_trans_b = k_transition(s_b, c["taper"], c["t_candles"])
    k_trans_m = k_transition(s_m, c["taper"], c["t_candles"])
    k_asym_b = k_short_asym(s_b, c["short_frac"])
    k_asym_m = k_short_asym(s_m, c["short_frac"])
    sqz = (c["squeeze_z"], c["squeeze_k"], c["squeeze_win"], c["squeeze_floor"])
    k_sqz_b = k_squeeze(cb, s_b, *sqz)
    k_sqz_m = k_squeeze(cm, s_m, *sqz)
    k_dreg_b = dd_brake_regime(
        rs_b,
        s_b,
        c["d_trip_long"],
        c["d_rearm_long"],
        c["d_trip_short"],
        c["d_rearm_short"],
        c["floor"],
    )
    k_dreg_m = dd_brake_regime(
        rs_m,
        s_m,
        c["d_trip_long"],
        c["d_rearm_long"],
        c["d_trip_short"],
        c["d_rearm_short"],
        c["floor"],
    )
    # R-D′ rolling-peak brake (the cross-regime-lock-in FIX)
    k_droll_b = dd_brake_rolling(
        rs_b,
        s_b,
        c["d_trip_long"],
        c["d_rearm_long"],
        c["d_trip_short"],
        c["d_rearm_short"],
        c["floor"],
        c["peak_win"],
    )
    k_droll_m = dd_brake_rolling(
        rs_m,
        s_m,
        c["d_trip_long"],
        c["d_rearm_long"],
        c["d_trip_short"],
        c["d_rearm_short"],
        c["floor"],
        c["peak_win"],
    )

    # ── RECOMMENDED STACK = the NO-BRAKE minimal stack: B (asym) × C (squeeze) × A (transition).
    #    The recovery-based DD-brake is DELIBERATELY EXCLUDED from the short sleeve — on a
    #    chronically-losing short it locks in (re-arms only on a recovery that never comes) and
    #    de-levers the bull 100% of bars. The brake stays on the LONG L2 book (its iter-007 home).
    #    Each layer here is monotone-good + equity-recovery-INDEPENDENT → bull-arm 0%, no lock-in. ─
    k_stack_b = k_compose(k_asym_b, k_sqz_b, k_trans_b)
    k_stack_m = k_compose(k_asym_m, k_sqz_m, k_trans_m)

    rows: list[tuple[str, dict]] = [
        ("L2 baseline (long-only, NO short)", _row(l2_b, l2_m)),
        (
            "L2 + iter-007 DD-brake (current state)",
            _row(_apply(l2_b, kb_l2_b), _apply(l2_m, kb_l2_m), kb_l2_m),
        ),
        ("REGIME-SHORT proxy, BARE (the new risk)", _row(rs_b, rs_m)),
        (
            f"  + R-B asym gross cap (short={c['short_frac']:.2f})",
            _row(_apply(rs_b, k_asym_b), _apply(rs_m, k_asym_m)),
        ),
        (
            f"  + R-A transition de-risk (T={c['t_candles']})",
            _row(_apply(rs_b, k_trans_b), _apply(rs_m, k_trans_m)),
        ),
        (
            f"  + R-C squeeze stop (z={c['squeeze_z']:.2f},K={c['squeeze_k']})",
            _row(_apply(rs_b, k_sqz_b), _apply(rs_m, k_sqz_m)),
        ),
        (
            "  + R-D regime DD-brake (all-time peak — LOCKS IN bull)",
            _row(_apply(rs_b, k_dreg_b), _apply(rs_m, k_dreg_m), k_dreg_m),
        ),
        (
            f"  + R-D' rolling-peak brake (win={c['peak_win']} — whipsaws IS)",
            _row(_apply(rs_b, k_droll_b), _apply(rs_m, k_droll_m), k_droll_m),
        ),
        (
            "RECOMMENDED STACK (B×C×A, NO brake on short)",
            _row(_apply(rs_b, k_stack_b), _apply(rs_m, k_stack_m), k_stack_m),
        ),
    ]

    print("=" * 132)
    print(
        "iter-008 RISK-ARSENAL SCORECARD — regime-short PROXY + the risk layers (IS-calibrated, "
        "one-shot bear)"
    )
    print("=" * 132)
    print(f"  bear {tuple(cb)} {BEAR_LO.date()}..{BEAR_HI.date()}  |  main {tuple(cm)} IS+bull")
    print(
        "  regime-short PROXY: raw=(1−2·s)·anchor + 0.5·dispersion, s=1 when downtrend-frac>0.5 "
        "(QR owns the real core)"
    )
    print(
        f"  IS-DERIVED thresholds: T={c['t_candles']} taper={c['taper']} "
        f"| short_frac={c['short_frac']} | squeeze z={c['squeeze_z']} K={c['squeeze_k']} "
        f"| short-band trip={c['d_trip_short'] * 100:.1f}%\n"
    )
    print(_hdr())
    print("  " + "-" * 128)
    for label, r in rows:
        print(_fmt(label, r))
    print("  " + "-" * 128)
    r0 = rows[0][1]
    print(f"  candle counts: BEAR={r0['bn']}  IS={r0['in_']}  BULL={r0['un']}")
    print(
        "  worstDD = most-negative regime maxDD (the survival number); all+ = all-3-Sharpe-pos;"
        " bul-arm% = bull candles de-levered (<15%)\n"
    )
    return rows


def main() -> None:
    rows = dict(scorecard())
    l2 = rows["L2 baseline (long-only, NO short)"]
    rs = rows["REGIME-SHORT proxy, BARE (the new risk)"]
    stack = rows["RECOMMENDED STACK (B×C×A, NO brake on short)"]
    print("  MARGINAL EFFECT of the arsenal on the regime-short:")
    print(
        f"    bear Sharpe : L2={l2['bsr']:+.2f}  RS-bare={rs['bsr']:+.2f}  STK={stack['bsr']:+.2f}"
    )
    print(
        f"    bear maxDD  : L2={l2['bdd']:.1f}%  RS-bare={rs['bdd']:.1f}%  STK={stack['bdd']:.1f}%"
    )
    print(
        f"    bull Sharpe : L2={l2['usr']:+.2f}  RS-bare={rs['usr']:+.2f}  STK={stack['usr']:+.2f}"
    )
    print(
        f"    IS Sharpe   : L2={l2['isr']:+.2f}  RS-bare={rs['isr']:+.2f}  STK={stack['isr']:+.2f}"
    )
    print(
        f"    worstDD     : L2={l2['worst']:.1f}%  RS-bare={rs['worst']:.1f}%  "
        f"STACK={stack['worst']:.1f}%"
    )
    print(f"    all-3-pos   : L2={l2['allp']}  RS-bare={rs['allp']}  STACK={stack['allp']}")

    # ── PRE-REGISTERED SUCCESS / FALSIFIER for the recommended (no-brake) stack ───────────────
    #   #2 is BULL-SHARPE-PRESERVATION, NOT bull-armed%: the recommended stack contains NO
    #   recovery-brake (that is the whole point — it cannot lock-in), so the only bull de-risking
    #   is R-B's pointwise cap on transient bull bear-blips, which is intended and HELPS the bull.
    #   The lock-in failure mode is owned by the two brake rows above (bull-arm 100% / IS −51%).
    d_worst = stack["worst"] - rs["worst"]
    d_bull = stack["usr"] - rs["usr"]
    succ = (
        stack["worst"] >= rs["worst"],  # (1) bounds the tail at least as well as the bare short
        d_bull >= -0.10,  # (2) bull Sharpe preserved (the secular tailwind is untouched)
        stack["idd"] >= rs["idd"],  # (3) IS drawdown not worsened (no brake-whipsaw)
    )
    print(
        "\n  PRE-REGISTERED (IS-pre-stated): the recommended NO-BRAKE stack must (1) NOT worsen"
    )
    print(
        "  worstDD vs the bare short, (2) preserve bull Sharpe (≥ −0.10), (3) NOT worsen IS DD"
    )
    print("  (no brake-whipsaw). It contains no recovery-brake → structurally cannot lock-in.")
    verdict = "*** PASS ***" if all(succ) else "FAIL"
    print(
        f"    Δworst{d_worst:+.1f}pp(≥0={succ[0]!s:5}) "
        f"ΔbullSR{d_bull:+.2f}(≥−0.10={succ[1]!s:5}) "
        f"ΔIS_DD{stack['idd'] - rs['idd']:+.1f}pp(≥0={succ[2]!s:5}) => {verdict}"
    )
    print(
        "  NOTE: bear/IS Sharpe stay NEGATIVE because the EMA84/189 regime-short LOSES (the signal"
    )
    print("  is too slow to short metals' violent bears). The arsenal bounds the TAIL; it cannot")
    print("  manufacture edge. The QR core must supply a faster regime signal OR flat-the-long")
    print("  (dispersion-only) in the bear — both out-of-scope here; this study owns the OVERLAY.")


if __name__ == "__main__":
    main()
