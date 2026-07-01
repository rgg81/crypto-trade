"""iter-015 COST TEARDOWN — where is the ~0.094/day turnover of the iter-013 book spent?

The CONFIRMED baseline (iter-013 DEPLOYED, lam=0.25, band delta=0.005, VIX ON) has a real GROSS edge
(+0.81 cost-off) that turnover eats to net +0.61 @6bps -> +0.42 @12bps. This teardown DECOMPOSES the
deployed banded turnover to find WHERE the cost is spent, so the next levers (band width, rebal
frequency) can be aimed. IS-ONLY (< 2025-03-24); NO OOS number is computed (turnover + gross are
signal-mechanics, not OOS-tuned). Turnover is VIX-INDEPENDENT (the VIX brake is an outer scalar on
the net return, it does NOT touch the unit-gross weight book), so no VIX is loaded here.

The deployed (unbanded) target book is an EXACT additive blend of three unit-gross sleeves:

    mom  = gross_norm( crash_braked_multi_horizon )   # fast+mid+slow horizons + bear-gate
    ltr  = gross_norm( 3y-1y long-term reversal )      # SLOW value proxy
    dirn = gross_norm( sign(12m ret)/rvol )            # TSMOM directional sleeve
    neu  = (mom + 0.5*ltr) / ||mom + 0.5*ltr||_1       # the iter-011 neutral book
    c    = 0.75*neu + 0.25*dirn                        # = comp_MOM + comp_LTR + comp_TSMOM (exact)
    w_tgt= c / ||c||_1                                 # deployed target book (pre-band, pre-shift)

so w_tgt splits EXACTLY into three sleeve sub-books (wc_MOM + wc_LTR + wc_TSMOM = w_tgt), and the
per-sleeve daily |Δ(sub-book)| is a clean attribution of which sleeve MOVES the book (churns).

Run: uv run python analysis/portfolio/tradfi/cost_teardown.py
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
import iter_011_mom_ltr as i11  # noqa: E402
import iter_013_directional as i13  # noqa: E402
import universe_tradfi as ut  # noqa: E402

DELTA = i13.CHOSEN_DELTA  # 0.005 deployed band
LAM = i13.DEPLOYED_LAM  # 0.25 deployed directional fraction
W_LTR = i11.W_LTR  # 0.5 neutral-book LTR weight


def _turn(w: pd.DataFrame) -> float:
    """Mean per-day gross turnover Σ|Δw| over the IS window (matches ct.turnover)."""
    return ct.turnover(w, ct.LO0, ct.OOS_CUTOFF)


def _unbanded_book(raw: pd.DataFrame) -> pd.DataFrame:
    """Gross-normed target book, one-bar execution lag, NO band (delta=0 pipeline)."""
    g = raw.abs().sum(axis=1).replace(0, np.nan)
    return raw.div(g, axis=0).fillna(0.0).shift(1)


def _sleeve_components(pn):
    """The EXACT additive split of the deployed unbanded target book into 3 sleeve sub-books.

    Returns (w_tgt, wc_mom, wc_ltr, wc_tsmom) all lagged one bar; the three sub-books sum to w_tgt.
    """
    mom = i11.mom_sleeve(pn)  # gross_norm(crash-braked multi-horizon)
    ltr = i11.ltr_sleeve(pn)  # gross_norm(3y-1y reversal)
    dirn = i13.tsmom_sleeve(pn)  # gross_norm(sign(12m)/rvol)
    g_neu = (mom.add(ltr.mul(W_LTR), fill_value=0.0)).abs().sum(axis=1).replace(0, np.nan)
    comp_mom = mom.mul((1.0 - LAM), axis=0).div(g_neu, axis=0)  # 0.75 * mom / G
    comp_ltr = ltr.mul((1.0 - LAM) * W_LTR, axis=0).div(g_neu, axis=0)  # 0.375 * ltr / G
    comp_tsmom = dirn.mul(LAM)  # 0.25 * dirn
    combined = comp_mom.add(comp_ltr, fill_value=0.0).add(comp_tsmom, fill_value=0.0)
    h = combined.abs().sum(axis=1).replace(0, np.nan)
    w_tgt = combined.div(h, axis=0).fillna(0.0).shift(1)
    wc_mom = comp_mom.div(h, axis=0).fillna(0.0).shift(1)
    wc_ltr = comp_ltr.div(h, axis=0).fillna(0.0).shift(1)
    wc_tsmom = comp_tsmom.div(h, axis=0).fillna(0.0).shift(1)
    return w_tgt, wc_mom, wc_ltr, wc_tsmom


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

    print("=" * 100)
    print(
        "iter-015 COST TEARDOWN — iter-013 DEPLOYED book (lam=0.25, band=0.005); IS-only, VIX-indep"
    )
    print("=" * 100)

    # ---- (A) total + band effect ----
    raw_dep = i13.combined_raw(pn, LAM)
    w_banded = i3.banded_book(raw_dep, DELTA)
    w_unband = _unbanded_book(raw_dep)
    t_band = _turn(w_banded)
    t_unband = _turn(w_unband)
    ann1 = t_band * ct.COST_SIDE * ct.CANDLES_PER_YEAR * 100.0
    ann2 = t_band * (2 * ct.COST_SIDE) * ct.CANDLES_PER_YEAR * 100.0
    print("\n(A) TOTAL turnover & the band's existing reduction (IS mean Σ|Δw|/day):")
    print(f"    deployed banded (delta={DELTA:.3f}) : {t_band:.4f}/day")
    print(f"    unbanded target  (delta=0)          : {t_unband:.4f}/day")
    print(
        f"    -> band already removes {(1 - t_band / t_unband) * 100:.0f}% of raw target churn; "
        f"turnover-implied annual cost = {ann1:.1f}% @6bps / {ann2:.1f}% @12bps"
    )

    # ---- (B) per-sleeve standalone ----
    print("\n(B) PER-SLEEVE standalone churn (each unit-gross sleeve through the SAME pipeline):")
    print(f"    {'sleeve':<22} {'unbanded':>9} {'banded':>8}  {'band-cut':>8}")
    sleeves = {
        "MOM (crash-braked MH)": i11.mom_sleeve(pn),
        "LTR (3y-1y reversal)": i11.ltr_sleeve(pn),
        "TSMOM (sign 12m/rvol)": i13.tsmom_sleeve(pn),
    }
    for name, s in sleeves.items():
        tu = _turn(_unbanded_book(s))
        tb = _turn(i3.banded_book(s, DELTA))
        print(f"    {name:<22} {tu:>9.4f} {tb:>8.4f}  {(1 - tb / tu) * 100:>7.0f}%")

    # ---- (C) within-momentum horizons ----
    print("\n(C) WITHIN-MOMENTUM horizon decomposition (standalone, same pipeline):")
    print(f"    {'component':<26} {'unbanded':>9} {'banded':>8}")
    mom_parts = {
        "sleeve 3-1m (63/21) FAST": i5.sleeve(pn, 63),
        "sleeve 6-1m (126/21) MID": i5.sleeve(pn, 126),
        "sleeve 12-1m (252/21) SLOW": i5.sleeve(pn, 252),
        "EW blend {3,6,12} no-gate": i5.mh_raw(pn),
        "crash-braked (with bear-gate)": i6.crash_braked_raw(pn),
    }
    for name, s in mom_parts.items():
        tu = _turn(_unbanded_book(s))
        tb = _turn(i3.banded_book(s, DELTA))
        print(f"    {name:<26} {tu:>9.4f} {tb:>8.4f}")

    # ---- (D) exact sub-book attribution ----
    w_tgt, wc_mom, wc_ltr, wc_tsmom = _sleeve_components(pn)
    ident = float(
        np.nanmax(
            np.abs(
                (wc_mom.add(wc_ltr, fill_value=0.0).add(wc_tsmom, fill_value=0.0)).to_numpy()
                - w_tgt.to_numpy()
            )
        )
    )
    churn = {"MOM": _turn(wc_mom), "LTR": _turn(wc_ltr), "TSMOM": _turn(wc_tsmom)}
    tot = sum(churn.values())
    print("\n(D) EXACT additive sub-book attribution of the deployed UNBANDED target book:")
    print(f"    (sub-books sum to w_tgt; max|resid|={ident:.1e})  total unbanded={t_unband:.4f}")
    print(f"    {'sleeve':<8} {'Σ|Δsub|/day':>12} {'share of book movement':>24}")
    for k, v in churn.items():
        print(f"    {k:<8} {v:>12.4f} {v / tot * 100:>22.0f}%")

    # ---- (E) small/marginal trades ----
    dw = (w_banded - w_banded.shift(1)).abs()
    dw_is = dw[dw.index < ct.OOS_CUTOFF]
    vals = dw_is.to_numpy().ravel()
    vals = vals[vals > 1e-12]  # per-name trade EVENTS (non-zero |Δw|)
    total_flow = vals.sum()
    print(
        "\n(E) SMALL/MARGINAL trade distribution (per-name |Δw| events, deployed banded book, IS):"
    )
    print(f"    {'threshold τ':>12} {'% of events < τ':>16} {'% of turnover < τ':>18}")
    for tau in (0.0002, 0.0005, 0.001, 0.002, 0.005):
        below = vals < tau
        pct_events = below.mean() * 100
        pct_flow = vals[below].sum() / total_flow * 100
        print(f"    {tau:>12.4f} {pct_events:>15.0f}% {pct_flow:>17.0f}%")
    print(f"    (median trade size={np.median(vals):.4f}; mean={vals.mean():.4f})")

    # ---- (F) leak self-check + read ----
    net0, _ = i3.banded_net(raw_dep, ret_fwd, DELTA)
    cut = net0.index[len(net0) // 2]
    pn_c = {k: v.copy() for k, v in pn.items()}
    pn_c["close"].loc[pn_c["close"].index >= cut] *= -7.0
    pn_c["ret_fwd"].loc[pn_c["ret_fwd"].index >= cut] += 5.0
    net1, _ = i3.banded_net(i13.combined_raw(pn_c, LAM), pn_c["ret_fwd"], DELTA)
    common = net0.index.intersection(net1.index)
    common = common[common < cut]
    leak_ok = np.allclose(net0.loc[common].to_numpy(), net1.loc[common].to_numpy(), atol=1e-12)
    print(
        f"\n(F) future-bar leak self-check (banded net bit-identical pre-cut): "
        f"{'PASS' if leak_ok else 'FAIL'}"
    )


if __name__ == "__main__":
    main()
