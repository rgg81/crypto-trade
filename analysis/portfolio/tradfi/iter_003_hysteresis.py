"""iter-003 — causal HYSTERESIS no-trade band on iter-002's sector-relative signal.

ONE change vs iter-002: add a per-name no-trade BAND on the gross-normalized target weight book.
The SECTOR-RELATIVE SIGNAL is unchanged (`raw = sector_neutralize(mom/rvol)` from iter-002).
iter-002 has a real GROSS edge (IS_Sharpe +0.26 cost-off) that turnover eats down to +0.08 net —
cost drag +0.18 from ~0.084/day turnover (~21x/yr). The band re-trades a name only when its target
weight has moved more than delta from the currently-held weight; otherwise it CARRIES the held
weight. Fewer re-trades -> lower cost term -> (hopefully) more of the +0.26 gross survives into net.

Mechanism (the proven crypto iter_020 / metals iter_011 SNAP band, ported to net_from_raw):

    w_tgt   = gross_normalize(raw)                    # target book decided at close[t] (pre-shift)
    w_held[t,i] = w_held[t-1,i]  if |w_tgt[t,i] - w_held[t-1,i]| <= delta  else  w_tgt[t,i]
    w_held  = w_held * (base_gross / held_gross)      # re-gross-normalize to ~1 each bar
    w       = w_held.shift(1)                         # SAME one-bar execution lag as net_from_raw
    net     = vol_target( Σ w·ret_fwd  -  COST·Σ|Δw| )  # cost on the ACTUAL banded turnover

The band recursion is STRICTLY CAUSAL: w_held[t] reads only w_tgt[<=t] (all past-priced) and
w_held[t-1]. No information from candle t's realized return enters the held book. The `.shift(1)`
then gives the standard execution lag, so net[t<cut] is bit-identical when inputs after `cut` are
corrupted (see test_iter003_banded_future_bar_no_leak).

delta = 0 reproduces iter-002 EXACTLY (the band is the identity; renorm is a no-op; net is
bit-identical to net_from_raw). This is the pre-registered identity check.

This is a STRUCTURAL parameter proven by an IS sweep (delta swept on robustness, not OOS-tuned).
OOS stays HIDDEN (perf_line reveal_oos=False) unless --confirm (CONFIRMATION only). The sweep is
ALWAYS IS-only — no OOS number is computed without --confirm.
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
import iter_002_sector_rel as i2  # noqa: E402
import universe_tradfi as ut  # noqa: E402

# Band sizes swept (per-name absolute target-weight move threshold). 0.0 is the iter-002 identity.
DELTA_GRID = [0.0, 0.005, 0.01, 0.02, 0.03]
# Chosen delta: IS-robust pick from the sweep (band reduces turnover AND holds/improves net Sharpe).
CHOSEN_DELTA = 0.005


def hysteresis_band(w_tgt: pd.DataFrame, delta: float) -> pd.DataFrame:
    """Per-name SNAP no-trade band (strictly causal, path-dependent).

    held[t,i] = held[t-1,i] if |w_tgt[t,i] - held[t-1,i]| <= delta else w_tgt[t,i]. delta<=0 returns
    w_tgt unchanged (bit-identical identity). The recursion only reads w_tgt[<=t] and held[t-1] — no
    forward leak.
    """
    if delta <= 0.0:
        return w_tgt.copy()
    v = w_tgt.fillna(0.0).to_numpy()
    out = np.empty_like(v)
    prev = v[0].copy()
    out[0] = prev
    for t in range(1, len(v)):
        row = v[t]
        moved = np.abs(row - prev) > delta
        prev = np.where(moved, row, prev)
        out[t] = prev
    return pd.DataFrame(out, index=w_tgt.index, columns=w_tgt.columns)


def banded_book(raw: pd.DataFrame, delta: float) -> pd.DataFrame:
    """Gross-normalize raw -> apply causal band -> re-gross-normalize -> .shift(1) lag.

    Returns the LAGGED held weight book `w` (same role/shape as net_from_raw's `w`). At delta=0 this
    equals net_from_raw's `w` bit-for-bit.
    """
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    w_tgt = raw.div(gross, axis=0).fillna(0.0)  # target book, gross-normalized, PRE-shift
    held = hysteresis_band(w_tgt, delta)
    base_gross = w_tgt.abs().sum(axis=1)  # 1.0 on active rows, 0.0 on warm-up
    held_gross = held.abs().sum(axis=1).replace(0, np.nan)
    held = held.mul((base_gross / held_gross).fillna(0.0), axis=0)  # renorm gross to ~1 each bar
    return held.shift(1)


def banded_net(
    raw: pd.DataFrame, ret_fwd: pd.DataFrame, delta: float, *, cost_on: bool = True
) -> tuple[pd.Series, pd.DataFrame]:
    """Leak-safe vol-targeted net of the banded book + the lagged held book.

    Mirrors core_tradfi.net_from_raw exactly, but on the post-band held weights: PnL = Σ w·ret_fwd,
    taker cost on the ACTUAL banded |Δw| turnover, then portfolio vol-target. `cost_on=False` gives
    the gross (cost-off) net used to attribute net lift to cost-saving vs signal change.
    """
    w = banded_book(raw, delta)
    pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
    cost = ct.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1) if cost_on else 0.0
    net = (pnl - cost).dropna()
    return ct.vol_target(net), w


def _sector_residual(w: pd.DataFrame) -> float:
    """Max per-sector |net dollar| / gross over IS active rows (0 = perfectly sector-neutral)."""
    w_is = w[w.index < ct.OOS_CUTOFF]
    gross = w_is.abs().sum(axis=1)
    live = gross > 1e-9
    if not live.any():
        return float("nan")
    sectors: dict[str, list[str]] = {}
    for c in w.columns:
        sectors.setdefault(ut.SECTOR_MAP.get(c, f"__{c}"), []).append(c)
    worst = 0.0
    for cols in sectors.values():
        if len(cols) < 2:  # singleton sectors are forced to 0 already
            continue
        resid = w_is.loc[live, cols].sum(axis=1).abs() / gross[live]
        worst = max(worst, float(resid.max()))
    return worst


def _sweep_row(raw, ret_fwd, delta, base_turn):
    """One IS-only sweep row: (net, gross, drag, turnover, maxDD, regimes, turn-vs-base%)."""
    net, w = banded_net(raw, ret_fwd, delta, cost_on=True)
    gnet, _ = banded_net(raw, ret_fwd, delta, cost_on=False)
    sh_net = ct.msharpe(net, ct.LO0, ct.OOS_CUTOFF)
    sh_gross = ct.msharpe(gnet, ct.LO0, ct.OOS_CUTOFF)
    turn = ct.turnover(w, ct.LO0, ct.OOS_CUTOFF)
    mdd = ct.maxdd(ct.is_only(net)) * 100
    reg = ct.regime_sharpe(ct.is_only(net))
    tpc = "" if base_turn is None else f" ({(turn / base_turn - 1) * 100:+.0f}%)"
    return {
        "net": sh_net,
        "gross": sh_gross,
        "drag": sh_gross - sh_net,
        "turn": turn,
        "mdd": mdd,
        "reg": reg,
        "tpc": tpc,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--delta", type=float, default=CHOSEN_DELTA, help="chosen no-trade band size")
    ap.add_argument("--confirm", action="store_true", help="reveal OOS (CONFIRMATION only)")
    ap.add_argument("--data-dir", default=None)
    args = ap.parse_args()

    base = Path(args.data_dir) if args.data_dir else ct._ROOT / "data"
    syms = sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)
    coins = ct.load_tradfi(syms, args.data_dir)
    if not coins:
        print("No ingested tradfi data found. Run ingest_dukascopy_stocks.py first.")
        return

    pn = ct.panels(coins)
    raw = i2.sector_rel_raw(pn)  # iter-002 sector-relative SIGNAL — UNCHANGED
    ret_fwd = pn["ret_fwd"]

    # --- IDENTITY: delta=0 must reproduce iter-002 net bit-for-bit ---
    net0_band, _ = banded_net(raw, ret_fwd, 0.0)
    net0_i2, _ = ct.net_from_raw(raw, ret_fwd)
    ident = bool(np.allclose(net0_band.to_numpy(), net0_i2.reindex(net0_band.index).to_numpy()))
    print("=" * 96)
    print("iter-003 — causal HYSTERESIS band on iter-002 sector-relative momentum (IS-only)")
    print("=" * 96)
    print(
        f"  IDENTITY delta=0 reproduces iter-002: {'PASS' if ident else 'FAIL'}  "
        f"(IS_Sharpe={ct.msharpe(net0_band, ct.LO0, ct.OOS_CUTOFF):+.2f}, iter-002 target +0.08)"
    )

    # --- delta sweep (IS-only; never computes OOS) ---
    print(
        f"\n  {'delta':>6} {'netSh':>6} {'grossSh':>8} {'drag':>6} {'turn/day':>9} {'maxDD':>7}  "
        f"{'bull':>5} {'bear':>5} {'chop':>5}   turn-vs-iter002"
    )
    base_turn = None
    for delta in DELTA_GRID:
        r = _sweep_row(raw, ret_fwd, delta, base_turn)
        if delta == 0.0:
            base_turn = r["turn"]
        tag = "  <- iter-002" if delta == 0.0 else ("  <- CHOSEN" if delta == args.delta else "")
        print(
            f"  {delta:>6.3f} {r['net']:>+6.2f} {r['gross']:>+8.2f} {r['drag']:>+6.2f} "
            f"{r['turn']:>9.4f} {r['mdd']:>6.1f}% "
            f"{r['reg']['bull']:>+5.2f} {r['reg']['bear']:>+5.2f} {r['reg']['chop']:>+5.2f}"
            f"{r['tpc']}{tag}"
        )

    # --- chosen-delta headline ---
    d = args.delta
    net, w = banded_net(raw, ret_fwd, d)
    gnet, _ = banded_net(raw, ret_fwd, d, cost_on=False)
    print(f"\n  CHOSEN delta={d:.3f}")
    print(ct.perf_line(f"iter-003 d={d:.3f}", net, reveal_oos=args.confirm))
    print(f"  regimes (IS): {ct.regime_sharpe(ct.is_only(net))}")
    print(
        f"  turnover/day: {ct.turnover(w, ct.LO0, ct.OOS_CUTOFF):.4f}  "
        f"(iter-002 {base_turn:.4f}; "
        f"{(ct.turnover(w, ct.LO0, ct.OOS_CUTOFF) / base_turn - 1) * 100:+.0f}%)"
    )
    sh_net = ct.msharpe(net, ct.LO0, ct.OOS_CUTOFF)
    sh_gross = ct.msharpe(gnet, ct.LO0, ct.OOS_CUTOFF)
    print(
        f"  diag: gross(cost-off) IS_Sharpe={sh_gross:+.2f}  net={sh_net:+.2f}  "
        f"(cost drag {sh_gross - sh_net:+.2f}; iter-002 gross +0.26 / net +0.08 / drag +0.18)"
    )
    print(
        f"  sector-neutrality residual (max |sector$|/gross, IS active): {_sector_residual(w):.1e} "
        f" (0 = perfectly per-sector-neutral; band-induced drift)"
    )


if __name__ == "__main__":
    main()
