"""iter-007 — THE ALL-WEATHER BOOK: L2 + portfolio-level DRAWDOWN-BRAKE kill-switch.

The user's objective: the L2 baseline (anchor + 0.5·dispersion, vol-targeted) is a strong
metals BULL book but took a −45% drawdown on the never-seen 2011–2015 metals bear. Signal-level
brakes (the bear_floor grid, the convex blend) FAILED that bear because the slow EMA84/189 confirms
the downtrend too late — the bear's first plunge (27% of bars → 36% of the loss) is un-avoidable by
any CAUSAL signal. The remaining lever is a REACTIVE, portfolio-level overlay that caps the realised
tail AFTER the signal layer: a DRAWDOWN BRAKE (R-layer kill-switch). It bounds the bear to ~−23%
while keeping the bull intact — the all-weather book.

=========================================================================================
THE LOAD-BEARING PRIMITIVE — `dd_brake_scalar`
=========================================================================================
A causal scalar k[t] ∈ {floor, 1.0} produced by a HYSTERESIS state machine on the
KILL-SWITCHED equity's own peak-to-trough drawdown dd[t]:

    ARM  (k → floor)  when dd crosses below −D_trip   (the book is in a > D_trip drawdown)
    DISARM (k → 1.0)  when dd RECOVERS above −D_rearm  (shallower: D_rearm < D_trip)

The hysteresis band [D_rearm, D_trip] (i) stops chattering and (ii) — critically — re-arms on a
RECOVERY of the drawdown (dd climbing back toward 0), NOT on a return to the old peak, so a clean
V-recovery that lifts the book out of the deep drawdown re-arms exposure quickly (it does NOT wait
to recoup the whole loss; that would be the "de-lever-at-the-bottom" trap).

PAST-ONLY RECURSION (leak-safe). At candle t the decision uses the realised return through t−1
ONLY: dd[t] is computed from the kill-switched equity up to t−1, then k[t] is set, then candle t is
realised with k[t] and the equity advances for the NEXT decision. The recursion is self-consistent
— the brake watches the drawdown of the very book it actually trades (the kill-switched equity), but
every read of that equity is strictly past-only. This mirrors the `.shift(1)` lag the rest of the
pipeline uses; no future information enters k[t].

=========================================================================================
WHERE IT SITS (parity-correct, live-deployable)
=========================================================================================
The underlying book L2 → ONE `net_from_raw` → the vol-targeted per-candle net return `net0`. The
brake delivers:

    net_ks[t] = k[t] · net0[t]

Because per-candle net return is LINEAR in deployed gross, this is EXACTLY equivalent to multiplying
every metal's order size by the same scalar k[t] each candle. k ≤ 1 ALWAYS → the overlay can only
REDUCE exposure (it over-rides the vol-target ceiling DOWNWARD; it never levers up). In live trading
this is a single scalar applied to the whole book each candle — trivially parity-correct and
deployable.

`floor` MUST be > 0. A full halt (k = 0) is self-locking: a frozen equity earns 0, never recovers,
never crosses −D_rearm → the book is dead forever. floor = 0.25 keeps a quarter unit deployed so the
re-arm can catch the recovery. (Proven structurally; floor = 0 is excluded by construction.)

=========================================================================================
IS-ONLY CALIBRATION (pre-registration; the bear is never used to tune)
=========================================================================================
The thresholds are DERIVED LIVE (not hard-coded) by `iter_007_calibrate.calibrate()`, which is
structurally bear-blind (loads ONLY `data/`, the IS window, and raises if pointed at bear data).
Pre-stated rule, fixed before computing: D_trip = the depth at the worst-quintile (20%) of the IS
L2 drawdown distribution; D_rearm = D_trip/2 (hysteresis); floor = 0.25 (non-zero residual).
On the current IS data this computes to D_trip ≈ 15.3%, D_rearm ≈ 7.6% — armed on exactly the worst
20% of IS bars (real tail stress: the 2015 −24% gold year, 2018, 2021, 2022; not noise). These
IS-derived values are FROZEN and evaluated ONCE on the 2011–2015 bear; no tuning to the bear number.
Run `iter_007_calibrate.py` to reproduce them.

Run:  uv run python analysis/portfolio/metals/iter_007_allweather.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import bear_test_2011 as bear  # noqa: E402  (ingest_bear — self-heals data_bear/ if missing)
import iter_001_trend as it  # noqa: E402  (anchor build_raw at baseline FLOOR=0.5)
import iter_002_mn_overlay as ov  # noqa: E402  (gross_norm + mn_dispersion_raw)
import iter_007_calibrate as cal  # noqa: E402  (IS-only, bear-blind threshold derivation)
import universe_metals as um  # noqa: E402

gn = ov.gross_norm

# ── windows ─────────────────────────────────────────────────────────────────────────────────
BEAR_DIR = _HERE.parents[2] / "data_bear"  # gold/silver 2010-06→2015-04 (deep history)
MAIN_DIR = _HERE.parents[2] / "data"  # the 4 metals, IS + bull
BEAR_LO = pd.Timestamp("2011-09-01")  # metals peak → IS cutoff (pure unseen bear)
BEAR_HI = pd.Timestamp("2015-03-24")  # = IS start; the frozen unseen wall
IS_LO, IS_HI = um.LO0, um.OOS_CUTOFF  # IS window (… → 2025-03-24, OOS_CUTOFF frozen)
BULL_LO, BULL_HI = um.OOS_CUTOFF, um.HI1  # bull window (2025-03-24 → 2026-06)

# ── brake-threshold defaults (CONVENIENCE ONLY — the AUTHORITATIVE values are derived live by
#    iter_007_calibrate.calibrate(); the scorecard + any production caller use those, not these). ──
D_TRIP = (
    0.15  # ≈ the IS-derived value (calibrate() computes 0.153); a sane default for the signature
)
D_REARM = 0.075  # = D_trip/2 hysteresis (calibrate() computes 0.0763)
FLOOR_RECOMMENDED = 0.25  # quarter-unit deployed while armed (must be > 0; floor=0 self-locks)
FLOOR_ALT = 0.33  # reported as robustness (shallower cut)

EMA_FAST, EMA_SLOW = 84, 189  # inherited from the anchor — NOT re-fit for the convex blend

# COVID-crash V-recovery window (IS) — used to verify the re-arm catches clean V-recoveries.
COVID_LO = pd.Timestamp("2020-02-15")
COVID_HI = pd.Timestamp("2020-07-01")


# ── THE LOAD-BEARING PRIMITIVE — drawdown-brake scalar ────────────────────────────────────────
def dd_brake_scalar(
    net0: pd.Series,
    d_trip: float = D_TRIP,
    d_rearm: float = D_REARM,
    floor: float = FLOOR_RECOMMENDED,
) -> pd.Series:
    """Causal hysteresis drawdown-brake scalar k[t] ∈ {floor, 1.0}.

    The brake reacts to the peak-to-trough drawdown of the equity the book ACTUALLY trades (the
    kill-switched equity), so the recursion folds k back into the equity it watches. STRICTLY
    PAST-ONLY: at candle t the decision uses the realised return through t−1 only — k[t] is set
    from dd computed on the kill-switched equity up to t−1, then candle t is realised with k[t].
    This is the leak-safe mirror of the `.shift(1)` lag used everywhere else in the pipeline.

    State machine (hysteresis band [d_rearm, d_trip]):
      - start UN-armed (k = 1.0).
      - if NOT armed and dd[t−1] ≤ −d_trip   → ARM    (k[t] = floor)
      - if     armed and dd[t−1] ≥ −d_rearm  → DISARM (k[t] = 1.0)   [shallower re-arm]
      - else hold the previous state.
    dd[t−1] = eq/peak − 1 is the running peak-to-trough drawdown of the kill-switched equity through
    candle t−1. Re-arm triggers on a RECOVERY of the drawdown (dd climbing back above −d_rearm), NOT
    on regaining the old peak — so a V-recovery re-arms quickly instead of locking in the loss.

    floor MUST be > 0: a full halt (floor = 0) freezes the equity, which then never recovers above
    −d_rearm, so the brake never disarms — an absorbing self-lock. Keep floor = 0.25.
    """
    if floor <= 0.0:
        raise ValueError("floor must be > 0 (floor=0 is a self-locking full halt — dead book)")
    r = net0.to_numpy()
    n = len(r)
    k = np.ones(n)
    eq = 1.0  # kill-switched equity level through the PREVIOUS candle (t−1)
    peak = 1.0
    armed = False
    for t in range(n):
        dd = eq / peak - 1.0  # drawdown known at the close of t−1 (past-only)
        if armed:
            if dd >= -d_rearm:
                armed = False
        else:
            if dd <= -d_trip:
                armed = True
        k[t] = floor if armed else 1.0
        eq *= 1.0 + k[t] * r[t]  # realise candle t with k[t], advance for the NEXT decision
        peak = max(peak, eq)
    return pd.Series(k, index=net0.index)


def apply_brake(net0: pd.Series, k: pd.Series) -> pd.Series:
    """Delivered return net_ks[t] = k[t]·net0[t] — exposure scaled by k (parity-correct)."""
    return net0 * k.reindex(net0.index).fillna(1.0)


# ── underlying books (produce net0 = vol-targeted net BEFORE the brake) ───────────────────────
def book_l2(coins: dict[str, pd.DataFrame]) -> pd.Series:
    """L2 baseline book: gn(anchor[FLOOR=0.5]) + 0.5·gn(dispersion) → ONE net_from_raw → net0."""
    pan = um.panels(coins)
    close, ret_fwd = pan["close"], pan["ret_fwd"]
    raw = gn(it.build_raw(coins)) + 0.5 * gn(ov.mn_dispersion_raw(close))
    net, _ = um.net_from_raw(raw, ret_fwd)
    return net


# ── convex blend (QR's signal-level brake — reported as the scorecard's middle row) ───────────
def downtrend_fraction(coins: dict[str, pd.DataFrame]) -> pd.Series:
    """b ∈ [0,1] = fraction of PRESENT metals with EMA84 < EMA189 (broad-downtrend share).

    Uses ONLY the anchor's existing EMA84/189 cross — zero new parameters. Causal (ewm uses
    past/present closes only); the downstream net_from_raw lags the blended book one candle.
    Present = close.notna() (PIT eligibility); b counts down-metals over the present set, 0 when
    no metal has history yet.
    """
    close = um.panels(coins)["close"]
    elig = close.notna()
    ef = close.ewm(span=EMA_FAST, adjust=False).mean()
    es = close.ewm(span=EMA_SLOW, adjust=False).mean()
    down = ((ef < es) & elig).astype(float)
    pres = elig.sum(axis=1).replace(0, np.nan)
    return (down.sum(axis=1) / pres).fillna(0.0)


def convex_book(coins: dict[str, pd.DataFrame]) -> pd.Series:
    """Convex blend (1−b)·gn(anchor) + b·gn(dispersion), b = downtrend fraction (parameter-free).

    Mechanism: broad bull ⇒ b≈0 ⇒ pure anchor; broad bear ⇒ b≈1 ⇒ pure dispersion. The ONLY change
    vs L2 is additive → per-bar convex blend (the QR's signal-level brake). One net_from_raw.
    """
    pan = um.panels(coins)
    close, ret_fwd = pan["close"], pan["ret_fwd"]
    b = downtrend_fraction(coins)
    a = gn(it.build_raw(coins))  # anchor at baseline FLOOR=0.5
    d = gn(ov.mn_dispersion_raw(close))
    raw = a.mul(1.0 - b, axis=0) + d.mul(b, axis=0)  # per-bar convex blend
    net, _ = um.net_from_raw(raw, ret_fwd)
    return net


# ── per-regime stats ──────────────────────────────────────────────────────────────────────────
def regime_stats(net: pd.Series, lo: pd.Timestamp, hi: pd.Timestamp) -> tuple[float, float, int]:
    """(monthly Sharpe, maxDD% on the slice, n candles) over [lo, hi). maxDD is sliced — no leak."""
    s = net[(net.index >= lo) & (net.index < hi)]
    if len(s) < 2:
        return float("nan"), float("nan"), len(s)
    return um.msharpe(s, lo, hi), um.maxdd(s) * 100, len(s)


def armed_fraction(k: pd.Series, lo: pd.Timestamp, hi: pd.Timestamp) -> float:
    """Fraction of candles in [lo, hi) the brake is ENGAGED (k < 1) — % of bars de-levered."""
    s = k[(k.index >= lo) & (k.index < hi)]
    return float((s < 1.0).mean()) * 100 if len(s) else float("nan")


def _row_baseline(net_bear: pd.Series, net_main: pd.Series) -> dict:
    """Per-regime scorecard row for a book with NO brake (baseline / convex)."""
    bsr, bdd, bn = regime_stats(net_bear, BEAR_LO, BEAR_HI)
    isr, idd, in_ = regime_stats(net_main, IS_LO, IS_HI)
    usr, udd, un = regime_stats(net_main, BULL_LO, BULL_HI)
    worst = min(bdd, idd, udd)
    return dict(
        bsr=bsr,
        bdd=bdd,
        isr=isr,
        idd=idd,
        usr=usr,
        udd=udd,
        worst=worst,
        allp=(bsr > 0) and (isr > 0) and (usr > 0),
        bull_armed=0.0,
        bn=bn,
        in_=in_,
        un=un,
    )


def _row_braked(
    net0_bear: pd.Series, net0_main: pd.Series, floor: float, d_trip: float, d_rearm: float
) -> dict:
    """Per-regime scorecard row for L2 + DD-brake at a given floor (incl. bull-armed %).

    d_trip/d_rearm are the IS-DERIVED thresholds from iter_007_calibrate.calibrate() — NOT literals.
    """
    kb = dd_brake_scalar(net0_bear, d_trip, d_rearm, floor)
    km = dd_brake_scalar(net0_main, d_trip, d_rearm, floor)
    row = _row_baseline(apply_brake(net0_bear, kb), apply_brake(net0_main, km))
    row["bull_armed"] = armed_fraction(km, BULL_LO, BULL_HI)
    return row


# ── the all-weather scorecard ────────────────────────────────────────────────────────────────
def all_weather_scorecard() -> list[tuple[str, dict]]:
    """Build + print the per-regime ALL-WEATHER SCORECARD; return the rows for re-use/testing."""
    bear.ingest_bear()  # self-heal data_bear/ (gold/silver 2010→2015) if missing — idempotent
    cb = um.load_metals(BEAR_DIR)
    cm = um.load_metals(MAIN_DIR)
    c = cal.calibrate()  # IS-DERIVED thresholds, computed live (bear-blind) — not literals
    dt, dr = c["d_trip"], c["d_rearm"]

    net0_l2_b, net0_l2_m = book_l2(cb), book_l2(cm)
    rows: list[tuple[str, dict]] = [
        ("L2 (baseline)", _row_baseline(net0_l2_b, net0_l2_m)),
        ("convex blend", _row_baseline(convex_book(cb), convex_book(cm))),
        ("L2 + DD-brake floor=0.25 (RECOMMENDED)", _row_braked(net0_l2_b, net0_l2_m, 0.25, dt, dr)),
        ("L2 + DD-brake floor=0.33", _row_braked(net0_l2_b, net0_l2_m, 0.33, dt, dr)),
    ]

    print("=" * 122)
    print(
        "iter-007 ALL-WEATHER SCORECARD — L2 + portfolio DRAWDOWN-BRAKE (IS-calibrated, one-shot "
        "bear)"
    )
    print("=" * 122)
    print(f"  bear {tuple(cb)} {BEAR_LO.date()}..{BEAR_HI.date()}  |  main {tuple(cm)} IS+bull")
    print(
        "  net_ks[t] = k[t]·net0[t] ; k ∈ {floor, 1.0} = causal hysteresis brake on the "
        "kill-switched equity's own drawdown"
    )
    print(
        f"  IS-DERIVED thresholds (iter_007_calibrate.calibrate(), computed live): "
        f"D_trip={dt * 100:.1f}%  D_rearm={dr * 100:.1f}% (= D_trip/2)  "
        f"floor∈{{{FLOOR_RECOMMENDED}, {FLOOR_ALT}}}\n"
    )

    print("  IS-CALIBRATION PROVENANCE (IS L2 book ONLY; bear-blind — computed, not literals):")
    print(
        f"    L2 IS Sharpe={c['is_sharpe']:+.2f}  IS maxDD={c['is_maxdd'] * 100:.1f}%  "
        f"n={c['n_is']}  |  rule: D_trip = depth at the {cal.ARM_QUANTILE:.0%} IS-drawdown quantile"
    )
    print(
        f"    %IS bars armed (dd ≤ −D_trip) = {c['pct_bars_armed'] * 100:.1f}% (target "
        f"{cal.ARM_QUANTILE:.0%}) → D_trip sits in the genuine IS tail, not noise\n"
    )

    hdr = (
        f"  {'config':40} | {'BEAR_SR':>7} {'BEAR_DD':>8} | {'IS_SR':>6} {'IS_DD':>7} | "
        f"{'BULL_SR':>7} {'BULL_DD':>8} | {'worstDD':>8} {'all+':>5} {'bull-armed':>11}"
    )
    print(hdr)
    print("  " + "-" * 118)
    for label, r in rows:
        print(
            f"  {label:40} | {r['bsr']:>+7.2f} {r['bdd']:>7.1f}% | {r['isr']:>+6.2f} "
            f"{r['idd']:>6.1f}% | {r['usr']:>+7.2f} {r['udd']:>7.1f}% | {r['worst']:>7.1f}% "
            f"{str(r['allp']):>5} {r['bull_armed']:>10.1f}%"
        )
    print("  " + "-" * 118)
    r0 = rows[0][1]
    print(f"  candle counts: BEAR={r0['bn']}  IS={r0['in_']}  BULL={r0['un']}")
    print(
        "  columns: per-regime monthly Sharpe + maxDD%; worstDD = most-negative regime maxDD "
        "(the survival number);"
    )
    print(
        "           all+ = all-3-Sharpe-positive; bull-armed% = fraction of bull candles the "
        "brake is engaged (must be < 15%)\n"
    )

    return rows


def _covid_recovery_check() -> None:
    """One-line recovery check: does the re-arm catch the clean 2020 COVID V-recovery (IS)?

    On the COVID crash window the metals book V-recovers fast. A correct hysteresis brake should
    NOT stay armed across it (re-arming on the recovery, not on regaining the old peak) → bull/IS
    armed% near the crash should be ~0. We verify the brake is essentially un-engaged here.
    """
    cm = um.load_metals(MAIN_DIR)
    c = cal.calibrate()  # use the SAME IS-derived thresholds as the scorecard (not the defaults)
    km = dd_brake_scalar(book_l2(cm), c["d_trip"], c["d_rearm"], FLOOR_RECOMMENDED)
    covid_armed = armed_fraction(km, COVID_LO, COVID_HI)
    print(
        f"  RECOVERY CHECK (2020 COVID V-recovery {COVID_LO.date()}..{COVID_HI.date()}, IS): "
        f"brake armed {covid_armed:.1f}% of the window "
        f"→ {'OK (clean V re-arms, no lock-in)' if covid_armed < 5.0 else 'WARN (lingering arm)'}"
    )


def main() -> None:
    rows = dict(all_weather_scorecard())
    _covid_recovery_check()

    # pre-registered SUCCESS / FALSIFIER readout for the two brake floors
    l2 = rows["L2 (baseline)"]
    print(
        "\n  PRE-REGISTERED SUCCESS (worstDD ≥ −27% & BULL_SR ≥ +1.5 & IS_SR ≥ +0.30)  |  "
        "FALSIFIER (bull-armed > 15% OR worstDD doesn't improve ≥ 10pp vs L2):"
    )
    for label in ("L2 + DD-brake floor=0.25 (RECOMMENDED)", "L2 + DD-brake floor=0.33"):
        r = rows[label]
        d_worst = r["worst"] - l2["worst"]
        succ = (r["worst"] >= -27.0, r["usr"] >= 1.5, r["isr"] >= 0.30)
        fals = (r["bull_armed"] > 15.0) or (d_worst < 10.0)
        verdict = "*** PASS ***" if (all(succ) and not fals) else "FAIL"
        print(
            f"    {label:40}  worstDD{r['worst']:+.1f}%(≥−27={succ[0]!s:5}) "
            f"BULL_SR{r['usr']:+.2f}(≥1.5={succ[1]!s:5}) IS_SR{r['isr']:+.2f}(≥0.30={succ[2]!s:5}) "
            f"| Δworst{d_worst:+.1f}pp bull-armed{r['bull_armed']:.1f}% falsified={fals!s:5} "
            f"=> {verdict}"
        )


if __name__ == "__main__":
    main()
