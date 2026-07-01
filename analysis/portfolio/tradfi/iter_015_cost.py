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
NOT tune delta / freq to OOS.

SELECTION (Critic-revised 2026-07-01): NOT max-net at the grid CORNER. The chosen cell is the
LEAST-AGGRESSIVE robust cell — the SMALLEST band+freq change from the iter-013 baseline
(delta=0.005, freq=1) that clears ALL FOUR IS gates:
    net@2x (12bps) >= +0.50   AND   gross(cost-off) >= +0.78   AND
    net-beta <= 0.15          AND   +positive-years >= 13.
net-beta is the realized OLS beta of the deployed (banded, 1x-cost) net on the EQUAL-WEIGHT 69-name
universe forward return (iter_013.net_beta / market_return, REUSED verbatim; VIX-off, so the
baseline cell reproduces iter-013's beta-of-record +0.12 exactly). Ties in step-distance prefer
freq=1 (no live-parity / stride-epoch risk). This maps the FULL joint grid (delta x freq, incl.
delta=0.025) and picks the minimal safe interior — it does NOT pick the aggressive corner.

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

BASE_DELTA = i13.CHOSEN_DELTA  # 0.005 deployed band (iter-013 baseline cell)
LAM = i13.DEPLOYED_LAM  # 0.25 deployed directional fraction

DELTA_GRID = (0.005, 0.010, 0.015, 0.020, 0.030, 0.050)  # LEVER A sweep (0.005 = current)
FREQ_GRID = (1, 2, 5, 10)  # LEVER B sweep (1 = daily = current)

# FULL joint grid mapped for the least-aggressive-robust selection (interior mapped incl. 0.025).
JOINT_DELTAS = (0.005, 0.010, 0.015, 0.020, 0.025)
JOINT_FREQS = (1, 2, 5, 10)

# The FOUR IS gates a cost cell must clear to be "robust" (Critic criterion of record).
GATE_N2X, GATE_GROSS, GATE_BETA, GATE_YRS = 0.50, 0.78, 0.15, 13

# DEPLOYED cost cell = the least-aggressive robust pick this script selects from the joint grid
# (asserted below to equal the data-driven choice). freq=1 = daily -> NO live-parity/stride-epoch
# risk; delta 0.005 -> 0.010 is a single band-width step off the iter-013 baseline.
CHOSEN_DELTA = 0.010
CHOSEN_FREQ = 1


def _clears(r: dict) -> bool:
    """A cell is robust iff it clears ALL FOUR IS gates (net@2x / gross / net-beta / +yrs)."""
    return (
        r["net2x"] >= GATE_N2X
        and r["gross"] >= GATE_GROSS
        and r["beta"] <= GATE_BETA
        and r["npos"] >= GATE_YRS
    )


def _aggressiveness(delta: float, freq: int) -> tuple:
    """Rank key: SMALLER = less aggressive. Grid-step distance from the (0.005, 1) baseline, then
    a freq=1 preference (avoids the freq>1 stride live-parity risk), then delta-step then freq."""
    di = {d: i for i, d in enumerate(JOINT_DELTAS)}
    fi = {f: i for i, f in enumerate(JOINT_FREQS)}
    return (di[delta] + fi[freq], 0 if freq == 1 else 1, di[delta], fi[freq])


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
def _deployed_net1x(pn, ret_fwd, s_vix, delta, freq):
    """The deployed (lam=0.25, VIX-ON, 1x-cost) net-return series for a (delta, freq) cell.

    Used for the per-year table on the CHOSEN cell — same object whose monthly Sharpe drives +yrs.
    """
    raw = i13.combined_raw(pn, LAM)
    net_1x, _ = banded_net_freq(raw, ret_fwd, delta, freq, ct.COST_SIDE)
    return net_1x * s_vix.reindex(net_1x.index).fillna(1.0)


def _cell(pn, ret_fwd, s_vix, mkt, delta, freq):
    """Deployed (lam=0.25 + VIX-ON) IS metrics for a (delta, freq) cell.

    Returns net@1x (6bps), net@2x (12bps), gross (cost-off), turnover/day, net-beta, +pos-years.
    The Sharpes / turnover carry the iter-008 VIX brake (outer past-only scalar, exposure only).
    net-beta is the REALIZED OLS beta of the deployed 1x-cost net on the EW-69 universe forward
    return (iter_013.net_beta, REUSED verbatim). It is measured VIX-OFF — the VIX brake is an
    unchanged outer scalar and moves beta by <0.001 — so the baseline cell reproduces iter-013's
    beta-of-record +0.12 exactly and the levers' effect on the book's market tilt is isolated.
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
        "beta": i13.net_beta(
            net_1x, mkt
        ),  # VIX-off realized book beta -> reproduces iter-013 +0.12
        "npos": npos,
        "nyr": nyr,
    }


def _fmt(tag, delta, freq, r, mark=""):
    return (
        f"    {tag:<8} d={delta:<5.3f} f={freq:<2d}| n1x={r['net1x']:+.2f} n2x={r['net2x']:+.2f}"
        f" turn={r['turn']:.4f} gross={r['gross']:+.2f} beta={r['beta']:+.3f}"
        f" +yrs={r['npos']}/{r['nyr']}{mark}"
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
    mkt = i13.market_return(pn)  # EW-69 universe forward return = PIT market proxy for net-beta
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
    base = _cell(pn, ret_fwd, s_vix, mkt, BASE_DELTA, 1)
    print(
        f"\n  IDENTITY freq=1 & delta=0.005 == iter-013 deployed: {'PASS' if ident else 'FAIL'}  "
        f"(net1x={base['net1x']:+.2f} net2x={base['net2x']:+.2f} gross={base['gross']:+.2f} "
        f"turn={base['turn']:.4f} beta={base['beta']:+.3f} +yrs={base['npos']}/{base['nyr']})"
    )
    print(
        f"  GATES (least-aggressive-robust): net2x>=+{GATE_N2X:.2f} AND gross>=+{GATE_GROSS:.2f} "
        f"AND net-beta<={GATE_BETA:.2f} AND +yrs>={GATE_YRS}"
    )

    # --- LEVER A: band delta sweep (freq=1 = daily) ---
    print("\n(A) LEVER A — hysteresis band delta sweep (freq=1 daily):")
    for d in DELTA_GRID:
        r = _cell(pn, ret_fwd, s_vix, mkt, d, 1)
        mark = "  <- current" if d == BASE_DELTA else ""
        print(_fmt("bandA", d, 1, r, mark + ("  [clears ALL]" if _clears(r) else "")))

    # --- LEVER B: rebalance frequency sweep (delta=0.005 = current band) ---
    print("\n(B) LEVER B — rebalance frequency sweep (delta=0.005 current band):")
    for f in FREQ_GRID:
        r = _cell(pn, ret_fwd, s_vix, mkt, BASE_DELTA, f)
        mark = "  <- current" if f == 1 else ""
        print(_fmt("freqB", BASE_DELTA, f, r, mark + ("  [clears ALL]" if _clears(r) else "")))

    # --- (C) FULL JOINT grid (delta x freq, incl. delta=0.025) — net-beta on EVERY cell ---
    print(
        "\n(C) FULL JOINT band x freq grid — net@1x/net@2x/turn/gross/net-beta/+yrs (every cell):"
    )
    grid = {}
    for d in JOINT_DELTAS:
        for f in JOINT_FREQS:
            r = _cell(pn, ret_fwd, s_vix, mkt, d, f)
            grid[(d, f)] = r
            print(_fmt("joint", d, f, r, "  [clears ALL]" if _clears(r) else ""))

    # --- (D) LEAST-AGGRESSIVE ROBUST pick: min step-distance from baseline clearing ALL four gates
    print(
        "\n(D) LEAST-AGGRESSIVE ROBUST cell (smallest band+freq change clearing ALL four gates; "
        "ties prefer freq=1):"
    )
    print(
        f"    baseline (d=0.005,f=1): net1x={base['net1x']:+.2f} net2x={base['net2x']:+.2f} "
        f"turn={base['turn']:.4f} gross={base['gross']:+.2f} beta={base['beta']:+.3f} "
        f"+yrs={base['npos']}/{base['nyr']}"
    )
    robust = sorted((k for k, r in grid.items() if _clears(r)), key=lambda k: _aggressiveness(*k))
    if not robust:
        print("    NO cell clears all four gates — no non-corner robust cell exists on this grid.")
        chosen = None
    else:
        chosen = robust[0]
        d, f = chosen
        r = grid[chosen]
        print(_fmt("CHOSEN", d, f, r, "  <- LEAST-AGGRESSIVE ROBUST"))
        held = r["gross"] >= base["gross"] - 0.06
        print(
            f"    read: net2x {base['net2x']:+.2f} -> {r['net2x']:+.2f} (>=+0.50 robust), gross "
            f"{base['gross']:+.2f} -> {r['gross']:+.2f} "
            f"({'HELD -> REAL cost-capture' if held else 'DROPPED -> de-lever'}), net-beta "
            f"{base['beta']:+.3f} -> {r['beta']:+.3f} "
            f"({'<=0.15 controlled' if r['beta'] <= GATE_BETA else '>0.15 BREACH'})"
        )
        # why the aggressive corner is REJECTED (the old headline; never net-beta-checked)
        corner = grid[(0.020, 10)]
        print(
            f"    (rejected corner d=0.020,f=10: net2x={corner['net2x']:+.2f} "
            f"gross={corner['gross']:+.2f} beta={corner['beta']:+.3f} "
            f"+yrs={corner['npos']}/{corner['nyr']} -> "
            f"{'beta>0.15 FAILS the criterion' if corner['beta'] > GATE_BETA else 'ok'})"
        )
        # self-consistency: the pinned deployed constants MUST equal the data-driven pick
        assert chosen == (CHOSEN_DELTA, CHOSEN_FREQ), (
            f"pinned deployed cell {(CHOSEN_DELTA, CHOSEN_FREQ)} != data-driven pick {chosen}"
        )

    # --- (E) PER-YEAR table for the CHOSEN cell vs iter-013 baseline (flag any sign flip) ---
    if chosen is not None:
        d, f = chosen
        y_base = i11.year_table(_deployed_net1x(pn, ret_fwd, s_vix, BASE_DELTA, 1))
        y_ch = i11.year_table(_deployed_net1x(pn, ret_fwd, s_vix, d, f))
        print(
            f"\n(E) PER-YEAR monthly-Sharpe — iter-013 (d=0.005,f=1) -> CHOSEN (d={d:.3f},f={f}) "
            "(* = sign flip):"
        )
        for yr in sorted(y_ch):
            a, b = y_base[yr][0], y_ch[yr][0]
            flip = "  * FLIP" if (a > 0) != (b > 0) else ""
            print(f"      {yr}: {a:+.2f} -> {b:+.2f}{flip}")
        na = sum(1 for s, _ in y_base.values() if s > 0)
        nb = sum(1 for s, _ in y_ch.values() if s > 0)
        flips = sum(1 for yr in y_ch if (y_base[yr][0] > 0) != (y_ch[yr][0] > 0))
        print(
            f"      +yrs: iter-013={na}/{len(y_base)} -> CHOSEN={nb}/{len(y_ch)}  "
            f"(sign flips: {flips} -> {'no noise year-count crossing' if flips == 0 else 'CHECK'})"
        )

    # --- (F) LEAK SELF-CHECK pinned to the CHOSEN deployed cell (corrupt panel + fwd returns) ---
    d_lk, f_lk = chosen if chosen is not None else (CHOSEN_DELTA, CHOSEN_FREQ)
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
        f"\n(F) future-bar leak self-check (deployed net bit-identical pre-cut, d={d_lk:.3f} "
        f"f={f_lk}): {'PASS' if leak_ok else 'FAIL'}"
    )


if __name__ == "__main__":
    main()
