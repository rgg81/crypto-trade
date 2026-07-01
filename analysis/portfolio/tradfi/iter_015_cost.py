"""iter-015 COST DISCIPLINE — two turnover levers on the CONFIRMED iter-013 book (IS-only).

Goal: close the gross->net gap (gross +0.81 -> net +0.61 @6bps -> +0.42 @12bps) so the book is
2x-cost-ROBUST (net >= +0.50 @12bps) while PRESERVING the gross edge (~+0.81) and the 13/16-year
profile. This is COST REDUCTION, NOT new signal: the SIGNALS (mom / LTR / TSMOM / VIX weights) are
UNCHANGED — only the turnover / rebalance MECHANICS move.

Two parametrized levers, both leak-safe, both on the deployed lam=0.25 + VIX-ON book:

  LEVER A  band delta   : the iter-003 hysteresis no-trade band width (re-snap threshold).
  LEVER B  rebal freq   : hold the target book for `freq` trading days, refresh only on rebalance
                          days (past-only ffill of a strictly-past target row -> leak-safe).

  banded_book_freq(raw, delta, freq):
      w_tgt = gross_norm(raw)                   # unit-gross target, pre-shift (decided at close[t])
      w_tgt = stride_hold(w_tgt, freq)          # LEVER B: carry last rebalance's target forward
      held  = hysteresis_band(w_tgt, delta)     # LEVER A: iter-003 SNAP band on the (strided) tgt
      held  = held * (base_gross / held_gross)  # re-gross-norm to ~1 each bar
      w     = held.shift(1)                     # standard one-bar execution lag

IDENTITY (pre-registered): freq=1 AND delta=0.005 reproduces the iter-013 deployed banded book
bit-for-bit (stride_hold is the identity at freq=1; band is iter-003). VIX brake is the SAME outer
past-only scalar as iter-013 (unchanged, exposure-only, does not touch turnover).

Every metric is IS-only (< 2025-03-24); NO OOS number is computed (there is no --confirm path). Do
NOT tune delta / freq to OOS. The chosen cell (if any) is picked on IS net@2x subject to holding
gross ~+0.81 and +yrs >= 13 — a cost-robustness objective, not an OOS fit.

Run: uv run python analysis/portfolio/tradfi/iter_015_cost.py
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
import iter_008_vix_stop as i8  # noqa: E402
import iter_011_mom_ltr as i11  # noqa: E402
import iter_013_directional as i13  # noqa: E402
import universe_tradfi as ut  # noqa: E402

BASE_DELTA = i13.CHOSEN_DELTA  # 0.005 deployed band
LAM = i13.DEPLOYED_LAM  # 0.25 deployed directional fraction

DELTA_GRID = (0.005, 0.010, 0.015, 0.020, 0.030, 0.050)  # LEVER A sweep (0.005 = current)
FREQ_GRID = (1, 2, 5, 10)  # LEVER B sweep (1 = daily = current)


# ---------------------------------------------------------------- parametrized leak-safe build ----
def stride_hold(w_tgt: pd.DataFrame, freq: int, phase: int = 0) -> pd.DataFrame:
    """Hold the target book between rebalances: refresh only on rows where pos % freq == phase.

    Non-rebalance rows carry the LAST rebalance's target forward (ffill of a strictly-past row ->
    past-only / leak-safe). freq<=1 returns w_tgt unchanged (the daily-rebalance identity).
    """
    if freq <= 1:
        return w_tgt
    mask = (np.arange(len(w_tgt)) % freq) == (phase % freq)
    held = w_tgt.where(pd.Series(mask, index=w_tgt.index), other=np.nan)
    return held.ffill().fillna(0.0)


def banded_book_freq(raw: pd.DataFrame, delta: float, freq: int, phase: int = 0) -> pd.DataFrame:
    """Deployed weight book with BOTH levers: stride-hold the target, then the iter-003 SNAP band.

    freq=1 & delta -> equals i3.banded_book(raw, delta); freq=1 & delta=0.005 -> iter-013 deployed.
    """
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    w_tgt = raw.div(gross, axis=0).fillna(0.0)  # unit-gross target, pre-shift
    w_tgt = stride_hold(w_tgt, freq, phase)  # LEVER B
    held = i3.hysteresis_band(w_tgt, delta)  # LEVER A
    base_gross = w_tgt.abs().sum(axis=1)
    held_gross = held.abs().sum(axis=1).replace(0, np.nan)
    held = held.mul((base_gross / held_gross).fillna(0.0), axis=0)
    return held.shift(1)


def banded_net_freq(
    raw: pd.DataFrame,
    ret_fwd: pd.DataFrame,
    delta: float,
    freq: int,
    cost_side: float,
    phase: int = 0,
) -> tuple[pd.Series, pd.DataFrame]:
    """Leak-safe vol-targeted net of the two-lever book at a CUSTOM per-side cost (0=gross).

    Mirrors i3.banded_net exactly (PnL = Σ w·ret_fwd, cost on ACTUAL banded |Δw|, portfolio
    vol-target) but on the strided+banded weight book and at an arbitrary per-side cost.
    """
    w = banded_book_freq(raw, delta, freq, phase)
    pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
    cost = cost_side * (w - w.shift(1)).abs().sum(axis=1)
    net = (pnl - cost).dropna()
    return ct.vol_target(net), w


# ---- IS-only deployed metric bundle ----
def _cell(pn, ret_fwd, s_vix, delta, freq):
    """Deployed (lam=0.25 + VIX-ON) IS metrics for a (delta, freq) cell.

    Returns net@1x (6bps), net@2x (12bps), gross (cost-off), turnover/day, +positive-years — all
    with the SAME iter-008 VIX brake applied as an outer past-only scalar (exposure only).
    """
    raw = i13.combined_raw(pn, LAM)

    def _vix(net):
        return net * s_vix.reindex(net.index).fillna(1.0)

    net_g, _ = banded_net_freq(raw, ret_fwd, delta, freq, 0.0)
    net_1x, w = banded_net_freq(raw, ret_fwd, delta, freq, ct.COST_SIDE)
    net_2x, _ = banded_net_freq(raw, ret_fwd, delta, freq, 2.0 * ct.COST_SIDE)
    d1x, d2x, dg = _vix(net_1x), _vix(net_2x), _vix(net_g)
    npos, nyr = i11.n_pos_years(d1x)
    return {
        "net1x": ct.msharpe(d1x, ct.LO0, ct.OOS_CUTOFF),
        "net2x": ct.msharpe(d2x, ct.LO0, ct.OOS_CUTOFF),
        "gross": ct.msharpe(dg, ct.LO0, ct.OOS_CUTOFF),
        "turn": ct.turnover(w, ct.LO0, ct.OOS_CUTOFF),
        "npos": npos,
        "nyr": nyr,
    }


def _fmt(tag, delta, freq, r, mark=""):
    return (
        f"    {tag:<8} d={delta:<5.3f} f={freq:<2d}| n1x={r['net1x']:+.2f} n2x={r['net2x']:+.2f}"
        f" turn={r['turn']:.4f} gross={r['gross']:+.2f} +yrs={r['npos']}/{r['nyr']}{mark}"
    )


def main():
    ap = argparse.ArgumentParser()
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
    vix = i8.load_vix_close(ret_fwd.index, args.data_dir)
    s_vix = i8.vix_scale(vix)  # base=20 / floor=0.50 (iter-008 UNCHANGED)

    print("=" * 100)
    print(
        "iter-015 COST DISCIPLINE — band + rebal-freq levers on iter-013 (lam=0.25 + VIX, IS-only)"
    )
    print("=" * 100)

    # --- IDENTITY: freq=1 & delta=0.005 reproduces iter-013 deployed banded book bit-for-bit ---
    w_id = banded_book_freq(i13.combined_raw(pn, LAM), BASE_DELTA, 1)
    w_dep = i3.banded_book(i13.combined_raw(pn, LAM), BASE_DELTA)
    ident = bool(np.allclose(w_id.fillna(0.0).to_numpy(), w_dep.fillna(0.0).to_numpy(), atol=1e-15))
    base = _cell(pn, ret_fwd, s_vix, BASE_DELTA, 1)
    print(
        f"\n  IDENTITY freq=1 & delta=0.005 == iter-013 deployed: {'PASS' if ident else 'FAIL'}  "
        f"(net1x={base['net1x']:+.2f} net2x={base['net2x']:+.2f} gross={base['gross']:+.2f} "
        f"turn={base['turn']:.4f} +yrs={base['npos']}/{base['nyr']})"
    )
    print("  TARGET: net2x >= +0.50 while HOLDING gross ~+0.81 and +yrs >= 13 (cost-capture)")

    # --- LEVER A: band delta sweep (freq=1 = daily) ---
    print("\n(A) LEVER A — hysteresis band delta sweep (freq=1 daily):")
    best_a = None
    for d in DELTA_GRID:
        r = _cell(pn, ret_fwd, s_vix, d, 1)
        mark = "  <- current" if d == BASE_DELTA else ""
        ok = r["net2x"] >= 0.50 and r["gross"] >= 0.75 and r["npos"] >= 13
        if ok and (best_a is None or r["net2x"] > best_a[2]["net2x"]):
            best_a = (d, 1, r)
        print(_fmt("bandA", d, 1, r, mark + ("  [meets target]" if ok else "")))

    # --- LEVER B: rebalance frequency sweep (delta=0.005 = current band) ---
    print("\n(B) LEVER B — rebalance frequency sweep (delta=0.005 current band):")
    best_b = None
    for f in FREQ_GRID:
        r = _cell(pn, ret_fwd, s_vix, BASE_DELTA, f)
        mark = "  <- current" if f == 1 else ""
        ok = r["net2x"] >= 0.50 and r["gross"] >= 0.75 and r["npos"] >= 13
        if ok and (best_b is None or r["net2x"] > best_b[2]["net2x"]):
            best_b = (BASE_DELTA, f, r)
        print(_fmt("freqB", BASE_DELTA, f, r, mark + ("  [meets target]" if ok else "")))

    # --- JOINT: a small band x freq grid around the promising cells ---
    print("\n(C) JOINT band x freq grid (find the cost-robust corner):")
    best = None
    for d in (0.005, 0.010, 0.015, 0.020):
        for f in (1, 2, 5, 10):
            r = _cell(pn, ret_fwd, s_vix, d, f)
            ok = r["net2x"] >= 0.50 and r["gross"] >= 0.75 and r["npos"] >= 13
            # BEST = max net2x among cells HOLDING gross>=0.75 AND +yrs>=13 (cost-capture)
            if ok and (best is None or r["net2x"] > best[2]["net2x"]):
                best = (d, f, r)
            print(_fmt("joint", d, f, r, "  [meets target]" if ok else ""))

    # --- VERDICT ---
    print("\n(D) BEST cost-robust config (max net2x s.t. gross>=+0.75 AND +yrs>=13):")
    print(
        f"    baseline (d=0.005,f=1): net1x={base['net1x']:+.2f} net2x={base['net2x']:+.2f} "
        f"turn={base['turn']:.4f} gross={base['gross']:+.2f} +yrs={base['npos']}/{base['nyr']}"
    )
    if best is None:
        print("    NO cell reaches net2x>=+0.50 holding gross>=+0.75 AND +yrs>=13 — best-effort:")
        # best-effort: max net2x holding +yrs>=13 (relax gross floor to see if it is de-lever)
        allcells = []
        for d in (0.005, 0.010, 0.015, 0.020):
            for f in (1, 2, 5, 10):
                allcells.append((d, f, _cell(pn, ret_fwd, s_vix, d, f)))
        be = max((c for c in allcells if c[2]["npos"] >= 13), key=lambda c: c[2]["net2x"])
        d, f, r = be
        held = r["gross"] >= base["gross"] - 0.06
        print(_fmt("best-eff", d, f, r))
        print(
            f"    read: net2x {base['net2x']:+.2f} -> {r['net2x']:+.2f}, gross {base['gross']:+.2f}"
            f" -> {r['gross']:+.2f} "
            f"({'GROSS HELD -> cost-capture' if held else 'GROSS DROPPED -> de-lever'})"
        )
    else:
        d, f, r = best
        print(_fmt("BEST", d, f, r, "  <- CHOSEN"))
        held = r["gross"] >= base["gross"] - 0.06
        print(
            f"    read: net2x {base['net2x']:+.2f} -> {r['net2x']:+.2f} (target met), gross "
            f"{base['gross']:+.2f} -> {r['gross']:+.2f} "
            f"({'GROSS HELD -> REAL cost-capture' if held else 'GROSS DROPPED -> de-lever'})"
        )

    # --- LEAK SELF-CHECK on the two-lever build (corrupt panel + forward returns post-cutoff) ---
    d_lk, f_lk = (best[0], best[1]) if best is not None else (0.020, 5)
    raw = i13.combined_raw(pn, LAM)
    net0, _ = banded_net_freq(raw, ret_fwd, d_lk, f_lk, ct.COST_SIDE)
    cut = net0.index[len(net0) // 2]
    pn_c = {k: v.copy() for k, v in pn.items()}
    pn_c["close"].loc[pn_c["close"].index >= cut] *= -7.0
    pn_c["ret_fwd"].loc[pn_c["ret_fwd"].index >= cut] += 5.0
    net1, _ = banded_net_freq(
        i13.combined_raw(pn_c, LAM), pn_c["ret_fwd"], d_lk, f_lk, ct.COST_SIDE
    )
    common = net0.index.intersection(net1.index)
    common = common[common < cut]
    leak_ok = np.allclose(net0.loc[common].to_numpy(), net1.loc[common].to_numpy(), atol=1e-12)
    print(
        f"\n(E) future-bar leak self-check (two-lever net bit-identical pre-cut, d={d_lk:.3f} "
        f"f={f_lk}): {'PASS' if leak_ok else 'FAIL'}"
    )


if __name__ == "__main__":
    main()
