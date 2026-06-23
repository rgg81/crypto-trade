"""Verify the iter-v2-006 finding: standalone XS-mom (8h, rank 21-40) OOS +1.20.

Cost was the assassin of every prior signal, so before treating this as the v2 candidate, confirm:
  (1) cost-robustness — OOS survives 2x-taker AND slip_pessimistic (turn is only 0.185, should hold)
  (2) not a single-window fluke — OOS sub-windows 2025-03..12 vs 2026
  (3) lookback-robustness — the OOS edge is not a knife-edge in L (L in {42,63,84,126,168})
  (4) dollar-neutrality + turnover sanity
OOS is REVEALED here (this is the confirmation of the pre-identified candidate).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
os.chdir(_ROOT)
sys.path.insert(0, str(_ROOT / "analysis"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from portfolio_v2 import engine_v2 as e2  # noqa: E402
from portfolio_v2 import universe_v2 as uv  # noqa: E402
from portfolio_v2.diag_v2_001 import per_year_sharpe, slip_pessimistic  # noqa: E402
from portfolio_v2.engine_v2 import _xsmom, build_panel  # noqa: E402

OOS = e2.OOS_CUTOFF
W1_HI = pd.Timestamp("2026-01-01")


def stats(net):
    eq = (1 + net).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    oos = net[net.index >= OOS]
    odd = float(((1 + oos).cumprod() / (1 + oos).cumprod().cummax() - 1).min()) if len(oos) else 0.0
    return {
        "IS": e2.msharpe(net, e2.LO0, OOS),
        "OOS": e2.msharpe(net, OOS, e2.HI1),
        "OOS_25": e2.msharpe(net, OOS, W1_HI),
        "OOS_26": e2.msharpe(net, W1_HI, e2.HI1),
        "maxDD": dd * 100,
        "oosDD": odd * 100,
    }


def main():
    pool = uv.load_pool_pit()
    panel = build_panel(pool)

    def sig_for(lb):
        elig = (
            uv.eligibility(pool, 20, 40, 168)
            .reindex(index=panel["opens"].index, columns=panel["cols"])
            .fillna(False)
        )
        xs, _ = _xsmom(panel["close"], elig, lb)
        return xs.div(xs.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)

    def run(sig, **kw):
        return e2.run_book_from_signal(
            pool, sig, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=e2.default_slip_bps, **kw
        )

    print("=" * 96)
    print("VERIFY — standalone XS-mom 8h, rank 21-40 (OOS revealed)")
    print("=" * 96)

    sig = sig_for(84)
    print("\n[1] cost-robustness (L=84):")
    for lbl, kw, fn in (
        ("default", {}, None),
        ("2x-taker", {"cost_mult": 2.0}, None),
        ("2x-slip", {"slip_mult": 2.0}, None),
        ("pessimistic", {}, slip_pessimistic),
    ):
        res = (
            run(sig, **kw)
            if fn is None
            else e2.run_book_from_signal(
                pool, sig, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=fn
            )
        )
        s = stats(res["net"])
        print(
            f"  {lbl:14} IS={s['IS']:+.2f} OOS={s['OOS']:+.2f} "
            f"[2025={s['OOS_25']:+.2f} 2026={s['OOS_26']:+.2f}] "
            f"maxDD={s['maxDD']:.0f}% oosDD={s['oosDD']:.0f}% turn={res['turnover']:.3f}"
        )

    print("\n[2] lookback-robustness (default cost) — OOS must not be a knife-edge in L:")
    for lb in (42, 63, 84, 126, 168):
        res = run(sig_for(lb))
        s = stats(res["net"])
        print(
            f"  L={lb:3d}  IS={s['IS']:+.2f} LATE n/a  OOS={s['OOS']:+.2f} "
            f"[2025={s['OOS_25']:+.2f} 2026={s['OOS_26']:+.2f}]  turn={res['turnover']:.3f}"
        )

    print("\n[3] per-year (L=84):", per_year_sharpe(run(sig)["net"]))
    # dollar-neutrality of the held book
    res = run(sig)
    w = res["held_w"]
    print(f"[4] held-book gross long vs short balance: max|Σw| over candles = "
          f"{float(w.sum(axis=1).abs().max()):.3f} (engine-inherent); "
          f"signal max|Σ| = {float(sig.sum(axis=1).abs().max()):.2e}")


if __name__ == "__main__":
    main()
