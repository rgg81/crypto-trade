"""portfolio-iteration-v2 iter-v2-006 — REBALANCE FREQUENCY (8h vs weekly vs monthly).

User idea: cost/turnover has been the binding constraint (killed the XS-mom blend, the ML, cost-stress).
The engine rebalances every 8h candle. A weekly/monthly rebalance cuts turnover ~5-20x and damps the
whipsaw that killed routing. Test whether lower-frequency rebalancing rescues the cost-fragile but
LATE-alive XS-mom signal (and how it affects the trend book).

Approximation (EXPLORATION-grade): hold the SIGNAL piecewise-constant between rebalance dates (ffill
from the first candle of each ISO week / month), then run the normal pipeline. Turnover then concentrates
on rebalance dates. (A clean live version would hold target WEIGHTS; the band absorbs the small per-candle
/rvol drift here. If promising, do the exact-weight-hold version for CONFIRMATION.)

Run:  uv run python analysis/portfolio_v2/iter_v2_006_rebal.py [--reveal]
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
from portfolio_v2.engine_v2 import _signals, _xsmom, build_panel  # noqa: E402

REVEAL = "--reveal" in sys.argv
EARLY_LO, EARLY_HI = pd.Timestamp("2021-01-01"), pd.Timestamp("2024-01-01")
LATE_LO, LATE_HI = pd.Timestamp("2024-01-01"), e2.OOS_CUTOFF


def era(net):
    return e2.msharpe(net, EARLY_LO, EARLY_HI), e2.msharpe(net, LATE_LO, LATE_HI)


def _norm(sig):
    return sig.div(sig.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)


def resample_signal(sig: pd.DataFrame, freq: str | None) -> pd.DataFrame:
    """Hold the signal piecewise-constant: update only on the first candle of each period (W/M)."""
    if freq is None:
        return sig
    per = pd.Series(sig.index.to_period(freq), index=sig.index)
    is_first = per != per.shift(1)
    return sig.loc[is_first].reindex(sig.index).ffill().fillna(0.0)


def line(label, res, *, show_oos=False):
    net = res["net"]
    e_, l_ = era(net)
    is_ = e2.msharpe(net, e2.LO0, e2.OOS_CUTOFF)
    oos = f"  OOS={e2.msharpe(net, e2.OOS_CUTOFF, e2.HI1):+.2f}" if (show_oos and REVEAL) else ""
    print(f"  {label:30} IS={is_:+.2f} EARLY={e_:+.2f} LATE={l_:+.2f} turn={res['turnover']:.3f}{oos}")
    print(f"     per-year={per_year_sharpe(net)}")


def main():
    print("=" * 100)
    print("iter-v2-006 — REBALANCE FREQUENCY (8h / weekly / monthly), rank 21-40 (OOS hidden)")
    print("=" * 100)
    pool = uv.load_pool_pit()
    panel = build_panel(pool)
    sig = _signals(panel)
    elig = (
        uv.eligibility(pool, 20, 40, 168)
        .reindex(index=panel["opens"].index, columns=panel["cols"])
        .fillna(False)
    )
    trend = _norm(sig["trend"].where(elig).fillna(0.0))
    xs, _ = _xsmom(panel["close"], elig, 84)
    xs = _norm(xs)

    def run(sigp, **kw):
        return e2.run_book_from_signal(
            pool, sigp, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=e2.default_slip_bps, **kw
        )

    anc = e2.run_book(pool, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=e2.default_slip_bps)
    line("anchor (8h, trend+carry λ)", anc, show_oos=True)
    anc_e, anc_l = era(anc["net"])

    for name, base_sig in (("xs-mom", xs), ("trend", trend)):
        print(f"\n[{name}] rebalance-frequency sweep")
        for freq, lbl in ((None, "8h (per-candle)"), ("W", "weekly"), ("M", "monthly")):
            s = resample_signal(base_sig, freq)
            line(f"{name} {lbl}", run(s), show_oos=True)
        # cost robustness of the LOW-frequency versions (the point: cheaper => survives stress)
        for freq, lbl in (("W", "weekly"), ("M", "monthly")):
            s = resample_signal(base_sig, freq)
            line(f"{name} {lbl} 2x-taker", run(s, cost_mult=2.0), show_oos=True)
            line(
                f"{name} {lbl} pessimistic",
                e2.run_book_from_signal(
                    pool, s, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=slip_pessimistic
                ),
                show_oos=True,
            )

    print("\n[gate read — IS + LATE only; anchor LATE +1.16, turn 0.297]")
    print("  Looking for: a low-turnover config whose LATE Sharpe >= anchor +1.16 AND survives 2x-taker.")


if __name__ == "__main__":
    main()
